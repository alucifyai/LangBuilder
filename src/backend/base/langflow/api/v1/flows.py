from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

import orjson
from aiofile import async_open
from anyio import Path
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlmodel import and_, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession, cascade_delete_flow, remove_api_keys, validate_is_component
from langflow.api.v1.schemas import FlowListCreate
from langflow.helpers.user import get_user_by_flow_id_or_endpoint_name
from langflow.initial_setup.constants import STARTER_FOLDER_NAME
from langflow.logging import logger
from langflow.services.database.models.flow.model import (
    AccessTypeEnum,
    Flow,
    FlowCreate,
    FlowHeader,
    FlowRead,
    FlowUpdate,
)
from langflow.services.database.models.flow.utils import get_webhook_component_in_flow
from langflow.services.database.models.folder.constants import DEFAULT_FOLDER_NAME
from langflow.services.database.models.folder.model import Folder
from langflow.services.deps import get_settings_service
from langflow.services.rbac.audit import log_audit_event_safe
from langflow.services.rbac.dependencies import (
    require_delete,
    require_export,
    require_read,
    require_update,
)
from langflow.utils.compression import compress_response

# build router
router = APIRouter(prefix="/flows", tags=["Flows"])


async def _verify_fs_path(path: str | None) -> None:
    if path:
        path_ = Path(path)
        if not await path_.exists():
            await path_.touch()


async def _save_flow_to_fs(flow: Flow) -> None:
    if flow.fs_path:
        async with async_open(flow.fs_path, "w") as f:
            try:
                await f.write(flow.model_dump_json())
            except OSError:
                logger.exception("Failed to write flow %s to path %s", flow.name, flow.fs_path)


async def _new_flow(
    *,
    session: AsyncSession,
    flow: FlowCreate,
    user_id: UUID,
):
    try:
        await _verify_fs_path(flow.fs_path)

        """Create a new flow."""
        if flow.user_id is None:
            flow.user_id = user_id

        # First check if the flow.name is unique
        # there might be flows with name like: "MyFlow", "MyFlow (1)", "MyFlow (2)"
        # so we need to check if the name is unique with `like` operator
        # if we find a flow with the same name, we add a number to the end of the name
        # based on the highest number found
        if (await session.exec(select(Flow).where(Flow.name == flow.name).where(Flow.user_id == user_id))).first():
            flows = (
                await session.exec(
                    select(Flow).where(Flow.name.like(f"{flow.name} (%")).where(Flow.user_id == user_id)  # type: ignore[attr-defined]
                )
            ).all()
            if flows:
                # Use regex to extract numbers only from flows that follow the copy naming pattern:
                # "{original_name} ({number})"
                # This avoids extracting numbers from the original flow name if it naturally contains parentheses
                #
                # Examples:
                # - For flow "My Flow": matches "My Flow (1)", "My Flow (2)" → extracts 1, 2
                # - For flow "Analytics (Q1)": matches "Analytics (Q1) (1)" → extracts 1
                #   but does NOT match "Analytics (Q1)" → avoids extracting the original "1"
                extract_number = re.compile(rf"^{re.escape(flow.name)} \((\d+)\)$")
                numbers = []
                for _flow in flows:
                    result = extract_number.search(_flow.name)
                    if result:
                        numbers.append(int(result.groups(1)[0]))
                if numbers:
                    flow.name = f"{flow.name} ({max(numbers) + 1})"
                else:
                    flow.name = f"{flow.name} (1)"
            else:
                flow.name = f"{flow.name} (1)"
        # Now check if the endpoint is unique
        if (
            flow.endpoint_name
            and (
                await session.exec(
                    select(Flow).where(Flow.endpoint_name == flow.endpoint_name).where(Flow.user_id == user_id)
                )
            ).first()
        ):
            flows = (
                await session.exec(
                    select(Flow)
                    .where(Flow.endpoint_name.like(f"{flow.endpoint_name}-%"))  # type: ignore[union-attr]
                    .where(Flow.user_id == user_id)
                )
            ).all()
            if flows:
                # The endpoint name is like "my-endpoint","my-endpoint-1", "my-endpoint-2"
                # so we need to get the highest number and add 1
                # we need to get the last part of the endpoint name
                numbers = [int(flow.endpoint_name.split("-")[-1]) for flow in flows]
                flow.endpoint_name = f"{flow.endpoint_name}-{max(numbers) + 1}"
            else:
                flow.endpoint_name = f"{flow.endpoint_name}-1"

        db_flow = Flow.model_validate(flow, from_attributes=True)
        db_flow.updated_at = datetime.now(timezone.utc)

        if db_flow.folder_id is None:
            # Make sure flows always have a folder
            default_folder = (
                await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == user_id))
            ).first()
            if default_folder:
                db_flow.folder_id = default_folder.id

        session.add(db_flow)
    except Exception as e:
        # If it is a validation error, return the error message
        if hasattr(e, "errors"):
            raise HTTPException(status_code=400, detail=str(e)) from e
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e)) from e

    return db_flow


@router.post("/", response_model=FlowRead, status_code=201)
async def create_flow(
    *,
    session: DbSession,
    flow: FlowCreate,
    current_user: CurrentActiveUser,
):
    """Create a new flow.

    Requires flow.create permission in the workspace/project context.
    If folder_id is provided, checks project.create permission on that folder.
    Otherwise checks general flow.create permission at user scope.
    Creates audit log entry on success.
    """
    # RBAC check: For create operations, check permission on parent folder if provided
    from langflow.services.rbac.enforcement import RBACEnforcementEngine

    engine = RBACEnforcementEngine(session=session)

    # Determine the target folder for permission check
    target_folder_id = flow.folder_id
    if not target_folder_id:
        # Get default folder for user
        default_folder = (
            await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == current_user.id))
        ).first()
        if default_folder:
            target_folder_id = default_folder.id

    # Check permission on the parent folder/project
    if target_folder_id:
        has_perm = await engine.has_permission(
            user_id=current_user.id,
            permission="project.create",
            resource_type="project",
            resource_id=target_folder_id,
        )
        if not has_perm:
            await log_audit_event_safe(
                session=session,
                actor_id=current_user.id,
                action="flow.create_denied",
                resource_type="flow",
                resource_id=None,
                status="denied",
                details={"folder_id": str(target_folder_id), "reason": "insufficient_permissions"},
            )
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions: You do not have 'project.create' permission on this project",
            )

    try:
        db_flow = await _new_flow(session=session, flow=flow, user_id=current_user.id)
        await session.commit()
        await session.refresh(db_flow)

        await _save_flow_to_fs(db_flow)

        # Audit log
        await log_audit_event_safe(
            session=session,
            actor_id=current_user.id,
            action="flow.created",
            resource_type="flow",
            resource_id=db_flow.id,
            details={"name": db_flow.name, "folder_id": str(db_flow.folder_id) if db_flow.folder_id else None},
        )

    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            # Get the name of the column that failed
            columns = str(e).split("UNIQUE constraint failed: ")[1].split(".")[1].split("\n")[0]
            # UNIQUE constraint failed: flow.user_id, flow.name
            # or UNIQUE constraint failed: flow.name
            # if the column has id in it, we want the other column
            column = columns.split(",")[1] if "id" in columns.split(",")[0] else columns.split(",")[0]

            raise HTTPException(
                status_code=400, detail=f"{column.capitalize().replace('_', ' ')} must be unique"
            ) from e
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e)) from e
    return db_flow


@router.get("/", response_model=list[FlowRead] | Page[FlowRead] | list[FlowHeader], status_code=200)
async def read_flows(
    *,
    current_user: CurrentActiveUser,
    session: DbSession,
    remove_example_flows: bool = False,
    components_only: bool = False,
    get_all: bool = True,
    folder_id: UUID | None = None,
    params: Annotated[Params, Depends()],
    header_flows: bool = False,
):
    """Retrieve a list of flows with pagination support.

    Args:
        current_user (User): The current authenticated user.
        session (Session): The database session.
        settings_service (SettingsService): The settings service.
        components_only (bool, optional): Whether to return only components. Defaults to False.

        get_all (bool, optional): Whether to return all flows without pagination. Defaults to True.
        **This field must be True because of backward compatibility with the frontend - Release: 1.0.20**

        folder_id (UUID, optional): The project ID. Defaults to None.
        params (Params): Pagination parameters.
        remove_example_flows (bool, optional): Whether to remove example flows. Defaults to False.
        header_flows (bool, optional): Whether to return only specific headers of the flows. Defaults to False.

    Returns:
        list[FlowRead] | Page[FlowRead] | list[FlowHeader]
        A list of flows or a paginated response containing the list of flows or a list of flow headers.
    """
    try:
        auth_settings = get_settings_service().auth_settings

        default_folder = (await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME))).first()
        default_folder_id = default_folder.id if default_folder else None

        starter_folder = (await session.exec(select(Folder).where(Folder.name == STARTER_FOLDER_NAME))).first()
        starter_folder_id = starter_folder.id if starter_folder else None

        if not starter_folder and not default_folder:
            raise HTTPException(
                status_code=404,
                detail="Starter project and default project not found. Please create a project and add flows to it.",
            )

        if not folder_id:
            folder_id = default_folder_id

        if auth_settings.AUTO_LOGIN:
            stmt = select(Flow).where(
                (Flow.user_id == None) | (Flow.user_id == current_user.id)  # noqa: E711
            )
        else:
            stmt = select(Flow).where(Flow.user_id == current_user.id)

        if remove_example_flows:
            stmt = stmt.where(Flow.folder_id != starter_folder_id)

        if components_only:
            stmt = stmt.where(Flow.is_component == True)  # noqa: E712

        if get_all:
            flows = (await session.exec(stmt)).all()
            flows = validate_is_component(flows)
            if components_only:
                flows = [flow for flow in flows if flow.is_component]
            if remove_example_flows and starter_folder_id:
                flows = [flow for flow in flows if flow.folder_id != starter_folder_id]
            if header_flows:
                # Convert to FlowHeader objects and compress the response
                flow_headers = [FlowHeader.model_validate(flow, from_attributes=True) for flow in flows]
                return compress_response(flow_headers)

            # Compress the full flows response
            return compress_response(flows)

        stmt = stmt.where(Flow.folder_id == folder_id)

        import warnings

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=DeprecationWarning, module=r"fastapi_pagination\.ext\.sqlalchemy"
            )
            return await apaginate(session, stmt, params=params)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _read_flow(
    session: AsyncSession,
    flow_id: UUID,
    user_id: UUID,
):
    """Read a flow."""
    stmt = select(Flow).where(Flow.id == flow_id).where(Flow.user_id == user_id)

    return (await session.exec(stmt)).first()


@router.get("/{flow_id}", response_model=FlowRead, status_code=200)
async def read_flow(
    *,
    session: DbSession,
    flow_id: UUID,
    current_user: CurrentActiveUser,
    _: None = Depends(require_read("flow", "flow_id")),
):
    """Read a flow.

    Requires flow.read permission on the specified flow.
    """
    if user_flow := await _read_flow(session, flow_id, current_user.id):
        # Audit log
        await log_audit_event_safe(
            session=session,
            actor_id=current_user.id,
            action="flow.read",
            resource_type="flow",
            resource_id=flow_id,
            details={"name": user_flow.name},
        )
        return user_flow
    raise HTTPException(status_code=404, detail="Flow not found")


@router.get("/public_flow/{flow_id}", response_model=FlowRead, status_code=200)
async def read_public_flow(
    *,
    session: DbSession,
    flow_id: UUID,
):
    """Read a public flow."""
    access_type = (await session.exec(select(Flow.access_type).where(Flow.id == flow_id))).first()
    if access_type is not AccessTypeEnum.PUBLIC:
        raise HTTPException(status_code=403, detail="Flow is not public")

    current_user = await get_user_by_flow_id_or_endpoint_name(str(flow_id))
    return await read_flow(session=session, flow_id=flow_id, current_user=current_user)


@router.patch("/{flow_id}", response_model=FlowRead, status_code=200)
async def update_flow(
    *,
    session: DbSession,
    flow_id: UUID,
    flow: FlowUpdate,
    current_user: CurrentActiveUser,
    _: None = Depends(require_update("flow", "flow_id")),
):
    """Update a flow.

    Requires flow.update permission on the specified flow.
    Creates audit log entry on success.
    """
    settings_service = get_settings_service()
    try:
        db_flow = await _read_flow(
            session=session,
            flow_id=flow_id,
            user_id=current_user.id,
        )

        if not db_flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        update_data = flow.model_dump(exclude_unset=True, exclude_none=True)

        # Specifically handle endpoint_name when it's explicitly set to null or empty string
        if flow.endpoint_name is None or flow.endpoint_name == "":
            update_data["endpoint_name"] = None

        if settings_service.settings.remove_api_keys:
            update_data = remove_api_keys(update_data)

        for key, value in update_data.items():
            setattr(db_flow, key, value)

        await _verify_fs_path(db_flow.fs_path)

        webhook_component = get_webhook_component_in_flow(db_flow.data)
        db_flow.webhook = webhook_component is not None
        db_flow.updated_at = datetime.now(timezone.utc)

        if db_flow.folder_id is None:
            default_folder = (await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME))).first()
            if default_folder:
                db_flow.folder_id = default_folder.id

        session.add(db_flow)
        await session.commit()
        await session.refresh(db_flow)

        await _save_flow_to_fs(db_flow)

        # Audit log
        await log_audit_event_safe(
            session=session,
            actor_id=current_user.id,
            action="flow.updated",
            resource_type="flow",
            resource_id=flow_id,
            details={"name": db_flow.name, "updated_fields": list(update_data.keys())},
        )

    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            # Get the name of the column that failed
            columns = str(e).split("UNIQUE constraint failed: ")[1].split(".")[1].split("\n")[0]
            # UNIQUE constraint failed: flow.user_id, flow.name
            # or UNIQUE constraint failed: flow.name
            # if the column has id in it, we want the other column
            column = columns.split(",")[1] if "id" in columns.split(",")[0] else columns.split(",")[0]
            raise HTTPException(
                status_code=400, detail=f"{column.capitalize().replace('_', ' ')} must be unique"
            ) from e

        if hasattr(e, "status_code"):
            raise HTTPException(status_code=e.status_code, detail=str(e)) from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    return db_flow


@router.delete("/{flow_id}", status_code=200)
async def delete_flow(
    *,
    session: DbSession,
    flow_id: UUID,
    current_user: CurrentActiveUser,
    _: None = Depends(require_delete("flow", "flow_id")),
):
    """Delete a flow.

    Requires flow.delete permission on the specified flow.
    Creates audit log entry on success.
    """
    flow = await _read_flow(
        session=session,
        flow_id=flow_id,
        user_id=current_user.id,
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    flow_name = flow.name  # Save name for audit log before deletion

    await cascade_delete_flow(session, flow.id)
    await session.commit()

    # Audit log
    await log_audit_event_safe(
        session=session,
        actor_id=current_user.id,
        action="flow.deleted",
        resource_type="flow",
        resource_id=flow_id,
        details={"name": flow_name},
    )

    return {"message": "Flow deleted successfully"}


@router.post("/{flow_id}/export", response_model=dict, status_code=200)
async def export_flow(
    *,
    session: DbSession,
    flow_id: UUID,
    current_user: CurrentActiveUser,
    _: None = Depends(require_export("flow", "flow_id")),
):
    """Export flow as JSON (PRD Story 1.1 @AC3).

    Requires flow.export permission on the specified flow.
    Creates audit log entry on success.

    Returns:
        dict: Exported flow data including id, name, data, description, and exported_at timestamp
    """
    flow = await _read_flow(
        session=session,
        flow_id=flow_id,
        user_id=current_user.id,
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Export logic - serialize flow data
    exported_data = {
        "id": str(flow.id),
        "name": flow.name,
        "data": flow.data,
        "description": flow.description,
        "endpoint_name": flow.endpoint_name,
        "is_component": flow.is_component,
        "folder_id": str(flow.folder_id) if flow.folder_id else None,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    # Remove API keys for security
    exported_data = remove_api_keys(exported_data)

    # Audit log
    await log_audit_event_safe(
        session=session,
        actor_id=current_user.id,
        action="flow.exported",
        resource_type="flow",
        resource_id=flow_id,
        details={"name": flow.name},
    )

    return exported_data


@router.post("/batch/", response_model=list[FlowRead], status_code=201)
async def create_flows(
    *,
    session: DbSession,
    flow_list: FlowListCreate,
    current_user: CurrentActiveUser,
):
    """Create multiple new flows.

    Requires project.create permission on each flow's parent folder.
    Creates audit log entries on success.
    """
    from langflow.services.rbac.enforcement import RBACEnforcementEngine

    engine = RBACEnforcementEngine(session=session)

    # Check RBAC permissions for each flow's parent folder
    for flow in flow_list.flows:
        flow.user_id = current_user.id

        # Determine target folder
        target_folder_id = flow.folder_id
        if not target_folder_id:
            default_folder = (
                await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == current_user.id))
            ).first()
            if default_folder:
                target_folder_id = default_folder.id

        # Check permission on parent folder
        if target_folder_id:
            has_perm = await engine.has_permission(
                user_id=current_user.id,
                permission="project.create",
                resource_type="project",
                resource_id=target_folder_id,
            )
            if not has_perm:
                await log_audit_event_safe(
                    session=session,
                    actor_id=current_user.id,
                    action="flow.batch_create_denied",
                    resource_type="flow",
                    resource_id=None,
                    status="denied",
                    details={"folder_id": str(target_folder_id), "flow_name": flow.name, "reason": "insufficient_permissions"},
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions: You do not have 'project.create' permission on project {target_folder_id} for flow '{flow.name}'",
                )

    db_flows = []
    for flow in flow_list.flows:
        db_flow = Flow.model_validate(flow, from_attributes=True)
        session.add(db_flow)
        db_flows.append(db_flow)

    await session.commit()

    for db_flow in db_flows:
        await session.refresh(db_flow)
        # Audit log for each created flow
        await log_audit_event_safe(
            session=session,
            actor_id=current_user.id,
            action="flow.batch_created",
            resource_type="flow",
            resource_id=db_flow.id,
            details={"name": db_flow.name, "folder_id": str(db_flow.folder_id) if db_flow.folder_id else None},
        )

    return db_flows


@router.post("/upload/", response_model=list[FlowRead], status_code=201)
async def upload_file(
    *,
    session: DbSession,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentActiveUser,
    folder_id: UUID | None = None,
):
    """Upload flows from a file.

    Requires project.create permission on the target folder for each flow.
    Creates audit log entries on success.
    """
    from langflow.services.rbac.enforcement import RBACEnforcementEngine

    contents = await file.read()
    data = orjson.loads(contents)
    flow_list = FlowListCreate(**data) if "flows" in data else FlowListCreate(flows=[FlowCreate(**data)])

    engine = RBACEnforcementEngine(session=session)

    # Check RBAC permissions for each flow before uploading
    for flow in flow_list.flows:
        flow.user_id = current_user.id
        if folder_id:
            flow.folder_id = folder_id

        # Determine target folder
        target_folder_id = flow.folder_id
        if not target_folder_id:
            default_folder = (
                await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == current_user.id))
            ).first()
            if default_folder:
                target_folder_id = default_folder.id

        # Check permission on parent folder
        if target_folder_id:
            has_perm = await engine.has_permission(
                user_id=current_user.id,
                permission="project.create",
                resource_type="project",
                resource_id=target_folder_id,
            )
            if not has_perm:
                await log_audit_event_safe(
                    session=session,
                    actor_id=current_user.id,
                    action="flow.upload_denied",
                    resource_type="flow",
                    resource_id=None,
                    status="denied",
                    details={
                        "folder_id": str(target_folder_id),
                        "flow_name": flow.name,
                        "filename": file.filename,
                        "reason": "insufficient_permissions",
                    },
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions: You do not have 'project.create' permission on project {target_folder_id} for flow '{flow.name}'",
                )

    # Now create the flows
    response_list = []
    for flow in flow_list.flows:
        response = await _new_flow(session=session, flow=flow, user_id=current_user.id)
        response_list.append(response)

    try:
        await session.commit()
        for db_flow in response_list:
            await session.refresh(db_flow)
            await _save_flow_to_fs(db_flow)
            # Audit log for each uploaded flow
            await log_audit_event_safe(
                session=session,
                actor_id=current_user.id,
                action="flow.uploaded",
                resource_type="flow",
                resource_id=db_flow.id,
                details={
                    "name": db_flow.name,
                    "folder_id": str(db_flow.folder_id) if db_flow.folder_id else None,
                    "filename": file.filename,
                },
            )
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            # Get the name of the column that failed
            columns = str(e).split("UNIQUE constraint failed: ")[1].split(".")[1].split("\n")[0]
            # UNIQUE constraint failed: flow.user_id, flow.name
            # or UNIQUE constraint failed: flow.name
            # if the column has id in it, we want the other column
            column = columns.split(",")[1] if "id" in columns.split(",")[0] else columns.split(",")[0]

            raise HTTPException(
                status_code=400, detail=f"{column.capitalize().replace('_', ' ')} must be unique"
            ) from e
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(e)) from e

    return response_list


@router.delete("/")
async def delete_multiple_flows(
    flow_ids: list[UUID],
    user: CurrentActiveUser,
    db: DbSession,
):
    """Delete multiple flows by their IDs.

    Requires flow.delete permission on each flow.
    Creates audit log entries on success.

    Args:
        flow_ids (List[str]): The list of flow IDs to delete.
        user (User, optional): The user making the request. Defaults to the current active user.
        db (Session, optional): The database session.

    Returns:
        dict: A dictionary containing the number of flows deleted.

    """
    from langflow.services.rbac.enforcement import RBACEnforcementEngine

    try:
        flows_to_delete = (
            await db.exec(select(Flow).where(col(Flow.id).in_(flow_ids)).where(Flow.user_id == user.id))
        ).all()

        # Check RBAC permissions for each flow before deleting
        engine = RBACEnforcementEngine(session=db)
        for flow in flows_to_delete:
            has_perm = await engine.has_permission(
                user_id=user.id,
                permission="flow.delete",
                resource_type="flow",
                resource_id=flow.id,
            )
            if not has_perm:
                await log_audit_event_safe(
                    session=db,
                    actor_id=user.id,
                    action="flow.batch_delete_denied",
                    resource_type="flow",
                    resource_id=flow.id,
                    status="denied",
                    details={"name": flow.name, "reason": "insufficient_permissions"},
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions: You do not have 'flow.delete' permission on flow '{flow.name}' (ID: {flow.id})",
                )

        # Delete flows
        flow_names = [(flow.id, flow.name) for flow in flows_to_delete]  # Save for audit logging
        for flow in flows_to_delete:
            await cascade_delete_flow(db, flow.id)

        await db.commit()

        # Audit log for each deleted flow
        for flow_id, flow_name in flow_names:
            await log_audit_event_safe(
                session=db,
                actor_id=user.id,
                action="flow.batch_deleted",
                resource_type="flow",
                resource_id=flow_id,
                details={"name": flow_name},
            )

        return {"deleted": len(flows_to_delete)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/download/", status_code=200)
async def download_multiple_file(
    flow_ids: list[UUID],
    user: CurrentActiveUser,
    db: DbSession,
):
    """Download all flows as a zip file.

    Requires flow.export permission on each flow.
    Creates audit log entries on success.
    """
    from langflow.services.rbac.enforcement import RBACEnforcementEngine

    flows = (await db.exec(select(Flow).where(and_(Flow.user_id == user.id, Flow.id.in_(flow_ids))))).all()  # type: ignore[attr-defined]

    if not flows:
        raise HTTPException(status_code=404, detail="No flows found.")

    # Check RBAC permissions for each flow before downloading
    engine = RBACEnforcementEngine(session=db)
    for flow in flows:
        has_perm = await engine.has_permission(
            user_id=user.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow.id,
        )
        if not has_perm:
            await log_audit_event_safe(
                session=db,
                actor_id=user.id,
                action="flow.download_denied",
                resource_type="flow",
                resource_id=flow.id,
                status="denied",
                details={"name": flow.name, "reason": "insufficient_permissions"},
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions: You do not have 'flow.export' permission on flow '{flow.name}' (ID: {flow.id})",
            )

    flows_without_api_keys = [remove_api_keys(flow.model_dump()) for flow in flows]

    # Audit log for each downloaded flow (before streaming)
    for flow in flows:
        await log_audit_event_safe(
            session=db,
            actor_id=user.id,
            action="flow.downloaded",
            resource_type="flow",
            resource_id=flow.id,
            details={"name": flow.name, "count": len(flows)},
        )

    if len(flows_without_api_keys) > 1:
        # Create a byte stream to hold the ZIP file
        zip_stream = io.BytesIO()

        # Create a ZIP file
        with zipfile.ZipFile(zip_stream, "w") as zip_file:
            for flow in flows_without_api_keys:
                # Convert the flow object to JSON
                flow_json = json.dumps(jsonable_encoder(flow))

                # Write the JSON to the ZIP file
                zip_file.writestr(f"{flow['name']}.json", flow_json)

        # Seek to the beginning of the byte stream
        zip_stream.seek(0)

        # Generate the filename with the current datetime
        current_time = datetime.now(tz=timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_time}_langflow_flows.zip"

        return StreamingResponse(
            zip_stream,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    return flows_without_api_keys[0]


all_starter_folder_flows_response: Response | None = None


@router.get("/basic_examples/", response_model=list[FlowRead], status_code=200)
async def read_basic_examples(
    *,
    session: DbSession,
):
    """Retrieve a list of basic example flows.

    Args:
        session (Session): The database session.

    Returns:
        list[FlowRead]: A list of basic example flows.
    """
    try:
        global all_starter_folder_flows_response  # noqa: PLW0603

        if all_starter_folder_flows_response:
            return all_starter_folder_flows_response
        # Get the starter folder
        starter_folder = (await session.exec(select(Folder).where(Folder.name == STARTER_FOLDER_NAME))).first()

        if not starter_folder:
            return []

        # Get all flows in the starter folder
        all_starter_folder_flows = (await session.exec(select(Flow).where(Flow.folder_id == starter_folder.id))).all()

        flow_reads = [FlowRead.model_validate(flow, from_attributes=True) for flow in all_starter_folder_flows]
        all_starter_folder_flows_response = compress_response(flow_reads)

        # Return compressed response using our utility function
        return all_starter_folder_flows_response  # noqa: TRY300

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

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

from langbuilder.api.utils import CurrentActiveUser, DbSession, cascade_delete_flow, remove_api_keys, validate_is_component
from langbuilder.api.v1.rbac import get_rbac_service
from langbuilder.api.v1.schemas import FlowListCreate
from langbuilder.helpers.user import get_user_by_flow_id_or_endpoint_name
from langbuilder.initial_setup.constants import STARTER_FOLDER_NAME
from langbuilder.logging import logger
from langbuilder.services.database.models.flow.model import (
    AccessTypeEnum,
    Flow,
    FlowCreate,
    FlowHeader,
    FlowRead,
    FlowUpdate,
)
from langbuilder.services.database.models.flow.utils import get_webhook_component_in_flow
from langbuilder.services.database.models.folder.constants import DEFAULT_FOLDER_NAME
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.deps import get_settings_service
from langbuilder.services.rbac.service import RBACService
from langbuilder.utils.compression import compress_response

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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Create a new flow with Create permission check.

    Task 3.2: Enforces Create permission on the parent project (folder) before allowing flow creation.
    Users must have Create permission on the target project to create flows within it.
    """
    try:
        # Task 3.2: Check Create permission on parent project scope
        # Determine the target folder/project for permission check
        target_folder_id = flow.folder_id
        if target_folder_id is None:
            # If no folder specified, get the default folder
            default_folder = (
                await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == current_user.id))
            ).first()
            if default_folder:
                target_folder_id = default_folder.id
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Default project not found. Please create a project first."
                )

        # Check Create permission on the target project
        can_create = await rbac_service.can_access(
            user_id=current_user.id,
            permission_name="Create",
            scope_type="Project",
            scope_id=target_folder_id,
        )

        if not can_create:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to create flows in this project"
            )

        db_flow = await _new_flow(session=session, flow=flow, user_id=current_user.id)
        await session.flush()

        # Assign Owner role to creator (Task 2.3: Default Role Assignments)
        # Query for the Owner role
        from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
        from langbuilder.services.database.models.folder.constants import is_starter_project
        owner_role_stmt = select(Role).where(Role.name == "Owner")
        owner_role_result = await session.exec(owner_role_stmt)
        owner_role = owner_role_result.first()

        if owner_role:
            # Determine if this flow is in the user's Starter Project folder
            # Only mark as immutable if it's the user's own Starter Project
            is_immutable_assignment = False
            if db_flow.folder_id:
                folder = (await session.exec(
                    select(Folder).where(Folder.id == db_flow.folder_id)
                )).first()
                if folder and is_starter_project(folder.name) and folder.user_id == current_user.id:
                    is_immutable_assignment = True

            # Create role assignment for the flow creator
            assignment = UserRoleAssignment(
                user_id=current_user.id,
                role_id=owner_role.id,
                scope_type="Flow",
                scope_id=db_flow.id,
                is_immutable=is_immutable_assignment,
                created_by=current_user.id,
            )
            session.add(assignment)
        else:
            logger.warning(f"Owner role not found when creating flow {db_flow.id}")

        await session.commit()
        await session.refresh(db_flow)

        await _save_flow_to_fs(db_flow)

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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
    remove_example_flows: bool = False,
    components_only: bool = False,
    get_all: bool = True,
    folder_id: UUID | None = None,
    params: Annotated[Params, Depends()],
    header_flows: bool = False,
):
    """Retrieve a list of flows with pagination support.

    Task 3.1: Now filters flows by Read permission using RBACService.
    Only returns flows that the user has Read permission to access.

    Args:
        current_user (User): The current authenticated user.
        session (Session): The database session.
        rbac_service (RBACService): The RBAC service for permission checks.
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

        # Get all flows (no user_id pre-filter - rely on RBAC)
        stmt = select(Flow)

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

            # Task 3.1: Filter flows by Read permission
            # Check each flow for Read permission and only return accessible flows
            readable_flows = []
            for flow in flows:
                try:
                    can_read = await rbac_service.can_access(
                        user_id=current_user.id,
                        permission_name="Read",
                        scope_type="Flow",
                        scope_id=flow.id,
                    )
                    if can_read:
                        readable_flows.append(flow)
                except Exception as e:
                    # Log error but don't fail entire request
                    logger.warning(f"Error checking Read permission for flow {flow.id}: {e}")
                    # Skip this flow (fail closed)
                    continue

            flows = readable_flows

            if header_flows:
                # Convert to FlowHeader objects and compress the response
                flow_headers = [FlowHeader.model_validate(flow, from_attributes=True) for flow in flows]
                return compress_response(flow_headers)

            # Compress the full flows response
            return compress_response(flows)

        stmt = stmt.where(Flow.folder_id == folder_id)

        # Task 3.1: For paginated results, we need to filter by permission after fetching
        # Get all flows for this folder first
        flows_in_folder = (await session.exec(stmt)).all()

        # Filter by Read permission
        readable_flows = []
        for flow in flows_in_folder:
            try:
                can_read = await rbac_service.can_access(
                    user_id=current_user.id,
                    permission_name="Read",
                    scope_type="Flow",
                    scope_id=flow.id,
                )
                if can_read:
                    readable_flows.append(flow)
            except Exception as e:
                logger.warning(f"Error checking Read permission for flow {flow.id}: {e}")
                continue

        # For pagination, we need to manually handle it since we filtered after query
        # This is a simplified approach for MVP
        start_idx = (params.page - 1) * params.size
        end_idx = start_idx + params.size
        paginated_flows = readable_flows[start_idx:end_idx]

        # Create a Page response manually
        from fastapi_pagination import Page as PageResponse

        return PageResponse(
            items=paginated_flows,
            total=len(readable_flows),
            page=params.page,
            size=params.size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _read_flow(
    session: AsyncSession,
    flow_id: UUID,
    user_id: UUID,
):
    """Read a flow with user_id filtering (pre-RBAC).

    Use this function for endpoints without RBAC permission checks.
    Filters by user_id for basic ownership-based access control.
    """
    stmt = select(Flow).where(Flow.id == flow_id).where(Flow.user_id == user_id)

    return (await session.exec(stmt)).first()


async def _read_flow_by_id(
    session: AsyncSession,
    flow_id: UUID,
):
    """Read a flow by ID only (post-RBAC permission check).

    Use this function after RBAC permission checks have passed.
    Does not filter by user_id, allowing RBAC-granted cross-user access.
    """
    stmt = select(Flow).where(Flow.id == flow_id)

    return (await session.exec(stmt)).first()


@router.get("/{flow_id}", response_model=FlowRead, status_code=200)
async def read_flow(
    *,
    session: DbSession,
    flow_id: UUID,
    current_user: CurrentActiveUser,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Read a flow by ID with Read permission check.

    Task 3.5: Enforces Read permission before returning flow details.
    Permission inheritance: Checks flow-specific permission first, then falls back to
    project-level permission if the flow belongs to a project the user has access to.
    """
    # Task 3.5: Check Read permission (with automatic project inheritance)
    can_read = await rbac_service.can_access(
        user_id=current_user.id,
        permission_name="Read",
        scope_type="Flow",
        scope_id=flow_id,
    )

    if not can_read:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to read this flow"
        )

    # After permission check passes, use _read_flow_by_id (allows RBAC-granted cross-user access)
    flow = await _read_flow_by_id(session=session, flow_id=flow_id)

    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    return flow


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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Update a flow with Update permission check.

    Task 3.3: Enforces Update permission before allowing flow modifications.
    Users must have Update permission on the flow to modify it.
    """
    settings_service = get_settings_service()
    try:
        # Task 3.3: Check Update permission before modifying flow
        can_update = await rbac_service.can_access(
            user_id=current_user.id,
            permission_name="Update",
            scope_type="Flow",
            scope_id=flow_id,
        )

        if not can_update:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this flow"
            )

        # Task 3.4 Fix: Use _read_flow_by_id after RBAC permission check
        # This allows RBAC-granted cross-user access (e.g., Admin updating another user's flow)
        db_flow = await _read_flow_by_id(
            session=session,
            flow_id=flow_id,
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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Delete a flow with Delete permission check.

    Task 3.4: Enforces Delete permission before allowing flow deletion.
    Users must have Delete permission on the flow to delete it.
    Only Admin and Owner roles have Delete permission per PRD.
    """
    # Task 3.4: Check Delete permission before deleting flow
    can_delete = await rbac_service.can_access(
        user_id=current_user.id,
        permission_name="Delete",
        scope_type="Flow",
        scope_id=flow_id,
    )

    if not can_delete:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this flow"
        )

    # Task 3.4 Fix: Use _read_flow_by_id after RBAC permission check
    # This allows RBAC-granted cross-user access (e.g., Admin deleting another user's flow)
    flow = await _read_flow_by_id(
        session=session,
        flow_id=flow_id,
    )
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    await cascade_delete_flow(session, flow.id)
    await session.commit()
    return {"message": "Flow deleted successfully"}


@router.post("/batch/", response_model=list[FlowRead], status_code=201)
async def create_flows(
    *,
    session: DbSession,
    flow_list: FlowListCreate,
    current_user: CurrentActiveUser,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Create multiple new flows with Create permission check.

    Task 3.2: Enforces Create permission on parent projects before allowing batch flow creation.
    Users must have Create permission on each target project.
    """
    # Task 3.2: Check Create permission for each flow's target project
    # Group flows by folder_id to minimize permission checks
    flows_by_folder = {}
    for flow in flow_list.flows:
        folder_id = flow.folder_id
        if folder_id is None:
            # Get default folder if not specified
            default_folder = (
                await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == current_user.id))
            ).first()
            if default_folder:
                folder_id = default_folder.id
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Default project not found. Please create a project first."
                )
            flow.folder_id = folder_id

        if folder_id not in flows_by_folder:
            flows_by_folder[folder_id] = []
        flows_by_folder[folder_id].append(flow)

    # Check Create permission for each unique folder
    for folder_id in flows_by_folder.keys():
        can_create = await rbac_service.can_access(
            user_id=current_user.id,
            permission_name="Create",
            scope_type="Project",
            scope_id=folder_id,
        )
        if not can_create:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have permission to create flows in project {folder_id}"
            )

    db_flows = []
    for flow in flow_list.flows:
        flow.user_id = current_user.id
        db_flow = Flow.model_validate(flow, from_attributes=True)
        session.add(db_flow)
        db_flows.append(db_flow)

    # Flush to get flow IDs before creating assignments
    await session.flush()

    # Assign Owner role to creator for each flow (Task 2.3: Default Role Assignments)
    from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role_result = await session.exec(owner_role_stmt)
    owner_role = owner_role_result.first()

    if owner_role:
        for db_flow in db_flows:
            assignment = UserRoleAssignment(
                user_id=current_user.id,
                role_id=owner_role.id,
                scope_type="Flow",
                scope_id=db_flow.id,
                is_immutable=False,
                created_by=current_user.id,
            )
            session.add(assignment)
    else:
        logger.warning("Owner role not found when creating batch flows")

    await session.commit()
    for db_flow in db_flows:
        await session.refresh(db_flow)
    return db_flows


@router.post("/upload/", response_model=list[FlowRead], status_code=201)
async def upload_file(
    *,
    session: DbSession,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentActiveUser,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
    folder_id: UUID | None = None,
):
    """Upload flows from a file with Create permission check.

    Task 3.2: Enforces Create permission on the target project before allowing flow upload.
    """
    contents = await file.read()
    data = orjson.loads(contents)
    response_list = []
    flow_list = FlowListCreate(**data) if "flows" in data else FlowListCreate(flows=[FlowCreate(**data)])

    # Task 3.2: Determine target folder and check Create permission
    target_folder_id = folder_id
    if target_folder_id is None:
        # Get default folder if not specified
        default_folder = (
            await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME, Folder.user_id == current_user.id))
        ).first()
        if default_folder:
            target_folder_id = default_folder.id
        else:
            raise HTTPException(
                status_code=500,
                detail="Default project not found. Please create a project first."
            )

    # Check Create permission on target folder
    can_create = await rbac_service.can_access(
        user_id=current_user.id,
        permission_name="Create",
        scope_type="Project",
        scope_id=target_folder_id,
    )
    if not can_create:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to create flows in this project"
        )

    # Now we set the user_id for all flows
    for flow in flow_list.flows:
        flow.user_id = current_user.id
        if folder_id:
            flow.folder_id = folder_id
        response = await _new_flow(session=session, flow=flow, user_id=current_user.id)
        response_list.append(response)

    try:
        # Flush to get flow IDs before creating assignments
        await session.flush()

        # Assign Owner role to creator for each uploaded flow (Task 2.3: Default Role Assignments)
        from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
        owner_role_stmt = select(Role).where(Role.name == "Owner")
        owner_role_result = await session.exec(owner_role_stmt)
        owner_role = owner_role_result.first()

        if owner_role:
            for db_flow in response_list:
                assignment = UserRoleAssignment(
                    user_id=current_user.id,
                    role_id=owner_role.id,
                    scope_type="Flow",
                    scope_id=db_flow.id,
                    is_immutable=False,
                    created_by=current_user.id,
                )
                session.add(assignment)
        else:
            logger.warning("Owner role not found when uploading flows")

        await session.commit()
        for db_flow in response_list:
            await session.refresh(db_flow)
            await _save_flow_to_fs(db_flow)
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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Delete multiple flows by their IDs with Delete permission check.

    Task 3.4: Enforces Delete permission before allowing batch flow deletion.
    Users must have Delete permission on each flow to delete it.
    Only Admin and Owner roles have Delete permission per PRD.

    Args:
        flow_ids (List[str]): The list of flow IDs to delete.
        user (User, optional): The user making the request. Defaults to the current active user.
        db (Session, optional): The database session.
        rbac_service (RBACService): The RBAC service for permission checks.

    Returns:
        dict: A dictionary containing the number of flows deleted.

    """
    try:
        # Task 3.4: Check Delete permission for each flow before deletion
        flows_to_delete = (
            await db.exec(select(Flow).where(col(Flow.id).in_(flow_ids)).where(Flow.user_id == user.id))
        ).all()

        # Filter flows by Delete permission
        authorized_flows = []
        for flow in flows_to_delete:
            try:
                can_delete = await rbac_service.can_access(
                    user_id=user.id,
                    permission_name="Delete",
                    scope_type="Flow",
                    scope_id=flow.id,
                )
                if can_delete:
                    authorized_flows.append(flow)
                else:
                    logger.warning(f"User {user.id} lacks Delete permission for flow {flow.id}")
            except Exception as e:
                # Log error but don't fail entire request
                logger.warning(f"Error checking Delete permission for flow {flow.id}: {e}")
                # Skip this flow (fail closed)
                continue

        # Delete authorized flows
        for flow in authorized_flows:
            await cascade_delete_flow(db, flow.id)

        await db.commit()
        return {"deleted": len(authorized_flows)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/download/", status_code=200)
async def download_multiple_file(
    flow_ids: list[UUID],
    user: CurrentActiveUser,
    db: DbSession,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Download all flows as a zip file with Read permission check.

    Task 3.5: Enforces Read permission before allowing flow download.
    Only flows with Read permission are included in the download.
    """
    # Task 3.5: Filter flows by Read permission
    # First get all flows (without user_id filter to allow RBAC cross-user access)
    flows = (await db.exec(select(Flow).where(Flow.id.in_(flow_ids)))).all()  # type: ignore[attr-defined]

    if not flows:
        raise HTTPException(status_code=404, detail="No flows found.")

    # Filter by Read permission
    readable_flows = []
    for flow in flows:
        try:
            can_read = await rbac_service.can_access(
                user_id=user.id,
                permission_name="Read",
                scope_type="Flow",
                scope_id=flow.id,
            )
            if can_read:
                readable_flows.append(flow)
        except Exception as e:
            logger.warning(f"Error checking Read permission for flow {flow.id}: {e}")
            continue

    if not readable_flows:
        raise HTTPException(status_code=404, detail="No flows found with Read permission.")

    flows_without_api_keys = [remove_api_keys(flow.model_dump()) for flow in readable_flows]

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
        filename = f"{current_time}_langbuilder_flows.zip"

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

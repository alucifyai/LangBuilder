# ruff: noqa: FAST002, E501
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Annotated
from urllib.parse import quote
from uuid import UUID

import orjson
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from sqlmodel import select

from langbuilder.api.utils import CurrentActiveUser, DbSession, cascade_delete_flow, custom_params, remove_api_keys
from langbuilder.api.v1.flows import create_flows
from langbuilder.api.v1.schemas import FlowListCreate
from langbuilder.helpers.flow import generate_unique_flow_name
from langbuilder.helpers.folders import generate_unique_folder_name
from langbuilder.initial_setup.constants import STARTER_FOLDER_NAME
from langbuilder.logging import logger
from langbuilder.services.database.models.flow.model import Flow, FlowCreate, FlowRead
from langbuilder.services.database.models.folder.constants import DEFAULT_FOLDER_NAME
from langbuilder.services.database.models.folder.model import (
    Folder,
    FolderCreate,
    FolderRead,
    FolderReadWithFlows,
    FolderUpdate,
)
from langbuilder.services.database.models.folder.pagination_model import FolderWithPaginatedFlows
from langbuilder.services.database.models.rbac.model import PermissionEnum, RoleEnum, ScopeTypeEnum
from langbuilder.services.deps import get_rbac_service
from langbuilder.services.rbac.service import RBACService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=FolderRead, status_code=201)
async def create_project(
    *,
    session: DbSession,
    project: FolderCreate,
    current_user: CurrentActiveUser,
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Create a new project with RBAC permission check.

    All authenticated users can create projects.
    Auto-assigns Owner role to the creator on the new project.
    For Default Project ("Starter Project"), the Owner assignment is immutable.
    """
    try:
        new_project = Folder.model_validate(project, from_attributes=True)
        new_project.user_id = current_user.id
        # First check if the project.name is unique
        # there might be flows with name like: "MyFlow", "MyFlow (1)", "MyFlow (2)"
        # so we need to check if the name is unique with `like` operator
        # if we find a flow with the same name, we add a number to the end of the name
        # based on the highest number found
        if (
            await session.exec(
                statement=select(Folder).where(Folder.name == new_project.name).where(Folder.user_id == current_user.id)
            )
        ).first():
            project_results = await session.exec(
                select(Folder).where(
                    Folder.name.like(f"{new_project.name}%"),  # type: ignore[attr-defined]
                    Folder.user_id == current_user.id,
                )
            )
            if project_results:
                project_names = [project.name for project in project_results]
                project_numbers = [int(name.split("(")[-1].split(")")[0]) for name in project_names if "(" in name]
                if project_numbers:
                    new_project.name = f"{new_project.name} ({max(project_numbers) + 1})"
                else:
                    new_project.name = f"{new_project.name} (1)"

        session.add(new_project)
        await session.commit()
        await session.refresh(new_project)

        # Auto-assign Owner role to creator
        # For Default Project ("Starter Project"), mark as immutable
        is_default_project = new_project.name == DEFAULT_FOLDER_NAME
        try:
            await rbac_service.assign_role(
                session=session,
                user_id=current_user.id,
                role_name=RoleEnum.OWNER,
                scope_type=ScopeTypeEnum.PROJECT,
                scope_id=new_project.id,
                is_immutable=is_default_project,
            )
            logger.info(
                f"Auto-assigned Owner role to user {current_user.id} for project {new_project.id} (immutable={is_default_project})"
            )
        except ValueError as ve:
            # If assignment already exists (shouldn't happen), log and continue
            logger.warning(f"Failed to auto-assign Owner role: {ve}")
        except Exception as assign_error:
            # Rollback project creation if role assignment fails
            logger.error(f"Failed to assign Owner role, rolling back project creation: {assign_error}")
            await session.delete(new_project)
            await session.commit()
            raise HTTPException(
                status_code=500, detail="Failed to assign ownership role for the new project"
            ) from assign_error

        if project.components_list:
            update_statement_components = (
                update(Flow).where(Flow.id.in_(project.components_list)).values(folder_id=new_project.id)  # type: ignore[attr-defined]
            )
            await session.exec(update_statement_components)
            await session.commit()

        if project.flows_list:
            update_statement_flows = (
                update(Flow).where(Flow.id.in_(project.flows_list)).values(folder_id=new_project.id)  # type: ignore[attr-defined]
            )
            await session.exec(update_statement_flows)
            await session.commit()

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return new_project


@router.get("/", response_model=list[FolderRead], status_code=200)
async def read_projects(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Retrieve a list of projects with RBAC filtering.

    Filters projects to only those the user has READ permission for.
    Uses get_accessible_scope_ids() for performance-optimized filtering.
    Excludes STARTER_FOLDER_NAME and sorts Default Project first.
    """
    try:
        # RBAC: Get all project IDs the user has READ permission for
        accessible_project_ids = await rbac_service.get_accessible_scope_ids(
            session=session,
            user_id=current_user.id,
            permission=PermissionEnum.READ,
            scope_type=ScopeTypeEnum.PROJECT,
        )

        if not accessible_project_ids:
            # User has no accessible projects, return empty list
            return []

        # Build query with RBAC filtering
        from sqlmodel import col

        projects = (await session.exec(select(Folder).where(col(Folder.id).in_(accessible_project_ids)))).all()

        # Filter out STARTER_FOLDER_NAME
        projects = [project for project in projects if project.name != STARTER_FOLDER_NAME]

        # Sort with DEFAULT_FOLDER_NAME first
        return sorted(projects, key=lambda x: x.name != DEFAULT_FOLDER_NAME)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{project_id}", response_model=FolderWithPaginatedFlows | FolderReadWithFlows, status_code=200)
async def read_project(
    *,
    session: DbSession,
    project_id: UUID,
    current_user: CurrentActiveUser,
    params: Annotated[Params | None, Depends(custom_params)],
    is_component: bool = False,
    is_flow: bool = False,
    search: str = "",
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Read a project with RBAC permission check.

    Requires READ permission on the project.
    Returns 404 if project not found OR user lacks permission (security best practice).
    """
    try:
        # First check if project exists (without user filter)
        project_stmt = select(Folder).options(selectinload(Folder.flows)).where(Folder.id == project_id)
        result = await session.exec(project_stmt)
        project = result.first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check READ permission
        has_permission = await rbac_service.can_access(
            session=session,
            user_id=current_user.id,
            permission=PermissionEnum.READ,
            scope_type=ScopeTypeEnum.PROJECT,
            scope_id=project_id,
        )

        if not has_permission:
            # Return 404 instead of 403 for security (don't reveal project exists)
            raise HTTPException(status_code=404, detail="Project not found")

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        if "No result found" in str(e):
            raise HTTPException(status_code=404, detail="Project not found") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    try:
        if params and params.page and params.size:
            stmt = select(Flow).where(Flow.folder_id == project_id)

            if Flow.updated_at is not None:
                stmt = stmt.order_by(Flow.updated_at.desc())  # type: ignore[attr-defined]
            if is_component:
                stmt = stmt.where(Flow.is_component == True)  # noqa: E712
            if is_flow:
                stmt = stmt.where(Flow.is_component == False)  # noqa: E712
            if search:
                stmt = stmt.where(Flow.name.like(f"%{search}%"))  # type: ignore[attr-defined]
            import warnings

            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", category=DeprecationWarning, module=r"fastapi_pagination\.ext\.sqlalchemy"
                )
                paginated_flows = await apaginate(session, stmt, params=params)

            return FolderWithPaginatedFlows(folder=FolderRead.model_validate(project), flows=paginated_flows)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    flows_from_current_user_in_project = [flow for flow in project.flows if flow.user_id == current_user.id]
    project.flows = flows_from_current_user_in_project
    return project


@router.patch("/{project_id}", response_model=FolderRead, status_code=200)
async def update_project(
    *,
    session: DbSession,
    project_id: UUID,
    project: FolderUpdate,  # Assuming FolderUpdate is a Pydantic model defining updatable fields
    current_user: CurrentActiveUser,
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Update a project with RBAC permission check.

    Requires UPDATE permission on the project.
    Returns 404 if project not found OR user lacks permission.
    """
    try:
        # First check if project exists
        project_stmt = select(Folder).where(Folder.id == project_id)
        result = await session.exec(project_stmt)
        existing_project = result.first()

        if not existing_project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check UPDATE permission
        has_permission = await rbac_service.can_access(
            session=session,
            user_id=current_user.id,
            permission=PermissionEnum.UPDATE,
            scope_type=ScopeTypeEnum.PROJECT,
            scope_id=project_id,
        )

        if not has_permission:
            # Return 404 instead of 403 for security
            raise HTTPException(status_code=404, detail="Project not found")

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    try:
        if project.name and project.name != existing_project.name:
            existing_project.name = project.name
            session.add(existing_project)
            await session.commit()
            await session.refresh(existing_project)
            return existing_project

        project_data = existing_project.model_dump(exclude_unset=True)
        for key, value in project_data.items():
            if key not in {"components", "flows"}:
                setattr(existing_project, key, value)
        session.add(existing_project)
        await session.commit()
        await session.refresh(existing_project)

        concat_project_components = project.components + project.flows

        flows_ids = (await session.exec(select(Flow.id).where(Flow.folder_id == existing_project.id))).all()

        excluded_flows = list(set(flows_ids) - set(concat_project_components))

        my_collection_project = (await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME))).first()
        if my_collection_project:
            update_statement_my_collection = (
                update(Flow).where(Flow.id.in_(excluded_flows)).values(folder_id=my_collection_project.id)  # type: ignore[attr-defined]
            )
            await session.exec(update_statement_my_collection)
            await session.commit()

        if concat_project_components:
            update_statement_components = (
                update(Flow).where(Flow.id.in_(concat_project_components)).values(folder_id=existing_project.id)  # type: ignore[attr-defined]
            )
            await session.exec(update_statement_components)
            await session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return existing_project


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    *,
    session: DbSession,
    project_id: UUID,
    current_user: CurrentActiveUser,
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Delete a project with RBAC permission check.

    Requires DELETE permission on the project.
    Returns 404 if project not found OR user lacks permission.
    Prevents deletion of Default Project ("Starter Project").
    """
    try:
        # First check if project exists
        project_stmt = select(Folder).where(Folder.id == project_id)
        result = await session.exec(project_stmt)
        project = result.first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check DELETE permission
        has_permission = await rbac_service.can_access(
            session=session,
            user_id=current_user.id,
            permission=PermissionEnum.DELETE,
            scope_type=ScopeTypeEnum.PROJECT,
            scope_id=project_id,
        )

        if not has_permission:
            # Return 404 instead of 403 for security
            raise HTTPException(status_code=404, detail="Project not found")

        # Prevent deletion of Default Project
        if project.name == DEFAULT_FOLDER_NAME:
            raise HTTPException(status_code=403, detail="Cannot delete the default project")

        # Delete all flows in the project
        flows = (await session.exec(select(Flow).where(Flow.folder_id == project_id))).all()
        if len(flows) > 0:
            for flow in flows:
                await cascade_delete_flow(session, flow.id)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    try:
        await session.delete(project)
        await session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/download/{project_id}", status_code=200)
async def download_file(
    *,
    session: DbSession,
    project_id: UUID,
    current_user: CurrentActiveUser,
    rbac_service: RBACService = Depends(get_rbac_service),
):
    """Download all flows from project as a zip file with RBAC permission check.

    Requires READ permission on the project.
    Returns 404 if project not found OR user lacks permission.
    """
    try:
        # First check if project exists
        query = select(Folder).where(Folder.id == project_id)
        result = await session.exec(query)
        project = result.first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check READ permission
        has_permission = await rbac_service.can_access(
            session=session,
            user_id=current_user.id,
            permission=PermissionEnum.READ,
            scope_type=ScopeTypeEnum.PROJECT,
            scope_id=project_id,
        )

        if not has_permission:
            # Return 404 instead of 403 for security
            raise HTTPException(status_code=404, detail="Project not found")

        flows_query = select(Flow).where(Flow.folder_id == project_id)
        flows_result = await session.exec(flows_query)
        flows = [FlowRead.model_validate(flow, from_attributes=True) for flow in flows_result.all()]

        if not flows:
            raise HTTPException(status_code=404, detail="No flows found in project")

        flows_without_api_keys = [remove_api_keys(flow.model_dump()) for flow in flows]
        zip_stream = io.BytesIO()

        with zipfile.ZipFile(zip_stream, "w") as zip_file:
            for flow in flows_without_api_keys:
                flow_json = json.dumps(jsonable_encoder(flow))
                zip_file.writestr(f"{flow['name']}.json", flow_json.encode("utf-8"))

        zip_stream.seek(0)

        current_time = datetime.now(tz=timezone.utc).astimezone().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_time}_{project.name}_flows.zip"

        # URL encode filename handle non-ASCII (ex. Cyrillic)
        encoded_filename = quote(filename)

        return StreamingResponse(
            zip_stream,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
        )

    except Exception as e:
        if "No result found" in str(e):
            raise HTTPException(status_code=404, detail="Project not found") from e
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/upload/", response_model=list[FlowRead], status_code=201)
async def upload_file(
    *,
    session: DbSession,
    file: Annotated[UploadFile, File(...)],
    current_user: CurrentActiveUser,
):
    """Upload flows from a file."""
    contents = await file.read()
    data = orjson.loads(contents)

    if not data:
        raise HTTPException(status_code=400, detail="No flows found in the file")

    project_name = await generate_unique_folder_name(data["folder_name"], current_user.id, session)

    data["folder_name"] = project_name

    project = FolderCreate(name=data["folder_name"], description=data["folder_description"])

    new_project = Folder.model_validate(project, from_attributes=True)
    new_project.id = None
    new_project.user_id = current_user.id
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)

    del data["folder_name"]
    del data["folder_description"]

    if "flows" in data:
        flow_list = FlowListCreate(flows=[FlowCreate(**flow) for flow in data["flows"]])
    else:
        raise HTTPException(status_code=400, detail="No flows found in the data")
    # Now we set the user_id for all flows
    for flow in flow_list.flows:
        flow_name = await generate_unique_flow_name(flow.name, current_user.id, session)
        flow.name = flow_name
        flow.user_id = current_user.id
        flow.folder_id = new_project.id

    return await create_flows(session=session, flow_list=flow_list, current_user=current_user)

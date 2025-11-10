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
from sqlalchemy import or_, update
from sqlalchemy.orm import selectinload
from sqlmodel import select

from langbuilder.api.utils import CurrentActiveUser, DbSession, cascade_delete_flow, custom_params, remove_api_keys
from langbuilder.api.v1.flows import create_flows
from langbuilder.api.v1.rbac import get_rbac_service
from langbuilder.api.v1.schemas import FlowListCreate
from langbuilder.helpers.flow import generate_unique_flow_name
from langbuilder.helpers.folders import generate_unique_folder_name
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
from langbuilder.services.rbac.service import RBACService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=FolderRead, status_code=201)
async def create_project(
    *,
    session: DbSession,
    project: FolderCreate,
    current_user: CurrentActiveUser,
):
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
        await session.flush()

        # Assign Owner role to creator (Task 2.3: Default Role Assignments)
        # Query for the Owner role
        from langbuilder.logging import logger
        from langbuilder.services.database.models.rbac import Role, UserRoleAssignment

        owner_role_stmt = select(Role).where(Role.name == "Owner")
        owner_role_result = await session.exec(owner_role_stmt)
        owner_role = owner_role_result.first()

        if owner_role:
            # Create role assignment for the project creator
            assignment = UserRoleAssignment(
                user_id=current_user.id,
                role_id=owner_role.id,
                scope_type="Project",
                scope_id=new_project.id,
                is_immutable=False,
                created_by=current_user.id,
            )
            session.add(assignment)
        else:
            logger.warning(f"Owner role not found when creating project {new_project.id}")

        # Set default_project_id if user doesn't have one (Task 2.3: Default Project Assignment)
        if not current_user.default_project_id:
            current_user.default_project_id = new_project.id
            session.add(current_user)

        await session.commit()
        await session.refresh(new_project)

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return new_project


@router.get("/", response_model=list[FolderRead], status_code=200)
async def read_projects(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Retrieve a list of projects for the current user.

    Task 3.1: Now filters projects by Read permission using RBACService.
    Only returns projects that the user has Read permission to access.

    Args:
        session (DbSession): The database session.
        current_user (CurrentActiveUser): The current authenticated user.
        rbac_service (RBACService): The RBAC service for permission checks.

    Returns:
        list[FolderRead]: A list of projects the user can read.
    """
    try:
        # Get all projects (no user_id pre-filter - rely on RBAC)
        projects = (
            await session.exec(select(Folder))
        ).all()
        # Note: Starter Projects are included so users can create role assignments for them

        # Task 3.1: Filter projects by Read permission
        # Check each project for Read permission and only return accessible projects
        readable_projects = []
        for project in projects:
            try:
                can_read = await rbac_service.can_access(
                    user_id=current_user.id,
                    permission_name="Read",
                    scope_type="Project",
                    scope_id=project.id,
                )
                if can_read:
                    readable_projects.append(project)
            except Exception as e:
                # Log error but don't fail entire request
                logger.warning(f"Error checking Read permission for project {project.id}: {e}")
                # Skip this project (fail closed)
                continue

        return sorted(readable_projects, key=lambda x: x.name != DEFAULT_FOLDER_NAME)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{project_id}", response_model=FolderWithPaginatedFlows | FolderReadWithFlows, status_code=200)
async def read_project(
    *,
    session: DbSession,
    project_id: UUID,
    current_user: CurrentActiveUser,
    params: Annotated[Params | None, Depends(custom_params)],
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
    is_component: bool = False,
    is_flow: bool = False,
    search: str = "",
):
    # RBAC: Check Read permission
    can_read = await rbac_service.can_access(
        user_id=current_user.id,
        permission_name="Read",
        scope_type="Project",
        scope_id=project_id,
    )

    if not can_read:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to read this project"
        )

    try:
        project = (
            await session.exec(
                select(Folder)
                .options(selectinload(Folder.flows))
                .where(Folder.id == project_id)
            )
        ).first()
    except Exception as e:
        if "No result found" in str(e):
            raise HTTPException(status_code=404, detail="Project not found") from e
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Update a project with Update permission check.

    Task 3.3: Enforces Update permission before allowing project modifications.
    Users must have Update permission on the project to modify it.
    """
    try:
        # Task 3.3: Check Update permission before modifying project
        can_update = await rbac_service.can_access(
            user_id=current_user.id,
            permission_name="Update",
            scope_type="Project",
            scope_id=project_id,
        )

        if not can_update:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this project"
            )

        existing_project = (
            await session.exec(select(Folder).where(Folder.id == project_id))
        ).first()
    except HTTPException:
        # Re-raise HTTP exceptions (including our 403 from permission check)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")

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
    rbac_service: Annotated[RBACService, Depends(get_rbac_service)],
):
    """Delete a project with Delete permission check.

    Task 3.4: Enforces Delete permission before allowing project deletion.
    Users must have Delete permission on the project to delete it.
    Only Admin and Owner roles have Delete permission per PRD.
    """
    # Task 3.4: Check Delete permission before deleting project
    can_delete = await rbac_service.can_access(
        user_id=current_user.id,
        permission_name="Delete",
        scope_type="Project",
        scope_id=project_id,
    )

    if not can_delete:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this project"
        )

    try:
        flows = (
            await session.exec(select(Flow).where(Flow.folder_id == project_id))
        ).all()
        if len(flows) > 0:
            for flow in flows:
                await cascade_delete_flow(session, flow.id)

        project = (
            await session.exec(select(Folder).where(Folder.id == project_id))
        ).first()
    except HTTPException:
        # Re-raise HTTP exceptions (including our 403 from permission check)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

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
):
    """Download all flows from project as a zip file."""
    try:
        query = select(Folder).where(Folder.id == project_id, Folder.user_id == current_user.id)
        result = await session.exec(query)
        project = result.first()

        if not project:
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

"""Project management API endpoints for RBAC system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.api.v1.rbac.dependencies import (
    check_project_permission,
    check_workspace_permission,
    get_permission_engine,
)
from langflow.services.database.models.rbac.project import (
    Project,
    ProjectCreate,
    ProjectRead,
    ProjectStatistics,
    ProjectUpdate,
)
from langflow.services.database.models.rbac.workspace import Workspace

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/projects",
    tags=["RBAC", "Projects"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> ProjectRead:
    """Create a new project."""

    # Get and validate workspace
    workspace = await session.get(Workspace, project_data.workspace_id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Check workspace permissions
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="create_project",
        resource_id=project_data.workspace_id,
        workspace_id=project_data.workspace_id,
    )
    
    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to create projects in this workspace: {result.reason}"
        )

    # Check if project name already exists in workspace
    statement = select(Project).where(
        Project.workspace_id == project_data.workspace_id,
        Project.name == project_data.name,
        Project.is_active == True
    )
    existing_result = await session.exec(statement)
    existing = existing_result.first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project '{project_data.name}' already exists in this workspace"
        )

    # Create project
    project = Project(
        **project_data.model_dump(),
        owner_id=current_user.id
    )

    session.add(project)
    await session.commit()
    await session.refresh(project)

    # TODO: Create default role assignments for owner
    # TODO: Log audit event

    return ProjectRead.model_validate(project)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
    workspace_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    is_active: bool | None = None,
    is_archived: bool | None = None,
) -> list[ProjectRead]:
    """List projects accessible to current user."""

    statement = select(Project)

    # Filter by workspace if specified
    if workspace_id:
        workspace = await session.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Check workspace access
        result = await permission_engine.check_permission(
            session=session,
            user=current_user,
            resource_type="workspace",
            action="read",
            resource_id=workspace_id,
            workspace_id=workspace_id,
        )
        
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to this workspace: {result.reason}"
            )

        statement = statement.where(Project.workspace_id == workspace_id)
    else:
        # Filter by user's accessible workspaces
        # TODO: Implement proper permission-based filtering
        accessible_workspace_subquery = select(Workspace.id).where(
            Workspace.owner_id == current_user.id,
            Workspace.is_deleted == False
        )
        statement = statement.where(Project.workspace_id.in_(accessible_workspace_subquery))

    # Apply additional filters
    if search:
        statement = statement.where(
            (Project.name.ilike(f"%{search}%")) |
            (Project.description.ilike(f"%{search}%"))
        )

    if is_active is not None:
        statement = statement.where(Project.is_active == is_active)

    if is_archived is not None:
        statement = statement.where(Project.is_archived == is_archived)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    projects = result.all()

    return [ProjectRead.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    project: Project = Depends(check_project_permission("read")),
) -> ProjectRead:
    """Get project by ID."""
    return ProjectRead.model_validate(project)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
    project: Project = Depends(check_project_permission("update")),
) -> ProjectRead:
    """Update project."""

    # Check name uniqueness if changing name
    if project_data.name and project_data.name != project.name:
        statement = select(Project).where(
            Project.workspace_id == project.workspace_id,
            Project.name == project_data.name,
            Project.id != project_id,
            Project.is_active == True
        )
        result = await session.exec(statement)
        existing = result.first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{project_data.name}' already exists in this workspace"
            )

    # Update project fields
    for field, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(project)

    # TODO: Log audit event

    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    project: Project = Depends(check_project_permission("delete")),
):
    """Archive project (soft delete)."""

    project.is_archived = True
    project.archived_at = datetime.now(timezone.utc)
    project.updated_at = datetime.now(timezone.utc)

    await session.commit()

    # TODO: Log audit event
    # TODO: Handle associated environments and flows


@router.get("/{project_id}/environments", response_model=list[dict])
async def list_project_environments(
    project_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    project: Project = Depends(check_project_permission("read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    """List environments in project."""

    from langflow.services.database.models.rbac.environment import Environment

    statement = select(Environment).where(
        Environment.project_id == project_id,
        Environment.is_active == True
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    environments = result.all()

    return [
        {
            "id": str(env.id),
            "name": env.name,
            "description": env.description,
            "type": env.type,
            "created_at": env.created_at.isoformat(),
            "is_active": env.is_active,
            "is_locked": env.is_locked,
            "deployment_count": env.deployment_count
        }
        for env in environments
    ]


@router.get("/{project_id}/flows", response_model=list[dict])
async def list_project_flows(
    project_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    project: Project = Depends(check_project_permission("read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    """List flows in project."""

    from langflow.services.database.models.flow.model import Flow

    statement = select(Flow).where(
        Flow.project_id == project_id
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    flows = result.all()

    return [
        {
            "id": str(flow.id),
            "name": flow.name,
            "description": flow.description,
            "created_at": flow.updated_at.isoformat() if flow.updated_at else None,
            "is_component": flow.is_component,
            "endpoint_name": flow.endpoint_name,
            "webhook": flow.webhook
        }
        for flow in flows
    ]


@router.get("/{project_id}/stats", response_model=ProjectStatistics)
async def get_project_statistics(
    project_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    project: Project = Depends(check_project_permission("read")),
) -> ProjectStatistics:
    """Get project statistics."""

    from langflow.services.database.models.rbac.environment import Environment, EnvironmentDeployment
    from langflow.services.database.models.flow.model import Flow

    # Count environments
    total_env_statement = select(func.count(Environment.id)).where(
        Environment.project_id == project_id
    )
    total_env_result = await session.exec(total_env_statement)
    total_environments = total_env_result.one()

    active_env_statement = select(func.count(Environment.id)).where(
        Environment.project_id == project_id,
        Environment.is_active == True
    )
    active_env_result = await session.exec(active_env_statement)
    active_environments = active_env_result.one()

    # Count flows
    total_flows_statement = select(func.count(Flow.id)).where(
        Flow.project_id == project_id
    )
    total_flows_result = await session.exec(total_flows_statement)
    total_flows = total_flows_result.one()

    # Count deployments
    total_deployments_statement = select(func.count(EnvironmentDeployment.id)).select_from(
        EnvironmentDeployment.join(Environment)
    ).where(
        Environment.project_id == project_id
    )
    total_deployments_result = await session.exec(total_deployments_statement)
    total_deployments = total_deployments_result.one()

    successful_deployments_statement = select(func.count(EnvironmentDeployment.id)).select_from(
        EnvironmentDeployment.join(Environment)
    ).where(
        Environment.project_id == project_id,
        EnvironmentDeployment.status == "success"
    )
    successful_deployments_result = await session.exec(successful_deployments_statement)
    successful_deployments = successful_deployments_result.one()

    failed_deployments_statement = select(func.count(EnvironmentDeployment.id)).select_from(
        EnvironmentDeployment.join(Environment)
    ).where(
        Environment.project_id == project_id,
        EnvironmentDeployment.status == "failed"
    )
    failed_deployments_result = await session.exec(failed_deployments_statement)
    failed_deployments = failed_deployments_result.one()

    # Get last deployment
    last_deployment_statement = select(EnvironmentDeployment).select_from(
        EnvironmentDeployment.join(Environment)
    ).where(
        Environment.project_id == project_id
    ).order_by(EnvironmentDeployment.started_at.desc()).limit(1)
    
    last_deployment_result = await session.exec(last_deployment_statement)
    last_deployment = last_deployment_result.first()

    return ProjectStatistics(
        project_id=project_id,
        total_flows=total_flows,
        active_flows=total_flows,  # TODO: Implement proper active flow counting
        total_environments=total_environments,
        active_environments=active_environments,
        total_deployments=total_deployments,
        successful_deployments=successful_deployments,
        failed_deployments=failed_deployments,
        last_deployment_at=last_deployment.started_at if last_deployment else None,
        # TODO: Implement remaining statistics
    )

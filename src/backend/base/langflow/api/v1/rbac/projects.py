"""Project management API endpoints for RBAC system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from langflow.api.utils import get_session
from langflow.services.auth.utils import get_current_active_user as get_current_user
from langflow.api.v1.rbac.dependencies import (
    check_project_permission,
    check_workspace_permission,
)
from langflow.services.database.models.rbac.project import (
    Project,
    ProjectCreate,
    ProjectRead,
    ProjectStatistics,
    ProjectUpdate,
)
from langflow.services.database.models.rbac.workspace import Workspace
from langflow.services.database.models.user.model import User

if TYPE_CHECKING:
    pass

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProjectRead:
    """Create a new project."""

    # Get and validate workspace
    workspace = session.get(Workspace, project_data.workspace_id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Check workspace permissions
    from langflow.api.v1.rbac.dependencies import PermissionChecker
    checker = PermissionChecker(session, current_user)
    if not checker.has_workspace_permission(workspace, "project:create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create projects in this workspace"
        )

    # Check if project name already exists in workspace
    existing = session.query(Project).filter(
        Project.workspace_id == project_data.workspace_id,
        Project.name == project_data.name,
        Project.is_active == True
    ).first()

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
    session.commit()
    session.refresh(project)

    # TODO: Create default role assignments for owner
    # TODO: Log audit event

    return ProjectRead.model_validate(project)


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    workspace_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    is_active: bool | None = None,
    is_archived: bool | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ProjectRead]:
    """List projects accessible to current user."""

    query = session.query(Project)

    # Filter by workspace if specified
    if workspace_id:
        workspace = session.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Check workspace access
        from langflow.api.v1.rbac.dependencies import PermissionChecker
        checker = PermissionChecker(session, current_user)
        if not checker.has_workspace_permission(workspace, "workspace:read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace"
            )

        query = query.filter(Project.workspace_id == workspace_id)
    else:
        # Filter by user's accessible workspaces
        # TODO: Implement proper permission-based filtering
        accessible_workspace_ids = session.query(Workspace.id).filter(
            Workspace.owner_id == current_user.id,
            Workspace.is_deleted == False
        ).subquery()
        query = query.filter(Project.workspace_id.in_(accessible_workspace_ids))

    # Apply additional filters
    if search:
        query = query.filter(
            Project.name.ilike(f"%{search}%") |
            Project.description.ilike(f"%{search}%")
        )

    if is_active is not None:
        query = query.filter(Project.is_active == is_active)

    if is_archived is not None:
        query = query.filter(Project.is_archived == is_archived)

    # Apply pagination
    projects = query.offset(skip).limit(limit).all()

    return [ProjectRead.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(check_project_permission("project:read")),
) -> ProjectRead:
    """Get project by ID."""
    return ProjectRead.model_validate(project)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(check_project_permission("project:update")),
) -> ProjectRead:
    """Update project."""

    # Check name uniqueness if changing name
    if project_data.name and project_data.name != project.name:
        existing = session.query(Project).filter(
            Project.workspace_id == project.workspace_id,
            Project.name == project_data.name,
            Project.id != project_id,
            Project.is_active == True
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project '{project_data.name}' already exists in this workspace"
            )

    # Update project fields
    from datetime import datetime, timezone
    for field, value in project_data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    project.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(project)

    # TODO: Log audit event

    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(check_project_permission("project:delete")),
):
    """Archive project (soft delete)."""

    from datetime import datetime, timezone

    project.is_archived = True
    project.archived_at = datetime.now(timezone.utc)
    project.updated_at = datetime.now(timezone.utc)

    session.commit()

    # TODO: Log audit event
    # TODO: Handle associated environments and flows


@router.get("/{project_id}/environments", response_model=list[dict])
async def list_project_environments(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(check_project_permission("project:read")),
) -> list[dict]:
    """List environments in project."""

    from langflow.services.database.models.rbac.environment import Environment

    environments = session.query(Environment).filter(
        Environment.project_id == project_id,
        Environment.is_active == True
    ).offset(skip).limit(limit).all()

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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(check_project_permission("project:read")),
) -> list[dict]:
    """List flows in project."""

    from langflow.services.database.models.flow.model import Flow

    flows = session.query(Flow).filter(
        Flow.project_id == project_id
    ).offset(skip).limit(limit).all()

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
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    project: Project = Depends(check_project_permission("project:read")),
) -> ProjectStatistics:
    """Get project statistics."""

    from langflow.services.database.models.rbac.environment import Environment, EnvironmentDeployment
    from langflow.services.database.models.flow.model import Flow

    # Count environments
    total_environments = session.query(Environment).filter(
        Environment.project_id == project_id
    ).count()

    active_environments = session.query(Environment).filter(
        Environment.project_id == project_id,
        Environment.is_active == True
    ).count()

    # Count flows
    total_flows = session.query(Flow).filter(
        Flow.project_id == project_id
    ).count()

    # Count deployments
    total_deployments = session.query(EnvironmentDeployment).join(Environment).filter(
        Environment.project_id == project_id
    ).count()

    successful_deployments = session.query(EnvironmentDeployment).join(Environment).filter(
        Environment.project_id == project_id,
        EnvironmentDeployment.status == "success"
    ).count()

    failed_deployments = session.query(EnvironmentDeployment).join(Environment).filter(
        Environment.project_id == project_id,
        EnvironmentDeployment.status == "failed"
    ).count()

    # Get last deployment
    last_deployment = session.query(EnvironmentDeployment).join(Environment).filter(
        Environment.project_id == project_id
    ).order_by(EnvironmentDeployment.started_at.desc()).first()

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

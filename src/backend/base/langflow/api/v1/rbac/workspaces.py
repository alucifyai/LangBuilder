"""Workspace management API endpoints for RBAC system."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from langflow.api.utils import get_current_user, get_session
from langflow.api.v1.rbac.dependencies import check_workspace_permission
from langflow.services.database.models.rbac.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceInvitation,
    WorkspaceRead,
    WorkspaceUpdate,
)
from langflow.services.database.models.user.model import User

if TYPE_CHECKING:
    pass

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> WorkspaceRead:
    """Create a new workspace."""
    # Check if workspace name already exists for this user
    existing = session.query(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Workspace.name == workspace_data.name,
        Workspace.is_deleted == False,  # noqa: E712
    ).first()

    if existing:
        msg = f"Workspace '{workspace_data.name}' already exists"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )

    # Create workspace
    workspace = Workspace(
        **workspace_data.model_dump(),
        owner_id=current_user.id,
    )

    session.add(workspace)
    session.commit()
    session.refresh(workspace)

    return WorkspaceRead.model_validate(workspace)


@router.get("/", response_model=list[WorkspaceRead])
async def list_workspaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    organization: str | None = None,
    is_active: bool | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceRead]:
    """List workspaces accessible to current user."""

    query = session.query(Workspace).filter(
        Workspace.is_deleted == False
    )

    # Filter by user access (owner or has role assignment)
    # TODO: Add proper permission checking based on role assignments
    query = query.filter(Workspace.owner_id == current_user.id)

    # Apply filters
    if search:
        query = query.filter(
            Workspace.name.ilike(f"%{search}%") |
            Workspace.description.ilike(f"%{search}%")
        )

    if organization:
        query = query.filter(Workspace.organization.ilike(f"%{organization}%"))

    if is_active is not None:
        query = query.filter(Workspace.is_active == is_active)

    # Apply pagination
    workspaces = query.offset(skip).limit(limit).all()

    return [WorkspaceRead.model_validate(ws) for ws in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:read")),
) -> WorkspaceRead:
    """Get workspace by ID."""
    return WorkspaceRead.model_validate(workspace)


@router.put("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: UUID,
    workspace_data: WorkspaceUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:update")),
) -> WorkspaceRead:
    """Update workspace."""

    # Check name uniqueness if changing name
    if workspace_data.name and workspace_data.name != workspace.name:
        existing = session.query(Workspace).filter(
            Workspace.owner_id == workspace.owner_id,
            Workspace.name == workspace_data.name,
            Workspace.id != workspace_id,
            Workspace.is_deleted == False
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workspace '{workspace_data.name}' already exists"
            )

    # Update workspace fields
    for field, value in workspace_data.model_dump(exclude_unset=True).items():
        setattr(workspace, field, value)

    workspace.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(workspace)

    # TODO: Log audit event

    return WorkspaceRead.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:delete")),
):
    """Soft delete workspace."""

    from datetime import datetime, timezone

    workspace.is_deleted = True
    workspace.deletion_requested_at = datetime.now(timezone.utc)
    workspace.updated_at = datetime.now(timezone.utc)

    session.commit()

    # TODO: Log audit event
    # TODO: Handle cascade deletion/archiving of projects, etc.


@router.post("/{workspace_id}/invite", response_model=dict)
async def invite_user_to_workspace(
    workspace_id: UUID,
    invitation_data: dict,  # TODO: Create proper schema
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:manage")),
) -> dict:
    """Invite a user to the workspace."""

    import secrets
    from datetime import datetime, timezone, timedelta

    email = invitation_data.get("email")
    role_id = invitation_data.get("role_id")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    # Check if user is already invited
    existing_invitation = session.query(WorkspaceInvitation).filter(
        WorkspaceInvitation.workspace_id == workspace_id,
        WorkspaceInvitation.email == email,
        WorkspaceInvitation.is_accepted == False
    ).first()

    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a pending invitation"
        )

    # Create invitation
    invitation = WorkspaceInvitation(
        workspace_id=workspace_id,
        email=email,
        role_id=role_id,
        invited_by_id=current_user.id,
        invitation_code=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )

    session.add(invitation)
    session.commit()

    # TODO: Send invitation email
    # TODO: Log audit event

    return {
        "message": "Invitation sent successfully",
        "invitation_id": str(invitation.id),
        "expires_at": invitation.expires_at.isoformat()
    }


@router.get("/{workspace_id}/users", response_model=list[dict])
async def list_workspace_users(
    workspace_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:read")),
) -> list[dict]:
    """List users in workspace with their roles."""

    # TODO: Implement proper query with role assignments
    # This is a placeholder implementation

    return [
        {
            "user_id": str(workspace.owner_id),
            "username": workspace.owner.username,
            "roles": ["workspace_owner"],
            "joined_at": workspace.created_at.isoformat(),
            "is_active": True
        }
    ]


@router.get("/{workspace_id}/projects", response_model=list[dict])
async def list_workspace_projects(
    workspace_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:read")),
) -> list[dict]:
    """List projects in workspace."""

    from langflow.services.database.models.rbac.project import Project

    projects = session.query(Project).filter(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    ).offset(skip).limit(limit).all()

    return [
        {
            "id": str(project.id),
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "is_active": project.is_active,
            "is_archived": project.is_archived
        }
        for project in projects
    ]


@router.get("/{workspace_id}/stats", response_model=dict)
async def get_workspace_statistics(
    workspace_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(check_workspace_permission("workspace:read")),
) -> dict:
    """Get workspace statistics."""

    from langflow.services.database.models.rbac.project import Project
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.rbac.user_group import UserGroup
    from langflow.services.database.models.flow.model import Flow

    # Count projects
    project_count = session.query(Project).filter(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    ).count()

    # Count users (via role assignments)
    user_count = session.query(RoleAssignment).filter(
        RoleAssignment.workspace_id == workspace_id,
        RoleAssignment.is_active == True,
        RoleAssignment.user_id.isnot(None)
    ).distinct(RoleAssignment.user_id).count()

    # Count groups
    group_count = session.query(UserGroup).filter(
        UserGroup.workspace_id == workspace_id,
        UserGroup.is_active == True
    ).count()

    # Count flows (across all projects in workspace)
    flow_count = session.query(Flow).join(Project).filter(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    ).count()

    return {
        "workspace_id": str(workspace_id),
        "project_count": project_count,
        "user_count": user_count + 1,  # +1 for owner
        "group_count": group_count,
        "flow_count": flow_count,
        "created_at": workspace.created_at.isoformat(),
        "last_updated": workspace.updated_at.isoformat()
    }

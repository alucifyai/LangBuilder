"""Workspace management API endpoints for RBAC system."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import check_workspace_permission
from langflow.services.database.models.rbac.workspace import (
    Workspace,
    WorkspaceCreate,
    WorkspaceInvitation,
    WorkspaceRead,
    WorkspaceUpdate,
)
if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/workspaces",
    tags=["RBAC", "Workspaces"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> WorkspaceRead:
    """Create a new workspace."""
    # Check if workspace name already exists for this user
    statement = select(Workspace).where(
        Workspace.owner_id == current_user.id,
        Workspace.name == workspace_data.name,
        Workspace.is_deleted == False,  # noqa: E712
    )
    result = await session.exec(statement)
    existing = result.first()

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
    await session.commit()
    await session.refresh(workspace)

    return WorkspaceRead.model_validate(workspace)


@router.get("/", response_model=list[WorkspaceRead])
async def list_workspaces(
    session: DbSession,
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    organization: str | None = None,
    is_active: bool | None = None,
) -> list[WorkspaceRead]:
    """List workspaces accessible to current user."""

    # Build base query
    statement = select(Workspace).where(Workspace.is_deleted == False)

    # Filter by user access (owner or has role assignment)
    # TODO: Add proper permission checking based on role assignments
    statement = statement.where(Workspace.owner_id == current_user.id)

    # Apply filters
    if search:
        statement = statement.where(
            (Workspace.name.ilike(f"%{search}%")) |
            (Workspace.description.ilike(f"%{search}%"))
        )

    if organization:
        statement = statement.where(Workspace.organization.ilike(f"%{organization}%"))

    if is_active is not None:
        statement = statement.where(Workspace.is_active == is_active)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    workspaces = result.all()

    return [WorkspaceRead.model_validate(ws) for ws in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceRead)
async def get_workspace(
    workspace_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("read")),
) -> WorkspaceRead:
    """Get workspace by ID."""
    return WorkspaceRead.model_validate(workspace)


@router.put("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: UUID,
    workspace_data: WorkspaceUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("update")),
) -> WorkspaceRead:
    """Update workspace."""

    # Check name uniqueness if changing name
    if workspace_data.name and workspace_data.name != workspace.name:
        statement = select(Workspace).where(
            Workspace.owner_id == workspace.owner_id,
            Workspace.name == workspace_data.name,
            Workspace.id != workspace_id,
            Workspace.is_deleted == False
        )
        result = await session.exec(statement)
        existing = result.first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workspace '{workspace_data.name}' already exists"
            )

    # Update workspace fields
    for field, value in workspace_data.model_dump(exclude_unset=True).items():
        setattr(workspace, field, value)

    workspace.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(workspace)

    # TODO: Log audit event

    return WorkspaceRead.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("delete")),
):
    """Soft delete workspace."""

    workspace.is_deleted = True
    workspace.deletion_requested_at = datetime.now(timezone.utc)
    workspace.updated_at = datetime.now(timezone.utc)

    await session.commit()

    # TODO: Log audit event
    # TODO: Handle cascade deletion/archiving of projects, etc.


@router.post("/{workspace_id}/invite", response_model=dict)
async def invite_user_to_workspace(
    workspace_id: UUID,
    invitation_data: dict,  # TODO: Create proper schema
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("manage")),
) -> dict:
    """Invite a user to the workspace."""

    email = invitation_data.get("email")
    role_id = invitation_data.get("role_id")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )

    # Check if user is already invited
    statement = select(WorkspaceInvitation).where(
        WorkspaceInvitation.workspace_id == workspace_id,
        WorkspaceInvitation.email == email,
        WorkspaceInvitation.is_accepted == False
    )
    result = await session.exec(statement)
    existing_invitation = result.first()

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
    await session.commit()

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
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
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
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("read")),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    """List projects in workspace."""

    from langflow.services.database.models.rbac.project import Project

    statement = select(Project).where(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    projects = result.all()

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
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace: Workspace = Depends(check_workspace_permission("read")),
) -> dict:
    """Get workspace statistics."""

    from sqlmodel import func
    from langflow.services.database.models.rbac.project import Project
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.rbac.user_group import UserGroup
    from langflow.services.database.models.flow.model import Flow

    # Count projects
    project_statement = select(func.count(Project.id)).where(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    )
    project_result = await session.exec(project_statement)
    project_count = project_result.one()

    # Count users (via role assignments)
    user_statement = select(func.count(func.distinct(RoleAssignment.user_id))).where(
        RoleAssignment.workspace_id == workspace_id,
        RoleAssignment.is_active == True,
        RoleAssignment.user_id.isnot(None)
    )
    user_result = await session.exec(user_statement)
    user_count = user_result.one()

    # Count groups
    group_statement = select(func.count(UserGroup.id)).where(
        UserGroup.workspace_id == workspace_id,
        UserGroup.is_active == True
    )
    group_result = await session.exec(group_statement)
    group_count = group_result.one()

    # Count flows (across all projects in workspace)
    flow_statement = select(func.count(Flow.id)).select_from(
        Flow.join(Project)
    ).where(
        Project.workspace_id == workspace_id,
        Project.is_active == True
    )
    flow_result = await session.exec(flow_statement)
    flow_count = flow_result.one()

    return {
        "workspace_id": str(workspace_id),
        "project_count": project_count,
        "user_count": user_count + 1,  # +1 for owner
        "group_count": group_count,
        "flow_count": flow_count,
        "created_at": workspace.created_at.isoformat(),
        "last_updated": workspace.updated_at.isoformat()
    }

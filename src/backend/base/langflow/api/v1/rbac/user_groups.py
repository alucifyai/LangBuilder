"""User Group management API endpoints for RBAC system."""

from typing import TYPE_CHECKING
from langflow.schema.serialize import UUIDstr

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    check_workspace_permission,
    get_permission_engine,
)
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.services.database.models.rbac.user_group import (
    UserGroup,
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
    UserGroupSync,
    UserGroupMembership,
    UserGroupMembershipCreate,
    UserGroupMembershipRead,
    GroupType,
)
from langflow.services.database.models.rbac.workspace import Workspace

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/user-groups",
    tags=["RBAC", "User Groups"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/", response_model=list[UserGroupRead])
async def list_user_groups(
    session: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: UUIDstr,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    group_type: GroupType | None = None,
    is_active: bool | None = None,
) -> list[UserGroupRead]:
    """List user groups in a workspace."""
    
    # Check workspace permission
    await check_workspace_permission(session, current_user, workspace_id, "user_group:read")

    statement = select(UserGroup).where(UserGroup.workspace_id == workspace_id)

    # Apply filters
    if search:
        statement = statement.where(
            (UserGroup.name.ilike(f"%{search}%")) |
            (UserGroup.description.ilike(f"%{search}%"))
        )

    if group_type:
        statement = statement.where(UserGroup.type == group_type)

    if is_active is not None:
        statement = statement.where(UserGroup.is_active == is_active)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    groups = result.all()

    return [UserGroupRead.model_validate(group) for group in groups]


@router.post("/", response_model=UserGroupRead, status_code=status.HTTP_201_CREATED)
async def create_user_group(
    group_data: UserGroupCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> UserGroupRead:
    """Create a new user group."""
    
    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group_data.workspace_id, "user_group:create"
    )

    # Verify workspace exists
    workspace = await session.get(Workspace, group_data.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Check for duplicate name in workspace
    statement = select(UserGroup).where(
        and_(
            UserGroup.workspace_id == group_data.workspace_id,
            UserGroup.name == group_data.name
        )
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User group with this name already exists in workspace"
        )

    # Create user group
    group = UserGroup(
        **group_data.model_dump(),
        created_by=current_user.id
    )
    
    session.add(group)
    await session.commit()
    await session.refresh(group)

    return UserGroupRead.model_validate(group)


@router.get("/{group_id}", response_model=UserGroupRead)
async def get_user_group(
    group_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> UserGroupRead:
    """Get user group by ID."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:read"
    )

    return UserGroupRead.model_validate(group)


@router.put("/{group_id}", response_model=UserGroupRead)
async def update_user_group(
    group_id: UUIDstr,
    group_data: UserGroupUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> UserGroupRead:
    """Update user group."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:update"
    )

    # Update fields
    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)

    await session.commit()
    await session.refresh(group)

    return UserGroupRead.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_group(
    group_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Delete user group."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:delete"
    )

    await session.delete(group)
    await session.commit()


@router.get("/{group_id}/members", response_model=list[UserGroupMembershipRead])
async def list_group_members(
    group_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[UserGroupMembershipRead]:
    """List members of a user group."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:read"
    )

    statement = select(UserGroupMembership).where(
        UserGroupMembership.group_id == group_id
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    memberships = result.all()

    return [UserGroupMembershipRead.model_validate(membership) for membership in memberships]


@router.post("/{group_id}/members", response_model=UserGroupMembershipRead, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: UUIDstr,
    membership_data: UserGroupMembershipCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> UserGroupMembershipRead:
    """Add a user to a group."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:update"
    )

    # Check if user is already a member
    statement = select(UserGroupMembership).where(
        and_(
            UserGroupMembership.group_id == group_id,
            UserGroupMembership.user_id == membership_data.user_id
        )
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )

    # Create membership
    membership = UserGroupMembership(
        group_id=group_id,
        user_id=membership_data.user_id,
        role=membership_data.role,
        added_by=current_user.id
    )
    
    session.add(membership)
    await session.commit()
    await session.refresh(membership)

    return UserGroupMembershipRead.model_validate(membership)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: UUIDstr,
    user_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Remove a user from a group."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:update"
    )

    # Find membership
    statement = select(UserGroupMembership).where(
        and_(
            UserGroupMembership.group_id == group_id,
            UserGroupMembership.user_id == user_id
        )
    )
    result = await session.exec(statement)
    membership = result.first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group"
        )

    await session.delete(membership)
    await session.commit()


@router.post("/{group_id}/sync", response_model=dict)
async def sync_user_group(
    group_id: UUIDstr,
    sync_data: UserGroupSync,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Sync user group with external provider (SCIM)."""
    
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User group not found"
        )

    # Check workspace permission
    await check_workspace_permission(
        session, current_user, group.workspace_id, "user_group:sync"
    )

    # Only synced groups can be synchronized
    if group.type != GroupType.SYNCED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only synced groups can be synchronized with external providers"
        )

    # Placeholder for actual SCIM sync logic
    # In a real implementation, this would:
    # 1. Connect to the external SCIM provider
    # 2. Fetch group membership data
    # 3. Update local memberships to match
    # 4. Log sync results
    
    return {
        "status": "completed",
        "members_added": 0,
        "members_removed": 0,
        "members_updated": 0,
        "sync_timestamp": "2024-01-01T00:00:00Z",
        "provider": sync_data.provider_type,
        "errors": []
    }
"""Group management API endpoints.

Provides CRUD operations for user groups.
PRD Story 2.1 - Assign Roles to Users and Groups within a Scope
PRD Story 2.3 - Provision Users and Groups via SSO/SCIM
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.crud import (
    add_user_to_group,
    create_group,
    delete_group,
    get_group_by_id,
    list_groups,
    remove_user_from_group,
    update_group,
)
from langflow.services.database.models.rbac.group import GroupCreate, GroupRead, GroupUpdate

router = APIRouter()


class GroupMembershipRequest(BaseModel):
    """Request schema for adding/removing group members."""

    user_id: UUID


@router.get("", response_model=list[GroupRead])
async def get_groups(
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """List all groups.

    Returns:
        List of Group objects

    Note: Requires 'group:read' permission
    """
    # TODO Phase 3: Add permission check

    groups = await list_groups(db=db)
    return [GroupRead.model_validate(g, from_attributes=True) for g in groups]


@router.get("/{group_id}", response_model=GroupRead)
async def get_group(
    group_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a specific group by ID.

    Args:
        group_id: UUID of the group

    Returns:
        Group object

    Raises:
        404: Group not found

    Note: Requires 'group:read' permission
    """
    # TODO Phase 3: Add permission check

    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found",
        )
    return GroupRead.model_validate(group, from_attributes=True)


@router.post("", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
async def create_new_group(
    group_data: GroupCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Create a new group.

    Request Body:
    - name: Unique group name
    - description: Optional description
    - external_id: Optional external IdP group ID for SCIM sync
    - metadata: Optional metadata (e.g., IdP attributes)
    - member_ids: Optional list of initial user IDs

    Returns:
        Created Group object

    Raises:
        409: Group name already exists

    Note: Requires 'group:create' permission
    """
    # TODO Phase 3: Add permission check

    group = await create_group(db=db, group_data=group_data)

    # Add initial members if provided
    if group_data.member_ids:
        for user_id in group_data.member_ids:
            try:
                await add_user_to_group(db=db, group_id=group.id, user_id=user_id)
            except HTTPException:
                # User not found, skip
                pass

    return GroupRead.model_validate(group, from_attributes=True)


@router.patch("/{group_id}", response_model=GroupRead)
async def update_existing_group(
    group_id: UUID,
    group_data: GroupUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update a group.

    Request Body (all fields optional):
    - name: New group name
    - description: New description
    - external_id: New external ID
    - metadata: Updated metadata
    - add_member_ids: List of user IDs to add to group
    - remove_member_ids: List of user IDs to remove from group

    Returns:
        Updated Group object

    Raises:
        404: Group not found
        409: Name conflict

    Note: Requires 'group:update' permission
    """
    # TODO Phase 3: Add permission check

    # Handle membership changes
    if group_data.add_member_ids:
        for user_id in group_data.add_member_ids:
            try:
                await add_user_to_group(db=db, group_id=group_id, user_id=user_id)
            except HTTPException:
                pass  # User not found or already in group

    if group_data.remove_member_ids:
        for user_id in group_data.remove_member_ids:
            try:
                await remove_user_from_group(db=db, group_id=group_id, user_id=user_id)
            except HTTPException:
                pass  # User not in group

    group = await update_group(db=db, group_id=group_id, group_data=group_data)
    return GroupRead.model_validate(group, from_attributes=True)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_group(
    group_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a group.

    Groups with active grants cannot be deleted.

    Args:
        group_id: UUID of the group to delete

    Raises:
        404: Group not found
        409: Group has active grants

    Note: Requires 'group:delete' permission
    """
    # TODO Phase 3: Add permission check

    await delete_group(db=db, group_id=group_id)
    return None  # 204 No Content


@router.post("/{group_id}/members", status_code=status.HTTP_204_NO_CONTENT)
async def add_group_member(
    group_id: UUID,
    request: GroupMembershipRequest,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Add a user to a group.

    Request Body:
    - user_id: UUID of the user to add

    Raises:
        404: Group or user not found

    Note: Idempotent - returns success if user already in group
    Note: Requires 'group:update' permission
    """
    # TODO Phase 3: Add permission check

    await add_user_to_group(db=db, group_id=group_id, user_id=request.user_id)
    return None  # 204 No Content


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Remove a user from a group.

    Args:
        group_id: UUID of the group
        user_id: UUID of the user to remove

    Raises:
        404: User not in group

    Note: Requires 'group:update' permission
    """
    # TODO Phase 3: Add permission check

    await remove_user_from_group(db=db, group_id=group_id, user_id=user_id)
    return None  # 204 No Content

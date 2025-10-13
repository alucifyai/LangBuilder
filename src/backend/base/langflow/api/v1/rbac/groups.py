"""Group Management API endpoints for RBAC.

Implements PRD Story 2.1 - User Group Management
- Create, Read, Update, Delete operations for user groups
- Add/remove users from groups (group membership management)
- Batch role assignments via groups
- Workspace-scoped group isolation
- SCIM integration support

AppGraph Impact Subgraph:
- group_management_api → REST API for user groups
- create_group_logic → Creates user group
- update_group_logic → Updates group
- delete_group_logic → Deletes group
- add_group_member_logic → Adds user to group
- remove_group_member_logic → Removes user from group
- list_groups_logic → Lists groups
- list_group_members_logic → Lists group members
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.user.model import User
from langflow.services.database.models.user_group.model import (
    UserGroup,
    UserGroupCreate,
    UserGroupMember,
    UserGroupMemberCreate,
    UserGroupMemberRead,
    UserGroupRead,
    UserGroupUpdate,
)
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.rbac.audit import log_audit_event
from langflow.services.rbac.cache import get_permission_cache

router = APIRouter(prefix="/admin/groups", tags=["Groups"])


async def _check_group_manage_permission(current_user: User) -> None:
    """Check if user has permission to manage groups.

    For now, only superusers can manage groups.
    TODO: Integrate with RBACEnforcementEngine once permission system is fully connected.

    Args:
        current_user: The current authenticated user

    Raises:
        HTTPException: 403 if user lacks permission
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Group management requires superuser access.",
        )


async def _get_user_by_identifier(identifier: str, session: DbSession) -> User | None:
    """Get user by username or user ID.

    Args:
        identifier: Username or user ID string
        session: Database session

    Returns:
        User if found, None otherwise
    """
    # Try UUID first
    try:
        from uuid import UUID
        user_id = UUID(identifier)
        user = await session.get(User, user_id)
        if user:
            return user
    except (ValueError, AttributeError):
        pass

    # Try username
    stmt = select(User).where(User.username == identifier)
    result = await session.exec(stmt)
    return result.first()


@router.get("/", response_model=list[UserGroupRead])
async def list_groups(
    workspace_id: UUID | None = Query(default=None, description="Filter by workspace ID"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[UserGroupRead]:
    """List user groups with optional workspace filtering.

    Implements PRD Story 2.1 @AC1 - List groups

    Args:
        workspace_id: Optional workspace filter
        skip: Pagination offset
        limit: Maximum results
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of user groups

    Raises:
        HTTPException: 403 if user lacks permission
    """
    await _check_group_manage_permission(current_user)

    # Build query
    stmt = select(UserGroup).offset(skip).limit(limit).order_by(UserGroup.created_at.desc())

    # Apply workspace filter if provided
    if workspace_id:
        stmt = stmt.where(UserGroup.workspace_id == workspace_id)

    # Execute query
    result = await session.exec(stmt)
    groups = result.all()

    return [UserGroupRead.model_validate(g) for g in groups]


@router.get("/{group_id}", response_model=UserGroupRead)
async def get_group(
    group_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> UserGroupRead:
    """Get a specific group by ID.

    Args:
        group_id: UUID of the group to retrieve
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The requested group

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if group not found
    """
    await _check_group_manage_permission(current_user)

    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found",
        )

    return UserGroupRead.model_validate(group)


@router.post("/", response_model=UserGroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: UserGroupCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> UserGroupRead:
    """Create a new user group within a workspace.

    Implements PRD Story 2.1 @AC1 - Create group

    Validations:
    - Workspace must exist
    - Group name must be unique within workspace
    - User must have group.create permission

    Args:
        group_data: Group creation data (includes workspace_id)
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The newly created group

    Raises:
        HTTPException: 400 if group name already exists in workspace
        HTTPException: 403 if user lacks permission
        HTTPException: 400 if workspace not found
    """
    await _check_group_manage_permission(current_user)

    # Validate workspace exists
    workspace = await session.get(Workspace, group_data.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace not found: {group_data.workspace_id}",
        )

    # Validate unique name within workspace
    stmt = select(UserGroup).where(
        UserGroup.workspace_id == group_data.workspace_id,
        UserGroup.name == group_data.name,
    )
    existing = (await session.exec(stmt)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group name must be unique within workspace. A group with name '{group_data.name}' already exists in this workspace.",
        )

    # Create group
    try:
        group = UserGroup(
            workspace_id=group_data.workspace_id,
            name=group_data.name,
            description=group_data.description,
            external_id=group_data.external_id,
            scim_synced=group_data.scim_synced if group_data.scim_synced is not None else False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)

        logger.info(f"Group created: {group.name} (ID: {group.id}) in workspace {group_data.workspace_id} by user {current_user.id}")

        # Audit logging (PRD Story 2.1)
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="group.created",
            resource_type="group",
            resource_id=group.id,
            details={"name": group.name, "workspace_id": str(group_data.workspace_id)}
        )

        return UserGroupRead.model_validate(group)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database error creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create group due to database constraint violation.",
        ) from e


@router.patch("/{group_id}", response_model=UserGroupRead)
async def update_group(
    group_id: UUID,
    group_data: UserGroupUpdate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> UserGroupRead:
    """Update an existing group.

    Implements PRD Story 2.1 - Update group

    Args:
        group_id: UUID of the group to update
        group_data: Group update data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The updated group

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if group not found
    """
    await _check_group_manage_permission(current_user)

    # Fetch the group
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found",
        )

    # Update group fields
    update_data = group_data.model_dump(exclude_unset=True)

    if update_data.get("name"):
        # Check name uniqueness within workspace if name is being changed
        if group.name != update_data["name"]:
            stmt = select(UserGroup).where(
                UserGroup.workspace_id == group.workspace_id,
                UserGroup.name == update_data["name"],
            )
            existing = (await session.exec(stmt)).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Group name '{update_data['name']}' already exists in this workspace.",
                )
        group.name = update_data["name"]

    if "description" in update_data:
        group.description = update_data["description"]

    if "is_active" in update_data and update_data["is_active"] is not None:
        group.is_active = update_data["is_active"]

    # Update timestamp
    group.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(group)

    logger.info(f"Group updated: {group.name} (ID: {group.id}) by user {current_user.id}")

    # Audit logging
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="group.updated",
        resource_type="group",
        resource_id=group.id,
        details={"name": group.name, "updated_fields": list(update_data.keys())}
    )

    return UserGroupRead.model_validate(group)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Delete a group.

    Implements PRD Story 2.1 @AC2 - Delete group

    Deletes the group and all memberships. Role assignments associated with
    the group are also removed (cascade delete).

    Args:
        group_id: UUID of the group to delete
        current_user: Currently authenticated user
        session: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if group not found
    """
    await _check_group_manage_permission(current_user)

    # Fetch the group
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found",
        )

    # Get member count for logging
    stmt = select(UserGroupMember).where(UserGroupMember.group_id == group_id)
    members = (await session.exec(stmt)).all()
    member_count = len(members)

    # Delete the group (cascade will delete members and role assignments)
    group_name = group.name
    await session.delete(group)
    await session.commit()

    logger.info(f"Group deleted: {group_name} (ID: {group_id}) with {member_count} members by user {current_user.id}")

    # Invalidate cache for all members
    cache = get_permission_cache()
    for member in members:
        await cache.invalidate_user(member.user_id)

    # Audit logging
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="group.deleted",
        resource_type="group",
        resource_id=group_id,
        details={"name": group_name, "member_count": member_count}
    )


@router.get("/{group_id}/members", response_model=list[UserGroupMemberRead])
async def list_group_members(
    group_id: UUID,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[UserGroupMemberRead]:
    """List members of a group.

    Args:
        group_id: UUID of the group
        skip: Pagination offset
        limit: Maximum results
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of group members

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if group not found
    """
    await _check_group_manage_permission(current_user)

    # Verify group exists
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found",
        )

    # Query members
    stmt = (
        select(UserGroupMember)
        .where(UserGroupMember.group_id == group_id)
        .offset(skip)
        .limit(limit)
        .order_by(UserGroupMember.joined_at.desc())
    )
    result = await session.exec(stmt)
    members = result.all()

    return [UserGroupMemberRead.model_validate(m) for m in members]


@router.post("/{group_id}/members", response_model=UserGroupMemberRead, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: UUID,
    member_data: UserGroupMemberCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> UserGroupMemberRead:
    """Add a user to a group.

    Implements PRD Story 2.1 @AC1 - Add user to group

    Args:
        group_id: UUID of the group
        member_data: Membership creation data (user_id)
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The created membership record

    Raises:
        HTTPException: 400 if user is already a member or user not found
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if group not found
    """
    await _check_group_manage_permission(current_user)

    # Verify group exists
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found",
        )

    # Verify user exists
    user = await session.get(User, member_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User not found: {member_data.user_id}",
        )

    # Check if already a member
    stmt = select(UserGroupMember).where(
        UserGroupMember.group_id == group_id,
        UserGroupMember.user_id == member_data.user_id,
    )
    existing = (await session.exec(stmt)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group",
        )

    # Add member
    try:
        member = UserGroupMember(
            group_id=group_id,
            user_id=member_data.user_id,
            is_active=True,
            joined_at=datetime.now(timezone.utc),
        )
        session.add(member)
        await session.commit()
        await session.refresh(member)

        logger.info(f"User {member_data.user_id} added to group {group_id} by user {current_user.id}")

        # Invalidate user cache (group membership changed)
        cache = get_permission_cache()
        await cache.invalidate_user(member_data.user_id)

        # Audit logging
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="group_member.added",
            resource_type="group",
            resource_id=group_id,
            details={"user_id": str(member_data.user_id), "user_username": user.username}
        )

        return UserGroupMemberRead.model_validate(member)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database error adding group member: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add user to group due to database constraint violation.",
        ) from e


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member(
    group_id: UUID,
    user_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Remove a user from a group.

    Implements PRD Story 2.1 @AC2 - Remove user from group

    Args:
        group_id: UUID of the group
        user_id: UUID of the user to remove
        current_user: Currently authenticated user
        session: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if group or membership not found
    """
    await _check_group_manage_permission(current_user)

    # Verify group exists
    group = await session.get(UserGroup, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found",
        )

    # Find membership
    stmt = select(UserGroupMember).where(
        UserGroupMember.group_id == group_id,
        UserGroupMember.user_id == user_id,
    )
    membership = (await session.exec(stmt)).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group",
        )

    # Remove member
    await session.delete(membership)
    await session.commit()

    logger.info(f"User {user_id} removed from group {group_id} by user {current_user.id}")

    # Invalidate user cache
    cache = get_permission_cache()
    await cache.invalidate_user(user_id)

    # Audit logging
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="group_member.removed",
        resource_type="group",
        resource_id=group_id,
        details={"user_id": str(user_id)}
    )

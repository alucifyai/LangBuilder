"""Event-based cache invalidation for RBAC system.

This module provides database event listeners that automatically invalidate
the permission cache when RBAC state changes occur. This ensures that permission
changes are immediately reflected without waiting for TTL expiration.

Event Listeners:
- RoleAssignment changes (create/update/delete) → invalidate user/group cache
- RolePermission changes (create/delete) → invalidate entire cache (role modified)
- UserGroupMember changes (create/update/delete) → invalidate user cache

See docs/code-generations/CACHE_INVALIDATION_STRATEGY.md for detailed strategy.
"""

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from langflow.services.rbac.cache import get_permission_cache

if TYPE_CHECKING:
    from sqlalchemy.orm.mapper import Mapper


logger = logging.getLogger(__name__)

# Track if listeners have been registered
_listeners_registered = False


def _invalidate_for_user(user_id: UUID) -> None:
    """Invalidate cache for a user (sync wrapper for async cache operation).

    Args:
        user_id: User UUID to invalidate

    Note:
        This is a synchronous wrapper since SQLAlchemy event listeners
        cannot be async. The cache operations are thread-safe.
    """
    import asyncio

    cache = get_permission_cache()

    try:
        # Create event loop if needed (for sync context)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the coroutine
            loop.create_task(cache.invalidate_user(user_id))
        else:
            # If no loop, run it
            loop.run_until_complete(cache.invalidate_user(user_id))
    except RuntimeError:
        # No event loop in current thread, create new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cache.invalidate_user(user_id))
        finally:
            loop.close()


def _invalidate_for_role(role_id: UUID) -> None:
    """Invalidate cache for a role (sync wrapper for async cache operation).

    Args:
        role_id: Role UUID to invalidate

    Note:
        This clears the entire cache since tracking all users with a role
        is complex. See CACHE_INVALIDATION_STRATEGY.md for details.
    """
    import asyncio

    cache = get_permission_cache()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cache.invalidate_role(role_id))
        else:
            loop.run_until_complete(cache.invalidate_role(role_id))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cache.invalidate_role(role_id))
        finally:
            loop.close()


def _invalidate_for_resource(resource_type: str, resource_id: UUID) -> None:
    """Invalidate cache for a resource (sync wrapper for async cache operation).

    Args:
        resource_type: Type of resource (e.g., "flow", "project")
        resource_id: Resource UUID to invalidate
    """
    import asyncio

    cache = get_permission_cache()

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cache.invalidate_resource(resource_type, resource_id))
        else:
            loop.run_until_complete(cache.invalidate_resource(resource_type, resource_id))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(cache.invalidate_resource(resource_type, resource_id))
        finally:
            loop.close()


async def _get_group_member_user_ids(session: AsyncSession, group_id: UUID) -> list[UUID]:
    """Get all active user IDs in a group.

    Args:
        session: Database session
        group_id: Group UUID

    Returns:
        List of user IDs
    """
    from sqlmodel import select

    from langflow.services.database.models.user_group.model import UserGroupMember

    result = await session.execute(
        select(UserGroupMember.user_id).where(
            UserGroupMember.group_id == group_id,
            UserGroupMember.is_active == True,  # noqa: E712
        )
    )
    return [row[0] for row in result.all()]


# ============================================================================
# Registration Function
# ============================================================================


def register_rbac_cache_invalidation_listeners() -> None:
    """Register all RBAC cache invalidation event listeners.

    This function should be called during application initialization to ensure
    that cache invalidation happens automatically when RBAC state changes.

    Example:
        >>> from langflow.services.rbac.events import register_rbac_cache_invalidation_listeners
        >>> register_rbac_cache_invalidation_listeners()

    Note:
        Event listeners are registered globally with SQLAlchemy and will trigger
        for all database sessions. They are automatically enabled when this module
        is imported and this function is called.
    """
    global _listeners_registered

    if _listeners_registered:
        logger.debug("RBAC cache invalidation listeners already registered")
        return

    # Import models to ensure they're registered with SQLAlchemy
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.rbac.role_permission import RolePermission
    from langflow.services.database.models.user_group.model import UserGroupMember

    # ============================================================================
    # RoleAssignment Event Listeners
    # ============================================================================

    @event.listens_for(RoleAssignment, "after_insert", propagate=True)
    def on_role_assignment_created(mapper: "Mapper", connection: Session, target: RoleAssignment) -> None:
        """Invalidate cache when role assignment is created."""
        logger.debug(f"Event: RoleAssignment created - {target.assignee_type} assignment {target.id}")

        if target.assignee_type == "user" and target.user_id:
            _invalidate_for_user(target.user_id)
            logger.info(f"Invalidated cache for user {target.user_id} (role assignment created)")

        elif target.assignee_type == "service_account" and target.service_account_id:
            _invalidate_for_user(target.service_account_id)
            logger.info(f"Invalidated cache for service account {target.service_account_id}")

        elif target.assignee_type == "group" and target.group_id:
            session = Session.object_session(target) or Session(bind=connection)

            try:
                members = session.query(UserGroupMember.user_id).filter(
                    UserGroupMember.group_id == target.group_id,
                    UserGroupMember.is_active == True,  # noqa: E712
                ).all()

                for (user_id,) in members:
                    _invalidate_for_user(user_id)

                logger.info(
                    f"Invalidated cache for {len(members)} users in group {target.group_id} "
                    "(role assignment created)"
                )
            except Exception as e:
                logger.error(f"Failed to invalidate cache for group members: {e}")

    @event.listens_for(RoleAssignment, "after_update", propagate=True)
    def on_role_assignment_updated(mapper: "Mapper", connection: Session, target: RoleAssignment) -> None:
        """Invalidate cache when role assignment is updated."""
        logger.debug(f"Event: RoleAssignment updated - {target.assignee_type} assignment {target.id}")

        if target.assignee_type == "user" and target.user_id:
            _invalidate_for_user(target.user_id)
            logger.info(f"Invalidated cache for user {target.user_id} (role assignment updated)")

        elif target.assignee_type == "service_account" and target.service_account_id:
            _invalidate_for_user(target.service_account_id)
            logger.info(f"Invalidated cache for service account {target.service_account_id}")

        elif target.assignee_type == "group" and target.group_id:
            session = Session.object_session(target) or Session(bind=connection)

            try:
                members = session.query(UserGroupMember.user_id).filter(
                    UserGroupMember.group_id == target.group_id,
                    UserGroupMember.is_active == True,  # noqa: E712
                ).all()

                for (user_id,) in members:
                    _invalidate_for_user(user_id)

                logger.info(
                    f"Invalidated cache for {len(members)} users in group {target.group_id} "
                    "(role assignment updated)"
                )
            except Exception as e:
                logger.error(f"Failed to invalidate cache for group members: {e}")

    @event.listens_for(RoleAssignment, "after_delete", propagate=True)
    def on_role_assignment_deleted(mapper: "Mapper", connection: Session, target: RoleAssignment) -> None:
        """Invalidate cache when role assignment is deleted."""
        logger.debug(f"Event: RoleAssignment deleted - {target.assignee_type} assignment {target.id}")

        if target.assignee_type == "user" and target.user_id:
            _invalidate_for_user(target.user_id)
            logger.info(f"Invalidated cache for user {target.user_id} (role assignment deleted)")

        elif target.assignee_type == "service_account" and target.service_account_id:
            _invalidate_for_user(target.service_account_id)
            logger.info(f"Invalidated cache for service account {target.service_account_id}")

        elif target.assignee_type == "group" and target.group_id:
            session = Session.object_session(target) or Session(bind=connection)

            try:
                members = session.query(UserGroupMember.user_id).filter(
                    UserGroupMember.group_id == target.group_id,
                    UserGroupMember.is_active == True,  # noqa: E712
                ).all()

                for (user_id,) in members:
                    _invalidate_for_user(user_id)

                logger.info(
                    f"Invalidated cache for {len(members)} users in group {target.group_id} "
                    "(role assignment deleted)"
                )
            except Exception as e:
                logger.error(f"Failed to invalidate cache for group members: {e}")

    # ============================================================================
    # RolePermission Event Listeners
    # ============================================================================

    @event.listens_for(RolePermission, "after_insert", propagate=True)
    def on_role_permission_created(mapper: "Mapper", connection: Session, target: RolePermission) -> None:
        """Invalidate cache when permission is added to role."""
        logger.debug(f"Event: RolePermission created - role {target.role_id}, permission {target.permission_id}")
        _invalidate_for_role(target.role_id)
        logger.info(f"Invalidated cache for role {target.role_id} (permission added)")

    @event.listens_for(RolePermission, "after_delete", propagate=True)
    def on_role_permission_deleted(mapper: "Mapper", connection: Session, target: RolePermission) -> None:
        """Invalidate cache when permission is removed from role."""
        logger.debug(f"Event: RolePermission deleted - role {target.role_id}, permission {target.permission_id}")
        _invalidate_for_role(target.role_id)
        logger.info(f"Invalidated cache for role {target.role_id} (permission removed)")

    # ============================================================================
    # UserGroupMember Event Listeners
    # ============================================================================

    @event.listens_for(UserGroupMember, "after_insert", propagate=True)
    def on_group_member_added(mapper: "Mapper", connection: Session, target: UserGroupMember) -> None:
        """Invalidate cache when user joins a group."""
        logger.debug(f"Event: UserGroupMember created - user {target.user_id} joined group {target.group_id}")
        _invalidate_for_user(target.user_id)
        logger.info(f"Invalidated cache for user {target.user_id} (joined group {target.group_id})")

    @event.listens_for(UserGroupMember, "after_update", propagate=True)
    def on_group_member_updated(mapper: "Mapper", connection: Session, target: UserGroupMember) -> None:
        """Invalidate cache when group membership is updated."""
        logger.debug(f"Event: UserGroupMember updated - user {target.user_id} in group {target.group_id}")
        _invalidate_for_user(target.user_id)
        logger.info(f"Invalidated cache for user {target.user_id} (group membership updated)")

    @event.listens_for(UserGroupMember, "after_delete", propagate=True)
    def on_group_member_removed(mapper: "Mapper", connection: Session, target: UserGroupMember) -> None:
        """Invalidate cache when user leaves a group."""
        logger.debug(f"Event: UserGroupMember deleted - user {target.user_id} left group {target.group_id}")
        _invalidate_for_user(target.user_id)
        logger.info(f"Invalidated cache for user {target.user_id} (left group {target.group_id})")

    _listeners_registered = True

    logger.info("RBAC cache invalidation event listeners registered")
    logger.debug(
        f"Listening for events on: {RoleAssignment.__tablename__}, "
        f"{RolePermission.__tablename__}, {UserGroupMember.__tablename__}"
    )


# ============================================================================
# Convenience Functions for Manual Cache Invalidation
# ============================================================================


async def invalidate_user_cache_async(session: AsyncSession, user_id: UUID) -> None:
    """Async helper to invalidate cache for a user.

    Use this in API endpoints or async contexts where you need explicit cache invalidation.

    Args:
        session: Async database session (unused, but kept for API consistency)
        user_id: User UUID to invalidate

    Example:
        >>> from langflow.services.rbac.events import invalidate_user_cache_async
        >>> await invalidate_user_cache_async(session, user.id)
    """
    cache = get_permission_cache()
    await cache.invalidate_user(user_id)
    logger.info(f"Manually invalidated cache for user {user_id}")


async def invalidate_group_members_cache_async(session: AsyncSession, group_id: UUID) -> None:
    """Async helper to invalidate cache for all members of a group.

    Use this when group role assignments change.

    Args:
        session: Async database session
        group_id: Group UUID

    Example:
        >>> from langflow.services.rbac.events import invalidate_group_members_cache_async
        >>> await invalidate_group_members_cache_async(session, group.id)
    """
    user_ids = await _get_group_member_user_ids(session, group_id)

    cache = get_permission_cache()
    for user_id in user_ids:
        await cache.invalidate_user(user_id)

    logger.info(f"Manually invalidated cache for {len(user_ids)} users in group {group_id}")


async def invalidate_role_cache_async(session: AsyncSession, role_id: UUID) -> None:
    """Async helper to invalidate cache for a role.

    Use this when role permissions are modified.

    Args:
        session: Async database session (unused, but kept for API consistency)
        role_id: Role UUID to invalidate

    Example:
        >>> from langflow.services.rbac.events import invalidate_role_cache_async
        >>> await invalidate_role_cache_async(session, role.id)
    """
    cache = get_permission_cache()
    await cache.invalidate_role(role_id)
    logger.info(f"Manually invalidated cache for role {role_id}")


async def invalidate_resource_cache_async(
    session: AsyncSession,
    resource_type: str,
    resource_id: UUID,
) -> None:
    """Async helper to invalidate cache for a resource.

    Use this when resource-scoped assignments change or resources move between scopes.

    Args:
        session: Async database session (unused, but kept for API consistency)
        resource_type: Type of resource (e.g., "flow", "project")
        resource_id: Resource UUID to invalidate

    Example:
        >>> from langflow.services.rbac.events import invalidate_resource_cache_async
        >>> await invalidate_resource_cache_async(session, "flow", flow.id)
    """
    cache = get_permission_cache()
    await cache.invalidate_resource(resource_type, resource_id)
    logger.info(f"Manually invalidated cache for {resource_type} {resource_id}")

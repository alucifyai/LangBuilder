"""RBAC enforcement engine for permission evaluation.

This module provides the core permission evaluation logic for the RBAC system,
including group role aggregation, scope resolution, and caching.
"""

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.rbac.cache import PermissionCache, get_permission_cache
from langflow.services.rbac.constants import expand_wildcards
from langflow.services.rbac.scope_resolver import ScopeResolver

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment

logger = logging.getLogger(__name__)


class RBACEnforcementEngine:
    """Core RBAC permission evaluation engine.

    Provides has_permission() method that checks if a user has a specific permission
    on a resource, considering:
    - Direct user role assignments
    - Group role assignments (aggregated from user's groups)
    - Scope hierarchy (workspace > project > environment > flow > component)
    - Permission caching for performance
    - Deny-by-default security model
    """

    def __init__(
        self,
        session: AsyncSession,
        cache: PermissionCache | None = None,
    ):
        """Initialize the RBAC enforcement engine.

        Args:
            session: Async database session for querying
            cache: Permission cache instance (uses global cache if None)
        """
        self.session = session
        self.cache = cache or get_permission_cache()
        self.scope_resolver = ScopeResolver(session)

    async def has_permission(
        self,
        user_id: UUID,
        permission: str,
        resource_type: str,
        resource_id: UUID,
    ) -> bool:
        """Check if user has permission on resource.

        This is the main entry point for permission checking. It:
        1. Checks cache for cached result
        2. Resolves scope chain from resource to workspace
        3. Gets effective role assignments (user + groups)
        4. Checks if any assignment grants the permission
        5. Caches the result

        Args:
            user_id: User or service account UUID
            permission: Permission string (e.g., "flow.read", "project.update")
            resource_type: Type of resource ("workspace", "project", "environment", "flow", "component")
            resource_id: UUID of the resource

        Returns:
            True if user has permission, False otherwise (deny-by-default)

        Examples:
            >>> engine = RBACEnforcementEngine(session)
            >>> has_read = await engine.has_permission(
            ...     user_id=user.id,
            ...     permission="flow.read",
            ...     resource_type="flow",
            ...     resource_id=flow.id
            ... )
        """
        # 1. Check cache
        cached_result = await self.cache.get(user_id, permission, resource_type, resource_id)
        if cached_result is not None:
            logger.debug(
                f"Permission check (cached): user={user_id}, perm={permission}, "
                f"resource={resource_type}/{resource_id} => {cached_result}"
            )
            return cached_result

        # 2. Resolve scope chain
        try:
            scope_chain = await self.scope_resolver.resolve_scope_chain(resource_type, resource_id)
        except ValueError as e:
            logger.error(f"Failed to resolve scope chain: {e}")
            # Cache negative result to avoid repeated failed lookups
            await self.cache.set(user_id, permission, resource_type, resource_id, False)
            return False

        # 3. Get effective role assignments (user + groups)
        assignments = await self.get_effective_assignments(user_id, scope_chain)

        # 4. Check if any assignment grants the permission
        has_perm = False
        for assignment in assignments:
            role_permissions = await self._get_role_permissions(assignment.role_id)

            # Check for exact permission match or wildcard
            if permission in role_permissions:
                has_perm = True
                logger.debug(
                    f"Permission granted: user={user_id}, perm={permission}, "
                    f"role={assignment.role_id}, scope={assignment.scope_type}/{assignment.scope_id}"
                )
                break

            # Check for wildcard patterns (e.g., "flow.*" grants "flow.read")
            expanded_permissions = expand_wildcards(role_permissions)
            if permission in expanded_permissions:
                has_perm = True
                logger.debug(
                    f"Permission granted (wildcard): user={user_id}, perm={permission}, "
                    f"role={assignment.role_id}, scope={assignment.scope_type}/{assignment.scope_id}"
                )
                break

        # 5. Cache result
        await self.cache.set(user_id, permission, resource_type, resource_id, has_perm)

        logger.debug(
            f"Permission check: user={user_id}, perm={permission}, "
            f"resource={resource_type}/{resource_id} => {has_perm}"
        )

        return has_perm

    async def get_effective_assignments(
        self,
        user_id: UUID,
        scope_chain: list[tuple[str, UUID]],
    ) -> list["RoleAssignment"]:
        """Get all effective role assignments for user across scope chain.

        Includes assignments via:
        - Direct user assignments
        - Group membership (aggregated from user's active groups)

        Returns assignments from closest scope to broadest scope, allowing
        "closest scope wins" precedence in permission evaluation.

        Args:
            user_id: User or service account UUID
            scope_chain: List of (scope_type, scope_id) tuples from specific to broad

        Returns:
            List of RoleAssignment objects
        """
        from langflow.services.database.models.rbac.role_assignment import RoleAssignment
        from langflow.services.database.models.user_group.model import UserGroupMember

        assignments: list[RoleAssignment] = []

        # Get user's active group memberships
        user_groups_result = await self.session.execute(
            select(UserGroupMember.group_id).where(
                UserGroupMember.user_id == user_id,
                UserGroupMember.is_active == True,  # noqa: E712
            )
        )
        group_ids = [row[0] for row in user_groups_result]

        logger.debug(f"User {user_id} is member of {len(group_ids)} groups")

        # For each scope in chain (closest to broadest)
        for scope_type, scope_id in scope_chain:
            # Direct user assignments
            user_assignments_result = await self.session.execute(
                select(RoleAssignment).where(
                    RoleAssignment.assignee_type == "user",
                    RoleAssignment.user_id == user_id,
                    RoleAssignment.scope_type == scope_type,
                    RoleAssignment.scope_id == scope_id,
                    RoleAssignment.is_active == True,  # noqa: E712
                    or_(
                        RoleAssignment.expires_at.is_(None),
                        RoleAssignment.expires_at > datetime.now(timezone.utc),
                    ),
                )
            )
            user_assignments = user_assignments_result.scalars().all()
            assignments.extend(user_assignments)

            logger.debug(
                f"Found {len(user_assignments)} direct assignments for user {user_id} "
                f"at {scope_type}/{scope_id}"
            )

            # Group assignments
            if group_ids:
                group_assignments_result = await self.session.execute(
                    select(RoleAssignment).where(
                        RoleAssignment.assignee_type == "group",
                        RoleAssignment.group_id.in_(group_ids),
                        RoleAssignment.scope_type == scope_type,
                        RoleAssignment.scope_id == scope_id,
                        RoleAssignment.is_active == True,  # noqa: E712
                        or_(
                            RoleAssignment.expires_at.is_(None),
                            RoleAssignment.expires_at > datetime.now(timezone.utc),
                        ),
                    )
                )
                group_assignments = group_assignments_result.scalars().all()
                assignments.extend(group_assignments)

                logger.debug(
                    f"Found {len(group_assignments)} group assignments for user {user_id} "
                    f"at {scope_type}/{scope_id}"
                )

        return assignments

    async def _get_role_permissions(self, role_id: UUID) -> set[str]:
        """Get all permission strings for a role.

        Args:
            role_id: Role UUID

        Returns:
            Set of permission strings (e.g., {"flow.read", "flow.update", "project.*"})
        """
        from langflow.services.database.models.rbac.permission import Permission
        from langflow.services.database.models.rbac.role_permission import RolePermission

        # Query role permissions with join to get permission resource_type and action
        result = await self.session.execute(
            select(Permission.resource_type, Permission.action)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )

        # Combine resource_type and action to form permission strings
        permissions = {f"{resource_type}.{action}" for resource_type, action in result.all()}

        logger.debug(f"Role {role_id} has {len(permissions)} permissions")

        return permissions

    async def check_resource_access(
        self,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
    ) -> bool:
        """Convenience method for checking resource access with common action patterns.

        Maps common CRUD actions to permission strings.

        Args:
            user_id: User UUID
            action: Action string ("read", "create", "update", "delete", "export", "deploy")
            resource_type: Type of resource
            resource_id: Resource UUID

        Returns:
            True if user can perform action on resource

        Examples:
            >>> can_read = await engine.check_resource_access(
            ...     user_id=user.id,
            ...     action="read",
            ...     resource_type="flow",
            ...     resource_id=flow.id
            ... )
        """
        # Map action to permission string
        permission = f"{resource_type}.{action}"

        return await self.has_permission(user_id, permission, resource_type, resource_id)

    async def get_user_permissions_for_resource(
        self,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
    ) -> set[str]:
        """Get all permissions a user has on a specific resource.

        Useful for generating UI permission matrices or debugging.

        Args:
            user_id: User UUID
            resource_type: Type of resource
            resource_id: Resource UUID

        Returns:
            Set of permission strings user has on the resource
        """
        # Resolve scope chain
        try:
            scope_chain = await self.scope_resolver.resolve_scope_chain(resource_type, resource_id)
        except ValueError as e:
            logger.error(f"Failed to resolve scope chain: {e}")
            return set()

        # Get effective assignments
        assignments = await self.get_effective_assignments(user_id, scope_chain)

        # Collect all permissions from all roles
        all_permissions: set[str] = set()
        for assignment in assignments:
            role_permissions = await self._get_role_permissions(assignment.role_id)
            all_permissions.update(role_permissions)

        # Expand wildcards
        expanded_permissions = expand_wildcards(all_permissions)

        return expanded_permissions

    async def invalidate_user_cache(self, user_id: UUID) -> None:
        """Invalidate cached permissions for a user.

        Should be called when:
        - User's role assignments change
        - User joins/leaves a group
        - User's group's role assignments change

        Args:
            user_id: User UUID
        """
        await self.cache.invalidate_user(user_id)
        logger.info(f"Invalidated permission cache for user {user_id}")

    async def invalidate_role_cache(self, role_id: UUID) -> None:
        """Invalidate cached permissions for all users with a role.

        Should be called when:
        - Role's permissions are modified
        - Role is deleted

        Args:
            role_id: Role UUID
        """
        await self.cache.invalidate_role(role_id)
        logger.info(f"Invalidated permission cache for role {role_id}")

    async def invalidate_resource_cache(
        self,
        resource_type: str,
        resource_id: UUID,
    ) -> None:
        """Invalidate cached permissions for a resource.

        Should be called when:
        - Resource-scoped role assignments change
        - Resource moves to different workspace/project

        Args:
            resource_type: Type of resource
            resource_id: Resource UUID
        """
        await self.cache.invalidate_resource(resource_type, resource_id)
        logger.info(f"Invalidated permission cache for {resource_type} {resource_id}")

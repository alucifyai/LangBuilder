"""Permission evaluation engine for RBAC system.

Implements Phase 2 of RBAC implementation:
- Permission checking logic
- Scope inheritance resolution
- Grant evaluation with caching

PRD References:
- Story 2.1 @AC4: Higher-scope grants cascade to lower scopes
- Story 3.1: Query and filter grants
- Story 4.1: Permission checking at runtime
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

    from langflow.services.database.models.rbac.grant import PrincipalType, ScopeType


class PermissionEvaluator:
    """Core permission evaluation engine.

    Evaluates whether a principal (user/group/service_account) has
    a specific permission at a given scope, considering:
    1. Direct grants to the principal
    2. Group membership grants
    3. Scope inheritance (workspace > project > environment > flow > component)
    4. Time-bound grants (expiration)
    """

    # Scope hierarchy ranks (lower number = higher scope, PRD Story 2.1 @AC3)
    SCOPE_HIERARCHY = {
        "workspace": 1,
        "project": 2,
        "environment": 3,
        "flow": 4,
        "component": 5,
    }

    def __init__(
        self,
        session: AsyncSession,
        use_cache: bool = True,
        audit_denials: bool = False
    ):
        """Initialize evaluator with database session.

        Args:
            session: Database session for queries
            use_cache: Whether to use permission caching (default True)
            audit_denials: Whether to audit permission denials (default False)
                          MEDIUM PRIORITY FIX #3: Permission check audit logging
                          Phase 2 Audit Recommendation #3
        """
        self.session = session
        self.use_cache = use_cache
        self.audit_denials = audit_denials
        if use_cache:
            from langflow.services.auth.permission_cache import get_permission_cache

            self.cache = get_permission_cache()
        else:
            self.cache = None

    async def has_permission(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permission: str,
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> bool:
        """Check if principal has permission at given scope.

        Implements PRD Story 4.1 @AC1: Permission checking at runtime.

        Args:
            principal_type: Type of principal (user, group, service_account)
            principal_id: ID of the principal
            permission: Permission to check (format: "resource_type:action")
            scope_type: Type of scope (workspace, project, environment, flow, component)
            scope_id: ID of the scoped resource

        Returns:
            True if principal has permission, False otherwise
        """
        from langflow.services.database.models.rbac.grant import PrincipalType as PT

        # Convert string to enum if needed
        if isinstance(principal_type, str):
            principal_type = PT(principal_type)

        # Check cache first
        if self.use_cache and self.cache:
            cached = await self.cache.get(
                principal_type, principal_id, permission, scope_type, scope_id
            )
            if cached is not None:
                return cached

        # Get all applicable grants (direct + inherited scopes)
        grants = await self._get_applicable_grants(
            principal_type=principal_type,
            principal_id=str(principal_id),
            scope_type=str(scope_type),
            scope_id=scope_id,
        )

        # Check if any grant includes the required permission
        result = False
        for grant in grants:
            # Skip expired grants (PRD Story 3.4 @AC3)
            if grant.expires_at and grant.expires_at < datetime.now(timezone.utc):
                continue

            # Get role and check permissions
            role = grant.role
            if permission in role.permissions:
                logger.debug(
                    f"Permission granted: {principal_type}:{principal_id} has {permission} "
                    f"at {scope_type}:{scope_id} via role {role.name}"
                )
                result = True
                break

        if not result:
            logger.debug(
                f"Permission denied: {principal_type}:{principal_id} lacks {permission} "
                f"at {scope_type}:{scope_id}"
            )

            # MEDIUM PRIORITY FIX #3: Audit permission denials
            # Phase 2 Audit Recommendation #3
            if self.audit_denials:
                try:
                    from langflow.services.database.models.rbac.crud import create_audit_log
                    from langflow.services.database.models.rbac.audit_log import AuditAction

                    await create_audit_log(
                        session=self.session,
                        action=AuditAction.PERMISSION_CHECK_DENIED,
                        actor_type=str(principal_type),
                        actor_id=str(principal_id),
                        resource_type=str(scope_type),
                        resource_id=scope_id,
                        details={
                            "permission": permission,
                            "result": "denied",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                except Exception as e:
                    # Don't fail permission check if audit logging fails
                    logger.warning(f"Failed to audit permission denial: {e}")

        # Cache the result
        if self.use_cache and self.cache:
            await self.cache.set(
                principal_type, principal_id, permission, scope_type, scope_id, result
            )

        return result

    async def has_any_permission(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permissions: list[str],
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> bool:
        """Check if principal has ANY of the specified permissions.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            permissions: List of permissions to check
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            True if principal has at least one permission, False otherwise
        """
        for permission in permissions:
            if await self.has_permission(principal_type, principal_id, permission, scope_type, scope_id):
                return True
        return False

    async def has_all_permissions(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permissions: list[str],
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> bool:
        """Check if principal has ALL of the specified permissions.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            permissions: List of permissions to check
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            True if principal has all permissions, False otherwise
        """
        for permission in permissions:
            if not await self.has_permission(principal_type, principal_id, permission, scope_type, scope_id):
                return False
        return True

    async def _get_applicable_grants(
        self,
        principal_type: PrincipalType | str,
        principal_id: str,
        scope_type: str,
        scope_id: str,
    ) -> list:
        """Get all grants applicable to the principal at the given scope.

        Includes:
        1. Direct grants to the principal at this scope
        2. Direct grants to the principal at higher scopes (inheritance)
        3. Group grants (if principal is a user)

        Implements PRD Story 2.1 @AC4: Scope inheritance.

        Args:
            principal_type: Type of principal
            principal_id: ID of the principal
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            List of Grant objects with populated role relationships
        """
        from sqlalchemy.orm import selectinload
        from sqlmodel import or_, select

        from langflow.services.database.models.rbac.grant import Grant, PrincipalType as PT

        # Build query for direct grants
        grants_query = (
            select(Grant)
            .options(selectinload(Grant.role))  # Eager load role for permission checking
            .where(
                Grant.principal_type == str(principal_type),
                Grant.principal_id == principal_id,
            )
        )

        # Execute query to get all grants for this principal
        # We'll filter by scope after fetching
        result = await self.session.exec(grants_query)
        all_grants = list(result.all())

        # Filter grants by scope inheritance using database-backed checking
        # HIGH PRIORITY FIX #1: Production scope inheritance
        # Phase 2 Audit Recommendation #1
        from langflow.services.auth.scope_resolver import ScopeResolver

        grants = []
        for grant in all_grants:
            # Check if this grant's scope includes the requested scope
            if await ScopeResolver.scope_includes(
                grant_scope_type=grant.scope_type,
                grant_scope_id=grant.scope_id,
                check_scope_type=scope_type,
                check_scope_id=scope_id,
                db=self.session,
            ):
                grants.append(grant)

        # If principal is a user, also get grants via group membership
        if str(principal_type) == str(PT.USER):
            group_grants = await self._get_group_grants_for_user(
                user_id=principal_id,
                scope_type=scope_type,
                scope_id=scope_id,
            )
            grants.extend(group_grants)

        return grants

    async def _get_group_grants_for_user(
        self,
        user_id: str,
        scope_type: str,
        scope_id: str,
    ) -> list:
        """Get grants from groups that the user is a member of.

        Implements PRD Story 2.3 @AC3: Group membership drives roles.

        Args:
            user_id: ID of the user
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            List of Grant objects from user's groups
        """
        from sqlalchemy.orm import selectinload
        from sqlmodel import or_, select, text

        from langflow.services.database.models.rbac.grant import Grant, PrincipalType

        # Get user's groups via user_group association table
        group_query = text(
            "SELECT group_id FROM user_group WHERE user_id = :user_id"
        )
        result = await self.session.exec(group_query, {"user_id": user_id})
        group_ids = [row[0] for row in result.all()]

        if not group_ids:
            return []

        # Get grants for these groups
        grants_query = (
            select(Grant)
            .options(selectinload(Grant.role))
            .where(
                Grant.principal_type == PrincipalType.GROUP,
                Grant.principal_id.in_(group_ids),
            )
        )

        # Execute query to get all group grants
        result = await self.session.exec(grants_query)
        all_grants = list(result.all())

        # Filter grants by scope inheritance using database-backed checking
        # HIGH PRIORITY FIX #1: Production scope inheritance
        from langflow.services.auth.scope_resolver import ScopeResolver

        grants = []
        for grant in all_grants:
            # Check if this grant's scope includes the requested scope
            if await ScopeResolver.scope_includes(
                grant_scope_type=grant.scope_type,
                grant_scope_id=grant.scope_id,
                check_scope_type=scope_type,
                check_scope_id=scope_id,
                db=self.session,
            ):
                grants.append(grant)

        return grants

    async def get_user_permissions_at_scope(
        self,
        user_id: UUID | str,
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> set[str]:
        """Get all permissions a user has at a given scope.

        Useful for UI permission checks and bulk authorization.

        Args:
            user_id: ID of the user
            scope_type: Type of scope
            scope_id: ID of the scoped resource

        Returns:
            Set of permission IDs the user has
        """
        from langflow.services.database.models.rbac.grant import PrincipalType

        grants = await self._get_applicable_grants(
            principal_type=PrincipalType.USER,
            principal_id=str(user_id),
            scope_type=str(scope_type),
            scope_id=scope_id,
        )

        permissions = set()
        now = datetime.now(timezone.utc)

        for grant in grants:
            # Skip expired grants
            if grant.expires_at and grant.expires_at < now:
                continue

            permissions.update(grant.role.permissions)

        return permissions


# Convenience function for quick permission checks
async def check_permission(
    session: AsyncSession,
    principal_type: PrincipalType | str,
    principal_id: UUID | str,
    permission: str,
    scope_type: ScopeType | str,
    scope_id: str,
) -> bool:
    """Convenience function for permission checking.

    Args:
        session: Database session
        principal_type: Type of principal
        principal_id: ID of the principal
        permission: Permission to check
        scope_type: Type of scope
        scope_id: ID of the scoped resource

    Returns:
        True if permission is granted, False otherwise
    """
    evaluator = PermissionEvaluator(session)
    return await evaluator.has_permission(
        principal_type=principal_type,
        principal_id=principal_id,
        permission=permission,
        scope_type=scope_type,
        scope_id=scope_id,
    )

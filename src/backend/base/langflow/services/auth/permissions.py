"""
Permission Enforcement Service

Provides permission checking with scope hierarchy support.
Implements the authorization logic for RBAC.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.grant.model import Grant, PrincipalType, ScopeType
from langflow.services.database.models.role.crud import get_role_by_id
from langflow.services.database.models.user.model import User


class PermissionDenied(Exception):
    """Exception raised when permission is denied."""

    def __init__(self, message: str = "Permission denied", required_permission: str | None = None):
        self.required_permission = required_permission
        super().__init__(message)


# Scope hierarchy (highest to lowest)
SCOPE_HIERARCHY = [
    ScopeType.WORKSPACE,
    ScopeType.PROJECT,
    ScopeType.ENVIRONMENT,
    ScopeType.FLOW,
    ScopeType.COMPONENT,
]


def get_scope_rank(scope_type: ScopeType) -> int:
    """Get the rank of a scope type in the hierarchy (lower is higher)."""
    try:
        return SCOPE_HIERARCHY.index(scope_type)
    except ValueError:
        return len(SCOPE_HIERARCHY)


async def get_user_grants(db: AsyncSession, user: User) -> list[Grant]:
    """
    Get all active grants for a user.
    Includes both direct user grants and grants via group membership.

    Args:
        db: Database session
        user: User to get grants for

    Returns:
        List of active (non-expired) grants
    """
    from langflow.services.database.models.group import get_user_groups

    now = datetime.now(timezone.utc)
    all_grants = []

    # 1. Get direct user grants
    stmt = (
        select(Grant)
        .where(Grant.principal_type == PrincipalType.USER)
        .where(Grant.principal_id == str(user.id))
        .where((Grant.expires_at.is_(None)) | (Grant.expires_at > now))
    )

    result = await db.exec(stmt)
    all_grants.extend(result.all())

    # 2. Get grants via group membership
    group_ids = await get_user_groups(db, user.id)
    for group_id in group_ids:
        stmt = (
            select(Grant)
            .where(Grant.principal_type == PrincipalType.GROUP)
            .where(Grant.principal_id == str(group_id))
            .where((Grant.expires_at.is_(None)) | (Grant.expires_at > now))
        )
        result = await db.exec(stmt)
        all_grants.extend(result.all())

    return all_grants


async def check_permission(
    db: AsyncSession,
    user: User,
    permission: str,
    scope_type: ScopeType,
    scope_id: str,
) -> bool:
    """
    Check if a user has a specific permission at a given scope.

    Implements scope hierarchy: permissions granted at higher scopes
    cascade down to lower scopes.

    Args:
        db: Database session
        user: User to check permission for
        permission: Permission ID to check (e.g., "flows:read")
        scope_type: Scope type where permission is required
        scope_id: Scope ID where permission is required

    Returns:
        True if user has permission, False otherwise
    """
    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Get all active grants for user
    grants = await get_user_grants(db, user)

    # Get the rank of the required scope
    required_rank = get_scope_rank(scope_type)

    # Check each grant
    for grant in grants:
        # Get the grant's scope rank
        grant_rank = get_scope_rank(grant.scope_type)

        # Only consider grants at same level or higher (lower rank number)
        if grant_rank > required_rank:
            continue

        # If grant is at same scope, check exact match
        if grant.scope_type == scope_type:
            if grant.scope_id != scope_id:
                continue

        # If grant is at higher scope, it applies (cascading)
        # For now, we assume scope_id contains the hierarchy
        # E.g., "workspace-1/project-2" means project-2 is in workspace-1
        # This is a simplified check - production would need proper hierarchy resolution

        # Get the role and check if it has the permission
        role = await get_role_by_id(db, UUID(grant.role_id))
        if role and permission in role.permissions:
            return True

    return False


async def require_permission(
    db: AsyncSession,
    user: User,
    permission: str,
    scope_type: ScopeType,
    scope_id: str,
) -> None:
    """
    Require a user to have a specific permission, raise exception if not.

    Args:
        db: Database session
        user: User to check permission for
        permission: Permission ID to check
        scope_type: Scope type where permission is required
        scope_id: Scope ID where permission is required

    Raises:
        PermissionDenied: If user does not have the required permission
    """
    has_permission = await check_permission(db, user, permission, scope_type, scope_id)

    if not has_permission:
        raise PermissionDenied(
            f"Permission required: {permission} at {scope_type}:{scope_id}",
            required_permission=permission,
        )


async def get_user_permissions(
    db: AsyncSession,
    user: User,
    scope_type: ScopeType,
    scope_id: str,
) -> set[str]:
    """
    Get all permissions a user has at a given scope.

    Args:
        db: Database session
        user: User to get permissions for
        scope_type: Scope type
        scope_id: Scope ID

    Returns:
        Set of permission IDs the user has at this scope
    """
    # Superusers have all permissions
    if user.is_superuser:
        # In production, this would return all permissions from the catalog
        return {"*"}  # Wildcard representing all permissions

    permissions = set()

    # Get all active grants for user
    grants = await get_user_grants(db, user)

    # Get the rank of the required scope
    required_rank = get_scope_rank(scope_type)

    # Check each grant
    for grant in grants:
        # Get the grant's scope rank
        grant_rank = get_scope_rank(grant.scope_type)

        # Only consider grants at same level or higher
        if grant_rank > required_rank:
            continue

        # If grant is at same scope, check exact match
        if grant.scope_type == scope_type:
            if grant.scope_id != scope_id:
                continue

        # Get the role and add its permissions
        role = await get_role_by_id(db, UUID(grant.role_id))
        if role:
            permissions.update(role.permissions)

    return permissions


async def check_any_permission(
    db: AsyncSession,
    user: User,
    permissions: list[str],
    scope_type: ScopeType,
    scope_id: str,
) -> bool:
    """
    Check if user has ANY of the given permissions at a scope.

    Args:
        db: Database session
        user: User to check
        permissions: List of permission IDs (user needs at least one)
        scope_type: Scope type
        scope_id: Scope ID

    Returns:
        True if user has at least one of the permissions
    """
    for permission in permissions:
        if await check_permission(db, user, permission, scope_type, scope_id):
            return True
    return False


async def check_all_permissions(
    db: AsyncSession,
    user: User,
    permissions: list[str],
    scope_type: ScopeType,
    scope_id: str,
) -> bool:
    """
    Check if user has ALL of the given permissions at a scope.

    Args:
        db: Database session
        user: User to check
        permissions: List of permission IDs (user needs all)
        scope_type: Scope type
        scope_id: Scope ID

    Returns:
        True if user has all permissions
    """
    for permission in permissions:
        if not await check_permission(db, user, permission, scope_type, scope_id):
            return False
    return True

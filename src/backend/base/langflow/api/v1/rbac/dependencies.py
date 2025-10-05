"""RBAC API permission check dependencies.

Provides permission checking for RBAC API endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.auth.permissions import PermissionEvaluator
from langflow.services.database.models.rbac.grant import PrincipalType


async def check_rbac_permission(
    permission: str,
    scope_type: str,
    scope_id: str,
    db: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Check if current user has RBAC permission.

    Args:
        permission: Permission to check (e.g., "role:create")
        scope_type: Scope type (usually "workspace" for RBAC operations)
        scope_id: Scope ID (workspace ID)
        db: Database session
        current_user: Current authenticated user

    Raises:
        HTTPException: 403 if permission denied
    """
    evaluator = PermissionEvaluator(session=db, use_cache=True, audit_denials=True)

    has_permission = await evaluator.has_permission(
        principal_type=PrincipalType.USER,
        principal_id=current_user.id,
        permission=permission,
        scope_type=scope_type,
        scope_id=scope_id,
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission} required at {scope_type}:{scope_id}",
        )


class RequireRBACPermission:
    """Dependency for checking RBAC permissions.

    Usage:
        @router.post("/roles")
        async def create_role(
            db: DbSession,
            current_user: CurrentActiveUser,
            _: None = Depends(RequireRBACPermission("role:create", "workspace"))
        ):
            ...
    """

    def __init__(self, permission: str, scope_type: str = "workspace"):
        """Initialize permission requirement.

        Args:
            permission: Permission to check (e.g., "role:create")
            scope_type: Scope type (default "workspace" for RBAC operations)
        """
        self.permission = permission
        self.scope_type = scope_type

    async def __call__(
        self,
        db: DbSession,
        current_user: CurrentActiveUser,
    ) -> None:
        """Check permission.

        For RBAC operations, we check at the user's default workspace.
        In a multi-workspace setup, this would be configurable.
        """
        # For now, use a default workspace concept
        # In production, this would come from user context or request
        workspace_id = "default"

        await check_rbac_permission(
            permission=self.permission,
            scope_type=self.scope_type,
            scope_id=workspace_id,
            db=db,
            current_user=current_user,
        )


# Type aliases for cleaner endpoint signatures
RequireRoleRead = Annotated[None, Depends(RequireRBACPermission("role:read"))]
RequireRoleCreate = Annotated[None, Depends(RequireRBACPermission("role:create"))]
RequireRoleUpdate = Annotated[None, Depends(RequireRBACPermission("role:update"))]
RequireRoleDelete = Annotated[None, Depends(RequireRBACPermission("role:delete"))]

RequirePermissionRead = Annotated[None, Depends(RequireRBACPermission("permission:read"))]

RequireGrantRead = Annotated[None, Depends(RequireRBACPermission("grant:read"))]
RequireGrantCreate = Annotated[None, Depends(RequireRBACPermission("grant:create"))]
RequireGrantUpdate = Annotated[None, Depends(RequireRBACPermission("grant:update"))]
RequireGrantDelete = Annotated[None, Depends(RequireRBACPermission("grant:delete"))]

RequireGroupRead = Annotated[None, Depends(RequireRBACPermission("group:read"))]
RequireGroupCreate = Annotated[None, Depends(RequireRBACPermission("group:create"))]
RequireGroupUpdate = Annotated[None, Depends(RequireRBACPermission("group:update"))]
RequireGroupDelete = Annotated[None, Depends(RequireRBACPermission("group:delete"))]

RequireServiceAccountRead = Annotated[None, Depends(RequireRBACPermission("service_account:read"))]
RequireServiceAccountCreate = Annotated[None, Depends(RequireRBACPermission("service_account:create"))]
RequireServiceAccountUpdate = Annotated[None, Depends(RequireRBACPermission("service_account:update"))]
RequireServiceAccountDelete = Annotated[None, Depends(RequireRBACPermission("service_account:delete"))]

RequireAuditLogRead = Annotated[None, Depends(RequireRBACPermission("audit_log:read"))]


# Simplified permission checker for IaC and compliance endpoints
def RequirePermission(permission: str):
    """Create a permission dependency.

    Simplified version that doesn't require scope for system-level operations.

    Args:
        permission: Permission to check (e.g., "iac:apply", "compliance:read")

    Returns:
        Dependency function
    """
    async def check_permission(
        db: DbSession,
        current_user: CurrentActiveUser,
    ) -> None:
        """Check if user has the required permission."""
        # For system-level operations (iac, compliance), check against "system" scope
        evaluator = PermissionEvaluator(session=db, use_cache=True, audit_denials=True)

        has_permission = await evaluator.has_permission(
            principal_type=PrincipalType.USER,
            principal_id=current_user.id,
            permission=permission,
            scope_type="system",
            scope_id="system",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required",
            )

    return check_permission

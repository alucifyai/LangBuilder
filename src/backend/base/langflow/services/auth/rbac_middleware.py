"""RBAC middleware and decorators for FastAPI.

Provides permission checking decorators and dependency injection
for protecting FastAPI routes with RBAC.

PRD Story 4.1: Runtime permission checking at API endpoints.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable

from fastapi import Depends, HTTPException, status
from loguru import logger

if TYPE_CHECKING:
    from uuid import UUID

    from langflow.services.database.models.rbac.grant import PrincipalType, ScopeType
    from langflow.services.database.models.user.model import User
    from sqlmodel.ext.asyncio.session import AsyncSession


# Dependency to get current user (uses existing auth)
async def get_current_user_dep() -> User:
    """Get current authenticated user.

    This integrates with the existing auth system.
    In the current codebase, this would use get_current_active_user.
    """
    from langflow.services.auth.utils import get_current_active_user

    # The actual dependency will be injected by FastAPI
    # This is a placeholder for the type
    raise NotImplementedError("Use FastAPI Depends(get_current_active_user)")


class RequirePermission:
    """Dependency class for requiring specific permissions on routes.

    Usage in FastAPI routes:
        @app.get("/flows/{flow_id}")
        async def get_flow(
            flow_id: str,
            user: User = Depends(get_current_active_user),
            _: None = Depends(RequirePermission("flow:read", "flow", lambda flow_id: flow_id))
        ):
            # User has flow:read permission on this flow
            ...
    """

    def __init__(
        self,
        permission: str,
        scope_type: str,
        scope_id_getter: Callable | str,
    ):
        """Initialize permission requirement.

        Args:
            permission: Permission required (e.g., "flow:read")
            scope_type: Scope type (e.g., "flow", "workspace")
            scope_id_getter: Either:
                - A callable that takes route params and returns scope_id
                - A string parameter name to extract from path
        """
        self.permission = permission
        self.scope_type = scope_type
        self.scope_id_getter = scope_id_getter

    async def __call__(
        self,
        user: User = Depends(get_current_user_dep),
        session: AsyncSession = Depends(),  # Database session dependency
    ) -> None:
        """Check if user has required permission.

        Args:
            user: Current authenticated user
            session: Database session

        Raises:
            HTTPException: 403 if permission denied
        """
        from langflow.services.auth.permissions import check_permission
        from langflow.services.database.models.rbac.grant import PrincipalType

        # Get scope_id (this is simplified - in production would extract from route params)
        if callable(self.scope_id_getter):
            scope_id = self.scope_id_getter()
        else:
            scope_id = self.scope_id_getter

        # Check permission
        has_perm = await check_permission(
            session=session,
            principal_type=PrincipalType.USER,
            principal_id=user.id,
            permission=self.permission,
            scope_type=self.scope_type,
            scope_id=scope_id,
        )

        if not has_perm:
            logger.warning(
                f"Permission denied: user {user.id} lacks {self.permission} "
                f"on {self.scope_type}:{scope_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.permission} required",
            )


def require_permission(permission: str, scope_type: str):
    """Decorator for protecting route functions with RBAC.

    This is a function decorator (not a FastAPI dependency).
    Use this when you need to check permissions based on route logic.

    Usage:
        @app.get("/flows/{flow_id}")
        @require_permission("flow:read", "flow")
        async def get_flow(flow_id: str, user: User = Depends(get_current_active_user)):
            # Permission is checked before this function runs
            ...

    Args:
        permission: Permission required
        scope_type: Scope type

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user and session from kwargs (injected by FastAPI)
            user = kwargs.get("user")
            session = kwargs.get("session")

            if not user or not session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Extract scope_id from route parameters
            # This is simplified - in production would be more sophisticated
            scope_id = kwargs.get(f"{scope_type}_id", kwargs.get("id"))

            if not scope_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Scope ID ({scope_type}_id) not provided",
                )

            # Check permission
            from langflow.services.auth.permissions import check_permission
            from langflow.services.database.models.rbac.grant import PrincipalType

            has_perm = await check_permission(
                session=session,
                principal_type=PrincipalType.USER,
                principal_id=user.id,
                permission=permission,
                scope_type=scope_type,
                scope_id=str(scope_id),
            )

            if not has_perm:
                logger.warning(
                    f"Permission denied: user {user.id} lacks {permission} "
                    f"on {scope_type}:{scope_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required",
                )

            # Permission granted, execute route function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def check_user_permission(
    user: User,
    session: AsyncSession,
    permission: str,
    scope_type: ScopeType | str,
    scope_id: str,
) -> bool:
    """Utility function for manual permission checks in route logic.

    Use this when you need conditional logic based on permissions
    rather than hard requirement.

    Args:
        user: Current user
        session: Database session
        permission: Permission to check
        scope_type: Scope type
        scope_id: Scope ID

    Returns:
        True if user has permission, False otherwise
    """
    from langflow.services.auth.permissions import check_permission
    from langflow.services.database.models.rbac.grant import PrincipalType

    return await check_permission(
        session=session,
        principal_type=PrincipalType.USER,
        principal_id=user.id,
        permission=permission,
        scope_type=scope_type,
        scope_id=scope_id,
    )


async def get_user_permissions(
    user: User,
    session: AsyncSession,
    scope_type: ScopeType | str,
    scope_id: str,
) -> set[str]:
    """Get all permissions a user has at a given scope.

    Useful for UI permission checks and feature flags.

    Args:
        user: Current user
        session: Database session
        scope_type: Scope type
        scope_id: Scope ID

    Returns:
        Set of permission IDs the user has
    """
    from langflow.services.auth.permissions import PermissionEvaluator

    evaluator = PermissionEvaluator(session)
    return await evaluator.get_user_permissions_at_scope(
        user_id=user.id,
        scope_type=scope_type,
        scope_id=scope_id,
    )


class RBACEnforcer:
    """Central RBAC enforcement class for programmatic permission checks.

    Use this in service layer code where you need to enforce permissions
    outside of FastAPI routes.
    """

    def __init__(self, session: AsyncSession):
        """Initialize enforcer with database session.

        Args:
            session: Database session
        """
        self.session = session

    async def enforce(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permission: str,
        scope_type: ScopeType | str,
        scope_id: str,
        error_message: str | None = None,
    ) -> None:
        """Enforce permission requirement, raising exception if denied.

        Args:
            principal_type: Type of principal
            principal_id: ID of principal
            permission: Required permission
            scope_type: Scope type
            scope_id: Scope ID
            error_message: Custom error message (optional)

        Raises:
            HTTPException: 403 if permission denied
        """
        from langflow.services.auth.permissions import check_permission

        has_perm = await check_permission(
            session=self.session,
            principal_type=principal_type,
            principal_id=principal_id,
            permission=permission,
            scope_type=scope_type,
            scope_id=scope_id,
        )

        if not has_perm:
            detail = error_message or f"Permission denied: {permission} required"
            logger.warning(
                f"RBAC enforcement failed: {principal_type}:{principal_id} "
                f"lacks {permission} on {scope_type}:{scope_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

    async def check(
        self,
        principal_type: PrincipalType | str,
        principal_id: UUID | str,
        permission: str,
        scope_type: ScopeType | str,
        scope_id: str,
    ) -> bool:
        """Check permission without raising exception.

        Args:
            principal_type: Type of principal
            principal_id: ID of principal
            permission: Permission to check
            scope_type: Scope type
            scope_id: Scope ID

        Returns:
            True if permission granted, False otherwise
        """
        from langflow.services.auth.permissions import check_permission

        return await check_permission(
            session=self.session,
            principal_type=principal_type,
            principal_id=principal_id,
            permission=permission,
            scope_type=scope_type,
            scope_id=scope_id,
        )

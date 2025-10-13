"""FastAPI dependencies for RBAC permission checking.

This module provides reusable FastAPI dependencies for protecting endpoints with
RBAC permission checks. The dependencies integrate with the existing authentication
system and the RBAC enforcement engine.

Usage:
    @router.patch("/api/v1/flows/{flow_id}")
    async def update_flow(
        flow_id: UUID,
        flow_data: FlowUpdate,
        _: None = Depends(require_permission("flow.update", "flow", "flow_id"))
    ):
        # If we reach here, user has permission
        ...

Logic Nodes (Task 4.1):
- rbac_middleware_dependency → FastAPI dependency for permission checks
- require_permission_decorator → Decorator for endpoint protection

PRD References:
- Story 1.1 @AC3: Export flow permission check
- Story 1.1 @AC4: CRUD permission checks on flows
"""

import logging
from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from langflow.services.auth.utils import get_current_active_user
from langflow.services.database.models.user.model import User
from langflow.services.deps import get_session
from langflow.services.rbac.enforcement import RBACEnforcementEngine

logger = logging.getLogger(__name__)


def require_permission(
    action: str,
    resource_type: str,
    resource_id_param: str = "id",
    scope_type: str | None = None,  # noqa: ARG001 - Reserved for future scope resolution feature
) -> Callable:
    """FastAPI dependency factory for permission checking.

    Creates a reusable dependency that checks if the current user has a specific
    permission on a resource. The dependency extracts the resource ID from the
    request path parameters and invokes the RBAC enforcement engine.

    Args:
        action: Permission action (e.g., "flow.update", "project.delete")
        resource_type: Resource type (e.g., "flow", "project", "workspace")
        resource_id_param: Path parameter name containing resource ID (default: "id")
        scope_type: Explicit scope type (default: infer from resource_type)

    Returns:
        Callable: FastAPI dependency function that returns None if permission granted,
                  raises HTTPException 403 if permission denied

    Raises:
        HTTPException 400: If resource ID parameter is missing or invalid UUID
        HTTPException 403: If user lacks required permission

    Examples:
        >>> # Protect endpoint with specific permission
        >>> @router.patch("/api/v1/flows/{flow_id}")
        >>> async def update_flow(
        ...     flow_id: UUID,
        ...     flow_data: FlowUpdate,
        ...     _: None = Depends(require_permission("flow.update", "flow", "flow_id"))
        ... ):
        ...     # User has flow.update permission on this flow
        ...     pass

        >>> # Use convenience decorator
        >>> @router.patch("/api/v1/flows/{flow_id}")
        >>> async def update_flow(
        ...     flow_id: UUID,
        ...     flow_data: FlowUpdate,
        ...     _: None = Depends(require_update("flow", "flow_id"))
        ... ):
        ...     # User has flow.update permission on this flow
        ...     pass
    """

    async def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_session),
    ) -> None:
        """Check permission for current user on resource.

        Args:
            request: FastAPI request object containing path params
            current_user: Authenticated user from get_current_active_user dependency
            db: Database session for RBAC queries

        Returns:
            None: Permission granted, endpoint can proceed

        Raises:
            HTTPException 400: If resource ID parameter missing or invalid
            HTTPException 403: If permission denied
        """
        # Extract resource ID from path parameters
        resource_id = request.path_params.get(resource_id_param)
        if not resource_id:
            logger.warning(
                "Permission check failed: Missing resource ID parameter '%s' in path params. Available params: %s",
                resource_id_param,
                list(request.path_params.keys()),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing resource ID parameter: {resource_id_param}",
            )

        # Convert to UUID if needed
        try:
            resource_uuid = UUID(resource_id) if isinstance(resource_id, str) else resource_id
        except (ValueError, TypeError) as e:
            logger.warning(
                "Permission check failed: Invalid UUID format for '%s': %s. Error: %s",
                resource_id_param,
                resource_id,
                e,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid UUID format for '{resource_id_param}': {resource_id}",
            ) from e

        # Superusers bypass RBAC permission checks
        if current_user.is_superuser:
            logger.info(
                "Permission granted (superuser bypass): user=%s (%s), action=%s, resource_type=%s, resource_id=%s",
                current_user.id,
                current_user.username,
                action,
                resource_type,
                resource_uuid,
            )
            return  # Superuser has all permissions

        # Validate token scope first (PRD Story 4.2)
        # This ensures scoped API keys can only access resources within their scope
        from langflow.services.rbac.token_scope import validate_token_scope

        await validate_token_scope(
            request=request,
            resource_type=resource_type,
            resource_id=resource_uuid,
            session=db,
            current_user=current_user,  # GAP-2: Pass current_user for audit logging
        )

        # Initialize RBAC enforcement engine
        engine = RBACEnforcementEngine(session=db)

        # Check permission
        logger.debug(
            "Checking permission: user=%s, action=%s, resource_type=%s, resource_id=%s",
            current_user.id,
            action,
            resource_type,
            resource_uuid,
        )

        has_perm = await engine.has_permission(
            user_id=current_user.id,
            permission=action,
            resource_type=resource_type,
            resource_id=resource_uuid,
        )

        if not has_perm:
            logger.warning(
                "Permission denied: user=%s (%s), action=%s, resource_type=%s, resource_id=%s",
                current_user.id,
                current_user.username,
                action,
                resource_type,
                resource_uuid,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: You do not have '{action}' permission on this {resource_type}",
            )

        logger.info(
            "Permission granted: user=%s (%s), action=%s, resource_type=%s, resource_id=%s",
            current_user.id,
            current_user.username,
            action,
            resource_type,
            resource_uuid,
        )

        # Permission granted, endpoint can proceed

    return permission_checker


# Convenience decorators for common CRUD operations


def require_read(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for read permission check.

    Convenience wrapper for require_permission that checks <resource_type>.read permission.

    Args:
        resource_type: Type of resource (e.g., "flow", "project")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.get("/api/v1/flows/{flow_id}")
        >>> async def get_flow(
        ...     flow_id: UUID,
        ...     _: None = Depends(require_read("flow", "flow_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.read", resource_type, resource_id_param)


def require_create(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for create permission check.

    Convenience wrapper for require_permission that checks <resource_type>.create permission.

    Args:
        resource_type: Type of resource (e.g., "flow", "project")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.post("/api/v1/projects/{project_id}/flows")
        >>> async def create_flow(
        ...     project_id: UUID,
        ...     flow_data: FlowCreate,
        ...     _: None = Depends(require_create("flow", "project_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.create", resource_type, resource_id_param)


def require_update(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for update permission check.

    Convenience wrapper for require_permission that checks <resource_type>.update permission.

    Args:
        resource_type: Type of resource (e.g., "flow", "project")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.patch("/api/v1/flows/{flow_id}")
        >>> async def update_flow(
        ...     flow_id: UUID,
        ...     flow_data: FlowUpdate,
        ...     _: None = Depends(require_update("flow", "flow_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.update", resource_type, resource_id_param)


def require_delete(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for delete permission check.

    Convenience wrapper for require_permission that checks <resource_type>.delete permission.

    Args:
        resource_type: Type of resource (e.g., "flow", "project")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.delete("/api/v1/flows/{flow_id}")
        >>> async def delete_flow(
        ...     flow_id: UUID,
        ...     _: None = Depends(require_delete("flow", "flow_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.delete", resource_type, resource_id_param)


def require_export(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for export permission check.

    Convenience wrapper for require_permission that checks <resource_type>.export permission.
    Used for PRD Story 1.1 @AC3 (export flow permission).

    Args:
        resource_type: Type of resource (e.g., "flow")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.post("/api/v1/flows/{flow_id}/export")
        >>> async def export_flow(
        ...     flow_id: UUID,
        ...     _: None = Depends(require_export("flow", "flow_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.export", resource_type, resource_id_param)


def require_execute(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for execute permission check.

    Convenience wrapper for require_permission that checks <resource_type>.execute permission.
    Used for flow execution endpoints.

    Args:
        resource_type: Type of resource (e.g., "flow")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.post("/api/v1/flows/{flow_id}/run")
        >>> async def execute_flow(
        ...     flow_id: UUID,
        ...     _: None = Depends(require_execute("flow", "flow_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.execute", resource_type, resource_id_param)


def require_deploy(resource_type: str, resource_id_param: str = "id") -> Callable:
    """FastAPI dependency for deploy permission check.

    Convenience wrapper for require_permission that checks <resource_type>.deploy permission.
    Used for deployment/environment management endpoints.

    Args:
        resource_type: Type of resource (e.g., "environment", "flow")
        resource_id_param: Path parameter name containing resource ID (default: "id")

    Returns:
        FastAPI dependency function

    Examples:
        >>> @router.post("/api/v1/flows/{flow_id}/deploy")
        >>> async def deploy_flow(
        ...     flow_id: UUID,
        ...     environment_id: UUID,
        ...     _: None = Depends(require_deploy("flow", "flow_id"))
        ... ):
        ...     pass
    """
    return require_permission(f"{resource_type}.deploy", resource_type, resource_id_param)

"""
FastAPI Dependencies for Permission Enforcement

Provides decorators and dependencies for enforcing permissions in API endpoints.
"""

from functools import wraps
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Query

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.auth.permissions import (
    PermissionDenied,
    check_permission,
    require_permission,
)
from langflow.services.database.models.grant.model import ScopeType


def RequirePermission(
    permission: str,
    scope_type: ScopeType,
    scope_id_param: str = "id",
):
    """
    FastAPI dependency to require a permission at a specific scope.

    Usage:
        @router.get("/{flow_id}")
        async def get_flow(
            flow_id: str,
            _: Annotated[None, Depends(RequirePermission("flows:read", ScopeType.FLOW, "flow_id"))],
            db: DbSession,
            current_user: CurrentActiveUser,
        ):
            # User is guaranteed to have flows:read permission on this flow
            ...

    Args:
        permission: Permission ID required (e.g., "flows:read")
        scope_type: Scope type for the permission
        scope_id_param: Name of the path/query parameter containing the scope ID

    Returns:
        FastAPI dependency function
    """

    async def permission_dependency(
        current_user: CurrentActiveUser,
        db: DbSession,
        **kwargs,
    ) -> None:
        # Extract scope_id from kwargs (path/query params)
        scope_id = kwargs.get(scope_id_param)

        if not scope_id:
            raise HTTPException(
                status_code=400,
                detail=f"Missing scope identifier: {scope_id_param}",
            )

        try:
            await require_permission(
                db=db,
                user=current_user,
                permission=permission,
                scope_type=scope_type,
                scope_id=str(scope_id),
            )
        except PermissionDenied as e:
            raise HTTPException(
                status_code=403,
                detail=str(e),
            )

    return permission_dependency


async def check_flow_permission(
    flow_id: str,
    permission: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> bool:
    """
    Helper to check flow permissions.

    Args:
        flow_id: Flow ID
        permission: Permission to check (e.g., "flows:read")
        current_user: Current authenticated user
        db: Database session

    Returns:
        True if user has permission, False otherwise
    """
    return await check_permission(
        db=db,
        user=current_user,
        permission=permission,
        scope_type=ScopeType.FLOW,
        scope_id=flow_id,
    )


async def require_flow_permission(
    flow_id: str,
    permission: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> None:
    """
    Helper to require flow permissions.

    Args:
        flow_id: Flow ID
        permission: Permission to check
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If user lacks permission
    """
    try:
        await require_permission(
            db=db,
            user=current_user,
            permission=permission,
            scope_type=ScopeType.FLOW,
            scope_id=flow_id,
        )
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=str(e))


async def check_workspace_permission(
    workspace_id: str,
    permission: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> bool:
    """Helper to check workspace permissions."""
    return await check_permission(
        db=db,
        user=current_user,
        permission=permission,
        scope_type=ScopeType.WORKSPACE,
        scope_id=workspace_id,
    )


async def require_workspace_permission(
    workspace_id: str,
    permission: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> None:
    """Helper to require workspace permissions."""
    try:
        await require_permission(
            db=db,
            user=current_user,
            permission=permission,
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=str(e))


async def check_project_permission(
    project_id: str,
    permission: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> bool:
    """Helper to check project permissions."""
    return await check_permission(
        db=db,
        user=current_user,
        permission=permission,
        scope_type=ScopeType.PROJECT,
        scope_id=project_id,
    )


async def require_project_permission(
    project_id: str,
    permission: str,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> None:
    """Helper to require project permissions."""
    try:
        await require_permission(
            db=db,
            user=current_user,
            permission=permission,
            scope_type=ScopeType.PROJECT,
            scope_id=project_id,
        )
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=str(e))


# Example usage in router:
"""
from langflow.api.utils.permissions import require_flow_permission

@router.get("/{flow_id}")
async def get_flow(
    flow_id: str,
    current_user: CurrentActiveUser,
    db: DbSession,
):
    # Check permission before proceeding
    await require_flow_permission(flow_id, "flows:read", current_user, db)

    # User is authorized, proceed with logic
    flow = await get_flow_by_id(db, flow_id)
    return flow


@router.post("/")
async def create_flow(
    flow_data: FlowCreate,
    current_user: CurrentActiveUser,
    db: DbSession,
):
    # Check workspace-level permission for creating flows
    await require_workspace_permission(
        flow_data.workspace_id,
        "flows:create",
        current_user,
        db
    )

    # User is authorized, create the flow
    flow = await create_flow(db, flow_data)
    return flow
"""

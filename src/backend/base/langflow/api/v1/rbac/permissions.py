"""Permission catalog API endpoints.

Provides read-only access to the permission catalog.
PRD Story 1.1 - Permission Catalog
"""

from fastapi import APIRouter, Query

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.crud import get_permission_by_id, list_permissions
from langflow.services.database.models.rbac.permission import PermissionRead

router = APIRouter()


@router.get("", response_model=list[PermissionRead])
async def get_permissions(
    db: DbSession,
    current_user: CurrentActiveUser,
    resource_type: str | None = Query(None, description="Filter by resource type"),
    action: str | None = Query(None, description="Filter by action"),
):
    """List all permissions in the catalog.

    The permission catalog is read-only and defined by the system.

    Query Parameters:
    - resource_type: Filter permissions for a specific resource (e.g., 'flow', 'workspace')
    - action: Filter permissions by action (e.g., 'read', 'create')

    Returns:
        List of Permission objects
    """
    permissions = await list_permissions(
        db=db,
        resource_type=resource_type,
        action=action,
    )
    return [PermissionRead.model_validate(p, from_attributes=True) for p in permissions]


@router.get("/{permission_id}", response_model=PermissionRead)
async def get_permission(
    permission_id: str,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a specific permission by ID.

    Permission IDs follow the format: `resource_type:action`
    Examples: `flow:read`, `workspace:invite_users`

    Args:
        permission_id: Permission ID (e.g., "flow:read")

    Returns:
        Permission object

    Raises:
        404: Permission not found
    """
    from fastapi import HTTPException, status

    permission = await get_permission_by_id(db, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission '{permission_id}' not found",
        )
    return PermissionRead.model_validate(permission, from_attributes=True)

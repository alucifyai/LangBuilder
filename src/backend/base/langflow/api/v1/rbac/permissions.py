"""Permission Catalog API endpoints for RBAC.

Implements PRD Story 1.1 - Permission Catalog
- Read-only endpoint to list available permissions
- Filtering by resource_type and action
- Accessible to all authenticated users
"""

from fastapi import APIRouter, Query
from loguru import logger
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.permission import Permission, PermissionRead

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("/", response_model=list[PermissionRead])
async def list_permissions(
    resource_type: str | None = Query(
        default=None,
        description="Filter by resource type (e.g., 'flow', 'project', 'component')",
    ),
    action: str | None = Query(
        default=None,
        description="Filter by action (e.g., 'create', 'read', 'update', 'delete')",
    ),
    scope_level: str | None = Query(
        default=None,
        description="Filter by scope level (e.g., 'GLOBAL', 'WORKSPACE', 'PROJECT', 'FLOW')",
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[Permission]:
    """List available permissions from the permission catalog.

    Implements PRD Story 1.1 @AC1 - Permission Catalog Listing

    This is a read-only endpoint accessible to all authenticated users.
    It allows discovery of available permissions in the system for use in
    role creation and permission assignment.

    Args:
        resource_type: Optional filter by resource type (e.g., "flow", "project")
        action: Optional filter by action (e.g., "create", "read", "update", "delete")
        skip: Number of records to skip for pagination (default: 0)
        limit: Maximum number of records to return (default: 100, max: 500)
        current_user: Currently authenticated user (automatically injected)
        session: Database session (automatically injected)

    Returns:
        List of permissions matching the filter criteria

    Examples:
        GET /api/v1/admin/permissions/
            Returns all permissions

        GET /api/v1/admin/permissions/?resource_type=flow
            Returns all flow-related permissions

        GET /api/v1/admin/permissions/?resource_type=flow&action=read
            Returns only the flow.read permission

        GET /api/v1/admin/permissions/?action=delete
            Returns all delete permissions across all resource types
    """
    # Build query with filters
    stmt = select(Permission).where(Permission.is_active == True)  # noqa: E712

    if resource_type:
        stmt = stmt.where(Permission.resource_type == resource_type)

    if action:
        stmt = stmt.where(Permission.action == action)

    if scope_level:
        stmt = stmt.where(Permission.scope_level == scope_level)

    # Add pagination and ordering
    stmt = stmt.offset(skip).limit(limit).order_by(Permission.resource_type, Permission.action)

    # Execute query
    result = await session.exec(stmt)
    permissions = result.all()

    logger.info(
        f"User {current_user.id} listed {len(permissions)} permissions "
        f"(filters: resource_type={resource_type}, action={action}, scope_level={scope_level})"
    )

    return list(permissions)

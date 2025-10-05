"""Role management API endpoints.

Provides CRUD operations for custom roles.
PRD Story 1.2 - Create and Manage Custom Roles
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    RequireRoleCreate,
    RequireRoleDelete,
    RequireRoleRead,
    RequireRoleUpdate,
)
from langflow.services.database.models.rbac.crud import create_role, delete_role, get_role_by_id, list_roles, update_role
from langflow.services.database.models.rbac.role import RoleCreate, RoleRead, RoleUpdate

router = APIRouter()


@router.get("", response_model=list[RoleRead])
async def get_roles(
    db: DbSession,
    current_user: CurrentActiveUser,
    _perm: RequireRoleRead,
    include_system: bool = Query(True, description="Include system-defined roles"),
):
    """List all roles.

    Query Parameters:
    - include_system: If true, includes system roles (Admin, Editor, Viewer, Deployer).
                      If false, only shows custom roles.

    Returns:
        List of Role objects

    Requires: 'role:read' permission at workspace scope
    """
    roles = await list_roles(db=db, include_system=include_system)
    return [RoleRead.model_validate(r, from_attributes=True) for r in roles]


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
    _perm: RequireRoleRead,
):
    """Get a specific role by ID.

    Args:
        role_id: UUID of the role

    Returns:
        Role object

    Raises:
        404: Role not found

    Note: Requires 'role:read' permission
    """
    # TODO Phase 3: Add permission check

    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_id}' not found",
        )
    return RoleRead.model_validate(role, from_attributes=True)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_new_role(
    role_data: RoleCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Create a new custom role.

    Request Body:
    - name: Unique role name
    - description: Optional description
    - permissions: List of permission IDs (e.g., ["flow:read", "flow:update"])

    Returns:
        Created Role object

    Raises:
        400: Invalid permissions or duplicate name
        409: Role name already exists

    Note: Requires 'role:create' permission at workspace scope
    PRD Story 1.2 @AC1
    """
    # TODO Phase 3: Add permission check
    # await enforce_permission(db, current_user.id, "role:create", "workspace", workspace_id)

    role = await create_role(db=db, role_data=role_data)
    return RoleRead.model_validate(role, from_attributes=True)


@router.patch("/{role_id}", response_model=RoleRead)
async def update_existing_role(
    role_id: UUID,
    role_data: RoleUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update a custom role.

    System roles cannot be modified.

    Request Body (all fields optional):
    - name: New role name
    - description: New description
    - permissions: Updated permission list

    Returns:
        Updated Role object (with incremented version)

    Raises:
        403: Attempt to modify system role
        404: Role not found
        409: Name conflict with existing role

    Note: Requires 'role:update' permission
    PRD Story 1.2 @AC3 - Version tracking
    """
    # TODO Phase 3: Add permission check

    role = await update_role(db=db, role_id=role_id, role_data=role_data)
    return RoleRead.model_validate(role, from_attributes=True)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_role(
    role_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a custom role.

    System roles cannot be deleted.
    Roles with active grants cannot be deleted.

    Args:
        role_id: UUID of the role to delete

    Raises:
        403: Attempt to delete system role
        404: Role not found
        409: Role has active grants

    Note: Requires 'role:delete' permission
    """
    # TODO Phase 3: Add permission check

    await delete_role(db=db, role_id=role_id)
    return None  # 204 No Content

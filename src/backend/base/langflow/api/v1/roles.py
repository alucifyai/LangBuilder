from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.grant.crud import count_grants_by_role
from langflow.services.database.models.role.crud import (
    create_role,
    delete_role,
    get_all_roles,
    get_role_by_id,
    update_role,
)

router = APIRouter(tags=["Roles"], prefix="/roles")


# Request/Response Schemas
class RoleCreate(BaseModel):
    """Request schema for creating a new role."""

    name: str
    permissions: list[str]


class RoleUpdate(BaseModel):
    """Request schema for updating a role."""

    name: str | None = None
    permissions: list[str] | None = None


class RoleResponse(BaseModel):
    """Response schema for role data."""

    id: UUID
    name: str
    permissions: list[str] | None
    version: int
    created_at: datetime
    updated_at: datetime


class RolesListResponse(BaseModel):
    """Response schema for list of roles."""

    total_count: int
    roles: list[RoleResponse]


# Helper function to check admin privileges
async def require_admin(current_user: CurrentActiveUser) -> None:
    """
    Check if current user is an admin.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="admin_required: Only administrators can manage roles",
        )


@router.get("/", response_model=RolesListResponse)
async def list_roles(
    current_user: CurrentActiveUser,
    db: DbSession,
) -> RolesListResponse:
    """
    List all roles.

    Requires admin privileges.
    """
    await require_admin(current_user)

    roles = await get_all_roles(db)
    return RolesListResponse(
        total_count=len(roles),
        roles=[
            RoleResponse(
                id=role.id,
                name=role.name,
                permissions=role.permissions or [],
                version=role.version,
                created_at=role.created_at,
                updated_at=role.updated_at,
            )
            for role in roles
        ],
    )


@router.post("/", response_model=RoleResponse, status_code=201)
async def create_role_route(
    req: RoleCreate,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> RoleResponse:
    """
    Create a new role.

    Requires admin privileges.

    Args:
        req: Role creation request with name and permissions

    Returns:
        Created role

    Raises:
        HTTPException:
            - 403 if not admin
            - 409 if role name already exists
            - 400 if permissions are invalid
    """
    await require_admin(current_user)

    role = await create_role(db, name=req.name, permissions=req.permissions)

    # Create audit log entry
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.ROLE_CREATED,
        resource_type="role",
        resource_id=str(role.id),
        after_state={
            "name": role.name,
            "permissions": role.permissions or [],
            "version": role.version,
        },
    )

    return RoleResponse(
        id=role.id,
        name=role.name,
        permissions=role.permissions or [],
        version=role.version,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role_route(
    role_id: UUID,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> RoleResponse:
    """
    Get a specific role by ID.

    Requires admin privileges.

    Args:
        role_id: Role ID

    Returns:
        Role data

    Raises:
        HTTPException:
            - 403 if not admin
            - 404 if role not found
    """
    await require_admin(current_user)

    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=role.id,
        name=role.name,
        permissions=role.permissions or [],
        version=role.version,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role_route(
    role_id: UUID,
    req: RoleUpdate,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> RoleResponse:
    """
    Update a role and increment version.

    Requires admin privileges.

    Args:
        role_id: Role ID to update
        req: Role update request

    Returns:
        Updated role with incremented version

    Raises:
        HTTPException:
            - 403 if not admin
            - 404 if role not found
            - 409 if new name conflicts with existing role
            - 400 if permissions are invalid
    """
    await require_admin(current_user)

    # Get before state for audit log
    old_role = await get_role_by_id(db, role_id)
    if not old_role:
        raise HTTPException(status_code=404, detail="Role not found")

    before_state = {
        "name": old_role.name,
        "permissions": old_role.permissions or [],
        "version": old_role.version,
    }

    # Update role
    role = await update_role(
        db,
        role_id=role_id,
        name=req.name,
        permissions=req.permissions,
    )

    # Create audit log entry with before/after states
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.ROLE_UPDATED,
        resource_type="role",
        resource_id=str(role.id),
        before_state=before_state,
        after_state={
            "name": role.name,
            "permissions": role.permissions or [],
            "version": role.version,
        },
    )

    return RoleResponse(
        id=role.id,
        name=role.name,
        permissions=role.permissions or [],
        version=role.version,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.delete("/{role_id}")
async def delete_role_route(
    role_id: UUID,
    current_user: CurrentActiveUser,
    db: DbSession,
) -> dict[str, str]:
    """
    Delete a role.

    Requires admin privileges.
    Fails if the role has active grants.

    Args:
        role_id: Role ID to delete

    Returns:
        Success message

    Raises:
        HTTPException:
            - 403 if not admin
            - 404 if role not found
            - 409 if role has active grants
    """
    await require_admin(current_user)

    # Check if role exists
    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check for active grants
    grant_count = await count_grants_by_role(db, role_id)
    if grant_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete role: {grant_count} active grants exist",
        )

    # Capture before state for audit log
    before_state = {
        "name": role.name,
        "permissions": role.permissions or [],
        "version": role.version,
    }

    # Delete role
    await delete_role(db, role_id)

    # Create audit log entry
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.ROLE_DELETED,
        resource_type="role",
        resource_id=str(role_id),
        before_state=before_state,
    )

    return {"detail": "Role deleted successfully"}

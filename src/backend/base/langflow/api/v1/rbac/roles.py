"""Role management API endpoints for RBAC system."""

# NO future annotations per Phase 1 requirements
# from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.api.v1.rbac.dependencies import (
    check_role_permission,
    check_workspace_permission,
    get_workspace_by_id,
    get_permission_engine,
)
from langflow.schema.serialize import UUIDstr
from langflow.services.database.models.rbac.role import (
    Role,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    RoleType,
)
from langflow.services.database.models.rbac.permission import (
    Permission,
    PermissionRead,
)

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/roles",
    tags=["RBAC", "Roles"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> RoleRead:
    """Create a new role."""

    # Validate workspace if specified
    workspace = None
    if role_data.workspace_id:
        workspace = await session.get(Workspace, role_data.workspace_id)
        if not workspace or workspace.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Check workspace permissions
        result = await permission_engine.check_permission(
            session=session,
            user=current_user,
            resource_type="workspace",
            action="create_role",
            resource_id=role_data.workspace_id,
            workspace_id=role_data.workspace_id,
        )

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions to create roles in this workspace: {result.reason}"
            )
    else:
        # System-level role creation requires superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can create system-level roles"
            )

    # Check if role name already exists in workspace/system
    statement = select(Role).where(
        Role.workspace_id == role_data.workspace_id,
        Role.name == role_data.name,
        Role.is_active == True
    )
    result = await session.exec(statement)
    existing = result.first()

    if existing:
        scope = "workspace" if role_data.workspace_id else "system"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.name}' already exists in this {scope}"
        )

    # Validate parent role if specified
    if role_data.parent_role_id:
        parent_role = await session.get(Role, role_data.parent_role_id)
        if not parent_role or not parent_role.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent role not found"
            )

        # Check that parent role is in same workspace
        if parent_role.workspace_id != role_data.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent role must be in the same workspace"
            )

    # Create role
    role = Role(
        **role_data.model_dump(),
        created_by_id=current_user.id
    )

    session.add(role)
    await session.commit()
    await session.refresh(role)

    # TODO: Log audit event

    return RoleRead.model_validate(role)


@router.get("/", response_model=list[RoleRead])
async def list_roles(
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
    workspace_id: UUIDstr | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    type: str | None = None,  # noqa: A002
    is_system: bool | None = None,
    is_active: bool | None = None,
) -> list[RoleRead]:
    """List roles accessible to current user."""

    statement = select(Role)

    # Filter by workspace if specified
    if workspace_id:
        workspace = await session.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Check workspace access
        result = await permission_engine.check_permission(
            session=session,
            user=current_user,
            resource_type="workspace",
            action="read",
            resource_id=workspace_id,
            workspace_id=workspace_id,
        )

        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied to this workspace: {result.reason}"
            )

        statement = statement.where(Role.workspace_id == workspace_id)
    else:
        # Filter by user's accessible workspaces + system roles
        if current_user.is_superuser:
            # Superusers can see all roles
            pass
        else:
            # Regular users can see roles in their workspaces + system roles
            accessible_workspace_subquery = select(Workspace.id).where(
                Workspace.owner_id == current_user.id,
                Workspace.is_deleted == False
            )

            statement = statement.where(
                (Role.workspace_id.in_(accessible_workspace_subquery)) |
                (Role.workspace_id.is_(None))  # System roles
            )

    # Apply additional filters
    if search:
        statement = statement.where(
            (Role.name.ilike(f"%{search}%")) |
            (Role.description.ilike(f"%{search}%"))
        )

    if type:
        statement = statement.where(Role.type == type)

    if is_system is not None:
        statement = statement.where(Role.is_system == is_system)

    if is_active is not None:
        statement = statement.where(Role.is_active == is_active)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)

    result = await session.exec(statement)
    roles = result.all()

    return [RoleRead.model_validate(role) for role in roles]


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> "RoleRead":
    """Get role by ID."""
    from langflow.services.database.models.rbac.role import Role, RoleRead

    role = await session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check access permissions
    if role.workspace_id:
        from langflow.services.database.models.rbac.workspace import Workspace
        workspace = await session.get(Workspace, role.workspace_id)
        if workspace and workspace.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this role"
            )
    elif not current_user.is_superuser:
        # System roles can only be viewed by superusers
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to system roles"
        )

    return RoleRead.model_validate(role)


@router.put("/{role_id}", response_model=RoleRead)
async def update_role(
    role_id: UUIDstr,
    role_data: "RoleUpdate",
    session: DbSession,
    current_user: CurrentActiveUser,
) -> "RoleRead":
    """Update role."""
    from langflow.services.database.models.rbac.role import Role, RoleRead, RoleUpdate

    role = await session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if role is system role
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System roles cannot be modified"
        )

    # Check permissions
    if role.workspace_id:
        from langflow.services.database.models.rbac.workspace import Workspace
        workspace = await session.get(Workspace, role.workspace_id)
        if workspace and workspace.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this role"
            )
    elif not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can update system roles"
        )

    # Check name uniqueness if changing name
    if role_data.name and role_data.name != role.name:
        statement = select(Role).where(
            Role.workspace_id == role.workspace_id,
            Role.name == role_data.name,
            Role.id != role_id,
            Role.is_active == True
        )
        result = await session.exec(statement)
        existing = result.first()

        if existing:
            scope = "workspace" if role.workspace_id else "system"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_data.name}' already exists in this {scope}"
            )

    # Update role fields
    for field, value in role_data.model_dump(exclude_unset=True).items():
        setattr(role, field, value)

    role.updated_at = datetime.now(timezone.utc)
    role.version += 1
    await session.commit()
    await session.refresh(role)

    # TODO: Log audit event

    return RoleRead.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete role (deactivate)."""
    from langflow.services.database.models.rbac.role import Role

    role = await session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check if role is system role
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System roles cannot be deleted"
        )

    # Check permissions
    if role.workspace_id:
        from langflow.services.database.models.rbac.workspace import Workspace
        workspace = await session.get(Workspace, role.workspace_id)
        if workspace and workspace.owner_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete this role"
            )
    elif not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete system roles"
        )

    # Check if role has active assignments
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    statement = select(func.count(RoleAssignment.id)).where(
        RoleAssignment.role_id == role_id,
        RoleAssignment.is_active == True
    )
    result = await session.exec(statement)
    active_assignments = result.one()

    if active_assignments > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role with {active_assignments} active assignments"
        )

    # Deactivate role
    role.is_active = False
    role.updated_at = datetime.now(timezone.utc)
    await session.commit()

    # TODO: Log audit event


@router.get("/{role_id}/permissions", response_model=list[PermissionRead])
async def list_role_permissions(
    role_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> list["PermissionRead"]:
    """List permissions assigned to role."""
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.permission import Permission, PermissionRead, RolePermission

    role = await session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Get role permissions using async operations
    statement = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.is_granted == True
    )
    result = await session.exec(statement)
    role_permissions = result.all()

    permissions = []
    for rp in role_permissions:
        # Ensure permission_id is properly converted to UUID
        perm_id = rp.permission_id
        if isinstance(perm_id, str):
            perm_id = UUIDstr(perm_id)
        permission = await session.get(Permission, perm_id)
        if permission:
            permissions.append(PermissionRead.model_validate(permission))

    return permissions


@router.post("/{role_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    role_id: UUIDstr,
    permission_data: dict,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Assign permission to role."""
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.permission import Permission, RolePermission

    role = await session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    permission_id = permission_data.get("permission_id")
    if not permission_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="permission_id is required"
        )

    # Convert permission_id to UUIDstr if it's a string
    if isinstance(permission_id, str):
        try:
            permission_id = UUIDstr(permission_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid permission_id format"
            )

    permission = await session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    # Check if assignment already exists
    statement = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    )
    result = await session.exec(statement)
    existing = result.first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already assigned to role"
        )

    # Create role permission assignment
    role_permission = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
        granted_by_id=current_user.id,
        granted_at=datetime.now(timezone.utc),
        reason=permission_data.get("reason")
    )

    session.add(role_permission)
    await session.commit()

    # TODO: Log audit event

    return {
        "message": "Permission assigned successfully",
        "role_id": str(role_id),
        "permission_id": str(permission_id)
    }


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_id: UUIDstr,
    permission_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Remove permission from role."""
    from langflow.services.database.models.rbac.permission import RolePermission

    statement = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    )
    result = await session.exec(statement)
    role_permission = result.first()

    if not role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission assignment not found"
        )

    await session.delete(role_permission)
    await session.commit()

    # TODO: Log audit event


@router.put("/{role_id}/permissions", status_code=status.HTTP_200_OK)
async def update_role_permissions(
    role_id: UUIDstr,
    permission_data: dict,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Update role permissions (batch operation)."""
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.permission import Permission, RolePermission

    # Validate role exists
    role = await session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    permission_ids = permission_data.get("permission_ids", [])
    if not isinstance(permission_ids, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="permission_ids must be a list"
        )

    # Convert permission IDs to UUIDs and validate they exist
    validated_permission_ids = []
    for perm_id in permission_ids:
        if isinstance(perm_id, str):
            try:
                perm_id = UUIDstr(perm_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid permission_id format: {perm_id}"
                )
        validated_permission_ids.append(perm_id)

    # Validate all permissions exist
    for perm_id in validated_permission_ids:
        permission = await session.get(Permission, perm_id)
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Permission not found: {perm_id}"
            )

    # Get current role permissions
    current_statement = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.is_granted == True
    )
    current_result = await session.exec(current_statement)
    current_role_permissions = current_result.all()
    current_permission_ids = [rp.permission_id for rp in current_role_permissions]

    # Calculate changes
    to_add = [pid for pid in validated_permission_ids if pid not in current_permission_ids]
    to_remove = [pid for pid in current_permission_ids if pid not in validated_permission_ids]

    # Remove permissions that are no longer needed
    for perm_id in to_remove:
        delete_statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == perm_id
        )
        delete_result = await session.exec(delete_statement)
        role_permission = delete_result.first()
        if role_permission:
            await session.delete(role_permission)

    # Add new permissions
    for perm_id in to_add:
        # Check if assignment already exists (safety check)
        existing_statement = select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == perm_id
        )
        existing_result = await session.exec(existing_statement)
        existing = existing_result.first()

        if not existing:
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=perm_id,
                is_granted=True,
                granted_by_id=current_user.id,
                reason=f"Batch update by {current_user.username}"
            )
            session.add(role_permission)

    await session.commit()

    # TODO: Log audit event

    return {
        "message": "Role permissions updated successfully",
        "permissions_added": len(to_add),
        "permissions_removed": len(to_remove)
    }


@router.post("/initialize-system-roles", status_code=status.HTTP_201_CREATED)
async def initialize_system_roles(
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Initialize system roles and permissions."""

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can initialize system roles"
        )

    created_permissions = 0
    created_roles = 0

    # Create system permissions
    from langflow.services.database.models.rbac.permission import Permission, SYSTEM_PERMISSIONS
    from langflow.services.database.models.rbac.role import Role, SYSTEM_ROLES

    for perm_data in SYSTEM_PERMISSIONS:
        statement = select(Permission).where(Permission.code == perm_data["code"])
        result = await session.exec(statement)
        existing = result.first()

        if not existing:
            # Only add is_system=True if not already specified in perm_data
            permission_data = perm_data.copy()
            if "is_system" not in permission_data:
                permission_data["is_system"] = True

            permission = Permission(**permission_data)
            session.add(permission)
            created_permissions += 1

    # Create system roles
    for role_key, role_data in SYSTEM_ROLES.items():
        statement = select(Role).where(
            Role.name == role_data["name"],
            Role.workspace_id.is_(None)
        )
        result = await session.exec(statement)
        existing = result.first()

        if not existing:
            role = Role(
                **role_data,
                created_by_id=current_user.id,
                workspace_id=None
            )
            session.add(role)
            created_roles += 1

    await session.commit()

    return {
        "message": "System roles and permissions initialized",
        "permissions_created": created_permissions,
        "roles_created": created_roles
    }

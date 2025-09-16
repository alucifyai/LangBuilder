"""Role management API endpoints for RBAC system."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from langflow.api.utils import get_session
from langflow.services.auth.utils import get_current_active_user as get_current_user
from langflow.api.v1.rbac.dependencies import (
    check_role_permission,
    check_workspace_permission,
    get_workspace_by_id,
)
from langflow.services.database.models.rbac.permission import (
    Permission,
    PermissionRead,
    RolePermission,
    SYSTEM_PERMISSIONS,
)
from langflow.services.database.models.rbac.role import (
    Role,
    RoleCreate,
    RoleHierarchy,
    RoleRead,
    RoleUpdate,
    SYSTEM_ROLES,
)
from langflow.services.database.models.rbac.workspace import Workspace
from langflow.services.database.models.user.model import User

if TYPE_CHECKING:
    pass

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RoleRead:
    """Create a new role."""

    # Validate workspace if specified
    workspace = None
    if role_data.workspace_id:
        workspace = session.get(Workspace, role_data.workspace_id)
        if not workspace or workspace.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Check workspace permissions
        from langflow.api.v1.rbac.dependencies import PermissionChecker
        checker = PermissionChecker(session, current_user)
        if not checker.has_workspace_permission(workspace, "role:create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create roles in this workspace"
            )
    else:
        # System-level role creation requires superuser
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can create system-level roles"
            )

    # Check if role name already exists in workspace/system
    existing = session.query(Role).filter(
        Role.workspace_id == role_data.workspace_id,
        Role.name == role_data.name,
        Role.is_active == True
    ).first()

    if existing:
        scope = "workspace" if role_data.workspace_id else "system"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{role_data.name}' already exists in this {scope}"
        )

    # Validate parent role if specified
    if role_data.parent_role_id:
        parent_role = session.get(Role, role_data.parent_role_id)
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
    session.commit()
    session.refresh(role)

    # TODO: Log audit event

    return RoleRead.model_validate(role)


@router.get("/", response_model=list[RoleRead])
async def list_roles(
    workspace_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    type: str | None = None,  # noqa: A002
    is_system: bool | None = None,
    is_active: bool | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[RoleRead]:
    """List roles accessible to current user."""

    query = session.query(Role)

    # Filter by workspace if specified
    if workspace_id:
        workspace = session.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )

        # Check workspace access
        from langflow.api.v1.rbac.dependencies import PermissionChecker
        checker = PermissionChecker(session, current_user)
        if not checker.has_workspace_permission(workspace, "workspace:read"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this workspace"
            )

        query = query.filter(Role.workspace_id == workspace_id)
    else:
        # Filter by user's accessible workspaces + system roles
        if current_user.is_superuser:
            # Superusers can see all roles
            pass
        else:
            # Regular users can see roles in their workspaces + system roles
            accessible_workspace_ids = session.query(Workspace.id).filter(
                Workspace.owner_id == current_user.id,
                Workspace.is_deleted == False
            ).subquery()

            query = query.filter(
                (Role.workspace_id.in_(accessible_workspace_ids)) |
                (Role.workspace_id.is_(None))  # System roles
            )

    # Apply additional filters
    if search:
        query = query.filter(
            Role.name.ilike(f"%{search}%") |
            Role.description.ilike(f"%{search}%")
        )

    if type:
        query = query.filter(Role.type == type)

    if is_system is not None:
        query = query.filter(Role.is_system == is_system)

    if is_active is not None:
        query = query.filter(Role.is_active == is_active)

    # Apply pagination
    roles = query.offset(skip).limit(limit).all()

    return [RoleRead.model_validate(role) for role in roles]


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RoleRead:
    """Get role by ID."""

    role = session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Check access permissions
    if role.workspace_id:
        workspace = session.get(Workspace, role.workspace_id)
        if workspace:
            from langflow.api.v1.rbac.dependencies import PermissionChecker
            checker = PermissionChecker(session, current_user)
            if not checker.has_workspace_permission(workspace, "workspace:read"):
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
    role_id: UUID,
    role_data: RoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> RoleRead:
    """Update role."""

    role = session.get(Role, role_id)
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
        workspace = session.get(Workspace, role.workspace_id)
        if workspace:
            from langflow.api.v1.rbac.dependencies import PermissionChecker
            checker = PermissionChecker(session, current_user)
            if not checker.has_workspace_permission(workspace, "role:update"):
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
        existing = session.query(Role).filter(
            Role.workspace_id == role.workspace_id,
            Role.name == role_data.name,
            Role.id != role_id,
            Role.is_active == True
        ).first()

        if existing:
            scope = "workspace" if role.workspace_id else "system"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{role_data.name}' already exists in this {scope}"
            )

    # Update role fields
    from datetime import datetime, timezone
    for field, value in role_data.model_dump(exclude_unset=True).items():
        setattr(role, field, value)

    role.updated_at = datetime.now(timezone.utc)
    role.version += 1
    session.commit()
    session.refresh(role)

    # TODO: Log audit event

    return RoleRead.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete role (deactivate)."""

    role = session.get(Role, role_id)
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
        workspace = session.get(Workspace, role.workspace_id)
        if workspace:
            from langflow.api.v1.rbac.dependencies import PermissionChecker
            checker = PermissionChecker(session, current_user)
            if not checker.has_workspace_permission(workspace, "role:delete"):
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
    active_assignments = session.query(RoleAssignment).filter(
        RoleAssignment.role_id == role_id,
        RoleAssignment.is_active == True
    ).count()

    if active_assignments > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role with {active_assignments} active assignments"
        )

    # Deactivate role
    from datetime import datetime, timezone
    role.is_active = False
    role.updated_at = datetime.now(timezone.utc)
    session.commit()

    # TODO: Log audit event


@router.get("/{role_id}/permissions", response_model=list[PermissionRead])
async def list_role_permissions(
    role_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[PermissionRead]:
    """List permissions assigned to role."""

    role = session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Get role permissions
    role_permissions = session.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.is_granted == True
    ).all()

    permissions = []
    for rp in role_permissions:
        permission = session.get(Permission, rp.permission_id)
        if permission:
            permissions.append(PermissionRead.model_validate(permission))

    return permissions


@router.post("/{role_id}/permissions", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(
    role_id: UUID,
    permission_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Assign permission to role."""

    role = session.get(Role, role_id)
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

    permission = session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )

    # Check if assignment already exists
    existing = session.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already assigned to role"
        )

    # Create role permission assignment
    from datetime import datetime, timezone
    role_permission = RolePermission(
        role_id=role_id,
        permission_id=permission_id,
        granted_by_id=current_user.id,
        granted_at=datetime.now(timezone.utc),
        reason=permission_data.get("reason")
    )

    session.add(role_permission)
    session.commit()

    # TODO: Log audit event

    return {
        "message": "Permission assigned successfully",
        "role_id": str(role_id),
        "permission_id": str(permission_id)
    }


@router.delete("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_permission_from_role(
    role_id: UUID,
    permission_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Remove permission from role."""

    role_permission = session.query(RolePermission).filter(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id
    ).first()

    if not role_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission assignment not found"
        )

    session.delete(role_permission)
    session.commit()

    # TODO: Log audit event


@router.post("/initialize-system-roles", status_code=status.HTTP_201_CREATED)
async def initialize_system_roles(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
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
    for perm_data in SYSTEM_PERMISSIONS:
        existing = session.query(Permission).filter(
            Permission.code == perm_data["code"]
        ).first()

        if not existing:
            permission = Permission(
                **perm_data,
                is_system=True
            )
            session.add(permission)
            created_permissions += 1

    # Create system roles
    for role_key, role_data in SYSTEM_ROLES.items():
        existing = session.query(Role).filter(
            Role.name == role_data["name"],
            Role.workspace_id.is_(None)
        ).first()

        if not existing:
            role = Role(
                **role_data,
                created_by_id=current_user.id,
                workspace_id=None
            )
            session.add(role)
            created_roles += 1

    session.commit()

    return {
        "message": "System roles and permissions initialized",
        "permissions_created": created_permissions,
        "roles_created": created_roles
    }

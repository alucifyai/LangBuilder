"""RBAC (Role-Based Access Control) models and utilities.

This package provides the core RBAC data models for LangBuilder:
- Role: Predefined roles (Admin, Owner, Editor, Viewer)
- Permission: Base CRUD permissions
- RolePermission: Role-to-permission mappings
- UserRoleAssignment: User role assignments with scope support

All models support async database operations via CRUD functions.
"""
# ruff: noqa: RUF022

from .crud import (
    create_assignment,
    delete_assignment,
    get_all_assignments,
    get_all_permissions,
    get_all_roles,
    get_assignment_by_id,
    get_assignments_by_scope,
    get_permission_by_id,
    get_permission_by_name,
    get_permissions_for_role,
    get_role_by_id,
    get_role_by_name,
    get_role_permissions,
    get_user_assignment_for_scope,
    get_user_assignments,
    update_assignment,
)
from .model import (
    Permission,
    PermissionEnum,
    PermissionRead,
    Role,
    RoleEnum,
    RolePermission,
    RolePermissionRead,
    RoleRead,
    ScopeTypeEnum,
    UserRoleAssignment,
    UserRoleAssignmentCreate,
    UserRoleAssignmentRead,
    UserRoleAssignmentUpdate,
)

__all__ = [
    # Models
    "Role",
    "Permission",
    "RolePermission",
    "UserRoleAssignment",
    # Enums
    "RoleEnum",
    "PermissionEnum",
    "ScopeTypeEnum",
    # Read schemas
    "RoleRead",
    "PermissionRead",
    "RolePermissionRead",
    "UserRoleAssignmentRead",
    # Write schemas
    "UserRoleAssignmentCreate",
    "UserRoleAssignmentUpdate",
    # CRUD operations
    "get_role_by_id",
    "get_role_by_name",
    "get_all_roles",
    "get_permission_by_id",
    "get_permission_by_name",
    "get_all_permissions",
    "get_role_permissions",
    "get_permissions_for_role",
    "get_assignment_by_id",
    "get_user_assignments",
    "get_user_assignment_for_scope",
    "create_assignment",
    "update_assignment",
    "delete_assignment",
    "get_all_assignments",
    "get_assignments_by_scope",
]

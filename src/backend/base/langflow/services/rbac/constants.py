"""RBAC Constants: Permission Catalog and System Roles.

This module defines the complete permission catalog and system roles
for the LangBuilder RBAC implementation (Task 1.3).

Permissions are defined as tuples of:
(name, display_name, resource_type, action, scope_level)

System roles are defined with their display names, descriptions,
scope levels, and permission assignments.
"""

from typing import Any

# ============================================================================
# PERMISSION CATALOG (v2 EXPANDED - 45 permissions)
# ============================================================================
# Format: (name, display_name, resource_type, action, scope_level)

PERMISSIONS: list[tuple[str, str, str, str, str]] = [
    # === Workspace-level permissions ===
    ("workspace.read", "Read Workspace", "WORKSPACE", "READ", "WORKSPACE"),
    ("workspace.update", "Update Workspace", "WORKSPACE", "UPDATE", "WORKSPACE"),
    ("workspace.delete", "Delete Workspace", "WORKSPACE", "DELETE", "WORKSPACE"),
    (
        "workspace.invite_users",
        "Invite Users to Workspace",
        "WORKSPACE",
        "INVITE",
        "WORKSPACE",
    ),  # PRD @AC5
    (
        "workspace.manage_members",
        "Manage Workspace Members",
        "WORKSPACE",
        "MANAGE_MEMBERS",
        "WORKSPACE",
    ),
    # === Group management permissions ===
    ("group.create", "Create User Group", "GROUP", "CREATE", "WORKSPACE"),
    ("group.read", "Read User Group", "GROUP", "READ", "WORKSPACE"),
    ("group.update", "Update User Group", "GROUP", "UPDATE", "WORKSPACE"),
    ("group.delete", "Delete User Group", "GROUP", "DELETE", "WORKSPACE"),
    ("group.manage_members", "Manage Group Members", "GROUP", "MANAGE_MEMBERS", "WORKSPACE"),
    # === Project (Folder) permissions ===
    ("project.create", "Create Project", "PROJECT", "CREATE", "WORKSPACE"),
    ("project.read", "Read Project", "PROJECT", "READ", "PROJECT"),
    ("project.update", "Update Project", "PROJECT", "UPDATE", "PROJECT"),
    ("project.delete", "Delete Project", "PROJECT", "DELETE", "PROJECT"),
    # === Environment permissions ===
    ("environment.create", "Create Environment", "ENVIRONMENT", "CREATE", "PROJECT"),
    ("environment.read", "Read Environment", "ENVIRONMENT", "READ", "ENVIRONMENT"),
    ("environment.update", "Update Environment", "ENVIRONMENT", "UPDATE", "ENVIRONMENT"),
    ("environment.delete", "Delete Environment", "ENVIRONMENT", "DELETE", "ENVIRONMENT"),
    (
        "environment.deploy",
        "Deploy to Environment",
        "ENVIRONMENT",
        "DEPLOY",
        "ENVIRONMENT",
    ),  # PRD @AC4
    # === Flow permissions ===
    ("flow.create", "Create Flow", "FLOW", "CREATE", "PROJECT"),
    ("flow.read", "Read Flow", "FLOW", "READ", "FLOW"),
    ("flow.update", "Update Flow", "FLOW", "UPDATE", "FLOW"),
    ("flow.delete", "Delete Flow", "FLOW", "DELETE", "FLOW"),
    ("flow.execute", "Execute Flow", "FLOW", "EXECUTE", "FLOW"),
    ("flow.export", "Export Flow", "FLOW", "EXPORT", "FLOW"),  # PRD @AC3
    # === Component permissions ===
    ("component.read", "Read Component", "COMPONENT", "READ", "FLOW"),
    (
        "component.modify_settings",
        "Modify Component Settings",
        "COMPONENT",
        "UPDATE",
        "COMPONENT",
    ),  # PRD @AC7
    # === API Token permissions ===
    ("api_token.create", "Create API Token", "API_TOKEN", "CREATE", "PROJECT"),
    ("api_token.read", "Read API Token", "API_TOKEN", "READ", "PROJECT"),
    ("api_token.revoke", "Revoke API Token", "API_TOKEN", "DELETE", "PROJECT"),
    (
        "api_token.manage",
        "Manage API Tokens",
        "API_TOKEN",
        "MANAGE_TOKENS",
        "PROJECT",
    ),  # PRD @AC8
    # === RBAC Management permissions ===
    ("role.create", "Create Role", "ROLE", "CREATE", "WORKSPACE"),
    ("role.read", "Read Role", "ROLE", "READ", "WORKSPACE"),
    ("role.update", "Update Role", "ROLE", "UPDATE", "WORKSPACE"),
    ("role.delete", "Delete Role", "ROLE", "DELETE", "WORKSPACE"),
    ("role.manage", "Manage Roles", "ROLE", "MANAGE_ROLES", "WORKSPACE"),
    ("grant.create", "Assign Role (Create Grant)", "GRANT", "CREATE", "WORKSPACE"),
    ("grant.read", "Read Role Assignment", "GRANT", "READ", "WORKSPACE"),
    ("grant.revoke", "Revoke Role Assignment", "GRANT", "DELETE", "WORKSPACE"),
    # === User Management permissions ===
    ("user.read", "Read User", "USER", "READ", "WORKSPACE"),
    ("user.invite", "Invite User", "USER", "INVITE", "WORKSPACE"),
    ("user.manage", "Manage Users", "USER", "MANAGE_USERS", "WORKSPACE"),
    # === Audit & Compliance permissions ===
    ("audit.view", "View Audit Logs", "SYSTEM", "VIEW_AUDIT", "WORKSPACE"),
    ("audit.export", "Export Audit Logs", "SYSTEM", "EXPORT_AUDIT", "WORKSPACE"),
    # === Settings permissions ===
    ("settings.read", "Read Settings", "SYSTEM", "READ", "WORKSPACE"),
    ("settings.update", "Update Settings", "SYSTEM", "UPDATE", "WORKSPACE"),
    ("settings.manage", "Manage Settings", "SYSTEM", "MANAGE_SETTINGS", "WORKSPACE"),
]

# Total permissions count for validation
TOTAL_PERMISSIONS_COUNT = len(PERMISSIONS)

# ============================================================================
# SYSTEM ROLES (v2 EXPANDED - 6 roles)
# ============================================================================

SYSTEM_ROLES: dict[str, dict[str, Any]] = {
    "workspace_owner": {
        "display_name": "Workspace Owner",
        "description": "Full access to all resources in workspace, including workspace settings",
        "scope_level": "WORKSPACE",
        "permissions": [
            # All workspace permissions
            "workspace.read",
            "workspace.update",
            "workspace.delete",
            "workspace.invite_users",
            "workspace.manage_members",
            # All group permissions
            "group.create",
            "group.read",
            "group.update",
            "group.delete",
            "group.manage_members",
            # All project permissions
            "project.create",
            "project.read",
            "project.update",
            "project.delete",
            # All environment permissions
            "environment.create",
            "environment.read",
            "environment.update",
            "environment.delete",
            "environment.deploy",
            # All flow permissions
            "flow.create",
            "flow.read",
            "flow.update",
            "flow.delete",
            "flow.execute",
            "flow.export",
            # All component permissions
            "component.read",
            "component.modify_settings",
            # All API token permissions
            "api_token.create",
            "api_token.read",
            "api_token.revoke",
            "api_token.manage",
            # All RBAC management permissions
            "role.create",
            "role.read",
            "role.update",
            "role.delete",
            "role.manage",
            "grant.create",
            "grant.read",
            "grant.revoke",
            # All user management permissions
            "user.read",
            "user.invite",
            "user.manage",
            # All audit permissions
            "audit.view",
            "audit.export",
            # All settings permissions
            "settings.read",
            "settings.update",
            "settings.manage",
        ],
        "is_system_role": True,
    },
    "workspace_admin": {
        "display_name": "Workspace Admin",
        "description": "Manage users, roles, and settings within workspace",
        "scope_level": "WORKSPACE",
        "permissions": [
            "workspace.read",
            "workspace.update",
            "workspace.invite_users",
            "workspace.manage_members",
            # All group permissions
            "group.create",
            "group.read",
            "group.update",
            "group.delete",
            "group.manage_members",
            # Limited project permissions
            "project.read",
            "project.create",
            # Limited environment permissions
            "environment.read",
            # Limited flow permissions
            "flow.read",
            # All user management permissions
            "user.read",
            "user.invite",
            "user.manage",
            # All RBAC management permissions
            "role.create",
            "role.read",
            "role.update",
            "role.delete",
            "role.manage",
            "grant.create",
            "grant.read",
            "grant.revoke",
            # Audit permissions
            "audit.view",
            "audit.export",
            # Settings permissions
            "settings.read",
            "settings.update",
        ],
        "is_system_role": True,
    },
    "project_admin": {
        "display_name": "Project Admin",
        "description": "Full access to project and its contents",
        "scope_level": "PROJECT",
        "permissions": [
            "project.read",
            "project.update",
            "project.delete",
            # All environment permissions
            "environment.create",
            "environment.read",
            "environment.update",
            "environment.delete",
            "environment.deploy",
            # All flow permissions
            "flow.create",
            "flow.read",
            "flow.update",
            "flow.delete",
            "flow.execute",
            "flow.export",
            # All component permissions
            "component.read",
            "component.modify_settings",
            # All API token permissions
            "api_token.create",
            "api_token.read",
            "api_token.revoke",
            "api_token.manage",
        ],
        "is_system_role": True,
    },
    "editor": {
        "display_name": "Editor",
        "description": "Create and edit flows, deploy to environments",
        "scope_level": "PROJECT",
        "permissions": [
            "project.read",
            # Environment permissions
            "environment.read",
            "environment.deploy",
            # Flow permissions
            "flow.create",
            "flow.read",
            "flow.update",
            "flow.delete",
            "flow.execute",
            "flow.export",
            # Component permissions
            "component.read",
            "component.modify_settings",
        ],
        "is_system_role": True,
    },
    "viewer": {
        "display_name": "Viewer",
        "description": "Read-only access to flows and components",
        "scope_level": "PROJECT",
        "permissions": [
            "project.read",
            "environment.read",
            "flow.read",
            "component.read",
        ],
        "is_system_role": True,
    },
    "service_account": {
        "display_name": "Service Account",
        "description": "Programmatic access with token-scoped permissions",
        "scope_level": "PROJECT",
        "permissions": [],  # Permissions assigned per service account
        "is_system_role": True,
    },
}

# Total system roles count for validation
TOTAL_SYSTEM_ROLES_COUNT = len(SYSTEM_ROLES)

# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def get_all_permission_names() -> list[str]:
    """Get a list of all permission names from the catalog."""
    return [perm[0] for perm in PERMISSIONS]


def get_permission_by_name(name: str) -> tuple[str, str, str, str, str] | None:
    """Get permission tuple by name."""
    for perm in PERMISSIONS:
        if perm[0] == name:
            return perm
    return None


def expand_wildcards(permissions: list[str]) -> list[str]:
    """Expand wildcard permissions like 'workspace.*' to explicit permission lists.

    This function supports the implementation plan's wildcard pattern specification
    while maintaining explicit permission grants for security auditability.

    Args:
        permissions: List of permission names, may include wildcards (e.g., "workspace.*")

    Returns:
        List of expanded permission names (all wildcards resolved to explicit names)

    Examples:
        >>> expand_wildcards(["workspace.*", "flow.read"])
        ["workspace.read", "workspace.update", "workspace.delete", ..., "flow.read"]

        >>> expand_wildcards(["project.read"])
        ["project.read"]
    """
    expanded = []
    all_permissions = get_all_permission_names()

    for perm in permissions:
        if perm.endswith(".*"):
            # Wildcard pattern: expand to all permissions with matching resource prefix
            resource_prefix = perm[:-2]  # Remove ".*" suffix
            matching_perms = [p for p in all_permissions if p.startswith(f"{resource_prefix}.")]
            expanded.extend(matching_perms)
        else:
            # Explicit permission: add as-is
            expanded.append(perm)

    # Remove duplicates while preserving order
    seen = set()
    result = []
    for perm in expanded:
        if perm not in seen:
            seen.add(perm)
            result.append(perm)

    return result


def validate_role_permissions(role_name: str, permissions: list[str]) -> list[str]:
    """Validate that all permissions in a role exist in the catalog.

    Supports both explicit permissions and wildcard patterns.

    Args:
        role_name: Name of the role being validated
        permissions: List of permission names to validate (may include wildcards)

    Returns:
        List of invalid permission names (empty if all valid)
    """
    # Expand wildcards first
    expanded_permissions = expand_wildcards(permissions)

    # Validate expanded permissions against catalog
    valid_permissions = get_all_permission_names()
    invalid = []
    for perm in expanded_permissions:
        if perm not in valid_permissions:
            invalid.append(perm)
    return invalid


# Validate system roles on module import
for role_name, role_data in SYSTEM_ROLES.items():
    invalid = validate_role_permissions(role_name, role_data["permissions"])
    if invalid:
        msg = (
            f"System role '{role_name}' contains invalid permissions: {invalid}. "
            f"These permissions are not defined in the permission catalog."
        )
        raise ValueError(msg)

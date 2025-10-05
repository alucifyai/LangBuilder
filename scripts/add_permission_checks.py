#!/usr/bin/env python3
"""Script to add permission checks to RBAC API endpoints.

This script updates all RBAC API endpoint files to include permission checks
using the RequireRBACPermission dependencies.

CRITICAL FIX from Phase 3 Audit Report.
"""

import re
from pathlib import Path

# Mapping of endpoint functions to required permissions
ENDPOINT_PERMISSIONS = {
    # Roles API
    "get_roles": ("RequireRoleRead", "role:read"),
    "get_role": ("RequireRoleRead", "role:read"),
    "create_new_role": ("RequireRoleCreate", "role:create"),
    "update_existing_role": ("RequireRoleUpdate", "role:update"),
    "delete_existing_role": ("RequireRoleDelete", "role:delete"),

    # Permissions API
    "get_permissions": ("RequirePermissionRead", "permission:read"),
    "get_permission": ("RequirePermissionRead", "permission:read"),

    # Grants API
    "get_grants": ("RequireGrantRead", "grant:read"),
    "get_grant": ("RequireGrantRead", "grant:read"),
    "create_new_grant": ("RequireGrantCreate", "grant:create"),
    "update_existing_grant": ("RequireGrantUpdate", "grant:update"),
    "delete_existing_grant": ("RequireGrantDelete", "grant:delete"),

    # Groups API
    "get_groups": ("RequireGroupRead", "group:read"),
    "get_group": ("RequireGroupRead", "group:read"),
    "create_new_group": ("RequireGroupCreate", "group:create"),
    "update_existing_group": ("RequireGroupUpdate", "group:update"),
    "delete_existing_group": ("RequireGroupDelete", "group:delete"),
    "add_group_member": ("RequireGroupUpdate", "group:update"),
    "remove_group_member": ("RequireGroupUpdate", "group:update"),

    # ServiceAccounts API
    "get_service_accounts": ("RequireServiceAccountRead", "service_account:read"),
    "get_service_account": ("RequireServiceAccountRead", "service_account:read"),
    "create_new_service_account": ("RequireServiceAccountCreate", "service_account:create"),
    "update_existing_service_account": ("RequireServiceAccountUpdate", "service_account:update"),
    "delete_existing_service_account": ("RequireServiceAccountDelete", "service_account:delete"),
    "rotate_service_account_key": ("RequireServiceAccountUpdate", "service_account:update"),

    # AuditLog API
    "get_audit_logs": ("RequireAuditLogRead", "audit_log:read"),
    "get_audit_log": ("RequireAuditLogRead", "audit_log:read"),
}


def add_permission_check_to_endpoint(file_path: Path, function_name: str, permission_dep: str) -> None:
    """Add permission check parameter to an endpoint function.

    Args:
        file_path: Path to the API file
        function_name: Name of the endpoint function
        permission_dep: Permission dependency type (e.g., "RequireRoleRead")
    """
    content = file_path.read_text()

    # Pattern to match async function definition
    pattern = rf"(async def {function_name}\s*\([^)]*?current_user:\s*CurrentActiveUser)"

    # Add _perm parameter after current_user
    replacement = rf"\1,\n    _perm: {permission_dep}"

    # Update content
    updated_content = re.sub(pattern, replacement, content)

    if updated_content != content:
        file_path.write_text(updated_content)
        print(f"✅ Added {permission_dep} to {function_name} in {file_path.name}")
    else:
        print(f"⚠️  Could not find function {function_name} in {file_path.name}")


def add_imports_to_file(file_path: Path, required_deps: set[str]) -> None:
    """Add permission dependency imports to a file.

    Args:
        file_path: Path to the API file
        required_deps: Set of required dependency types
    """
    content = file_path.read_text()

    # Check if dependencies module is already imported
    if "from langflow.api.v1.rbac.dependencies import" in content:
        print(f"ℹ️  {file_path.name} already has dependency imports")
        return

    # Find the CurrentActiveUser import line
    pattern = r"(from langflow\.api\.utils import.*)"

    # Create import statement
    deps_str = ",\n    ".join(sorted(required_deps))
    import_statement = f"\nfrom langflow.api.v1.rbac.dependencies import (\n    {deps_str},\n)"

    # Add import after api.utils import
    updated_content = re.sub(pattern, rf"\1{import_statement}", content)

    if updated_content != content:
        file_path.write_text(updated_content)
        print(f"✅ Added imports to {file_path.name}")
    else:
        print(f"⚠️  Could not add imports to {file_path.name}")


def remove_todo_comments(file_path: Path) -> None:
    """Remove TODO comments about permission checks.

    Args:
        file_path: Path to the API file
    """
    content = file_path.read_text()

    # Remove TODO Phase 3 permission check comments
    pattern = r"\s*# TODO Phase 3: Add permission check.*\n"
    updated_content = re.sub(pattern, "", content)

    if updated_content != content:
        file_path.write_text(updated_content)
        print(f"✅ Removed TODO comments from {file_path.name}")


def main():
    """Main function to update all RBAC API files."""
    base_path = Path(__file__).parent.parent / "src/backend/base/langflow/api/v1/rbac"

    # Group endpoints by file
    file_endpoints = {}
    for func_name, (dep_type, _) in ENDPOINT_PERMISSIONS.items():
        # Determine file based on function name pattern
        if "role" in func_name and "service" not in func_name:
            file_name = "roles.py"
        elif "permission" in func_name:
            file_name = "permissions.py"
        elif "grant" in func_name:
            file_name = "grants.py"
        elif "group" in func_name:
            file_name = "groups.py"
        elif "service_account" in func_name:
            file_name = "service_accounts.py"
        elif "audit_log" in func_name:
            file_name = "audit_logs.py"
        else:
            continue

        if file_name not in file_endpoints:
            file_endpoints[file_name] = []
        file_endpoints[file_name].append((func_name, dep_type))

    # Process each file
    for file_name, endpoints in file_endpoints.items():
        file_path = base_path / file_name
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue

        print(f"\n📝 Processing {file_name}...")

        # Collect required dependencies for this file
        required_deps = {dep_type for _, dep_type in endpoints}

        # Add imports
        add_imports_to_file(file_path, required_deps)

        # Add permission checks to each endpoint
        for func_name, dep_type in endpoints:
            add_permission_check_to_endpoint(file_path, func_name, dep_type)

        # Remove TODO comments
        remove_todo_comments(file_path)

    print("\n✨ Permission checks added to all RBAC API endpoints!")
    print("ℹ️  Note: Review the changes and test thoroughly before deployment.")


if __name__ == "__main__":
    main()

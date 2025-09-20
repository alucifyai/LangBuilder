#!/usr/bin/env python3
"""Complete security fix to apply @secure_endpoint to ALL remaining endpoints."""

import re
from pathlib import Path

# Security configurations for different endpoint types
ENDPOINT_SECURITY_CONFIGS = {
    # Generic secure configs
    "default": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    # Audit specific
    "audit_read": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="audit_log",
        action="read",
        require_workspace_access=True,
        audit_action="read_audit_logs",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    # Workspace specific
    "workspace_read": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="workspace",
        action="read",
        require_workspace_access=True,
        audit_action="read_workspace",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    "workspace_write": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="workspace",
        action="update",
        require_workspace_access=True,
        audit_action="update_workspace",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    # Project specific
    "project_read": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="project",
        action="read",
        require_workspace_access=True,
        audit_action="read_project",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
        validate_project_exists=True,
    ),
    audit_enabled=True,
)""",

    "project_write": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="project",
        action="update",
        require_workspace_access=True,
        audit_action="update_project",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
        validate_project_exists=True,
    ),
    audit_enabled=True,
)""",

    # Role specific
    "role_read": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="role",
        action="read",
        require_workspace_access=True,
        audit_action="read_role",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    "role_write": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="role",
        action="update",
        require_workspace_access=True,
        audit_action="update_role",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    # Service account specific
    "service_account_read": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="service_account",
        action="read",
        require_workspace_access=True,
        audit_action="read_service_account",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",

    "service_account_write": """@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="service_account",
        action="update",
        require_workspace_access=True,
        audit_action="update_service_account",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)""",
}

def get_security_config_for_endpoint(filename: str, endpoint_name: str, http_method: str) -> str:
    """Get appropriate security config based on file and endpoint context."""

    # Map based on filename and HTTP method
    if "audit" in filename:
        return ENDPOINT_SECURITY_CONFIGS["audit_read"]
    elif "workspace" in filename:
        if http_method in ["post", "put", "patch", "delete"]:
            return ENDPOINT_SECURITY_CONFIGS["workspace_write"]
        else:
            return ENDPOINT_SECURITY_CONFIGS["workspace_read"]
    elif "project" in filename:
        if http_method in ["post", "put", "patch", "delete"]:
            return ENDPOINT_SECURITY_CONFIGS["project_write"]
        else:
            return ENDPOINT_SECURITY_CONFIGS["project_read"]
    elif "role" in filename:
        if http_method in ["post", "put", "patch", "delete"]:
            return ENDPOINT_SECURITY_CONFIGS["role_write"]
        else:
            return ENDPOINT_SECURITY_CONFIGS["role_read"]
    elif "service_account" in filename:
        if http_method in ["post", "put", "patch", "delete"]:
            return ENDPOINT_SECURITY_CONFIGS["service_account_write"]
        else:
            return ENDPOINT_SECURITY_CONFIGS["service_account_read"]
    else:
        return ENDPOINT_SECURITY_CONFIGS["default"]

def fix_function_signature(content: str, function_name: str) -> str:
    """Update function signature to include enhanced security dependencies."""

    # Pattern to match the function definition
    pattern = rf"(async def {function_name}\s*\(\s*)(.*?)(\s*\)\s*->[^:]*:)"

    def replace_signature(match):
        prefix = match.group(1)
        params = match.group(2)
        suffix = match.group(3)

        # Skip if already enhanced
        if "Annotated[CurrentActiveUser, Depends(get_authenticated_user)]" in params:
            return match.group(0)

        # Add request parameter if not present
        if "request: Request" not in params and "http_request: Request" not in params:
            if params.strip():
                params = "request: Request,\n    " + params
            else:
                params = "request: Request"

        # Update CurrentActiveUser dependency
        params = re.sub(
            r"current_user:\s*CurrentActiveUser(?!\s*=)",
            "current_user: Annotated[CurrentActiveUser, Depends(get_authenticated_user)]",
            params
        )

        # Add RuntimeEnforcementContext if not present
        if "RuntimeEnforcementContext" not in params:
            # Find insertion point after current_user
            params = re.sub(
                r"(current_user: Annotated\[CurrentActiveUser, Depends\(get_authenticated_user\)\]),?",
                r"\1,\n    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],",
                params
            )

        return f"{prefix}{params}{suffix}"

    return re.sub(pattern, replace_signature, content, flags=re.DOTALL)

def apply_security_to_file(filepath: Path) -> int:
    """Apply security decorators to all unsecured endpoints in a file."""

    print(f"🔧 Processing {filepath.name}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Find all @router decorators and their positions
    # This pattern handles cases where there might be decorators between @router and async def
    router_pattern = r'(@router\.(get|post|put|patch|delete)\([^)]*\))(?:\s*\n(?:@[^\n]*\n)*)*\s*\n\s*(async def (\w+)\s*\([^)]*\):)'

    matches = list(re.finditer(router_pattern, content, re.DOTALL | re.MULTILINE))

    if not matches:
        print(f"   ❌ No @router patterns found in {filepath.name}")
        return 0

    modifications = 0
    modified_content = content

    # Process matches in reverse order to maintain positions
    for match in reversed(matches):
        router_line = match.group(1)
        http_method = match.group(2)
        function_line = match.group(3)
        function_name = match.group(4)

        # Check if this endpoint already has @secure_endpoint
        # Look for @secure_endpoint in the 500 characters before this match
        before_match = content[:match.start()]
        recent_content = before_match[-500:] if len(before_match) > 500 else before_match

        if "@secure_endpoint" in recent_content:
            print(f"   ✅ {function_name} already secured")
            continue

        print(f"   🔒 Adding security to {function_name} ({http_method.upper()})")

        # Get appropriate security configuration
        security_config = get_security_config_for_endpoint(filepath.name, function_name, http_method)

        # Replace the router line with router + security decorator
        full_match = match.group(0)
        replacement = f"{router_line}\n{security_config}\n{function_line}:"

        modified_content = modified_content.replace(full_match, replacement)

        # Update function signature
        modified_content = fix_function_signature(modified_content, function_name)

        modifications += 1

    if modifications > 0:
        # Write the modified content back
        with open(filepath, 'w') as f:
            f.write(modified_content)

        print(f"   ✅ Applied {modifications} security decorators to {filepath.name}")
    else:
        print(f"   ℹ️ {filepath.name} already fully secured")

    return modifications

def main():
    """Apply security decorators to all missing endpoints."""

    print("🔒 COMPLETE SECURITY FIX - Adding @secure_endpoint to ALL remaining endpoints")
    print("=" * 80)

    rbac_path = Path("src/backend/base/langflow/api/v1/rbac")

    # Files that need security fixes (identified from audit)
    files_to_fix = [
        "audit.py",
        "projects.py",
        "roles.py",
        "service_accounts.py",
        "workspaces.py"
    ]

    total_modifications = 0

    for filename in files_to_fix:
        filepath = rbac_path / filename

        if filepath.exists():
            modifications = apply_security_to_file(filepath)
            total_modifications += modifications
        else:
            print(f"❌ {filename} not found")

    print("\n" + "=" * 80)
    print(f"✅ Security fix complete!")
    print(f"📊 Total security decorators applied: {total_modifications}")
    print("=" * 80)

if __name__ == "__main__":
    main()
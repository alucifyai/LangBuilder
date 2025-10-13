"""Unit tests for RBAC constants and permission catalog.

Tests the permission catalog, system roles, and validation functions
defined in constants.py (Task 1.3).
"""

import pytest
from langflow.services.rbac.constants import (
    PERMISSIONS,
    SYSTEM_ROLES,
    TOTAL_PERMISSIONS_COUNT,
    TOTAL_SYSTEM_ROLES_COUNT,
    get_all_permission_names,
    get_permission_by_name,
    validate_role_permissions,
)


class TestPermissionCatalog:
    """Test the permission catalog structure and content."""

    def test_permissions_count(self):
        """Test that the expected number of permissions are defined."""
        assert len(PERMISSIONS) == TOTAL_PERMISSIONS_COUNT
        assert TOTAL_PERMISSIONS_COUNT >= 45, "Should have at least 45 permissions as per PRD"

    def test_permission_tuple_structure(self):
        """Test that each permission tuple has the correct structure."""
        for perm in PERMISSIONS:
            assert isinstance(perm, tuple), "Each permission should be a tuple"
            assert len(perm) == 5, "Each permission should have 5 elements"
            name, display_name, resource_type, action, scope_level = perm
            assert isinstance(name, str) and name, "Permission name must be a non-empty string"
            assert isinstance(display_name, str) and display_name, "Display name must be a non-empty string"
            assert isinstance(resource_type, str) and resource_type, "Resource type must be a non-empty string"
            assert isinstance(action, str) and action, "Action must be a non-empty string"
            assert isinstance(scope_level, str) and scope_level, "Scope level must be a non-empty string"

    def test_permission_names_unique(self):
        """Test that all permission names are unique."""
        names = [perm[0] for perm in PERMISSIONS]
        assert len(names) == len(set(names)), "All permission names should be unique"

    def test_permission_naming_convention(self):
        """Test that permission names follow the {resource}.{action} pattern."""
        for perm in PERMISSIONS:
            name = perm[0]
            assert "." in name, f"Permission name '{name}' should contain a dot"
            parts = name.split(".")
            assert len(parts) == 2, f"Permission name '{name}' should have exactly 2 parts"
            assert parts[0] and parts[1], f"Both parts of '{name}' should be non-empty"

    def test_workspace_permissions_exist(self):
        """Test that workspace-level permissions are included (v2 requirement)."""
        workspace_perms = [p for p in PERMISSIONS if p[0].startswith("workspace.")]
        assert len(workspace_perms) >= 5, "Should have at least 5 workspace permissions"

        # Check for specific workspace permissions from PRD
        perm_names = [p[0] for p in workspace_perms]
        assert "workspace.read" in perm_names
        assert "workspace.update" in perm_names
        assert "workspace.invite_users" in perm_names
        assert "workspace.manage_members" in perm_names

    def test_group_permissions_exist(self):
        """Test that group management permissions are included (v2 requirement)."""
        group_perms = [p for p in PERMISSIONS if p[0].startswith("group.")]
        assert len(group_perms) >= 5, "Should have at least 5 group permissions"

        # Check for specific group permissions
        perm_names = [p[0] for p in group_perms]
        assert "group.create" in perm_names
        assert "group.read" in perm_names
        assert "group.update" in perm_names
        assert "group.delete" in perm_names
        assert "group.manage_members" in perm_names

    def test_environment_permissions_exist(self):
        """Test that environment-scoped permissions are included (v2 requirement)."""
        env_perms = [p for p in PERMISSIONS if p[0].startswith("environment.")]
        assert len(env_perms) >= 5, "Should have at least 5 environment permissions"

        # Check for specific environment permissions from PRD
        perm_names = [p[0] for p in env_perms]
        assert "environment.create" in perm_names
        assert "environment.read" in perm_names
        assert "environment.update" in perm_names
        assert "environment.delete" in perm_names
        assert "environment.deploy" in perm_names  # PRD @AC4

    def test_flow_permissions_exist(self):
        """Test that flow permissions include all required actions."""
        flow_perms = [p for p in PERMISSIONS if p[0].startswith("flow.")]
        perm_names = [p[0] for p in flow_perms]

        # PRD requirements
        assert "flow.create" in perm_names
        assert "flow.read" in perm_names
        assert "flow.update" in perm_names
        assert "flow.delete" in perm_names
        assert "flow.execute" in perm_names
        assert "flow.export" in perm_names  # PRD @AC3

    def test_rbac_management_permissions_exist(self):
        """Test that RBAC management permissions are included."""
        role_perms = [p for p in PERMISSIONS if p[0].startswith("role.")]
        grant_perms = [p for p in PERMISSIONS if p[0].startswith("grant.")]

        assert len(role_perms) >= 4, "Should have role management permissions"
        assert len(grant_perms) >= 3, "Should have grant management permissions"

    def test_audit_permissions_exist(self):
        """Test that audit permissions are included."""
        audit_perms = [p for p in PERMISSIONS if p[0].startswith("audit.")]
        perm_names = [p[0] for p in audit_perms]

        assert "audit.view" in perm_names
        assert "audit.export" in perm_names


class TestSystemRoles:
    """Test the system roles structure and content."""

    def test_system_roles_count(self):
        """Test that the expected number of system roles are defined."""
        assert len(SYSTEM_ROLES) == TOTAL_SYSTEM_ROLES_COUNT
        assert TOTAL_SYSTEM_ROLES_COUNT >= 6, "Should have at least 6 system roles"

    def test_system_role_structure(self):
        """Test that each system role has the correct structure."""
        required_keys = {"display_name", "description", "scope_level", "permissions", "is_system_role"}

        for role_name, role_data in SYSTEM_ROLES.items():
            assert isinstance(role_name, str) and role_name, "Role name must be a non-empty string"
            assert isinstance(role_data, dict), f"Role data for '{role_name}' must be a dict"
            assert required_keys.issubset(
                role_data.keys()
            ), f"Role '{role_name}' missing required keys: {required_keys - role_data.keys()}"

            assert isinstance(role_data["display_name"], str)
            assert isinstance(role_data["description"], str)
            assert isinstance(role_data["scope_level"], str)
            assert isinstance(role_data["permissions"], list)
            assert role_data["is_system_role"] is True

    def test_required_system_roles_exist(self):
        """Test that all required system roles are defined."""
        required_roles = {
            "workspace_owner",
            "workspace_admin",
            "project_admin",
            "editor",
            "viewer",
            "service_account",
        }

        assert required_roles.issubset(SYSTEM_ROLES.keys()), f"Missing roles: {required_roles - SYSTEM_ROLES.keys()}"

    def test_workspace_owner_has_all_permissions(self):
        """Test that workspace_owner has the most comprehensive permissions."""
        owner_perms = set(SYSTEM_ROLES["workspace_owner"]["permissions"])

        # Workspace owner should have more permissions than any other role
        for role_name, role_data in SYSTEM_ROLES.items():
            if role_name == "workspace_owner":
                continue
            if role_name == "service_account":
                continue  # Service accounts have custom permissions

            role_perms = set(role_data["permissions"])
            assert role_perms.issubset(
                owner_perms
            ), f"Workspace owner should have all permissions that '{role_name}' has"

    def test_workspace_admin_permissions(self):
        """Test that workspace_admin has expected permissions."""
        admin_perms = set(SYSTEM_ROLES["workspace_admin"]["permissions"])

        # Should have user management
        assert "user.read" in admin_perms
        assert "user.invite" in admin_perms
        assert "user.manage" in admin_perms

        # Should have role management
        assert "role.create" in admin_perms
        assert "role.read" in admin_perms
        assert "role.update" in admin_perms
        assert "role.delete" in admin_perms

        # Should have audit viewing
        assert "audit.view" in admin_perms

    def test_editor_permissions(self):
        """Test that editor role has appropriate permissions."""
        editor_perms = set(SYSTEM_ROLES["editor"]["permissions"])

        # Should have flow CRUD
        assert "flow.create" in editor_perms
        assert "flow.read" in editor_perms
        assert "flow.update" in editor_perms
        assert "flow.delete" in editor_perms
        assert "flow.execute" in editor_perms

        # Should have deployment permission
        assert "environment.deploy" in editor_perms

        # Should NOT have user management
        assert "user.manage" not in editor_perms

    def test_viewer_permissions(self):
        """Test that viewer role has read-only permissions."""
        viewer_perms = set(SYSTEM_ROLES["viewer"]["permissions"])

        # Should only have read permissions
        assert "project.read" in viewer_perms
        assert "environment.read" in viewer_perms
        assert "flow.read" in viewer_perms
        assert "component.read" in viewer_perms

        # Should NOT have any write/update/delete permissions
        for perm in viewer_perms:
            assert not any(
                action in perm for action in ["create", "update", "delete", "manage", "revoke", "deploy", "execute"]
            ), f"Viewer should not have write permission: {perm}"

    def test_service_account_role(self):
        """Test that service_account role has no default permissions."""
        sa_perms = SYSTEM_ROLES["service_account"]["permissions"]
        assert isinstance(sa_perms, list)
        assert len(sa_perms) == 0, "Service account should have no default permissions"

    def test_role_scope_levels(self):
        """Test that role scope levels are valid."""
        valid_scopes = {"WORKSPACE", "PROJECT", "FLOW", "COMPONENT", "ENVIRONMENT"}

        for role_name, role_data in SYSTEM_ROLES.items():
            scope = role_data["scope_level"]
            assert scope in valid_scopes, f"Role '{role_name}' has invalid scope level: {scope}"


class TestValidationFunctions:
    """Test the helper validation functions."""

    def test_get_all_permission_names(self):
        """Test getting all permission names."""
        names = get_all_permission_names()

        assert isinstance(names, list)
        assert len(names) == TOTAL_PERMISSIONS_COUNT
        assert all(isinstance(name, str) for name in names)
        assert len(names) == len(set(names)), "All names should be unique"

    def test_get_permission_by_name_existing(self):
        """Test getting an existing permission by name."""
        result = get_permission_by_name("workspace.read")

        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 5
        assert result[0] == "workspace.read"

    def test_get_permission_by_name_nonexistent(self):
        """Test getting a non-existent permission returns None."""
        result = get_permission_by_name("nonexistent.permission")
        assert result is None

    def test_validate_role_permissions_valid(self):
        """Test validating permissions with all valid permissions."""
        permissions = ["workspace.read", "project.create", "flow.read"]
        invalid = validate_role_permissions("test_role", permissions)

        assert isinstance(invalid, list)
        assert len(invalid) == 0, "All permissions should be valid"

    def test_validate_role_permissions_invalid(self):
        """Test validating permissions with some invalid permissions."""
        permissions = ["workspace.read", "invalid.permission", "another.invalid"]
        invalid = validate_role_permissions("test_role", permissions)

        assert isinstance(invalid, list)
        assert len(invalid) == 2
        assert "invalid.permission" in invalid
        assert "another.invalid" in invalid

    def test_validate_role_permissions_empty_list(self):
        """Test validating an empty permission list."""
        invalid = validate_role_permissions("test_role", [])
        assert isinstance(invalid, list)
        assert len(invalid) == 0

    def test_system_roles_auto_validation(self):
        """Test that system roles are auto-validated on import.

        This test verifies that invalid permissions in system roles
        would raise an error on module import.
        """
        # If we reach this point, validation passed
        # (module was imported successfully in imports at top)
        assert True

        # Verify each system role has only valid permissions
        all_perm_names = set(get_all_permission_names())
        for role_name, role_data in SYSTEM_ROLES.items():
            if role_name == "service_account":
                continue  # Service accounts have no default permissions

            for perm in role_data["permissions"]:
                assert (
                    perm in all_perm_names
                ), f"Role '{role_name}' has invalid permission: {perm}"


class TestPermissionCoverage:
    """Test permission catalog coverage of PRD requirements."""

    def test_prd_ac3_flow_export(self):
        """Test PRD @AC3: Flow export permission exists."""
        perm_names = get_all_permission_names()
        assert "flow.export" in perm_names, "PRD @AC3 requires flow.export permission"

    def test_prd_ac4_environment_deploy(self):
        """Test PRD @AC4: Environment deploy permission exists."""
        perm_names = get_all_permission_names()
        assert "environment.deploy" in perm_names, "PRD @AC4 requires environment.deploy permission"

    def test_prd_ac5_workspace_invite(self):
        """Test PRD @AC5: Workspace invite users permission exists."""
        perm_names = get_all_permission_names()
        assert "workspace.invite_users" in perm_names, "PRD @AC5 requires workspace.invite_users permission"

    def test_prd_ac7_component_modify(self):
        """Test PRD @AC7: Component modify settings permission exists."""
        perm_names = get_all_permission_names()
        assert "component.modify_settings" in perm_names, "PRD @AC7 requires component.modify_settings permission"

    def test_prd_ac8_api_token_manage(self):
        """Test PRD @AC8: API token management permission exists."""
        perm_names = get_all_permission_names()
        assert "api_token.manage" in perm_names, "PRD @AC8 requires api_token.manage permission"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_permission_name(self):
        """Test that empty permission names are not allowed."""
        for perm in PERMISSIONS:
            assert perm[0].strip(), "Permission names should not be empty or whitespace"

    def test_permission_display_names_descriptive(self):
        """Test that display names are descriptive."""
        for perm in PERMISSIONS:
            display_name = perm[1]
            assert len(display_name) > 5, f"Display name '{display_name}' should be descriptive"
            assert display_name[0].isupper(), f"Display name '{display_name}' should start with capital letter"

    def test_no_duplicate_resource_action_pairs(self):
        """Test that resource_type + action pairs are unique."""
        pairs = [(perm[2], perm[3]) for perm in PERMISSIONS]
        assert len(pairs) == len(set(pairs)), "Resource type + action pairs should be unique"

    def test_system_role_names_snake_case(self):
        """Test that system role names use snake_case convention."""
        for role_name in SYSTEM_ROLES.keys():
            assert role_name.islower(), f"Role name '{role_name}' should be lowercase"
            assert " " not in role_name, f"Role name '{role_name}' should not contain spaces"

    def test_system_role_display_names_title_case(self):
        """Test that system role display names use Title Case."""
        for role_data in SYSTEM_ROLES.values():
            display_name = role_data["display_name"]
            words = display_name.split()
            assert all(word[0].isupper() for word in words if len(word) > 0), f"Display name '{display_name}' should be Title Case"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

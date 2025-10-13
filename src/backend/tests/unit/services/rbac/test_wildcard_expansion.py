"""Unit tests for wildcard permission expansion feature.

Tests the expand_wildcards() function and wildcard support in
validate_role_permissions() (Gap Fix #1 from Audit Report).
"""

import pytest
from langflow.services.rbac.constants import (
    PERMISSIONS,
    expand_wildcards,
    get_all_permission_names,
    validate_role_permissions,
)


class TestExpandWildcards:
    """Test wildcard permission expansion functionality."""

    def test_expand_single_wildcard(self):
        """Test expanding a single wildcard pattern."""
        # Expand workspace.* to all workspace permissions
        result = expand_wildcards(["workspace.*"])

        # Should include all workspace permissions
        assert "workspace.read" in result
        assert "workspace.update" in result
        assert "workspace.delete" in result
        assert "workspace.invite_users" in result
        assert "workspace.manage_members" in result

        # Should have exactly 5 workspace permissions
        workspace_perms = [p for p in PERMISSIONS if p[0].startswith("workspace.")]
        assert len([p for p in result if p.startswith("workspace.")]) == len(workspace_perms)

    def test_expand_multiple_wildcards(self):
        """Test expanding multiple wildcard patterns."""
        result = expand_wildcards(["workspace.*", "group.*"])

        # Should include workspace permissions
        assert "workspace.read" in result
        assert "workspace.manage_members" in result

        # Should include group permissions
        assert "group.create" in result
        assert "group.read" in result
        assert "group.manage_members" in result

    def test_expand_mixed_wildcards_and_explicit(self):
        """Test expanding mix of wildcards and explicit permissions."""
        result = expand_wildcards(["workspace.*", "flow.read", "flow.execute"])

        # Should include expanded wildcards
        assert "workspace.read" in result

        # Should include explicit permissions
        assert "flow.read" in result
        assert "flow.execute" in result

    def test_expand_explicit_only(self):
        """Test that explicit permissions pass through unchanged."""
        explicit = ["flow.read", "flow.execute", "project.read"]
        result = expand_wildcards(explicit)

        assert result == explicit

    def test_expand_no_duplicates(self):
        """Test that expansion removes duplicates."""
        # Provide both wildcard and explicit permission
        result = expand_wildcards(["workspace.*", "workspace.read"])

        # workspace.read should appear only once
        assert result.count("workspace.read") == 1

    def test_expand_preserves_order(self):
        """Test that expansion preserves order (duplicates removed, first occurrence kept)."""
        result = expand_wildcards(["flow.read", "workspace.*", "workspace.read"])

        # flow.read should come first
        assert result.index("flow.read") < result.index("workspace.read")

    def test_expand_all_resource_types(self):
        """Test expanding wildcards for all resource types."""
        wildcards = [
            "workspace.*",
            "group.*",
            "project.*",
            "environment.*",
            "flow.*",
            "component.*",
            "api_token.*",
            "role.*",
            "grant.*",
            "user.*",
            "audit.*",
            "settings.*",
        ]

        result = expand_wildcards(wildcards)

        # Should include all permissions
        all_perms = get_all_permission_names()
        assert set(result) == set(all_perms)
        assert len(result) == len(all_perms)

    def test_expand_nonexistent_wildcard(self):
        """Test expanding wildcard for nonexistent resource."""
        # nonexistent.* should expand to empty (no matching permissions)
        result = expand_wildcards(["nonexistent.*"])
        assert result == []

    def test_expand_empty_list(self):
        """Test expanding empty permission list."""
        result = expand_wildcards([])
        assert result == []

    def test_expand_wildcard_edge_case_dot_only(self):
        """Test edge case: wildcard is just '.*'."""
        # ".*" should not match anything (no empty resource prefix)
        result = expand_wildcards([".*"])
        assert result == []

    def test_expand_wildcard_partial_match(self):
        """Test that partial wildcard patterns don't match."""
        # "work*" should not expand (must end with .*)
        result = expand_wildcards(["work*"])
        assert result == ["work*"]  # Returned as-is (invalid pattern)


class TestValidateRolePermissionsWithWildcards:
    """Test validate_role_permissions() with wildcard support."""

    def test_validate_wildcard_permissions_all_valid(self):
        """Test validation with valid wildcard permissions."""
        permissions = ["workspace.*", "flow.read"]
        invalid = validate_role_permissions("test_role", permissions)

        # All wildcards expand to valid permissions
        assert len(invalid) == 0

    def test_validate_wildcard_permissions_some_invalid(self):
        """Test validation with mix of valid wildcards and invalid explicit."""
        permissions = ["workspace.*", "invalid.permission"]
        invalid = validate_role_permissions("test_role", permissions)

        # Only invalid.permission should be invalid
        assert len(invalid) == 1
        assert "invalid.permission" in invalid

    def test_validate_explicit_permissions_still_works(self):
        """Test that explicit permission validation still works."""
        permissions = ["flow.read", "flow.execute"]
        invalid = validate_role_permissions("test_role", permissions)

        assert len(invalid) == 0

    def test_validate_wildcard_nonexistent_resource(self):
        """Test validation with wildcard for nonexistent resource."""
        permissions = ["nonexistent.*"]
        invalid = validate_role_permissions("test_role", permissions)

        # nonexistent.* expands to nothing, so nothing to validate (no errors)
        assert len(invalid) == 0


class TestWildcardImplementationPlanCompliance:
    """Test that wildcard expansion matches implementation plan specification."""

    def test_workspace_owner_wildcard_pattern(self):
        """Test workspace_owner pattern from implementation plan (lines 906-920)."""
        # Implementation plan specifies wildcards for workspace_owner
        plan_pattern = [
            "workspace.*",
            "group.*",
            "project.*",
            "environment.*",
            "flow.*",
            "component.*",
            "api_token.*",
            "role.*",
            "grant.*",
            "user.*",
            "audit.*",
            "settings.*",
        ]

        result = expand_wildcards(plan_pattern)

        # Should expand to all 47 permissions
        all_perms = get_all_permission_names()
        assert set(result) == set(all_perms)

    def test_workspace_admin_mixed_pattern(self):
        """Test workspace_admin pattern from implementation plan (lines 927-944)."""
        # Implementation plan uses mix of wildcards and explicit
        plan_pattern = [
            "workspace.read",
            "workspace.update",
            "workspace.invite_users",
            "workspace.manage_members",
            "group.*",
            "project.read",
            "project.create",
            "environment.read",
            "flow.read",
            "user.*",
            "role.*",
            "grant.*",
            "audit.view",
            "audit.export",
            "settings.read",
            "settings.update",
        ]

        result = expand_wildcards(plan_pattern)

        # Check explicit permissions preserved
        assert "workspace.read" in result
        assert "project.read" in result

        # Check wildcards expanded
        assert "group.create" in result
        assert "group.manage_members" in result
        assert "user.read" in result
        assert "user.invite" in result
        assert "role.create" in result

    def test_project_admin_wildcard_pattern(self):
        """Test project_admin pattern from implementation plan (lines 951-959)."""
        plan_pattern = [
            "project.read",
            "project.update",
            "project.delete",
            "environment.*",
            "flow.*",
            "component.*",
            "api_token.*",
        ]

        result = expand_wildcards(plan_pattern)

        # Check explicit permissions
        assert "project.read" in result
        assert "project.update" in result
        assert "project.delete" in result

        # Check wildcards expanded
        assert "environment.create" in result
        assert "environment.deploy" in result
        assert "flow.create" in result
        assert "flow.execute" in result
        assert "component.read" in result
        assert "api_token.create" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

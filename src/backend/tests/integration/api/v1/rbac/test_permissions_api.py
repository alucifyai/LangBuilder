"""Integration tests for Permissions API.

Tests PRD Story 3.3 - Permission Management API
End-to-end testing of permission listing via HTTP API.

Scenarios covered:
- List all permissions
- Filter permissions by resource type
- Authorization checks
- Permission metadata validation
"""

import pytest
from httpx import AsyncClient


class TestPermissionsAPIIntegration:
    """Integration tests for Permissions API endpoints."""

    @pytest.mark.asyncio
    async def test_list_permissions_via_api(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test listing all permissions via API.

        Scenario: Admin requests list of all permissions
        Expected: Returns list of system permissions
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()
        assert isinstance(permissions, list)
        assert len(permissions) >= len(test_permissions)

        # Verify test permissions are included
        permission_ids = {p["id"] for p in permissions}
        for test_perm in test_permissions:
            assert str(test_perm.id) in permission_ids

    @pytest.mark.asyncio
    async def test_list_permissions_filter_by_resource_type(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test filtering permissions by resource type.

        Scenario: Admin requests only flow permissions
        Expected: Returns only permissions for flow resource
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/?resource_type=flow",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()
        assert isinstance(permissions, list)

        # All returned permissions should be for flow resource
        for perm in permissions:
            assert perm["resource_type"] == "flow"

    @pytest.mark.asyncio
    async def test_list_permissions_with_pagination(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test listing permissions with pagination parameters.

        Scenario: Admin requests permissions with skip and limit
        Expected: Pagination works correctly
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/?skip=0&limit=5",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()
        assert isinstance(permissions, list)
        assert len(permissions) <= 5

    @pytest.mark.asyncio
    async def test_list_permissions_requires_authentication(
        self,
        client: AsyncClient,
    ):
        """Test that listing permissions requires authentication.

        Scenario: Unauthenticated request to list permissions
        Expected: 403 Forbidden (authentication is still required)
        """
        # Act
        response = await client.get("api/v1/rbac/permissions/")

        # Assert
        # Note: FastAPI dependency injection returns 403 for missing auth
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_permissions_allowed_for_all_users(
        self,
        client: AsyncClient,
        logged_in_headers,  # Regular user
    ):
        """Test that listing permissions is available to all authenticated users.

        Scenario: Regular user lists permissions (PRD Story 1.1 @AC1)
        Expected: 200 OK - Permission catalog is accessible to all users
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/",
            headers=logged_in_headers,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()
        assert isinstance(permissions, list)

    @pytest.mark.asyncio
    async def test_permission_structure_validation(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test that permission objects have correct structure.

        Scenario: Admin lists permissions
        Expected: Each permission has required fields
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()
        assert len(permissions) > 0

        # Verify structure of first permission
        first_perm = permissions[0]
        assert "id" in first_perm
        assert "resource_type" in first_perm
        assert "action" in first_perm
        assert "display_name" in first_perm
        assert "description" in first_perm
        assert "scope_level" in first_perm

    @pytest.mark.asyncio
    async def test_list_permissions_empty_filter(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test listing permissions with non-matching filter.

        Scenario: Admin filters by non-existent resource type
        Expected: Returns empty list
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/?resource_type=nonexistent",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()
        assert isinstance(permissions, list)
        assert len(permissions) == 0

    @pytest.mark.asyncio
    async def test_permissions_include_all_crud_actions(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test that CRUD actions are available for resources.

        Scenario: Admin lists flow permissions
        Expected: Includes read, update, delete, export actions
        """
        # Act
        response = await client.get(
            "api/v1/rbac/permissions/?resource_type=flow",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        permissions = response.json()

        # Collect all actions for flow resource
        flow_actions = {p["action"] for p in permissions}

        # Verify standard CRUD actions exist
        expected_actions = {"read", "update", "delete", "export"}
        for action in expected_actions:
            assert action in flow_actions, f"Action '{action}' should exist for flow resource"

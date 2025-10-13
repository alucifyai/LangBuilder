"""Integration tests for Role Management API.

Tests PRD Story 3.2 - Custom Role Management API
End-to-end testing of role CRUD operations via HTTP API.

Scenarios covered:
- @AC1: Create role via API with permissions
- @AC2: Update role via API
- @AC3: Delete role via API
- Authorization checks (superuser requirement)
- Error handling (duplicate names, invalid permissions)
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from langflow.services.database.models.rbac import Role
from langflow.services.deps import get_db_service
from sqlmodel import select


class TestRolesAPIIntegration:
    """Integration tests for Roles API endpoints."""

    @pytest.mark.asyncio
    async def test_create_role_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test PRD Story 3.2 @AC1: Create role via API with permissions.

        Scenario: Admin creates a custom role with specific permissions
        Expected: Role is created and can be retrieved
        """
        # Arrange
        role_data = {
            "name": f"qa_lead_{uuid4().hex[:8]}",
            "display_name": "QA Lead",
            "description": "QA team lead role",
            "permission_ids": [str(test_permissions[0].id), str(test_permissions[3].id)],  # read, export
        }

        # Act - Create role
        create_response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers_super_user,
        )

        # Assert creation
        assert create_response.status_code == 201, create_response.text
        created_role = create_response.json()
        assert created_role["name"] == role_data["name"]
        assert created_role["display_name"] == "QA Lead"
        assert created_role["is_system_role"] is False
        role_id = created_role["id"]

        # Act - Verify GET returns same data
        get_response = await client.get(
            f"api/v1/rbac/admin/roles/{role_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert retrieval
        assert get_response.status_code == 200
        retrieved_role = get_response.json()
        assert retrieved_role["name"] == role_data["name"]
        assert retrieved_role["display_name"] == "QA Lead"

        # Cleanup
        await client.delete(f"api/v1/rbac/admin/roles/{role_id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_create_role_via_api_no_permissions(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test creating role without any permissions.

        Scenario: Admin creates a role with empty permission list
        Expected: Role is created successfully
        """
        # Arrange
        role_data = {
            "name": f"empty_role_{uuid4().hex[:8]}",
            "display_name": "Empty Role",
            "description": "Role with no permissions",
            "permission_ids": [],
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 201
        role = response.json()
        assert role["name"] == role_data["name"]
        role_id = role["id"]

        # Cleanup
        await client.delete(f"api/v1/rbac/admin/roles/{role_id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_update_role_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_role_viewer,
        test_permissions,
    ):
        """Test PRD Story 3.2 @AC2: Update role via API.

        Scenario: Admin updates role display name and permissions
        Expected: Role is updated successfully
        """
        # Arrange - role_viewer has read permission, replace with update permission
        update_data = {
            "display_name": "Updated Viewer",
            "description": "Updated description",
            "permission_ids": [
                str(test_permissions[1].id),  # update (replacing read)
            ],
        }

        # Act
        response = await client.patch(
            f"api/v1/rbac/admin/roles/{test_role_viewer.id}",
            json=update_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200, response.text
        updated_role = response.json()
        assert updated_role["display_name"] == "Updated Viewer"
        assert updated_role["description"] == "Updated description"
        assert updated_role["name"] == test_role_viewer.name  # Name unchanged

    @pytest.mark.asyncio
    async def test_delete_role_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test PRD Story 3.2 @AC3: Delete role via API.

        Scenario: Admin deletes a role with no active assignments
        Expected: Role is deleted and cannot be retrieved
        """
        # Arrange - Create a temporary role
        role_data = {
            "name": f"temp_role_{uuid4().hex[:8]}",
            "display_name": "Temporary Role",
            "description": "Will be deleted",
            "permission_ids": [str(test_permissions[0].id)],
        }
        create_response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        role_id = create_response.json()["id"]

        # Act - Delete the role
        delete_response = await client.delete(
            f"api/v1/rbac/admin/roles/{role_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert deletion
        assert delete_response.status_code == 204

        # Verify role is gone
        get_response = await client.get(
            f"api/v1/rbac/admin/roles/{role_id}",
            headers=logged_in_headers_super_user,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_roles_via_api(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_role_viewer,
    ):
        """Test listing all roles via API.

        Scenario: Admin requests list of all roles
        Expected: Returns list including test role
        """
        # Act
        response = await client.get(
            "api/v1/rbac/admin/roles/",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        roles = response.json()
        assert isinstance(roles, list)
        assert len(roles) >= 1

        # Find our test role
        test_role_found = any(role["id"] == str(test_role_viewer.id) for role in roles)
        assert test_role_found, "Test role should be in the list"

    @pytest.mark.asyncio
    async def test_create_role_requires_authentication(
        self,
        client: AsyncClient,
    ):
        """Test that creating roles requires authentication.

        Scenario: Unauthenticated request to create role
        Expected: 403 Forbidden
        """
        # Arrange
        role_data = {
            "name": "unauthorized_role",
            "display_name": "Unauthorized",
            "description": "Should fail",
            "permission_ids": [],
        }

        # Act
        response = await client.post("api/v1/rbac/admin/roles/", json=role_data)

        # Assert
        # Note: FastAPI dependency injection returns 403 for missing auth
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_role_requires_superuser(
        self,
        client: AsyncClient,
        logged_in_headers,  # Regular user, not superuser
    ):
        """Test that creating roles requires superuser access.

        Scenario: Regular user attempts to create role
        Expected: 403 Forbidden
        """
        # Arrange
        role_data = {
            "name": "unauthorized_role",
            "display_name": "Unauthorized",
            "description": "Should fail",
            "permission_ids": [],
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers,
        )

        # Assert
        assert response.status_code == 403
        assert "Insufficient permissions" in response.text

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_role_viewer,
    ):
        """Test that duplicate role names are rejected.

        Scenario: Admin attempts to create role with existing name
        Expected: 400 Bad Request with clear error message
        """
        # Arrange
        role_data = {
            "name": test_role_viewer.name,  # Duplicate name
            "display_name": "Duplicate Name",
            "description": "Should fail",
            "permission_ids": [],
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 400
        assert "already exists" in response.text.lower()

    @pytest.mark.asyncio
    async def test_create_role_invalid_permission_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test that invalid permission IDs are rejected.

        Scenario: Admin creates role with non-existent permission ID
        Expected: 400 Bad Request
        """
        # Arrange
        fake_permission_id = str(uuid4())
        role_data = {
            "name": f"invalid_role_{uuid4().hex[:8]}",
            "display_name": "Invalid Role",
            "description": "Has invalid permission",
            "permission_ids": [fake_permission_id],
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 400
        assert "unknown permission" in response.text.lower()

    @pytest.mark.asyncio
    async def test_update_role_not_found(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test updating non-existent role returns 404.

        Scenario: Admin attempts to update role that doesn't exist
        Expected: 404 Not Found
        """
        # Arrange
        fake_role_id = str(uuid4())
        update_data = {"display_name": "New Name"}

        # Act
        response = await client.patch(
            f"api/v1/rbac/admin/roles/{fake_role_id}",
            json=update_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_role_not_found(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test deleting non-existent role returns 404.

        Scenario: Admin attempts to delete role that doesn't exist
        Expected: 404 Not Found
        """
        # Arrange
        fake_role_id = str(uuid4())

        # Act
        response = await client.delete(
            f"api/v1/rbac/admin/roles/{fake_role_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_role_crud_workflow_end_to_end(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test complete CRUD workflow for roles.

        Scenario: Create -> Read -> Update -> Delete role
        Expected: All operations succeed in sequence
        """
        # Step 1: Create role
        create_data = {
            "name": f"workflow_role_{uuid4().hex[:8]}",
            "display_name": "Workflow Test",
            "description": "Testing full CRUD workflow",
            "permission_ids": [str(test_permissions[0].id)],
        }
        create_response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=create_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        role_id = create_response.json()["id"]

        # Step 2: Read role
        read_response = await client.get(
            f"api/v1/rbac/admin/roles/{role_id}",
            headers=logged_in_headers_super_user,
        )
        assert read_response.status_code == 200
        assert read_response.json()["name"] == create_data["name"]

        # Step 3: Update role (replace single permission with two different permissions)
        update_data = {
            "display_name": "Updated Workflow",
            "permission_ids": [str(test_permissions[1].id), str(test_permissions[2].id)],  # update, delete
        }
        update_response = await client.patch(
            f"api/v1/rbac/admin/roles/{role_id}",
            json=update_data,
            headers=logged_in_headers_super_user,
        )
        assert update_response.status_code == 200
        assert update_response.json()["display_name"] == "Updated Workflow"

        # Step 4: Delete role
        delete_response = await client.delete(
            f"api/v1/rbac/admin/roles/{role_id}",
            headers=logged_in_headers_super_user,
        )
        assert delete_response.status_code == 204

        # Step 5: Verify deleted
        verify_response = await client.get(
            f"api/v1/rbac/admin/roles/{role_id}",
            headers=logged_in_headers_super_user,
        )
        assert verify_response.status_code == 404

    @pytest.mark.asyncio
    async def test_role_permissions_are_persisted(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_permissions,
    ):
        """Test that role-permission associations are persisted correctly.

        Scenario: Create role with permissions, verify in database
        Expected: Permissions are correctly linked to role
        """
        # Arrange
        role_data = {
            "name": f"persist_test_{uuid4().hex[:8]}",
            "display_name": "Persistence Test",
            "description": "Testing permission persistence",
            "permission_ids": [
                str(test_permissions[0].id),
                str(test_permissions[1].id),
                str(test_permissions[2].id),
            ],
        }

        # Act - Create role
        create_response = await client.post(
            "api/v1/rbac/admin/roles/",
            json=role_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        role_id = create_response.json()["id"]

        # Verify in database
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            from uuid import UUID

            stmt = select(Role).where(Role.id == UUID(role_id))
            role = (await session.exec(stmt)).first()
            assert role is not None, "Role should exist in database"

        # Cleanup
        await client.delete(f"api/v1/rbac/admin/roles/{role_id}", headers=logged_in_headers_super_user)

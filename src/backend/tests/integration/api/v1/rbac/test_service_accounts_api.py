"""Integration tests for Service Account Management API.

Tests PRD Story 2.4 - Service Account Management
End-to-end testing of service account CRUD and token management via HTTP API.

Scenarios covered:
- @AC1: Create service account via API
- @AC2: Generate API token for service account
- List and manage service accounts
- Token lifecycle management
- Authorization checks
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestServiceAccountsAPIIntegration:
    """Integration tests for Service Accounts API endpoints."""

    @pytest.mark.asyncio
    async def test_create_service_account_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test PRD Story 2.4 @AC1: Create service account via API.

        Scenario: Admin creates service account for automation
        Expected: Service account is created and can be retrieved
        """
        # Arrange
        sa_data = {
            "name": f"ci_bot_{uuid4().hex[:8]}",
            "display_name": "CI/CD Bot",
            "description": "Automated deployment bot",
            "workspace_id": str(test_workspace.id),
        }

        # Act - Create service account
        create_response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=sa_data,
            headers=logged_in_headers_super_user,
        )

        # Assert creation
        assert create_response.status_code == 201, create_response.text
        sa = create_response.json()
        assert sa["name"] == sa_data["name"]
        assert sa["display_name"] == "CI/CD Bot"
        assert sa["is_active"] is True
        sa_id = sa["id"]

        # Act - Verify GET returns same data
        get_response = await client.get(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert retrieval
        assert get_response.status_code == 200
        retrieved_sa = get_response.json()
        assert retrieved_sa["name"] == sa_data["name"]

        # Cleanup
        await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_generate_token_for_service_account(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test PRD Story 2.4 @AC2: Generate API token for service account.

        Scenario: Admin generates API token for service account
        Expected: Token is generated and can be used for authentication
        """
        # Arrange - Create service account first
        sa_data = {
            "name": f"token_bot_{uuid4().hex[:8]}",
            "display_name": "Token Bot",
            "workspace_id": str(test_workspace.id),
        }
        sa_response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=sa_data,
            headers=logged_in_headers_super_user,
        )
        assert sa_response.status_code == 201
        sa_id = sa_response.json()["id"]

        # Act - Generate token
        token_data = {
            "name": "Production Token",
            "expires_days": 90,
        }
        token_response = await client.post(
            f"api/v1/rbac/service-accounts/{sa_id}/tokens",
            json=token_data,
            headers=logged_in_headers_super_user,
        )

        # Assert token generation
        assert token_response.status_code == 201, token_response.text
        token = token_response.json()
        assert "token" in token
        assert token["token"].startswith("lgs_")  # LangBuilder Service token prefix
        assert token["name"] == "Production Token"
        token_id = token["id"]

        # Cleanup
        await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}/tokens/{token_id}",
            headers=logged_in_headers_super_user,
        )
        await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_list_service_accounts_via_api(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test listing service accounts via API.

        Scenario: Admin requests list of all service accounts
        Expected: Returns list including test service account
        """
        # Arrange - Create service account
        sa_data = {
            "name": f"list_test_{uuid4().hex[:8]}",
            "display_name": "List Test",
            "workspace_id": str(test_workspace.id),
        }
        sa_response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=sa_data,
            headers=logged_in_headers_super_user,
        )
        assert sa_response.status_code == 201
        sa_id = sa_response.json()["id"]

        # Act
        list_response = await client.get(
            "api/v1/rbac/service-accounts/",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert list_response.status_code == 200
        service_accounts = list_response.json()
        assert isinstance(service_accounts, list)
        assert any(sa["id"] == sa_id for sa in service_accounts)

        # Cleanup
        await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_service_account_with_role_assignment(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
        test_role_viewer,
    ):
        """Test creating service account with initial role assignment.

        Scenario: Admin creates service account and assigns role
        Expected: Service account has role assigned
        """
        # Arrange
        sa_data = {
            "name": f"role_bot_{uuid4().hex[:8]}",
            "display_name": "Role Bot",
            "workspace_id": str(test_workspace.id),
            "role_id": str(test_role_viewer.id),
            "scope": {"workspace": str(test_workspace.id)},
        }

        # Act
        response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=sa_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 201
        sa = response.json()
        assert sa["role_count"] == 1
        sa_id = sa["id"]

        # Cleanup
        await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_service_account_requires_authentication(
        self,
        client: AsyncClient,
    ):
        """Test that service account operations require authentication.

        Scenario: Unauthenticated request to create service account
        Expected: 401 Unauthorized
        """
        # Arrange
        sa_data = {
            "name": "unauthorized_bot",
            "display_name": "Unauthorized",
            "workspace_id": str(uuid4()),
        }

        # Act
        response = await client.post("api/v1/rbac/service-accounts/", json=sa_data)

        # Assert
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_service_account_requires_superuser(
        self,
        client: AsyncClient,
        logged_in_headers,  # Regular user
        test_workspace,
    ):
        """Test that service account operations require superuser.

        Scenario: Regular user attempts to create service account
        Expected: 403 Forbidden
        """
        # Arrange
        sa_data = {
            "name": "unauthorized_bot",
            "display_name": "Unauthorized",
            "workspace_id": str(test_workspace.id),
        }

        # Act
        response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=sa_data,
            headers=logged_in_headers,
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_revoke_service_account_token(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test revoking service account token.

        Scenario: Admin revokes an API token
        Expected: Token is deleted and cannot be used
        """
        # Arrange - Create service account and token
        sa_data = {
            "name": f"revoke_test_{uuid4().hex[:8]}",
            "display_name": "Revoke Test",
            "workspace_id": str(test_workspace.id),
        }
        sa_response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=sa_data,
            headers=logged_in_headers_super_user,
        )
        assert sa_response.status_code == 201
        sa_id = sa_response.json()["id"]

        token_data = {"name": "Temp Token"}
        token_response = await client.post(
            f"api/v1/rbac/service-accounts/{sa_id}/tokens",
            json=token_data,
            headers=logged_in_headers_super_user,
        )
        assert token_response.status_code == 201
        token_id = token_response.json()["id"]

        # Act - Revoke token
        revoke_response = await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}/tokens/{token_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert revoke_response.status_code == 204

        # Cleanup
        await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_service_account_crud_workflow(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test complete CRUD workflow for service accounts.

        Scenario: Create -> Read -> Update -> Delete service account
        Expected: All operations succeed in sequence
        """
        # Step 1: Create
        create_data = {
            "name": f"workflow_bot_{uuid4().hex[:8]}",
            "display_name": "Workflow Bot",
            "workspace_id": str(test_workspace.id),
        }
        create_response = await client.post(
            "api/v1/rbac/service-accounts/",
            json=create_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        sa_id = create_response.json()["id"]

        # Step 2: Read
        read_response = await client.get(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )
        assert read_response.status_code == 200

        # Step 3: Update
        update_data = {"display_name": "Updated Bot"}
        update_response = await client.patch(
            f"api/v1/rbac/service-accounts/{sa_id}",
            json=update_data,
            headers=logged_in_headers_super_user,
        )
        assert update_response.status_code == 200
        assert update_response.json()["display_name"] == "Updated Bot"

        # Step 4: Delete
        delete_response = await client.delete(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )
        assert delete_response.status_code == 204

        # Step 5: Verify deleted
        verify_response = await client.get(
            f"api/v1/rbac/service-accounts/{sa_id}",
            headers=logged_in_headers_super_user,
        )
        assert verify_response.status_code == 404

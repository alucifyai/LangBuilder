"""Integration tests for Grant Management API.

Tests PRD Story 3.5 - Role Assignment Management API
End-to-end testing of grant CRUD operations via HTTP API.

Scenarios covered:
- @AC1: Create grant (assign role) via API
- @AC2: Revoke grant (remove role) via API
- List grants for users and roles
- Authorization checks
- Error handling (invalid assignments)
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from langflow.services.database.models.rbac import RoleAssignment
from langflow.services.deps import get_db_service
from sqlmodel import select

from .conftest import create_role_assignment


class TestGrantsAPIIntegration:
    """Integration tests for Grants API endpoints."""

    @pytest.mark.asyncio
    async def test_create_grant_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_editor,
        test_project,
    ):
        """Test PRD Story 3.5 @AC1: Assign role via API.

        Scenario: Admin assigns editor role to user for specific project
        Expected: Grant is created and can be retrieved
        """
        # Arrange
        grant_data = {
            "principal": f"user:{active_user.username}",
            "role_id": str(test_role_editor.id),
            "scope": {"project": str(test_project.id)},
        }

        # Act - Create grant
        create_response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers_super_user,
        )

        # Assert creation
        assert create_response.status_code == 201, create_response.text
        created_grant = create_response.json()
        assert created_grant["user_id"] == str(active_user.id)
        assert created_grant["role_id"] == str(test_role_editor.id)
        grant_id = created_grant["id"]

        # Act - Verify GET returns same data
        get_response = await client.get(
            f"api/v1/rbac/grants/{grant_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert retrieval
        assert get_response.status_code == 200
        retrieved_grant = get_response.json()
        assert retrieved_grant["user_id"] == str(active_user.id)
        assert retrieved_grant["role_id"] == str(test_role_editor.id)

        # Cleanup
        await client.delete(f"api/v1/rbac/grants/{grant_id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_revoke_grant_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_viewer,
        test_flow,
    ):
        """Test PRD Story 3.5 @AC2: Revoke grant via API.

        Scenario: Admin revokes a role assignment
        Expected: Grant is deleted and cannot be retrieved
        """
        # Arrange - Create grant first
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            grant = await create_role_assignment(
                session,
                user_id=active_user.id,
                role_id=test_role_viewer.id,
                scope_type="flow",
                scope_id=test_flow.id,
            )
            grant_id = grant.id

        # Act - Revoke grant
        delete_response = await client.delete(
            f"api/v1/rbac/grants/{grant_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert deletion
        assert delete_response.status_code == 204

        # Verify grant is gone
        get_response = await client.get(
            f"api/v1/rbac/grants/{grant_id}",
            headers=logged_in_headers_super_user,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_grants_for_user(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_viewer,
        test_flow,
    ):
        """Test listing grants for a specific user.

        Scenario: Admin requests all grants for a user
        Expected: Returns list of user's role assignments
        """
        # Arrange - Create grant for user
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            grant = await create_role_assignment(
                session,
                user_id=active_user.id,
                role_id=test_role_viewer.id,
                scope_type="flow",
                scope_id=test_flow.id,
            )

        # Act
        response = await client.get(
            f"api/v1/rbac/grants/?user_id={active_user.id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        grants = response.json()
        assert isinstance(grants, list)
        assert len(grants) >= 1
        assert any(g["id"] == str(grant.id) for g in grants)

        # Cleanup
        await client.delete(f"api/v1/rbac/grants/{grant.id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_list_grants_for_role(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_editor,
        test_project,
    ):
        """Test listing grants for a specific role.

        Scenario: Admin requests all assignments of a role
        Expected: Returns list of role's assignments
        """
        # Arrange - Create grant
        grant_data = {
            "principal": f"user:{active_user.username}",
            "role_id": str(test_role_editor.id),
            "scope": {"project": str(test_project.id)},
        }
        create_response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        grant_id = create_response.json()["id"]

        # Act
        response = await client.get(
            f"api/v1/rbac/grants/?role_id={test_role_editor.id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 200
        grants = response.json()
        assert isinstance(grants, list)
        assert len(grants) >= 1
        assert any(g["id"] == grant_id for g in grants)

        # Cleanup
        await client.delete(f"api/v1/rbac/grants/{grant_id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_create_grant_with_expiration(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_viewer,
        test_flow,
    ):
        """Test creating grant with expiration time.

        Scenario: Admin assigns temporary role (expires in 7 days)
        Expected: Grant is created with expiration date
        """
        # Arrange
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        grant_data = {
            "principal": f"user:{active_user.username}",
            "role_id": str(test_role_viewer.id),
            "scope": {"flow": str(test_flow.id)},
            "valid_until": expires_at,
        }

        # Act
        response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 201
        grant = response.json()
        assert grant["expires_at"] is not None  # API returns expires_at field
        grant_id = grant["id"]

        # Cleanup
        await client.delete(f"api/v1/rbac/grants/{grant_id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_create_grant_for_service_account(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_super_user,
        test_role_editor,
        test_project,
        test_workspace,
    ):
        """Test creating grant for service account principal.

        Scenario: Admin assigns role to service account
        Expected: Grant is created with service_account_id
        Tests: PRD Story 2.4 - Service Account Integration
        """
        # Arrange - Create service account directly in DB
        from langflow.services.database.models.rbac import ServiceAccount
        from langflow.services.deps import get_db_service

        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            service_account = ServiceAccount(
                name="test_service_account",
                display_name="Test Service Account",
                description="Service account for grant testing",
                workspace_id=test_workspace.id,
                created_by_user_id=active_super_user.id,
                is_active=True,
            )
            session.add(service_account)
            await session.commit()
            await session.refresh(service_account)
            sa_id = service_account.id

        try:
            # Arrange - Create grant for service account
            grant_data = {
                "principal": f"service_account:{sa_id}",
                "role_id": str(test_role_editor.id),
                "scope": {"project": str(test_project.id)},
            }

            # Act - Create grant
            create_response = await client.post(
                "api/v1/rbac/grants/",
                json=grant_data,
                headers=logged_in_headers_super_user,
            )

            # Assert creation
            assert create_response.status_code == 201, create_response.text
            created_grant = create_response.json()
            assert created_grant["service_account_id"] == str(sa_id)
            assert created_grant["role_id"] == str(test_role_editor.id)
            assert created_grant["assignee_type"] == "service_account"
            grant_id = created_grant["id"]

            # Cleanup grant
            await client.delete(f"api/v1/rbac/grants/{grant_id}", headers=logged_in_headers_super_user)
        finally:
            # Cleanup service account
            async with db_manager.with_session() as session:
                sa = await session.get(ServiceAccount, sa_id)
                if sa:
                    await session.delete(sa)
                    await session.commit()

    @pytest.mark.asyncio
    async def test_create_grant_requires_authentication(
        self,
        client: AsyncClient,
    ):
        """Test that creating grants requires authentication.

        Scenario: Unauthenticated request to create grant
        Expected: 403 Forbidden
        """
        # Arrange
        grant_data = {
            "principal": "user:nonexistent",
            "role_id": str(uuid4()),
            "scope": {"project": str(uuid4())},
        }

        # Act
        response = await client.post("api/v1/rbac/grants/", json=grant_data)

        # Assert
        # Note: FastAPI dependency injection returns 403 for missing auth
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_grant_requires_superuser(
        self,
        client: AsyncClient,
        logged_in_headers,  # Regular user
    ):
        """Test that creating grants requires superuser access.

        Scenario: Regular user attempts to create grant
        Expected: 403 Forbidden
        """
        # Arrange
        grant_data = {
            "principal": "user:nonexistent",
            "role_id": str(uuid4()),
            "scope": {"project": str(uuid4())},
        }

        # Act
        response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers,
        )

        # Assert
        assert response.status_code == 403
        assert "Insufficient permissions" in response.text

    @pytest.mark.asyncio
    async def test_create_grant_invalid_user_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_role_viewer,
        test_project,
    ):
        """Test that invalid user ID is rejected.

        Scenario: Admin attempts to assign role to non-existent user
        Expected: 404 Not Found
        """
        # Arrange
        grant_data = {
            "principal": "user:nonexistentuser123",
            "role_id": str(test_role_viewer.id),
            "scope": {"project": str(test_project.id)},
        }

        # Act
        response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 404
        assert "user" in response.text.lower()

    @pytest.mark.asyncio
    async def test_create_grant_invalid_role_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_project,
    ):
        """Test that invalid role ID is rejected.

        Scenario: Admin attempts to assign non-existent role
        Expected: 404 Not Found
        """
        # Arrange
        fake_role_id = str(uuid4())
        grant_data = {
            "principal": f"user:{active_user.username}",
            "role_id": fake_role_id,
            "scope": {"project": str(test_project.id)},
        }

        # Act
        response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 404
        assert "role" in response.text.lower()

    @pytest.mark.asyncio
    async def test_delete_grant_not_found(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test deleting non-existent grant returns 404.

        Scenario: Admin attempts to delete grant that doesn't exist
        Expected: 404 Not Found
        """
        # Arrange
        fake_grant_id = str(uuid4())

        # Act
        response = await client.delete(
            f"api/v1/rbac/grants/{fake_grant_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_grant_crud_workflow_end_to_end(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_viewer,
        test_flow,
    ):
        """Test complete CRUD workflow for grants.

        Scenario: Create -> Read -> Delete grant
        Expected: All operations succeed in sequence
        """
        # Step 1: Create grant
        create_data = {
            "principal": f"user:{active_user.username}",
            "role_id": str(test_role_viewer.id),
            "scope": {"flow": str(test_flow.id)},
        }
        create_response = await client.post(
            "api/v1/rbac/grants/",
            json=create_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        grant_id = create_response.json()["id"]

        # Step 2: Read grant
        read_response = await client.get(
            f"api/v1/rbac/grants/{grant_id}",
            headers=logged_in_headers_super_user,
        )
        assert read_response.status_code == 200
        assert read_response.json()["user_id"] == str(active_user.id)

        # Step 3: Delete grant
        delete_response = await client.delete(
            f"api/v1/rbac/grants/{grant_id}",
            headers=logged_in_headers_super_user,
        )
        assert delete_response.status_code == 204

        # Step 4: Verify deleted
        verify_response = await client.get(
            f"api/v1/rbac/grants/{grant_id}",
            headers=logged_in_headers_super_user,
        )
        assert verify_response.status_code == 404

    @pytest.mark.asyncio
    async def test_grant_persisted_in_database(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_editor,
        test_project,
    ):
        """Test that grants are persisted correctly in database.

        Scenario: Create grant via API, verify in database
        Expected: Grant exists in database with correct attributes
        """
        # Arrange
        grant_data = {
            "principal": f"user:{active_user.username}",
            "role_id": str(test_role_editor.id),
            "scope": {"project": str(test_project.id)},
        }

        # Act - Create grant
        create_response = await client.post(
            "api/v1/rbac/grants/",
            json=grant_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        grant_id = create_response.json()["id"]

        # Verify in database
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            from uuid import UUID

            stmt = select(RoleAssignment).where(RoleAssignment.id == UUID(grant_id))
            grant = (await session.exec(stmt)).first()
            assert grant is not None, "Grant should exist in database"
            assert grant.user_id == active_user.id
            assert grant.role_id == test_role_editor.id

        # Cleanup
        await client.delete(f"api/v1/rbac/grants/{grant_id}", headers=logged_in_headers_super_user)

    @pytest.mark.asyncio
    async def test_list_grants_with_pagination(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        active_user,
        test_role_viewer,
        test_role_editor,
        test_flow,
    ):
        """Test listing grants with pagination parameters.

        Scenario: Admin requests grants with skip and limit
        Expected: Pagination works correctly
        """
        # Arrange - Create multiple grants
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            grant1 = await create_role_assignment(
                session,
                user_id=active_user.id,
                role_id=test_role_viewer.id,
                scope_type="flow",
                scope_id=test_flow.id,
            )
            grant2 = await create_role_assignment(
                session,
                user_id=active_user.id,
                role_id=test_role_editor.id,
                scope_type="flow",
                scope_id=test_flow.id,
            )

        try:
            # Act - Request with pagination
            response = await client.get(
                f"api/v1/rbac/grants/?user_id={active_user.id}&skip=0&limit=1",
                headers=logged_in_headers_super_user,
            )

            # Assert
            assert response.status_code == 200
            grants = response.json()
            assert isinstance(grants, list)
            assert len(grants) == 1  # Should only return 1 due to limit
        finally:
            # Cleanup
            await client.delete(f"api/v1/rbac/grants/{grant1.id}", headers=logged_in_headers_super_user)
            await client.delete(f"api/v1/rbac/grants/{grant2.id}", headers=logged_in_headers_super_user)

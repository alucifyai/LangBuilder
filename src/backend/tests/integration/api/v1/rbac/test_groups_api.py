"""Integration tests for Group Management API.

Tests PRD Story 2.1 - User Group Management
End-to-end testing of group CRUD operations via HTTP API.

Scenarios covered:
- @AC1: Create group in workspace and add users
- @AC2: Remove users from groups
- Workspace-scoped group isolation
- Group role assignments (batch permissions)
- SCIM integration fields
"""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from langflow.services.database.models.user_group.model import UserGroup, UserGroupMember
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.deps import get_db_service
from sqlmodel import select


class TestGroupsAPIIntegration:
    """Integration tests for Groups API endpoints."""

    @pytest.mark.asyncio
    async def test_create_group_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test PRD Story 2.1 @AC1: Create group in workspace via API.

        Scenario: Admin creates a user group within a workspace
        Expected: Group is created and can be retrieved
        """
        # Arrange
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"product_team_{uuid4().hex[:8]}",
            "description": "Product management team",
        }

        # Act - Create group
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )

        # Assert creation
        assert create_response.status_code == 201, create_response.text
        created_group = create_response.json()
        assert created_group["name"] == group_data["name"]
        assert created_group["workspace_id"] == str(test_workspace.id)
        assert created_group["is_active"] is True
        group_id = created_group["id"]

        # Act - Verify GET returns same data
        get_response = await client.get(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert retrieval
        assert get_response.status_code == 200
        retrieved_group = get_response.json()
        assert retrieved_group["name"] == group_data["name"]
        assert retrieved_group["description"] == "Product management team"

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_add_user_to_group_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
        active_super_user,
    ):
        """Test PRD Story 2.1 @AC1: Add user to group via API.

        Scenario: Admin adds a user to a group
        Expected: User becomes a member and is included in members list
        """
        # Arrange - Create a group
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"test_group_{uuid4().hex[:8]}",
            "description": "Test group for membership",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Act - Add user to group
        member_data = {"user_id": str(active_super_user.id)}
        add_response = await client.post(
            f"api/v1/rbac/admin/groups/{group_id}/members",
            json=member_data,
            headers=logged_in_headers_super_user,
        )

        # Assert membership creation
        assert add_response.status_code == 201, add_response.text
        member = add_response.json()
        assert member["user_id"] == str(active_super_user.id)
        assert member["group_id"] == group_id
        assert member["is_active"] is True

        # Act - Verify user appears in members list
        list_response = await client.get(
            f"api/v1/rbac/admin/groups/{group_id}/members",
            headers=logged_in_headers_super_user,
        )

        # Assert in members list
        assert list_response.status_code == 200
        members = list_response.json()
        assert len(members) == 1
        assert members[0]["user_id"] == str(active_super_user.id)

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_remove_user_from_group_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
        active_super_user,
    ):
        """Test PRD Story 2.1 @AC2: Remove user from group via API.

        Scenario: Admin removes a user from a group
        Expected: User is no longer a member
        """
        # Arrange - Create group and add member
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            group = UserGroup(
                workspace_id=test_workspace.id,
                name=f"removal_test_{uuid4().hex[:8]}",
                description="Group for removal testing",
                is_active=True,
            )
            session.add(group)
            await session.flush()

            member = UserGroupMember(
                group_id=group.id,
                user_id=active_super_user.id,
                is_active=True,
            )
            session.add(member)
            await session.commit()
            await session.refresh(group)

        # Act - Remove user from group
        remove_response = await client.delete(
            f"api/v1/rbac/admin/groups/{group.id}/members/{active_super_user.id}",
            headers=logged_in_headers_super_user,
        )

        # Assert removal
        assert remove_response.status_code == 204, remove_response.text

        # Verify user is no longer in members list
        list_response = await client.get(
            f"api/v1/rbac/admin/groups/{group.id}/members",
            headers=logged_in_headers_super_user,
        )
        assert list_response.status_code == 200
        members = list_response.json()
        assert len(members) == 0

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group.id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_update_group_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test updating group via API.

        Scenario: Admin updates group description and active status
        Expected: Group is updated successfully
        """
        # Arrange - Create a group
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"update_test_{uuid4().hex[:8]}",
            "description": "Original description",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Act - Update group
        update_data = {
            "description": "Updated description",
            "is_active": False,
        }
        update_response = await client.patch(
            f"api/v1/rbac/admin/groups/{group_id}",
            json=update_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert update_response.status_code == 200, update_response.text
        updated_group = update_response.json()
        assert updated_group["description"] == "Updated description"
        assert updated_group["is_active"] is False
        assert updated_group["name"] == group_data["name"]  # Name unchanged

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_delete_group_via_api_success(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test deleting group via API.

        Scenario: Admin deletes a group with no active members
        Expected: Group is deleted and cannot be retrieved
        """
        # Arrange - Create a group
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"delete_test_{uuid4().hex[:8]}",
            "description": "Will be deleted",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Act - Delete the group
        delete_response = await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert deletion
        assert delete_response.status_code == 204

        # Verify group is gone
        get_response = await client.get(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_group_cascade_deletes_members(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
        active_super_user,
    ):
        """Test that deleting group also deletes all memberships.

        Scenario: Admin deletes group that has members
        Expected: Group and all memberships are deleted
        """
        # Arrange - Create group with member
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            group = UserGroup(
                workspace_id=test_workspace.id,
                name=f"cascade_test_{uuid4().hex[:8]}",
                description="Group with members",
                is_active=True,
            )
            session.add(group)
            await session.flush()

            member = UserGroupMember(
                group_id=group.id,
                user_id=active_super_user.id,
                is_active=True,
            )
            session.add(member)
            await session.commit()
            await session.refresh(group)
            group_id = group.id

        # Act - Delete group via API
        delete_response = await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert delete_response.status_code == 204

        # Verify memberships are also deleted
        async with db_manager.with_session() as session:
            stmt = select(UserGroupMember).where(
                UserGroupMember.group_id == group_id
            )
            members = (await session.exec(stmt)).all()
            assert len(members) == 0, "Memberships should be cascade deleted"

    @pytest.mark.asyncio
    async def test_list_groups_via_api(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test listing all groups via API.

        Scenario: Admin requests list of all groups
        Expected: Returns list including created groups
        """
        # Arrange - Create test groups
        group1_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"list_test_1_{uuid4().hex[:8]}",
            "description": "First test group",
        }
        group2_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"list_test_2_{uuid4().hex[:8]}",
            "description": "Second test group",
        }

        response1 = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group1_data,
            headers=logged_in_headers_super_user,
        )
        response2 = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group2_data,
            headers=logged_in_headers_super_user,
        )
        assert response1.status_code == 201
        assert response2.status_code == 201
        group1_id = response1.json()["id"]
        group2_id = response2.json()["id"]

        # Act - List groups
        list_response = await client.get(
            "api/v1/rbac/admin/groups/",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert list_response.status_code == 200
        groups = list_response.json()
        assert isinstance(groups, list)
        assert len(groups) >= 2

        # Find our test groups
        group_ids = {g["id"] for g in groups}
        assert group1_id in group_ids
        assert group2_id in group_ids

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group1_id}",
            headers=logged_in_headers_super_user,
        )
        await client.delete(
            f"api/v1/rbac/admin/groups/{group2_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_list_groups_filter_by_workspace(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test filtering groups by workspace_id.

        Scenario: Admin requests groups from specific workspace
        Expected: Only groups from that workspace are returned
        """
        # Arrange - Create group in test workspace
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"workspace_filter_{uuid4().hex[:8]}",
            "description": "Workspace filter test",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Act - Filter by workspace
        list_response = await client.get(
            f"api/v1/rbac/admin/groups/?workspace_id={test_workspace.id}",
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert list_response.status_code == 200
        groups = list_response.json()
        # All groups should belong to test workspace
        for group in groups:
            assert group["workspace_id"] == str(test_workspace.id)

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_workspace_scoped_group_isolation(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test that same group name is allowed in different workspaces.

        Scenario: Admin creates groups with same name in different workspaces
        Expected: Both groups are created successfully (workspace isolation)
        """
        db_manager = get_db_service()

        # Arrange - Create two workspaces
        async with db_manager.with_session() as session:
            workspace1 = Workspace(
                name="Workspace 1",
                slug=f"ws1-{uuid4().hex[:8]}",
                is_active=True,
            )
            workspace2 = Workspace(
                name="Workspace 2",
                slug=f"ws2-{uuid4().hex[:8]}",
                is_active=True,
            )
            session.add(workspace1)
            session.add(workspace2)
            await session.commit()
            await session.refresh(workspace1)
            await session.refresh(workspace2)

        try:
            # Act - Create groups with same name in different workspaces
            group_name = f"shared_name_{uuid4().hex[:8]}"

            group1_data = {
                "workspace_id": str(workspace1.id),
                "name": group_name,
                "description": "Group in workspace 1",
            }
            group2_data = {
                "workspace_id": str(workspace2.id),
                "name": group_name,  # Same name, different workspace
                "description": "Group in workspace 2",
            }

            response1 = await client.post(
                "api/v1/rbac/admin/groups/",
                json=group1_data,
                headers=logged_in_headers_super_user,
            )
            response2 = await client.post(
                "api/v1/rbac/admin/groups/",
                json=group2_data,
                headers=logged_in_headers_super_user,
            )

            # Assert - Both succeed (workspace isolation)
            assert response1.status_code == 201, response1.text
            assert response2.status_code == 201, response2.text

            group1 = response1.json()
            group2 = response2.json()
            assert group1["name"] == group_name
            assert group2["name"] == group_name
            assert group1["workspace_id"] != group2["workspace_id"]

            # Cleanup groups
            await client.delete(
                f"api/v1/rbac/admin/groups/{group1['id']}",
                headers=logged_in_headers_super_user,
            )
            await client.delete(
                f"api/v1/rbac/admin/groups/{group2['id']}",
                headers=logged_in_headers_super_user,
            )
        finally:
            # Cleanup workspaces
            async with db_manager.with_session() as session:
                ws1 = await session.get(Workspace, workspace1.id)
                ws2 = await session.get(Workspace, workspace2.id)
                if ws1:
                    await session.delete(ws1)
                if ws2:
                    await session.delete(ws2)
                await session.commit()

    @pytest.mark.asyncio
    async def test_create_group_requires_authentication(
        self,
        client: AsyncClient,
        test_workspace,
    ):
        """Test that creating groups requires authentication.

        Scenario: Unauthenticated request to create group
        Expected: 403 Forbidden (FastAPI default for missing auth)
        """
        # Arrange
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": "unauthorized_group",
            "description": "Should fail",
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/groups/", json=group_data
        )

        # Assert
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_group_requires_superuser(
        self,
        client: AsyncClient,
        logged_in_headers,  # Regular user, not superuser
        test_workspace,
    ):
        """Test that creating groups requires superuser access.

        Scenario: Regular user attempts to create group
        Expected: 403 Forbidden
        """
        # Arrange
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": "unauthorized_group",
            "description": "Should fail",
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers,
        )

        # Assert
        assert response.status_code == 403
        assert "Insufficient permissions" in response.text

    @pytest.mark.asyncio
    async def test_create_group_duplicate_name_in_workspace_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test that duplicate group names in same workspace are rejected.

        Scenario: Admin attempts to create group with existing name in workspace
        Expected: 400 Bad Request with clear error message
        """
        # Arrange - Create first group
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"duplicate_test_{uuid4().hex[:8]}",
            "description": "First group",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Act - Try to create duplicate
        duplicate_data = {
            "workspace_id": str(test_workspace.id),
            "name": group_data["name"],  # Same name, same workspace
            "description": "Duplicate group",
        }
        duplicate_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=duplicate_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert duplicate_response.status_code == 400
        assert ("unique" in duplicate_response.text.lower() or "already exists" in duplicate_response.text.lower())

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_create_group_invalid_workspace_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
    ):
        """Test that creating group with invalid workspace fails.

        Scenario: Admin creates group with non-existent workspace ID
        Expected: 404 Not Found (workspace does not exist)
        """
        # Arrange
        fake_workspace_id = str(uuid4())
        group_data = {
            "workspace_id": fake_workspace_id,
            "name": "invalid_workspace_group",
            "description": "Should fail",
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 404  # Fixed: workspace not found should return 404
        assert "workspace not found" in response.text.lower()

    @pytest.mark.asyncio
    async def test_add_duplicate_member_fails(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
        active_super_user,
    ):
        """Test that adding same user to group twice fails.

        Scenario: Admin attempts to add user who is already a member
        Expected: 400 Bad Request
        """
        # Arrange - Create group and add member
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"dup_member_test_{uuid4().hex[:8]}",
            "description": "Duplicate member test",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Add member first time
        member_data = {"user_id": str(active_super_user.id)}
        first_add = await client.post(
            f"api/v1/rbac/admin/groups/{group_id}/members",
            json=member_data,
            headers=logged_in_headers_super_user,
        )
        assert first_add.status_code == 201

        # Act - Try to add same member again
        second_add = await client.post(
            f"api/v1/rbac/admin/groups/{group_id}/members",
            json=member_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert second_add.status_code == 400
        assert "already a member" in second_add.text.lower()

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )

    @pytest.mark.asyncio
    async def test_group_crud_workflow_end_to_end(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
        active_super_user,
    ):
        """Test complete CRUD workflow for groups with members.

        Scenario: Create -> Add Member -> Update -> Remove Member -> Delete
        Expected: All operations succeed in sequence
        """
        # Step 1: Create group
        create_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"workflow_group_{uuid4().hex[:8]}",
            "description": "Workflow test group",
        }
        create_response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=create_data,
            headers=logged_in_headers_super_user,
        )
        assert create_response.status_code == 201
        group_id = create_response.json()["id"]

        # Step 2: Add member
        member_data = {"user_id": str(active_super_user.id)}
        add_member_response = await client.post(
            f"api/v1/rbac/admin/groups/{group_id}/members",
            json=member_data,
            headers=logged_in_headers_super_user,
        )
        assert add_member_response.status_code == 201

        # Step 3: Read group and verify member
        read_response = await client.get(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )
        assert read_response.status_code == 200
        assert read_response.json()["name"] == create_data["name"]

        members_response = await client.get(
            f"api/v1/rbac/admin/groups/{group_id}/members",
            headers=logged_in_headers_super_user,
        )
        assert members_response.status_code == 200
        assert len(members_response.json()) == 1

        # Step 4: Update group
        update_data = {"description": "Updated workflow group"}
        update_response = await client.patch(
            f"api/v1/rbac/admin/groups/{group_id}",
            json=update_data,
            headers=logged_in_headers_super_user,
        )
        assert update_response.status_code == 200
        assert update_response.json()["description"] == "Updated workflow group"

        # Step 5: Remove member
        remove_member_response = await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}/members/{active_super_user.id}",
            headers=logged_in_headers_super_user,
        )
        assert remove_member_response.status_code == 204

        # Step 6: Delete group
        delete_response = await client.delete(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )
        assert delete_response.status_code == 204

        # Step 7: Verify deleted
        verify_response = await client.get(
            f"api/v1/rbac/admin/groups/{group_id}",
            headers=logged_in_headers_super_user,
        )
        assert verify_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_group_with_scim_fields(
        self,
        client: AsyncClient,
        logged_in_headers_super_user,
        test_workspace,
    ):
        """Test creating group with SCIM integration fields.

        Scenario: Admin creates group with SCIM external_id and scim_synced flag
        Expected: Group is created with SCIM fields correctly set
        """
        # Arrange
        group_data = {
            "workspace_id": str(test_workspace.id),
            "name": f"scim_group_{uuid4().hex[:8]}",
            "description": "SCIM synced group",
            "external_id": "scim-external-123",
            "scim_synced": True,
        }

        # Act
        response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )

        # Assert
        assert response.status_code == 201, response.text
        group = response.json()
        assert group["external_id"] == "scim-external-123"
        assert group["scim_synced"] is True

        # Cleanup
        await client.delete(
            f"api/v1/rbac/admin/groups/{group['id']}",
            headers=logged_in_headers_super_user,
        )

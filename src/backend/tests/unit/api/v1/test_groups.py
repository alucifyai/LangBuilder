"""Unit tests for Group Management API.

Tests PRD Story 2.1 - User Group Management
- Create, Read, Update, Delete operations for groups
- Add/remove users from groups (membership management)
- Workspace-scoped group isolation
- SCIM integration support
"""

import pytest
from httpx import AsyncClient
from langflow.services.database.models.user.model import User
from langflow.services.database.models.user_group.model import UserGroup, UserGroupMember
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.deps import get_db_service
from sqlmodel import select

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(client):
    """Create test workspace in the database."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name="Test Workspace Groups",
            slug=f"test-workspace-groups-{id(client)}",
            description="Workspace for group testing",
            is_active=True,
        )
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)

    yield workspace

    # Cleanup
    async with db_manager.with_session() as session:
        workspace_db = await session.get(Workspace, workspace.id)
        if workspace_db:
            await session.delete(workspace_db)
        await session.commit()


@pytest.fixture
async def test_group(client, test_workspace):
    """Create a test group in the workspace."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        group = UserGroup(
            workspace_id=test_workspace.id,
            name="test_qa_team",
            description="QA team group for testing",
            is_active=True,
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)

    yield group

    # Cleanup
    async with db_manager.with_session() as session:
        group_db = await session.get(UserGroup, group.id)
        if group_db:
            await session.delete(group_db)
        await session.commit()


@pytest.fixture
async def test_user_regular(client):
    """Create a regular (non-superuser) test user."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        user = User(
            username=f"test_regular_{id(client)}",
            password="hashed_password",
            is_superuser=False,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    yield user

    # Cleanup
    async with db_manager.with_session() as session:
        user_db = await session.get(User, user.id)
        if user_db:
            await session.delete(user_db)
        await session.commit()


# ============================================================================
# LIST GROUPS Tests
# ============================================================================


async def test_list_groups_success(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test PRD Story 2.1: List groups endpoint returns groups."""
    response = await client.get(
        "api/v1/rbac/admin/groups/", headers=logged_in_headers_super_user
    )

    assert response.status_code == 200, response.text
    groups = response.json()
    assert isinstance(groups, list)
    assert len(groups) >= 1
    assert any(group["name"] == "test_qa_team" for group in groups)


async def test_list_groups_filter_by_workspace(
    client: AsyncClient, logged_in_headers_super_user, test_workspace, test_group
):
    """Test filtering groups by workspace_id."""
    response = await client.get(
        f"api/v1/rbac/admin/groups/?workspace_id={test_workspace.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    groups = response.json()
    assert isinstance(groups, list)
    # All returned groups should belong to the specified workspace
    for group in groups:
        assert group["workspace_id"] == str(test_workspace.id)


async def test_list_groups_with_pagination(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test pagination parameters work correctly."""
    response = await client.get(
        "api/v1/rbac/admin/groups/?skip=0&limit=5",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    groups = response.json()
    assert isinstance(groups, list)
    assert len(groups) <= 5


async def test_list_groups_requires_authentication(client: AsyncClient):
    """Test that listing groups requires authentication."""
    response = await client.get("api/v1/rbac/admin/groups/")

    # FastAPI returns 403 for missing authentication (not 401)
    assert response.status_code == 403, "Should require authentication"


async def test_list_groups_requires_superuser(
    client: AsyncClient, logged_in_headers
):
    """Test that non-superuser cannot list groups."""
    response = await client.get(
        "api/v1/rbac/admin/groups/", headers=logged_in_headers
    )

    assert response.status_code == 403, "Should require superuser access"
    assert "Insufficient permissions" in response.text


# ============================================================================
# GET GROUP Tests
# ============================================================================


async def test_get_group_success(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test getting a specific group by ID."""
    response = await client.get(
        f"api/v1/rbac/admin/groups/{test_group.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    group = response.json()
    assert group["id"] == str(test_group.id)
    assert group["name"] == "test_qa_team"
    assert group["description"] == "QA team group for testing"


async def test_get_group_not_found(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test getting a non-existent group returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"api/v1/rbac/admin/groups/{fake_id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404
    assert "not found" in response.text.lower()


async def test_get_group_requires_superuser(
    client: AsyncClient, logged_in_headers, test_group
):
    """Test that non-superuser cannot get group details."""
    response = await client.get(
        f"api/v1/rbac/admin/groups/{test_group.id}", headers=logged_in_headers
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


# ============================================================================
# CREATE GROUP Tests
# ============================================================================


async def test_create_group_success(
    client: AsyncClient, logged_in_headers_super_user, test_workspace
):
    """Test PRD Story 2.1 @AC1: Create group in workspace."""
    group_data = {
        "workspace_id": str(test_workspace.id),
        "name": "engineering_team",
        "description": "Engineering team group",
    }

    response = await client.post(
        "api/v1/rbac/admin/groups/",
        json=group_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    group = response.json()
    assert group["name"] == "engineering_team"
    assert group["description"] == "Engineering team group"
    assert group["workspace_id"] == str(test_workspace.id)
    assert group["is_active"] is True
    assert "id" in group

    # Cleanup
    group_id = group["id"]
    await client.delete(
        f"api/v1/rbac/admin/groups/{group_id}",
        headers=logged_in_headers_super_user,
    )


async def test_create_group_duplicate_name_in_workspace_fails(
    client: AsyncClient, logged_in_headers_super_user, test_workspace, test_group
):
    """Test that duplicate group names in same workspace are rejected."""
    group_data = {
        "workspace_id": str(test_workspace.id),
        "name": "test_qa_team",  # Same as existing group in same workspace
        "description": "Duplicate group",
    }

    response = await client.post(
        "api/v1/rbac/admin/groups/",
        json=group_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 400
    assert ("unique" in response.text.lower() or "already exists" in response.text.lower())


async def test_create_group_same_name_different_workspace_succeeds(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test that same group name in different workspace is allowed."""
    db_manager = get_db_service()

    # Create second workspace
    async with db_manager.with_session() as session:
        workspace2 = Workspace(
            name="Test Workspace 2",
            slug=f"test-workspace-2-{id(test_group)}",
            description="Second workspace",
            is_active=True,
        )
        session.add(workspace2)
        await session.commit()
        await session.refresh(workspace2)

    try:
        # Create group with same name in different workspace
        group_data = {
            "workspace_id": str(workspace2.id),
            "name": "test_qa_team",  # Same name as test_group but different workspace
            "description": "QA team in workspace 2",
        }

        response = await client.post(
            "api/v1/rbac/admin/groups/",
            json=group_data,
            headers=logged_in_headers_super_user,
        )

        assert response.status_code == 201, response.text
        group = response.json()
        assert group["name"] == "test_qa_team"
        assert group["workspace_id"] == str(workspace2.id)

        # Cleanup group
        await client.delete(
            f"api/v1/rbac/admin/groups/{group['id']}",
            headers=logged_in_headers_super_user,
        )
    finally:
        # Cleanup workspace
        async with db_manager.with_session() as session:
            workspace_db = await session.get(Workspace, workspace2.id)
            if workspace_db:
                await session.delete(workspace_db)
            await session.commit()


async def test_create_group_invalid_workspace_fails(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test that creating group with invalid workspace fails."""
    fake_workspace_id = "00000000-0000-0000-0000-000000000000"
    group_data = {
        "workspace_id": fake_workspace_id,
        "name": "invalid_group",
        "description": "Should fail",
    }

    response = await client.post(
        "api/v1/rbac/admin/groups/",
        json=group_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404  # Fixed: workspace not found should return 404, not 400
    assert "workspace not found" in response.text.lower()


async def test_create_group_requires_superuser(
    client: AsyncClient, logged_in_headers, test_workspace
):
    """Test that non-superuser cannot create groups."""
    group_data = {
        "workspace_id": str(test_workspace.id),
        "name": "unauthorized_group",
        "description": "Should fail",
    }

    response = await client.post(
        "api/v1/rbac/admin/groups/", json=group_data, headers=logged_in_headers
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


async def test_create_group_with_scim_fields(
    client: AsyncClient, logged_in_headers_super_user, test_workspace
):
    """Test creating group with SCIM integration fields."""
    group_data = {
        "workspace_id": str(test_workspace.id),
        "name": "scim_synced_group",
        "description": "SCIM synced group",
        "external_id": "scim-123456",
        "scim_synced": True,
    }

    response = await client.post(
        "api/v1/rbac/admin/groups/",
        json=group_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    group = response.json()
    assert group["external_id"] == "scim-123456"
    assert group["scim_synced"] is True

    # Cleanup
    await client.delete(
        f"api/v1/rbac/admin/groups/{group['id']}",
        headers=logged_in_headers_super_user,
    )


# ============================================================================
# UPDATE GROUP Tests
# ============================================================================


async def test_update_group_success(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test updating group description and active status."""
    update_data = {
        "description": "Updated QA team description",
        "is_active": False,
    }

    response = await client.patch(
        f"api/v1/rbac/admin/groups/{test_group.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    group = response.json()
    assert group["description"] == "Updated QA team description"
    assert group["is_active"] is False
    assert group["name"] == test_group.name  # Name unchanged


async def test_update_group_partial_update(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test that partial updates work (only updating some fields)."""
    # Only update description, leave other fields unchanged
    update_data = {"description": "Partially updated description"}

    response = await client.patch(
        f"api/v1/rbac/admin/groups/{test_group.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    group = response.json()
    assert group["description"] == "Partially updated description"
    assert group["name"] == test_group.name  # Unchanged
    assert group["is_active"] == test_group.is_active  # Unchanged


async def test_update_group_not_found(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test updating non-existent group returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    update_data = {"description": "New description"}

    response = await client.patch(
        f"api/v1/rbac/admin/groups/{fake_id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404


async def test_update_group_requires_superuser(
    client: AsyncClient, logged_in_headers, test_group
):
    """Test that non-superuser cannot update groups."""
    update_data = {"description": "Unauthorized update"}

    response = await client.patch(
        f"api/v1/rbac/admin/groups/{test_group.id}",
        json=update_data,
        headers=logged_in_headers,
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


# ============================================================================
# DELETE GROUP Tests
# ============================================================================


async def test_delete_group_success(
    client: AsyncClient, logged_in_headers_super_user, test_workspace
):
    """Test deleting a group with no members."""
    # Create a temporary group to delete
    group_data = {
        "workspace_id": str(test_workspace.id),
        "name": "temp_group_to_delete",
        "description": "Will be deleted",
    }

    create_response = await client.post(
        "api/v1/rbac/admin/groups/",
        json=group_data,
        headers=logged_in_headers_super_user,
    )
    assert create_response.status_code == 201
    group_id = create_response.json()["id"]

    # Now delete it
    delete_response = await client.delete(
        f"api/v1/rbac/admin/groups/{group_id}",
        headers=logged_in_headers_super_user,
    )

    assert delete_response.status_code == 204, delete_response.text

    # Verify it's gone
    get_response = await client.get(
        f"api/v1/rbac/admin/groups/{group_id}",
        headers=logged_in_headers_super_user,
    )
    assert get_response.status_code == 404


async def test_delete_group_cascade_deletes_members(
    client: AsyncClient, logged_in_headers_super_user, test_group, active_super_user
):
    """Test that deleting group also deletes all memberships."""
    db_manager = get_db_service()

    # Add a member to the group
    async with db_manager.with_session() as session:
        member = UserGroupMember(
            group_id=test_group.id,
            user_id=active_super_user.id,
            is_active=True,
        )
        session.add(member)
        await session.commit()

    # Delete the group
    response = await client.delete(
        f"api/v1/rbac/admin/groups/{test_group.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 204

    # Verify memberships are also deleted
    async with db_manager.with_session() as session:
        stmt = select(UserGroupMember).where(
            UserGroupMember.group_id == test_group.id
        )
        members = (await session.exec(stmt)).all()
        assert len(members) == 0, "Memberships should be cascade deleted"


async def test_delete_group_not_found(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test deleting non-existent group returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(
        f"api/v1/rbac/admin/groups/{fake_id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404


async def test_delete_group_requires_superuser(
    client: AsyncClient, logged_in_headers, test_group
):
    """Test that non-superuser cannot delete groups."""
    response = await client.delete(
        f"api/v1/rbac/admin/groups/{test_group.id}", headers=logged_in_headers
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


# ============================================================================
# GROUP MEMBERSHIP Tests
# ============================================================================


async def test_list_group_members_success(
    client: AsyncClient, logged_in_headers_super_user, test_group, active_super_user
):
    """Test listing members of a group."""
    db_manager = get_db_service()

    # Add a member to the group
    async with db_manager.with_session() as session:
        member = UserGroupMember(
            group_id=test_group.id,
            user_id=active_super_user.id,
            is_active=True,
        )
        session.add(member)
        await session.commit()

    # List members
    response = await client.get(
        f"api/v1/rbac/admin/groups/{test_group.id}/members",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    members = response.json()
    assert isinstance(members, list)
    assert len(members) >= 1
    assert any(m["user_id"] == str(active_super_user.id) for m in members)

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(UserGroupMember).where(
            UserGroupMember.group_id == test_group.id
        )
        members_db = (await session.exec(stmt)).all()
        for member in members_db:
            await session.delete(member)
        await session.commit()


async def test_list_group_members_empty_group(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test listing members of an empty group returns empty list."""
    response = await client.get(
        f"api/v1/rbac/admin/groups/{test_group.id}/members",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    members = response.json()
    assert isinstance(members, list)
    assert len(members) == 0


async def test_add_group_member_success(
    client: AsyncClient, logged_in_headers_super_user, test_group, test_user_regular
):
    """Test PRD Story 2.1 @AC1: Add user to group."""
    member_data = {
        "user_id": str(test_user_regular.id),
    }

    response = await client.post(
        f"api/v1/rbac/admin/groups/{test_group.id}/members",
        json=member_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    member = response.json()
    assert member["user_id"] == str(test_user_regular.id)
    assert member["group_id"] == str(test_group.id)
    assert member["is_active"] is True

    # Cleanup
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(UserGroupMember).where(
            UserGroupMember.group_id == test_group.id,
            UserGroupMember.user_id == test_user_regular.id,
        )
        member_db = (await session.exec(stmt)).first()
        if member_db:
            await session.delete(member_db)
        await session.commit()


async def test_add_group_member_duplicate_fails(
    client: AsyncClient, logged_in_headers_super_user, test_group, active_super_user
):
    """Test that adding same user to group twice fails."""
    db_manager = get_db_service()

    # Add member first time
    async with db_manager.with_session() as session:
        member = UserGroupMember(
            group_id=test_group.id,
            user_id=active_super_user.id,
            is_active=True,
        )
        session.add(member)
        await session.commit()

    # Try to add again
    member_data = {
        "user_id": str(active_super_user.id),
    }

    response = await client.post(
        f"api/v1/rbac/admin/groups/{test_group.id}/members",
        json=member_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 400
    assert "already a member" in response.text.lower()

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(UserGroupMember).where(
            UserGroupMember.group_id == test_group.id
        )
        members = (await session.exec(stmt)).all()
        for member in members:
            await session.delete(member)
        await session.commit()


async def test_add_group_member_invalid_user_fails(
    client: AsyncClient, logged_in_headers_super_user, test_group
):
    """Test that adding non-existent user to group fails."""
    fake_user_id = "00000000-0000-0000-0000-000000000000"
    member_data = {
        "user_id": fake_user_id,
    }

    response = await client.post(
        f"api/v1/rbac/admin/groups/{test_group.id}/members",
        json=member_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 400
    assert "user not found" in response.text.lower()


async def test_remove_group_member_success(
    client: AsyncClient, logged_in_headers_super_user, test_group, active_super_user
):
    """Test PRD Story 2.1 @AC2: Remove user from group."""
    db_manager = get_db_service()

    # Add member first
    async with db_manager.with_session() as session:
        member = UserGroupMember(
            group_id=test_group.id,
            user_id=active_super_user.id,
            is_active=True,
        )
        session.add(member)
        await session.commit()

    # Remove member
    response = await client.delete(
        f"api/v1/rbac/admin/groups/{test_group.id}/members/{active_super_user.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 204, response.text

    # Verify member is removed
    async with db_manager.with_session() as session:
        stmt = select(UserGroupMember).where(
            UserGroupMember.group_id == test_group.id,
            UserGroupMember.user_id == active_super_user.id,
        )
        member = (await session.exec(stmt)).first()
        assert member is None, "Member should be removed"


async def test_remove_group_member_not_a_member_fails(
    client: AsyncClient, logged_in_headers_super_user, test_group, test_user_regular
):
    """Test that removing non-member user fails."""
    response = await client.delete(
        f"api/v1/rbac/admin/groups/{test_group.id}/members/{test_user_regular.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404
    assert "not a member" in response.text.lower()


async def test_group_membership_requires_superuser(
    client: AsyncClient, logged_in_headers, test_group, test_user_regular
):
    """Test that non-superuser cannot manage group membership."""
    # Try to add member
    member_data = {"user_id": str(test_user_regular.id)}
    add_response = await client.post(
        f"api/v1/rbac/admin/groups/{test_group.id}/members",
        json=member_data,
        headers=logged_in_headers,
    )

    assert add_response.status_code == 403
    assert "Insufficient permissions" in add_response.text

    # Try to remove member
    remove_response = await client.delete(
        f"api/v1/rbac/admin/groups/{test_group.id}/members/{test_user_regular.id}",
        headers=logged_in_headers,
    )

    assert remove_response.status_code == 403
    assert "Insufficient permissions" in remove_response.text


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


async def test_openapi_docs_include_groups_endpoints(client: AsyncClient):
    """Test that OpenAPI docs are generated correctly for Groups endpoints."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    # Check that Groups endpoints are documented
    paths = openapi_spec.get("paths", {})
    assert "/api/v1/rbac/admin/groups/" in paths
    assert "/api/v1/rbac/admin/groups/{group_id}" in paths
    assert "/api/v1/rbac/admin/groups/{group_id}/members" in paths
    assert "/api/v1/rbac/admin/groups/{group_id}/members/{user_id}" in paths

    # Tags are defined on the router, check that at least one endpoint has Groups tag
    groups_paths = [p for p in paths.keys() if "groups" in p]
    assert len(groups_paths) >= 4, "At least 4 groups endpoints should be documented"

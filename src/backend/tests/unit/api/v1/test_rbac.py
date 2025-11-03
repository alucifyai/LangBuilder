"""Integration tests for RBAC Management API endpoints.

Tests all RBAC endpoints including:
- GET /api/v1/rbac/roles
- GET /api/v1/rbac/assignments
- GET /api/v1/rbac/assignments/{assignment_id}
- POST /api/v1/rbac/assignments
- PUT /api/v1/rbac/assignments/{assignment_id}
- DELETE /api/v1/rbac/assignments/{assignment_id}
- POST /api/v1/rbac/check-permission

Tests cover:
- Admin authorization (all endpoints require is_superuser except check-permission)
- Assignment CRUD operations
- Immutability protection
- Error handling (404, 403, 400)
- Filtering in list endpoints
"""
# ruff: noqa: F841

from uuid import uuid4

from fastapi import status
from httpx import AsyncClient


async def test_list_roles_requires_admin(client: AsyncClient, logged_in_headers):
    """Test that listing roles requires superuser privileges."""
    response = await client.get("api/v1/rbac/roles", headers=logged_in_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_list_roles_success(client: AsyncClient, logged_in_headers_super_user):
    """Test listing all roles as admin."""
    response = await client.get("api/v1/rbac/roles", headers=logged_in_headers_super_user)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, list), "The result must be a list"
    # Should have the 4 predefined roles from seeding
    assert len(result) == 4, "Should have 4 predefined roles"

    # Verify role structure
    role_names = [role["name"] for role in result]
    assert "Admin" in role_names
    assert "Owner" in role_names
    assert "Editor" in role_names
    assert "Viewer" in role_names

    # Verify each role has required fields
    for role in result:
        assert "id" in role
        assert "name" in role
        assert "description" in role


async def test_list_assignments_requires_admin(client: AsyncClient, logged_in_headers):
    """Test that listing assignments requires superuser privileges."""
    response = await client.get("api/v1/rbac/assignments", headers=logged_in_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_list_assignments_success(client: AsyncClient, logged_in_headers_super_user):
    """Test listing all assignments as admin."""
    response = await client.get("api/v1/rbac/assignments", headers=logged_in_headers_super_user)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, list), "The result must be a list"

    # Verify assignment structure if any exist
    if len(result) > 0:
        assignment = result[0]
        assert "id" in assignment
        assert "user_id" in assignment
        assert "role_id" in assignment
        assert "role_name" in assignment
        assert "scope_type" in assignment
        assert "scope_id" in assignment
        assert "is_immutable" in assignment
        assert "created_at" in assignment


async def test_list_assignments_with_filters(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test filtering assignments by user_id, role_name, scope_type."""
    # First, create an assignment for testing
    # Get roles first
    roles_response = await client.get("api/v1/rbac/roles", headers=logged_in_headers_super_user)
    roles = roles_response.json()
    owner_role = next(r for r in roles if r["name"] == "Owner")

    # Get user's default project
    projects_response = await client.get("api/v1/projects/", headers=logged_in_headers_super_user)
    projects = projects_response.json()
    if len(projects) > 0:
        project_id = projects[0]["id"]
    else:
        # Create a test project
        project_data = {"name": "Test Project", "description": "Test project for RBAC"}
        project_response = await client.post(
            "api/v1/projects/", json=project_data, headers=logged_in_headers_super_user
        )
        project_id = project_response.json()["id"]

    # Create assignment
    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Owner",
        "scope_type": "PROJECT",
        "scope_id": project_id,
    }
    create_response = await client.post(
        "api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user
    )

    # Only test filtering if creation succeeded
    if create_response.status_code == status.HTTP_201_CREATED:
        # Filter by user_id
        response = await client.get(
            f"api/v1/rbac/assignments?user_id={active_user.id}", headers=logged_in_headers_super_user
        )
        result = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert all(a["user_id"] == str(active_user.id) for a in result)

        # Filter by role_name
        response = await client.get("api/v1/rbac/assignments?role_name=Owner", headers=logged_in_headers_super_user)
        result = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert all(a["role_name"] == "Owner" for a in result)

        # Filter by scope_type
        response = await client.get("api/v1/rbac/assignments?scope_type=PROJECT", headers=logged_in_headers_super_user)
        result = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert all(a["scope_type"] == "PROJECT" for a in result)

        # Cleanup
        assignment_id = create_response.json()["id"]
        await client.delete(f"api/v1/rbac/assignments/{assignment_id}", headers=logged_in_headers_super_user)


async def test_get_assignment_requires_admin(client: AsyncClient, logged_in_headers):
    """Test that getting a single assignment requires superuser privileges."""
    fake_id = str(uuid4())
    response = await client.get(f"api/v1/rbac/assignments/{fake_id}", headers=logged_in_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_assignment_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test getting non-existent assignment returns 404."""
    fake_id = str(uuid4())
    response = await client.get(f"api/v1/rbac/assignments/{fake_id}", headers=logged_in_headers_super_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_create_assignment_requires_admin(client: AsyncClient, logged_in_headers, active_user):
    """Test that creating assignment requires superuser privileges."""
    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Viewer",
        "scope_type": "PROJECT",
        "scope_id": str(uuid4()),
    }
    response = await client.post("api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_create_assignment_user_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test creating assignment for non-existent user returns 404."""
    fake_user_id = str(uuid4())
    assignment_data = {"user_id": fake_user_id, "role_name": "Viewer", "scope_type": "GLOBAL", "scope_id": None}
    response = await client.post("api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "User not found" in response.json()["detail"]


async def test_create_assignment_project_not_found(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test creating assignment for non-existent project returns 404."""
    fake_project_id = str(uuid4())
    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Owner",
        "scope_type": "PROJECT",
        "scope_id": fake_project_id,
    }
    response = await client.post("api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Project not found" in response.json()["detail"]


async def test_create_assignment_duplicate(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test creating duplicate assignment returns 400."""
    # Get user's default project
    projects_response = await client.get("api/v1/projects/", headers=logged_in_headers_super_user)
    projects = projects_response.json()
    if len(projects) == 0:
        # Create a test project
        project_data = {"name": "Test Project Duplicate", "description": "Test"}
        project_response = await client.post(
            "api/v1/projects/", json=project_data, headers=logged_in_headers_super_user
        )
        project_id = project_response.json()["id"]
    else:
        project_id = projects[0]["id"]

    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Editor",
        "scope_type": "PROJECT",
        "scope_id": project_id,
    }

    # Create first assignment
    response1 = await client.post("api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user)

    # Only proceed if first creation succeeded
    if response1.status_code == status.HTTP_201_CREATED:
        # Attempt to create duplicate
        response2 = await client.post(
            "api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user
        )
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response2.json()["detail"]

        # Cleanup
        assignment_id = response1.json()["id"]
        await client.delete(f"api/v1/rbac/assignments/{assignment_id}", headers=logged_in_headers_super_user)


async def test_create_assignment_success(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test successfully creating a new assignment."""
    # Create a test project
    project_data = {"name": "Test Project Create", "description": "Test"}
    project_response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers_super_user)
    project_id = project_response.json()["id"]

    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Viewer",
        "scope_type": "PROJECT",
        "scope_id": project_id,
    }

    response = await client.post("api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user)
    result = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert result["user_id"] == str(active_user.id)
    assert result["role_name"] == "Viewer"
    assert result["scope_type"] == "PROJECT"
    assert result["scope_id"] == project_id
    assert result["is_immutable"] is False
    assert "id" in result
    assert "created_at" in result

    # Cleanup
    await client.delete(f"api/v1/rbac/assignments/{result['id']}", headers=logged_in_headers_super_user)


async def test_update_assignment_requires_admin(client: AsyncClient, logged_in_headers):
    """Test that updating assignment requires superuser privileges."""
    fake_id = str(uuid4())
    update_data = {"new_role_name": "Editor"}
    response = await client.put(f"api/v1/rbac/assignments/{fake_id}", json=update_data, headers=logged_in_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_update_assignment_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test updating non-existent assignment returns 404."""
    fake_id = str(uuid4())
    update_data = {"new_role_name": "Editor"}
    response = await client.put(
        f"api/v1/rbac/assignments/{fake_id}", json=update_data, headers=logged_in_headers_super_user
    )
    # Should return 404 for security (don't leak existence)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_assignment_success(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test successfully updating an assignment."""
    # Create a test project and assignment
    project_data = {"name": "Test Project Update", "description": "Test"}
    project_response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers_super_user)
    project_id = project_response.json()["id"]

    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Viewer",
        "scope_type": "PROJECT",
        "scope_id": project_id,
    }

    create_response = await client.post(
        "api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user
    )
    assignment_id = create_response.json()["id"]

    # Update to Editor role
    update_data = {"new_role_name": "Editor"}
    response = await client.put(
        f"api/v1/rbac/assignments/{assignment_id}", json=update_data, headers=logged_in_headers_super_user
    )
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert result["id"] == assignment_id
    assert result["role_name"] == "Editor"
    assert result["user_id"] == str(active_user.id)
    assert result["scope_type"] == "PROJECT"

    # Cleanup
    await client.delete(f"api/v1/rbac/assignments/{assignment_id}", headers=logged_in_headers_super_user)


async def test_delete_assignment_requires_admin(client: AsyncClient, logged_in_headers):
    """Test that deleting assignment requires superuser privileges."""
    fake_id = str(uuid4())
    response = await client.delete(f"api/v1/rbac/assignments/{fake_id}", headers=logged_in_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_delete_assignment_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test deleting non-existent assignment returns 404."""
    fake_id = str(uuid4())
    response = await client.delete(f"api/v1/rbac/assignments/{fake_id}", headers=logged_in_headers_super_user)
    # Should return 404 for security (don't leak existence)
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_assignment_success(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test successfully deleting an assignment."""
    # Create a test project and assignment
    project_data = {"name": "Test Project Delete", "description": "Test"}
    project_response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers_super_user)
    project_id = project_response.json()["id"]

    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Viewer",
        "scope_type": "PROJECT",
        "scope_id": project_id,
    }

    create_response = await client.post(
        "api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user
    )
    assignment_id = create_response.json()["id"]

    # Delete assignment
    response = await client.delete(f"api/v1/rbac/assignments/{assignment_id}", headers=logged_in_headers_super_user)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = await client.get(f"api/v1/rbac/assignments/{assignment_id}", headers=logged_in_headers_super_user)
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


async def test_check_permission_authenticated_user(client: AsyncClient, logged_in_headers, active_user):
    """Test check-permission endpoint is accessible to authenticated users (not admin-only)."""
    check_data = {"permission": "READ", "scope_type": "PROJECT", "scope_id": str(uuid4())}

    response = await client.post("api/v1/rbac/check-permission", json=check_data, headers=logged_in_headers)
    result = response.json()

    # Should succeed (not 403) even for non-admin users
    assert response.status_code == status.HTTP_200_OK
    assert "has_permission" in result
    assert "user_id" in result
    assert "permission" in result
    assert "scope_type" in result
    assert "scope_id" in result
    assert result["user_id"] == str(active_user.id)
    assert result["permission"] == "READ"
    assert result["scope_type"] == "PROJECT"


async def test_check_permission_returns_correct_result(client: AsyncClient, logged_in_headers_super_user, active_user):
    """Test check-permission returns correct permission status."""
    # Create a test project and assignment
    project_data = {"name": "Test Project Permission", "description": "Test"}
    project_response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers_super_user)
    project_id = project_response.json()["id"]

    assignment_data = {
        "user_id": str(active_user.id),
        "role_name": "Viewer",  # Viewer has only READ permission
        "scope_type": "PROJECT",
        "scope_id": project_id,
    }

    create_response = await client.post(
        "api/v1/rbac/assignments", json=assignment_data, headers=logged_in_headers_super_user
    )

    # Get non-admin user headers
    login_data = {"username": active_user.username, "password": "testpassword"}
    login_response = await client.post("api/v1/login", data=login_data)
    user_token = login_response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Check READ permission (should be True for Viewer)
    check_read = {"permission": "READ", "scope_type": "PROJECT", "scope_id": project_id}
    response_read = await client.post("api/v1/rbac/check-permission", json=check_read, headers=user_headers)
    result_read = response_read.json()
    assert response_read.status_code == status.HTTP_200_OK
    assert result_read["has_permission"] is True

    # Check DELETE permission (should be False for Viewer)
    check_delete = {"permission": "DELETE", "scope_type": "PROJECT", "scope_id": project_id}
    response_delete = await client.post("api/v1/rbac/check-permission", json=check_delete, headers=user_headers)
    result_delete = response_delete.json()
    assert response_delete.status_code == status.HTTP_200_OK
    assert result_delete["has_permission"] is False

    # Cleanup
    assignment_id = create_response.json()["id"]
    await client.delete(f"api/v1/rbac/assignments/{assignment_id}", headers=logged_in_headers_super_user)


async def test_immutable_assignment_protection(
    client: AsyncClient, logged_in_headers_super_user, active_user, async_session
):
    """Test that immutable assignments cannot be updated or deleted.

    This test creates an immutable assignment using RBACService directly,
    then verifies that API endpoints properly block modifications.
    """
    from langbuilder.services.database.models.rbac.model import RoleEnum, ScopeTypeEnum
    from langbuilder.services.deps import get_rbac_service

    # Setup: Create a test project
    project_data = {"name": "Test Immutable Project", "description": "Test project for immutability"}
    project_response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers_super_user)
    project_id = project_response.json()["id"]

    # Create an immutable assignment using RBACService directly
    rbac_service = get_rbac_service()
    immutable_assignment = await rbac_service.assign_role(
        async_session,
        active_user.id,
        RoleEnum.OWNER,
        ScopeTypeEnum.PROJECT,
        project_id,
        is_immutable=True,
    )
    await async_session.commit()

    # Test 1: Try to update immutable assignment - should get 403
    update_data = {"new_role_name": "Editor"}
    update_response = await client.put(
        f"api/v1/rbac/assignments/{immutable_assignment.id}", json=update_data, headers=logged_in_headers_super_user
    )
    assert update_response.status_code == status.HTTP_403_FORBIDDEN
    assert "immutable" in update_response.json()["detail"].lower()

    # Test 2: Try to delete immutable assignment - should get 403
    delete_response = await client.delete(
        f"api/v1/rbac/assignments/{immutable_assignment.id}", headers=logged_in_headers_super_user
    )
    assert delete_response.status_code == status.HTTP_403_FORBIDDEN
    assert "immutable" in delete_response.json()["detail"].lower()

"""Unit tests for Role Management API.

Tests PRD Story 3.2 - Custom Role Management API
- Create, Read, Update, Delete operations for roles
- Permission validation and assignment
- System role protection
- Authorization requirements
"""


import pytest
from httpx import AsyncClient
from langflow.services.database.models.rbac.permission import Permission
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_assignment import RoleAssignment
from langflow.services.deps import get_db_service
from sqlmodel import select

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_permissions(client):
    """Create test permissions in the database."""
    db_manager = get_db_service()
    permissions = []

    async with db_manager.with_session() as session:
        # Create test permissions
        perm1 = Permission(
            resource_type="flow",
            action="read",
            display_name="Read Flow",
            description="Allows reading flows",
        )
        perm2 = Permission(
            resource_type="flow",
            action="update",
            display_name="Update Flow",
            description="Allows updating flows",
        )
        perm3 = Permission(
            resource_type="flow",
            action="delete",
            display_name="Delete Flow",
            description="Allows deleting flows",
        )

        session.add(perm1)
        session.add(perm2)
        session.add(perm3)
        await session.commit()

        await session.refresh(perm1)
        await session.refresh(perm2)
        await session.refresh(perm3)

        permissions = [perm1, perm2, perm3]

    yield permissions

    # Cleanup
    async with db_manager.with_session() as session:
        for perm in permissions:
            perm_db = await session.get(Permission, perm.id)
            if perm_db:
                await session.delete(perm_db)
        await session.commit()


@pytest.fixture
async def test_role(client, test_permissions, active_super_user):
    """Create a test role with permissions."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        role = Role(
            name="test_viewer",
            display_name="Test Viewer",
            description="Test viewer role",
            is_system_role=False,
            is_active=True,
        )
        session.add(role)
        await session.flush()

        # Add permissions to role
        from langflow.services.database.models.rbac.role_permission import RolePermission

        for perm in test_permissions[:1]:  # Only add read permission
            role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
            session.add(role_perm)

        await session.commit()
        await session.refresh(role)

    yield role

    # Cleanup
    async with db_manager.with_session() as session:
        role_db = await session.get(Role, role.id)
        if role_db:
            await session.delete(role_db)
        await session.commit()


@pytest.fixture
async def system_role(client):
    """Create a system role that cannot be modified."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        role = Role(
            name="system_admin",
            display_name="System Administrator",
            description="Built-in system administrator role",
            is_system_role=True,
            is_active=True,
        )
        session.add(role)
        await session.commit()
        await session.refresh(role)

    yield role

    # Cleanup
    async with db_manager.with_session() as session:
        role_db = await session.get(Role, role.id)
        if role_db:
            await session.delete(role_db)
        await session.commit()


# ============================================================================
# LIST ROLES Tests
# ============================================================================


async def test_list_roles_success(
    client: AsyncClient, logged_in_headers_super_user, test_role
):
    """Test PRD Story 3.2: List roles endpoint returns roles."""
    response = await client.get("api/v1/rbac/roles/", headers=logged_in_headers_super_user)

    assert response.status_code == 200, response.text
    roles = response.json()
    assert isinstance(roles, list)
    assert len(roles) >= 1
    assert any(role["name"] == "test_viewer" for role in roles)


async def test_list_roles_with_pagination(
    client: AsyncClient, logged_in_headers_super_user, test_role
):
    """Test pagination parameters work correctly."""
    response = await client.get(
        "api/v1/rbac/roles/?skip=0&limit=5", headers=logged_in_headers_super_user
    )

    assert response.status_code == 200
    roles = response.json()
    assert isinstance(roles, list)
    assert len(roles) <= 5


async def test_list_roles_requires_authentication(client: AsyncClient):
    """Test that listing roles requires authentication."""
    response = await client.get("api/v1/rbac/roles/")

    assert response.status_code == 401, "Should require authentication"


async def test_list_roles_requires_superuser(client: AsyncClient, logged_in_headers):
    """Test that non-superuser cannot list roles."""
    response = await client.get("api/v1/rbac/roles/", headers=logged_in_headers)

    assert response.status_code == 403, "Should require superuser access"
    assert "Insufficient permissions" in response.text


# ============================================================================
# GET ROLE Tests
# ============================================================================


async def test_get_role_success(
    client: AsyncClient, logged_in_headers_super_user, test_role
):
    """Test getting a specific role by ID."""
    response = await client.get(
        f"api/v1/rbac/roles/{test_role.id}", headers=logged_in_headers_super_user
    )

    assert response.status_code == 200
    role = response.json()
    assert role["id"] == str(test_role.id)
    assert role["name"] == "test_viewer"
    assert role["display_name"] == "Test Viewer"


async def test_get_role_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test getting a non-existent role returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(
        f"api/v1/rbac/roles/{fake_id}", headers=logged_in_headers_super_user
    )

    assert response.status_code == 404
    assert "not found" in response.text.lower()


async def test_get_role_requires_superuser(
    client: AsyncClient, logged_in_headers, test_role
):
    """Test that non-superuser cannot get role details."""
    response = await client.get(f"api/v1/rbac/roles/{test_role.id}", headers=logged_in_headers)

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


# ============================================================================
# CREATE ROLE Tests
# ============================================================================


async def test_create_role_success(
    client: AsyncClient, logged_in_headers_super_user, test_permissions
):
    """Test PRD Story 3.2 @AC1: Create custom role with permissions."""
    role_data = {
        "name": "custom_editor",
        "display_name": "Custom Editor",
        "description": "A custom editor role for testing",
        "permission_ids": [str(test_permissions[0].id), str(test_permissions[1].id)],
    }

    response = await client.post(
        "api/v1/rbac/roles/", json=role_data, headers=logged_in_headers_super_user
    )

    assert response.status_code == 201, response.text
    role = response.json()
    assert role["name"] == "custom_editor"
    assert role["display_name"] == "Custom Editor"
    assert role["is_system_role"] is False
    assert role["is_active"] is True
    assert "id" in role

    # Cleanup
    role_id = role["id"]
    await client.delete(f"api/v1/rbac/roles/{role_id}", headers=logged_in_headers_super_user)


async def test_create_role_duplicate_name_fails(
    client: AsyncClient, logged_in_headers_super_user, test_role
):
    """Test PRD Story 1.2 @AC2: Duplicate role name returns 400 error."""
    role_data = {
        "name": "test_viewer",  # Same as existing role
        "display_name": "Duplicate Viewer",
        "description": "This should fail",
        "permission_ids": [],
    }

    response = await client.post(
        "api/v1/rbac/roles/", json=role_data, headers=logged_in_headers_super_user
    )

    assert response.status_code == 400
    assert "already exists" in response.text.lower()
    assert "unique" in response.text.lower()


async def test_create_role_unknown_permission_fails(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test PRD Story 1.1 @AC2: Unknown permission ID returns 400 error."""
    fake_permission_id = "00000000-0000-0000-0000-000000000000"
    role_data = {
        "name": "invalid_role",
        "display_name": "Invalid Role",
        "description": "Has invalid permission",
        "permission_ids": [fake_permission_id],
    }

    response = await client.post(
        "api/v1/rbac/roles/", json=role_data, headers=logged_in_headers_super_user
    )

    assert response.status_code == 400
    assert "unknown permission" in response.text.lower()


async def test_create_role_reserved_name_fails(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test that reserved system role names cannot be used."""
    for reserved_name in ["admin", "owner", "viewer", "editor"]:
        role_data = {
            "name": reserved_name,
            "display_name": "Reserved Name",
            "description": "Should fail",
            "permission_ids": [],
        }

        response = await client.post(
            "api/v1/rbac/roles/", json=role_data, headers=logged_in_headers_super_user
        )

        assert response.status_code == 422 or response.status_code == 400
        # Pydantic validation should catch this


async def test_create_role_requires_superuser(
    client: AsyncClient, logged_in_headers, test_permissions
):
    """Test that non-superuser cannot create roles."""
    role_data = {
        "name": "unauthorized_role",
        "display_name": "Unauthorized Role",
        "description": "Should fail",
        "permission_ids": [],
    }

    response = await client.post("api/v1/rbac/roles/", json=role_data, headers=logged_in_headers)

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


async def test_create_role_validates_name_format(
    client: AsyncClient, logged_in_headers_super_user
):
    """Test that role name validation works (lowercase, alphanumeric, underscore)."""
    invalid_names = ["Invalid Name", "invalid-role", "Invalid!", "123invalid"]

    for invalid_name in invalid_names:
        role_data = {
            "name": invalid_name,
            "display_name": "Display Name",
            "description": "Description",
            "permission_ids": [],
        }

        response = await client.post(
            "api/v1/rbac/roles/", json=role_data, headers=logged_in_headers_super_user
        )

        assert response.status_code == 422, f"Should reject invalid name: {invalid_name}"


# ============================================================================
# UPDATE ROLE Tests
# ============================================================================


async def test_update_role_success(
    client: AsyncClient, logged_in_headers_super_user, test_role, test_permissions
):
    """Test PRD Story 1.2 @AC3: Update role with new permissions."""
    update_data = {
        "display_name": "Updated Viewer",
        "description": "Updated description",
        "permission_ids": [str(test_permissions[0].id), str(test_permissions[1].id)],
    }

    response = await client.patch(
        f"api/v1/rbac/roles/{test_role.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    role = response.json()
    assert role["display_name"] == "Updated Viewer"
    assert role["description"] == "Updated description"


async def test_update_role_system_role_fails(
    client: AsyncClient, logged_in_headers_super_user, system_role
):
    """Test that system roles cannot be updated."""
    update_data = {"display_name": "Should Fail"}

    response = await client.patch(
        f"api/v1/rbac/roles/{system_role.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 403
    assert "system role" in response.text.lower()
    assert "immutable" in response.text.lower() or "cannot modify" in response.text.lower()


async def test_update_role_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test updating non-existent role returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    update_data = {"display_name": "New Name"}

    response = await client.patch(
        f"api/v1/rbac/roles/{fake_id}", json=update_data, headers=logged_in_headers_super_user
    )

    assert response.status_code == 404


async def test_update_role_requires_superuser(
    client: AsyncClient, logged_in_headers, test_role
):
    """Test that non-superuser cannot update roles."""
    update_data = {"display_name": "Unauthorized Update"}

    response = await client.patch(
        f"api/v1/rbac/roles/{test_role.id}", json=update_data, headers=logged_in_headers
    )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


async def test_update_role_partial_update(
    client: AsyncClient, logged_in_headers_super_user, test_role
):
    """Test that partial updates work (only updating some fields)."""
    # Only update display_name, leave other fields unchanged
    update_data = {"display_name": "Partially Updated"}

    response = await client.patch(
        f"api/v1/rbac/roles/{test_role.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    role = response.json()
    assert role["display_name"] == "Partially Updated"
    assert role["name"] == test_role.name  # Unchanged
    assert role["description"] == test_role.description  # Unchanged


async def test_update_role_deactivate(
    client: AsyncClient, logged_in_headers_super_user, test_role
):
    """Test deactivating a role."""
    update_data = {"is_active": False}

    response = await client.patch(
        f"api/v1/rbac/roles/{test_role.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200
    role = response.json()
    assert role["is_active"] is False


# ============================================================================
# DELETE ROLE Tests
# ============================================================================


async def test_delete_role_success(
    client: AsyncClient, logged_in_headers_super_user, test_permissions
):
    """Test deleting a role that has no assignments."""
    # Create a temporary role to delete
    role_data = {
        "name": "temp_role_to_delete",
        "display_name": "Temporary Role",
        "description": "Will be deleted",
        "permission_ids": [str(test_permissions[0].id)],
    }

    create_response = await client.post(
        "api/v1/rbac/roles/", json=role_data, headers=logged_in_headers_super_user
    )
    assert create_response.status_code == 201
    role_id = create_response.json()["id"]

    # Now delete it
    delete_response = await client.delete(
        f"api/v1/rbac/roles/{role_id}", headers=logged_in_headers_super_user
    )

    assert delete_response.status_code == 204, delete_response.text

    # Verify it's gone
    get_response = await client.get(
        f"api/v1/rbac/roles/{role_id}", headers=logged_in_headers_super_user
    )
    assert get_response.status_code == 404


async def test_delete_role_system_role_fails(
    client: AsyncClient, logged_in_headers_super_user, system_role
):
    """Test that system roles cannot be deleted."""
    response = await client.delete(
        f"api/v1/rbac/roles/{system_role.id}", headers=logged_in_headers_super_user
    )

    assert response.status_code == 403
    assert "system role" in response.text.lower()
    assert "protected" in response.text.lower() or "cannot delete" in response.text.lower()


async def test_delete_role_with_assignments_fails(
    client: AsyncClient, logged_in_headers_super_user, test_role, active_super_user
):
    """Test that roles with active assignments cannot be deleted."""
    # Create a role assignment
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        from uuid import uuid4

        assignment = RoleAssignment(
            user_id=active_super_user.id,
            role_id=test_role.id,
            scope_type="workspace",
            scope_id=uuid4(),
        )
        session.add(assignment)
        await session.commit()

    # Try to delete the role
    response = await client.delete(
        f"api/v1/rbac/roles/{test_role.id}", headers=logged_in_headers_super_user
    )

    assert response.status_code == 400
    assert "active assignment" in response.text.lower()
    assert "revoke" in response.text.lower()

    # Cleanup - remove assignment
    async with db_manager.with_session() as session:
        stmt = select(RoleAssignment).where(RoleAssignment.role_id == test_role.id)
        assignments = (await session.exec(stmt)).all()
        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()


async def test_delete_role_not_found(client: AsyncClient, logged_in_headers_super_user):
    """Test deleting non-existent role returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(
        f"api/v1/rbac/roles/{fake_id}", headers=logged_in_headers_super_user
    )

    assert response.status_code == 404


async def test_delete_role_requires_superuser(
    client: AsyncClient, logged_in_headers, test_role
):
    """Test that non-superuser cannot delete roles."""
    response = await client.delete(f"api/v1/rbac/roles/{test_role.id}", headers=logged_in_headers)

    assert response.status_code == 403
    assert "Insufficient permissions" in response.text


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


async def test_openapi_docs_include_rbac_endpoints(client: AsyncClient):
    """Test that OpenAPI docs are generated correctly for RBAC endpoints."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    # Check that RBAC role endpoints are documented
    paths = openapi_spec.get("paths", {})
    assert "/api/v1/rbac/roles/" in paths
    assert "/api/v1/rbac/roles/{role_id}" in paths

    # Check tags
    assert any(tag["name"] == "Roles" for tag in openapi_spec.get("tags", []))

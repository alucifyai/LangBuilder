"""Unit tests for Grant (Role Assignment) API.

Tests PRD Story 3.5 - Role Assignment Management
- Create role assignments (grants) for users and service accounts
- Revoke role assignments
- List and filter grants
- Validate principal and scope formats
- Ensure proper authorization checks
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from langflow.services.database.models.rbac.permission import Permission
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_assignment import RoleAssignment
from langflow.services.database.models.rbac.role_permission import RolePermission
from langflow.services.database.models.rbac.service_account import ServiceAccount
from langflow.services.deps import get_db_service

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_role(client):
    """Create a test role with permissions."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create permissions
        perm1 = Permission(
            name="flow.read",
            resource_type="flow",
            action="read",
            display_name="Read Flow",
            description="Allows reading flows",
            scope_level="FLOW",
            is_active=True,
            is_system_permission=True,
        )
        perm2 = Permission(
            name="flow.update",
            resource_type="flow",
            action="update",
            display_name="Update Flow",
            description="Allows updating flows",
            scope_level="FLOW",
            is_active=True,
            is_system_permission=True,
        )
        session.add(perm1)
        session.add(perm2)
        await session.flush()

        # Create role
        role = Role(
            name="test_editor",
            display_name="Test Editor",
            description="Test role for editor permissions",
            is_system_role=False,
            is_active=True,
        )
        session.add(role)
        await session.flush()

        # Associate permissions with role
        role_perm1 = RolePermission(role_id=role.id, permission_id=perm1.id)
        role_perm2 = RolePermission(role_id=role.id, permission_id=perm2.id)
        session.add(role_perm1)
        session.add(role_perm2)

        await session.commit()
        await session.refresh(role)

    yield role

    # Cleanup
    async with db_manager.with_session() as session:
        # Delete role (cascade will handle role_permissions)
        role_db = await session.get(Role, role.id)
        if role_db:
            await session.delete(role_db)

        # Delete permissions
        perm1_db = await session.get(Permission, perm1.id)
        if perm1_db:
            await session.delete(perm1_db)
        perm2_db = await session.get(Permission, perm2.id)
        if perm2_db:
            await session.delete(perm2_db)

        await session.commit()


@pytest.fixture
async def test_service_account(client, active_super_user):
    """Create a test service account."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        sa = ServiceAccount(
            name="test_sa",
            display_name="Test Service Account",
            description="Test service account",
            is_active=True,
            created_by_user_id=active_super_user.id,
        )
        session.add(sa)
        await session.commit()
        await session.refresh(sa)

    yield sa

    # Cleanup
    async with db_manager.with_session() as session:
        sa_db = await session.get(ServiceAccount, sa.id)
        if sa_db:
            await session.delete(sa_db)
        await session.commit()


@pytest.fixture
async def test_grant(client, active_user, test_role):
    """Create a test grant for cleanup testing."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        grant = RoleAssignment(
            role_id=test_role.id,
            assignee_type="user",
            user_id=active_user.id,
            service_account_id=None,
            group_id=None,
            scope_type="project",
            scope_id=uuid4(),
            is_active=True,
        )
        session.add(grant)
        await session.commit()
        await session.refresh(grant)

    yield grant

    # Cleanup
    async with db_manager.with_session() as session:
        grant_db = await session.get(RoleAssignment, grant.id)
        if grant_db:
            await session.delete(grant_db)
        await session.commit()


# ============================================================================
# CREATE GRANT Tests
# ============================================================================


async def test_create_grant_user_principal_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    active_user,
    test_role,
):
    """Test PRD Story 3.5 @AC1: Create grant for user principal."""
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    grant = response.json()

    assert "id" in grant
    assert grant["role_id"] == grant_data["role_id"]
    assert grant["assignee_type"] == "user"
    assert grant["user_id"] == str(active_user.id)
    assert grant["service_account_id"] is None
    assert grant["group_id"] is None
    assert grant["scope_type"] == "project"
    assert "scope_id" in grant
    assert grant["is_active"] is True
    assert grant["role_name"] == test_role.name
    assert grant["role_display_name"] == test_role.display_name

    # Cleanup
    await client.delete(
        f"api/v1/rbac/grants/{grant['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_grant_service_account_principal_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
    test_role,
):
    """Test PRD Story 3.5 @AC1: Create grant for service account principal."""
    grant_data = {
        "principal": f"service_account:{test_service_account.id}",
        "role_id": str(test_role.id),
        "scope": {"workspace": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    grant = response.json()

    assert grant["assignee_type"] == "service_account"
    assert grant["service_account_id"] == str(test_service_account.id)
    assert grant["user_id"] is None
    assert grant["scope_type"] == "workspace"

    # Cleanup
    await client.delete(
        f"api/v1/rbac/grants/{grant['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_grant_with_time_bounds(
    client: AsyncClient,
    logged_in_headers_super_user,
    active_user,
    test_role,
):
    """Test creating grant with valid_from and valid_until (time-boxed grant)."""
    now = datetime.now(timezone.utc)
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"flow": str(uuid4())},
        "valid_from": now.isoformat(),
        "valid_until": (now.replace(year=now.year + 1)).isoformat(),
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    grant = response.json()

    assert "expires_at" in grant
    assert grant["expires_at"] is not None

    # Cleanup
    await client.delete(
        f"api/v1/rbac/grants/{grant['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_grant_invalid_principal_format(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_role,
):
    """Test that invalid principal format is rejected."""
    grant_data = {
        "principal": "invalid_format",  # Missing colon
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 422  # Validation error


async def test_create_grant_invalid_principal_type(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_role,
):
    """Test that invalid principal type is rejected."""
    grant_data = {
        "principal": "invalid_type:alice",  # Invalid type
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 422  # Validation error


async def test_create_grant_user_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_role,
):
    """Test that creating grant for non-existent user returns 404."""
    grant_data = {
        "principal": "user:nonexistent_user",
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text
    assert "User" in response.json()["detail"]


async def test_create_grant_role_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
    active_user,
):
    """Test that creating grant with non-existent role returns 404."""
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(uuid4()),  # Non-existent role
        "scope": {"project": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text
    assert "Role" in response.json()["detail"]


async def test_create_grant_duplicate(
    client: AsyncClient,
    logged_in_headers_super_user,
    active_user,
    test_role,
):
    """Test that creating duplicate grant returns 400."""
    scope_id = uuid4()
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"project": str(scope_id)},
    }

    # Create first grant
    response1 = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )
    assert response1.status_code == 201

    # Try to create duplicate
    response2 = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )
    assert response2.status_code == 400, response2.text
    assert "already exists" in response2.json()["detail"].lower()

    # Cleanup
    grant1 = response1.json()
    await client.delete(
        f"api/v1/rbac/grants/{grant1['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_grant_invalid_scope_format(
    client: AsyncClient,
    logged_in_headers_super_user,
    active_user,
    test_role,
):
    """Test that invalid scope format is rejected."""
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"invalid_scope": str(uuid4())},  # Invalid scope type
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 422  # Validation error


async def test_create_grant_requires_superuser(
    client: AsyncClient,
    logged_in_headers,  # Regular user, not superuser
    active_user,
    test_role,
):
    """Test that creating grants requires superuser access."""
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }

    response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text
    assert "Insufficient permissions" in response.json()["detail"]


async def test_create_grant_requires_authentication(
    client: AsyncClient,
    active_user,
    test_role,
):
    """Test that creating grants requires authentication."""
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }

    response = await client.post("api/v1/rbac/grants/", json=grant_data)

    assert response.status_code in [401, 403], "Should require authentication"


# ============================================================================
# GET GRANT Tests
# ============================================================================


async def test_get_grant_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_grant,
    test_role,
):
    """Test getting a specific grant by ID."""
    response = await client.get(
        f"api/v1/rbac/grants/{test_grant.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    grant = response.json()

    assert grant["id"] == str(test_grant.id)
    assert grant["role_id"] == str(test_grant.role_id)
    assert grant["assignee_type"] == test_grant.assignee_type
    assert grant["scope_type"] == test_grant.scope_type
    assert grant["role_name"] == test_role.name


async def test_get_grant_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test getting non-existent grant returns 404."""
    response = await client.get(
        f"api/v1/rbac/grants/{uuid4()}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_get_grant_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_grant,
):
    """Test that getting grant requires superuser access."""
    response = await client.get(
        f"api/v1/rbac/grants/{test_grant.id}",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# LIST GRANTS Tests
# ============================================================================


async def test_list_grants_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_grant,
):
    """Test PRD Story 3.5 @AC3: List all grants."""
    response = await client.get(
        "api/v1/rbac/grants/",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    grants = response.json()

    assert isinstance(grants, list)
    assert len(grants) >= 1

    # Verify structure
    if grants:
        grant = grants[0]
        assert "id" in grant
        assert "role_id" in grant
        assert "assignee_type" in grant
        assert "scope_type" in grant
        assert "scope_id" in grant
        assert "is_active" in grant


async def test_list_grants_filter_by_principal_user(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_grant,
    active_user,
):
    """Test filtering grants by user principal."""
    response = await client.get(
        f"api/v1/rbac/grants/?principal=user:{active_user.username}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    grants = response.json()

    assert isinstance(grants, list)
    # All returned grants should be for this user
    for grant in grants:
        if grant["assignee_type"] == "user":
            assert grant["user_id"] == str(active_user.id)


async def test_list_grants_filter_by_role(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_grant,
    test_role,
):
    """Test filtering grants by role ID."""
    response = await client.get(
        f"api/v1/rbac/grants/?role_id={test_role.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    grants = response.json()

    assert isinstance(grants, list)
    # All returned grants should have this role
    for grant in grants:
        assert grant["role_id"] == str(test_role.id)


async def test_list_grants_filter_by_scope_type(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_grant,
):
    """Test filtering grants by scope type."""
    response = await client.get(
        f"api/v1/rbac/grants/?scope_type={test_grant.scope_type}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    grants = response.json()

    assert isinstance(grants, list)
    # All returned grants should have this scope type
    for grant in grants:
        assert grant["scope_type"] == test_grant.scope_type


async def test_list_grants_pagination(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test grants pagination."""
    # Test with limit
    response = await client.get(
        "api/v1/rbac/grants/?limit=5",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == 200
    grants = response.json()
    assert len(grants) <= 5

    # Test with skip and limit
    response = await client.get(
        "api/v1/rbac/grants/?skip=1&limit=3",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == 200
    grants = response.json()
    assert len(grants) <= 3


async def test_list_grants_invalid_scope_type(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test that invalid scope type filter is rejected."""
    response = await client.get(
        "api/v1/rbac/grants/?scope_type=invalid",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 400, response.text


async def test_list_grants_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
):
    """Test that listing grants requires superuser access."""
    response = await client.get(
        "api/v1/rbac/grants/",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# REVOKE GRANT Tests
# ============================================================================


async def test_revoke_grant_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    active_user,
    test_role,
):
    """Test PRD Story 3.5 @AC2: Revoke role assignment."""
    # Create grant
    grant_data = {
        "principal": f"user:{active_user.username}",
        "role_id": str(test_role.id),
        "scope": {"project": str(uuid4())},
    }
    create_response = await client.post(
        "api/v1/rbac/grants/",
        json=grant_data,
        headers=logged_in_headers_super_user,
    )
    assert create_response.status_code == 201
    grant = create_response.json()

    # Revoke grant
    response = await client.delete(
        f"api/v1/rbac/grants/{grant['id']}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 204

    # Verify grant is deleted
    get_response = await client.get(
        f"api/v1/rbac/grants/{grant['id']}",
        headers=logged_in_headers_super_user,
    )
    assert get_response.status_code == 404


async def test_revoke_grant_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test revoking non-existent grant returns 404."""
    response = await client.delete(
        f"api/v1/rbac/grants/{uuid4()}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_revoke_grant_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_grant,
):
    """Test that revoking grants requires superuser access."""
    response = await client.delete(
        f"api/v1/rbac/grants/{test_grant.id}",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


async def test_revoke_grant_requires_authentication(
    client: AsyncClient,
    test_grant,
):
    """Test that revoking grants requires authentication."""
    response = await client.delete(f"api/v1/rbac/grants/{test_grant.id}")

    assert response.status_code in [401, 403], "Should require authentication"


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


async def test_openapi_docs_include_grants_endpoints(client: AsyncClient):
    """Test that OpenAPI docs include the grants endpoints."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    paths = openapi_spec.get("paths", {})

    # Check all grant endpoints are documented
    assert "/api/v1/rbac/grants/" in paths
    assert "/api/v1/rbac/grants/{grant_id}" in paths

    # Check methods
    grants_path = paths["/api/v1/rbac/grants/"]
    assert "get" in grants_path  # List
    assert "post" in grants_path  # Create

    grant_id_path = paths["/api/v1/rbac/grants/{grant_id}"]
    assert "get" in grant_id_path  # Get
    assert "delete" in grant_id_path  # Revoke


async def test_openapi_docs_grants_tag(client: AsyncClient):
    """Test that Grants tag exists in OpenAPI docs."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    paths = openapi_spec.get("paths", {})
    grants_path = paths.get("/api/v1/rbac/grants/", {})
    post_spec = grants_path.get("post", {})
    tags = post_spec.get("tags", [])

    assert "Grants" in tags, f"Grants tag not found in endpoint tags: {tags}"

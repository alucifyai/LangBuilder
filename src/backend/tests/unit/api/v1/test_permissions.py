"""Unit tests for Permission Catalog API.

Tests PRD Story 1.1 - Permission Catalog
- Read-only endpoint to list available permissions
- Filtering by resource_type and action
- Accessible to all authenticated users
- Pagination support
"""

import pytest
from httpx import AsyncClient
from langflow.services.database.models.rbac.permission import Permission
from langflow.services.deps import get_db_service

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_permissions_catalog(client):
    """Create a comprehensive set of test permissions in the database."""
    db_manager = get_db_service()
    permissions = []

    async with db_manager.with_session() as session:
        # Create permissions for different resource types and actions
        permission_definitions = [
            ("flow", "create", "Create Flow", "Allows creating new flows"),
            ("flow", "read", "Read Flow", "Allows reading/viewing flows"),
            ("flow", "update", "Update Flow", "Allows updating existing flows"),
            ("flow", "delete", "Delete Flow", "Allows deleting flows"),
            ("flow", "export", "Export Flow", "Allows exporting flows"),
            ("project", "create", "Create Project", "Allows creating new projects"),
            ("project", "read", "Read Project", "Allows reading/viewing projects"),
            ("project", "update", "Update Project", "Allows updating projects"),
            ("project", "delete", "Delete Project", "Allows deleting projects"),
            ("component", "create", "Create Component", "Allows creating components"),
            ("component", "read", "Read Component", "Allows reading components"),
            ("component", "update", "Update Component", "Allows updating components"),
            ("component", "delete", "Delete Component", "Allows deleting components"),
        ]

        for resource_type, action, display_name, description in permission_definitions:
            perm = Permission(
                name=f"{resource_type}.{action}",
                resource_type=resource_type,
                action=action,
                display_name=display_name,
                description=description,
                scope_level="FLOW" if resource_type == "flow" else "PROJECT",
                is_active=True,
                is_system_permission=True,
            )
            session.add(perm)
            permissions.append(perm)

        await session.commit()

        # Refresh all permissions to get their IDs
        for perm in permissions:
            await session.refresh(perm)

    yield permissions

    # Cleanup
    async with db_manager.with_session() as session:
        for perm in permissions:
            perm_db = await session.get(Permission, perm.id)
            if perm_db:
                await session.delete(perm_db)
        await session.commit()


@pytest.fixture
async def inactive_permission(client):
    """Create an inactive permission for testing filtering."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        perm = Permission(
            name="flow.archive",
            resource_type="flow",
            action="archive",
            display_name="Archive Flow",
            description="Inactive permission for testing",
            scope_level="FLOW",
            is_active=False,
            is_system_permission=False,
        )
        session.add(perm)
        await session.commit()
        await session.refresh(perm)

    yield perm

    # Cleanup
    async with db_manager.with_session() as session:
        perm_db = await session.get(Permission, perm.id)
        if perm_db:
            await session.delete(perm_db)
        await session.commit()


# ============================================================================
# LIST PERMISSIONS Tests
# ============================================================================


async def test_list_permissions_success(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test PRD Story 1.1 @AC1: List all permissions endpoint returns permissions.

    This endpoint is accessible to all authenticated users (not just superusers).
    """
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200, response.text
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) >= 13  # At least the test permissions we created

    # Verify structure of returned permissions
    if permissions:
        perm = permissions[0]
        assert "id" in perm
        assert "resource_type" in perm
        assert "action" in perm
        assert "display_name" in perm
        assert "description" in perm
        assert "is_active" in perm
        assert "created_at" in perm


async def test_list_permissions_filter_by_resource_type(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test PRD Story 1.1 @AC1: Filter permissions by resource_type."""
    response = await client.get(
        "api/v1/rbac/permissions/?resource_type=flow", headers=logged_in_headers
    )

    assert response.status_code == 200, response.text
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) == 5  # create, read, update, delete, export

    # Verify all returned permissions are for flow resource
    for perm in permissions:
        assert perm["resource_type"] == "flow"


async def test_list_permissions_filter_by_action(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test PRD Story 1.1 @AC1: Filter permissions by action."""
    response = await client.get(
        "api/v1/rbac/permissions/?action=read", headers=logged_in_headers
    )

    assert response.status_code == 200, response.text
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) == 3  # flow.read, project.read, component.read

    # Verify all returned permissions have read action
    for perm in permissions:
        assert perm["action"] == "read"


async def test_list_permissions_filter_by_resource_and_action(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test PRD Story 1.1 @AC1: Filter permissions by both resource_type and action."""
    response = await client.get(
        "api/v1/rbac/permissions/?resource_type=project&action=create",
        headers=logged_in_headers,
    )

    assert response.status_code == 200, response.text
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) == 1

    # Verify the specific permission
    perm = permissions[0]
    assert perm["resource_type"] == "project"
    assert perm["action"] == "create"
    assert perm["display_name"] == "Create Project"


async def test_list_permissions_filter_by_scope_level(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test filtering permissions by scope_level."""
    response = await client.get(
        "api/v1/rbac/permissions/?scope_level=FLOW", headers=logged_in_headers
    )

    assert response.status_code == 200, response.text
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) == 5  # All flow permissions

    # Verify all returned permissions have FLOW scope
    for perm in permissions:
        assert perm["scope_level"] == "FLOW"
        assert perm["resource_type"] == "flow"


async def test_list_permissions_with_pagination(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test pagination parameters work correctly."""
    # Test with limit
    response = await client.get(
        "api/v1/rbac/permissions/?limit=5", headers=logged_in_headers
    )
    assert response.status_code == 200
    permissions = response.json()
    assert len(permissions) <= 5

    # Test with skip and limit
    response = await client.get(
        "api/v1/rbac/permissions/?skip=2&limit=3", headers=logged_in_headers
    )
    assert response.status_code == 200
    permissions = response.json()
    assert len(permissions) <= 3


async def test_list_permissions_pagination_boundary_values(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test pagination with boundary values."""
    # Test skip=0
    response = await client.get(
        "api/v1/rbac/permissions/?skip=0&limit=100", headers=logged_in_headers
    )
    assert response.status_code == 200

    # Test large skip value (should return empty list or fewer items)
    response = await client.get(
        "api/v1/rbac/permissions/?skip=1000&limit=10", headers=logged_in_headers
    )
    assert response.status_code == 200
    permissions = response.json()
    # Should return empty or very few results
    assert isinstance(permissions, list)


async def test_list_permissions_limit_validation(
    client: AsyncClient, logged_in_headers
):
    """Test that limit parameter is validated (max 500)."""
    # Test with limit > 500 (should be rejected or capped)
    response = await client.get(
        "api/v1/rbac/permissions/?limit=1000", headers=logged_in_headers
    )
    # Should either return 422 validation error or cap at 500
    assert response.status_code in [200, 422]


async def test_list_permissions_negative_pagination_fails(
    client: AsyncClient, logged_in_headers
):
    """Test that negative pagination values are rejected."""
    # Negative skip
    response = await client.get(
        "api/v1/rbac/permissions/?skip=-1", headers=logged_in_headers
    )
    assert response.status_code == 422  # Validation error

    # Negative limit
    response = await client.get(
        "api/v1/rbac/permissions/?limit=-1", headers=logged_in_headers
    )
    assert response.status_code == 422  # Validation error


async def test_list_permissions_only_active(
    client: AsyncClient, logged_in_headers, test_permissions_catalog, inactive_permission
):
    """Test that only active permissions are returned by default."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()

    # Verify all returned permissions are active
    for perm in permissions:
        assert perm["is_active"] is True

    # Verify inactive permission is not in results
    permission_ids = [p["id"] for p in permissions]
    assert str(inactive_permission.id) not in permission_ids


async def test_list_permissions_empty_result_with_filter(
    client: AsyncClient, logged_in_headers
):
    """Test that filtering with non-existent values returns empty list."""
    response = await client.get(
        "api/v1/rbac/permissions/?resource_type=nonexistent", headers=logged_in_headers
    )

    assert response.status_code == 200
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) == 0


async def test_list_permissions_requires_authentication(client: AsyncClient):
    """Test that listing permissions requires authentication."""
    response = await client.get("api/v1/rbac/permissions/")

    # Should return either 401 (Unauthorized) or 403 (Forbidden) when not authenticated
    assert response.status_code in [401, 403], "Should require authentication"


async def test_list_permissions_accessible_to_regular_users(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test that regular (non-superuser) users can list permissions.

    This is a key difference from the roles API - permissions are readable by all users.
    """
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200, "Regular users should be able to list permissions"
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) > 0


async def test_list_permissions_accessible_to_superusers(
    client: AsyncClient, logged_in_headers_super_user, test_permissions_catalog
):
    """Test that superusers can also list permissions."""
    response = await client.get(
        "api/v1/rbac/permissions/", headers=logged_in_headers_super_user
    )

    assert response.status_code == 200
    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) > 0


async def test_list_permissions_ordering(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test that permissions are ordered by resource_type and action."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()

    # Verify ordering (should be by resource_type, then action)
    if len(permissions) >= 2:
        for i in range(len(permissions) - 1):
            current = permissions[i]
            next_perm = permissions[i + 1]

            # Either resource_type increases, or if same, action should increase
            assert (
                current["resource_type"] < next_perm["resource_type"]
                or (
                    current["resource_type"] == next_perm["resource_type"]
                    and current["action"] <= next_perm["action"]
                )
            )


async def test_list_permissions_response_structure(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test that each permission has all required fields with correct types."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()
    assert len(permissions) > 0

    perm = permissions[0]

    # Required fields
    assert isinstance(perm["id"], str)
    assert isinstance(perm["name"], str)
    assert isinstance(perm["resource_type"], str)
    assert isinstance(perm["action"], str)
    assert isinstance(perm["display_name"], str)
    assert isinstance(perm["scope_level"], str)
    assert isinstance(perm["is_active"], bool)
    assert isinstance(perm["is_system_permission"], bool)
    assert isinstance(perm["created_at"], str)  # ISO datetime string

    # Optional field
    assert "description" in perm
    # description can be string or null

    # Verify name format is "resource_type.action"
    assert perm["name"] == f"{perm['resource_type']}.{perm['action']}"


async def test_list_permissions_filter_case_sensitive(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test that filters are case-sensitive."""
    # Lowercase should match
    response1 = await client.get(
        "api/v1/rbac/permissions/?resource_type=flow", headers=logged_in_headers
    )
    assert response1.status_code == 200
    permissions1 = response1.json()
    assert len(permissions1) > 0

    # Uppercase should not match (assuming lowercase storage)
    response2 = await client.get(
        "api/v1/rbac/permissions/?resource_type=FLOW", headers=logged_in_headers
    )
    assert response2.status_code == 200
    permissions2 = response2.json()
    assert len(permissions2) == 0  # No match due to case difference


async def test_list_permissions_multiple_resource_types(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test listing permissions across multiple resource types."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()

    # Collect unique resource types
    resource_types = set(p["resource_type"] for p in permissions)

    # Should have at least flow, project, component
    assert "flow" in resource_types
    assert "project" in resource_types
    assert "component" in resource_types


async def test_list_permissions_multiple_actions(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test listing permissions across multiple actions."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()

    # Collect unique actions
    actions = set(p["action"] for p in permissions)

    # Should have at least create, read, update, delete
    assert "create" in actions
    assert "read" in actions
    assert "update" in actions
    assert "delete" in actions


async def test_list_permissions_name_field(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test that permissions have properly formatted name field."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()
    assert len(permissions) > 0

    # Verify all permissions have properly formatted names
    for perm in permissions:
        assert "name" in perm
        # Name should be in format "resource_type.action"
        expected_name = f"{perm['resource_type']}.{perm['action']}"
        assert perm["name"] == expected_name


async def test_list_permissions_system_permission_flag(
    client: AsyncClient, logged_in_headers, test_permissions_catalog
):
    """Test that all catalog permissions are marked as system permissions."""
    response = await client.get("api/v1/rbac/permissions/", headers=logged_in_headers)

    assert response.status_code == 200
    permissions = response.json()
    assert len(permissions) > 0

    # All test catalog permissions should be system permissions
    for perm in permissions:
        assert "is_system_permission" in perm
        assert perm["is_system_permission"] is True


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


async def test_openapi_docs_include_permissions_endpoint(client: AsyncClient):
    """Test that OpenAPI docs include the permissions catalog endpoint."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    # Check that permissions endpoint is documented
    paths = openapi_spec.get("paths", {})
    assert "/api/v1/rbac/permissions/" in paths

    # Check the endpoint details
    permissions_path = paths["/api/v1/rbac/permissions/"]
    assert "get" in permissions_path

    get_spec = permissions_path["get"]
    assert "parameters" in get_spec

    # Verify query parameters are documented
    param_names = [p["name"] for p in get_spec["parameters"]]
    assert "resource_type" in param_names
    assert "action" in param_names
    assert "scope_level" in param_names
    assert "skip" in param_names
    assert "limit" in param_names


async def test_openapi_docs_permissions_tag(client: AsyncClient):
    """Test that Permissions tag exists in OpenAPI docs."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    # Check that the permissions endpoint uses the Permissions tag
    paths = openapi_spec.get("paths", {})
    permissions_path = paths.get("/api/v1/rbac/permissions/", {})
    get_spec = permissions_path.get("get", {})
    tags = get_spec.get("tags", [])

    # The endpoint should be tagged with "Permissions"
    assert "Permissions" in tags, f"Permissions tag not found in endpoint tags: {tags}"


async def test_openapi_docs_permissions_response_schema(client: AsyncClient):
    """Test that the permissions endpoint response schema is documented."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    paths = openapi_spec.get("paths", {})
    permissions_path = paths.get("/api/v1/rbac/permissions/", {})
    get_spec = permissions_path.get("get", {})
    responses = get_spec.get("responses", {})

    # Check 200 response is documented
    assert "200" in responses

    response_200 = responses["200"]
    assert "content" in response_200
    assert "application/json" in response_200["content"]

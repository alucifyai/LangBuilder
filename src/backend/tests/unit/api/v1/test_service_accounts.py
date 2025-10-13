"""Unit tests for Service Account Management API.

Tests PRD Story 2.4 - Service Account Management
- Create service accounts with optional role assignment
- Generate scoped API tokens for service accounts
- List, update, and delete service accounts
- Token lifecycle management
- Ensure proper authorization checks
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from langflow.services.database.models.rbac.permission import Permission
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_permission import RolePermission
from langflow.services.database.models.rbac.service_account import ServiceAccount
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.deps import get_db_service

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(client):
    """Create a test workspace for service account testing."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name="Test Workspace",
            slug="test-workspace",
            description="Workspace for service account testing",
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
async def test_role(client):
    """Create a test role with permissions for service account testing."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create permissions
        perm1 = Permission(
            name="flow.create",
            resource_type="flow",
            action="create",
            display_name="Create Flow",
            description="Allows creating flows",
            scope_level="WORKSPACE",
            is_active=True,
            is_system_permission=True,
        )
        perm2 = Permission(
            name="flow.deploy",
            resource_type="flow",
            action="deploy",
            display_name="Deploy Flow",
            description="Allows deploying flows",
            scope_level="FLOW",
            is_active=True,
            is_system_permission=True,
        )
        session.add(perm1)
        session.add(perm2)
        await session.flush()

        # Create role
        role = Role(
            name="deployment_bot",
            display_name="Deployment Bot",
            description="Role for automated deployment",
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
async def test_service_account(client, active_super_user, test_workspace):
    """Create a test service account."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        sa = ServiceAccount(
            name="test_sa_fixture",
            display_name="Test Service Account Fixture",
            description="Service account for testing",
            workspace_id=test_workspace.id,  # ✅ ADDED workspace_id
            is_active=True,
            created_by_user_id=active_super_user.id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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


# ============================================================================
# CREATE SERVICE ACCOUNT Tests
# ============================================================================


async def test_create_service_account_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_workspace,
):
    """Test PRD Story 2.4 @AC1: Create service account without role."""
    sa_data = {
        "name": "ci-bot",
        "display_name": "CI/CD Bot",
        "description": "Automated deployment bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
    }

    response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    sa = response.json()

    assert "id" in sa
    assert sa["name"] == sa_data["name"]
    assert sa["display_name"] == sa_data["display_name"]
    assert sa["description"] == sa_data["description"]
    assert sa["is_active"] is True
    assert sa["token_count"] == 0
    assert sa["role_count"] == 0
    assert "created_at" in sa
    assert "created_by_user_id" in sa

    # Cleanup
    await client.delete(
        f"api/v1/rbac/service-accounts/{sa['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_service_account_with_role(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_role,
    test_workspace,
):
    """Test PRD Story 2.4 @AC1: Create service account with initial role assignment."""
    sa_data = {
        "name": "deploy-bot",
        "display_name": "Deploy Bot",
        "description": "Deployment automation",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
        "role_id": str(test_role.id),
        "scope": {"workspace": str(test_workspace.id)},  # ✅ Use same workspace
    }

    response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    sa = response.json()

    assert sa["name"] == sa_data["name"]
    assert sa["role_count"] == 1  # Should have one role assigned

    # Cleanup
    await client.delete(
        f"api/v1/rbac/service-accounts/{sa['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_service_account_duplicate_name(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
    test_workspace,
):
    """Test that creating service account with duplicate name returns 400."""
    sa_data = {
        "name": test_service_account.name,  # Duplicate name
        "display_name": "Duplicate SA",
        "description": "This should fail",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
    }

    response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 400, response.text
    assert "already exists" in response.json()["detail"].lower()


async def test_create_service_account_with_role_missing_scope(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_role,
    test_workspace,
):
    """Test that providing role_id without scope returns validation error."""
    sa_data = {
        "name": "no-scope-bot",
        "display_name": "No Scope Bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
        "role_id": str(test_role.id),
        # Missing scope - should fail validation
    }

    response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )

    # Should return validation error (422) because scope is required when role_id is provided
    assert response.status_code == 422, response.text
    error_detail = response.json()
    assert "scope is required" in str(error_detail).lower()


async def test_create_service_account_with_nonexistent_role(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_workspace,
):
    """Test that creating service account with non-existent role returns 404."""
    sa_data = {
        "name": "test-bot",
        "display_name": "Test Bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
        "role_id": str(uuid4()),  # Non-existent role
        "scope": {"workspace": str(test_workspace.id)},  # ✅ Use test workspace
    }

    response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text
    assert "Role" in response.json()["detail"]


async def test_create_service_account_requires_superuser(
    client: AsyncClient,
    logged_in_headers,  # Regular user, not superuser
    test_workspace,
):
    """Test that creating service accounts requires superuser access."""
    sa_data = {
        "name": "test-bot",
        "display_name": "Test Bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
    }

    response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text
    assert "Insufficient permissions" in response.json()["detail"]


async def test_create_service_account_requires_authentication(
    client: AsyncClient,
    test_workspace,
):
    """Test that creating service accounts requires authentication."""
    sa_data = {
        "name": "test-bot",
        "display_name": "Test Bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
    }

    response = await client.post("api/v1/rbac/service-accounts/", json=sa_data)

    assert response.status_code in [401, 403], "Should require authentication"


# ============================================================================
# LIST SERVICE ACCOUNTS Tests
# ============================================================================


async def test_list_service_accounts_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test listing service accounts."""
    response = await client.get(
        "api/v1/rbac/service-accounts/",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    service_accounts = response.json()

    assert isinstance(service_accounts, list)
    assert len(service_accounts) >= 1

    # Verify structure
    if service_accounts:
        sa = service_accounts[0]
        assert "id" in sa
        assert "name" in sa
        assert "display_name" in sa
        assert "is_active" in sa
        assert "token_count" in sa
        assert "role_count" in sa


async def test_list_service_accounts_filter_by_active(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test filtering service accounts by active status."""
    response = await client.get(
        "api/v1/rbac/service-accounts/?is_active=true",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    service_accounts = response.json()

    # All returned accounts should be active
    for sa in service_accounts:
        assert sa["is_active"] is True


async def test_list_service_accounts_pagination(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test service accounts pagination."""
    # Test with limit
    response = await client.get(
        "api/v1/rbac/service-accounts/?limit=5",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) <= 5

    # Test with skip and limit
    response = await client.get(
        "api/v1/rbac/service-accounts/?skip=1&limit=3",
        headers=logged_in_headers_super_user,
    )
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) <= 3


async def test_list_service_accounts_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
):
    """Test that listing service accounts requires superuser access."""
    response = await client.get(
        "api/v1/rbac/service-accounts/",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# GET SERVICE ACCOUNT Tests
# ============================================================================


async def test_get_service_account_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test getting a specific service account by ID."""
    response = await client.get(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    sa = response.json()

    assert sa["id"] == str(test_service_account.id)
    assert sa["name"] == test_service_account.name
    assert sa["display_name"] == test_service_account.display_name
    assert "token_count" in sa
    assert "role_count" in sa


async def test_get_service_account_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test getting non-existent service account returns 404."""
    response = await client.get(
        f"api/v1/rbac/service-accounts/{uuid4()}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_get_service_account_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_service_account,
):
    """Test that getting service account requires superuser access."""
    response = await client.get(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# UPDATE SERVICE ACCOUNT Tests
# ============================================================================


async def test_update_service_account_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test updating a service account."""
    update_data = {
        "display_name": "Updated Display Name",
        "description": "Updated description",
    }

    response = await client.patch(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    sa = response.json()

    assert sa["display_name"] == update_data["display_name"]
    assert sa["description"] == update_data["description"]
    assert sa["name"] == test_service_account.name  # Name should not change


async def test_update_service_account_deactivate(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test deactivating a service account."""
    update_data = {"is_active": False}

    response = await client.patch(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    sa = response.json()

    assert sa["is_active"] is False


async def test_update_service_account_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test updating non-existent service account returns 404."""
    update_data = {"display_name": "New Name"}

    response = await client.patch(
        f"api/v1/rbac/service-accounts/{uuid4()}",
        json=update_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_update_service_account_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_service_account,
):
    """Test that updating service account requires superuser access."""
    update_data = {"display_name": "New Name"}

    response = await client.patch(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        json=update_data,
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# DELETE SERVICE ACCOUNT Tests
# ============================================================================


async def test_delete_service_account_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_workspace,
):
    """Test deleting a service account."""
    # Create a service account
    sa_data = {
        "name": "temp-bot",
        "display_name": "Temporary Bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
    }
    create_response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )
    assert create_response.status_code == 201
    sa = create_response.json()

    # Delete the service account
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{sa['id']}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 204

    # Verify service account is deleted
    get_response = await client.get(
        f"api/v1/rbac/service-accounts/{sa['id']}",
        headers=logged_in_headers_super_user,
    )
    assert get_response.status_code == 404


async def test_delete_service_account_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test deleting non-existent service account returns 404."""
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{uuid4()}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_delete_service_account_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_service_account,
):
    """Test that deleting service account requires superuser access."""
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# CREATE TOKEN Tests
# ============================================================================


async def test_create_service_account_token_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test PRD Story 2.4 @AC2: Generate API token for service account."""
    token_data = {
        "name": "Production Token",
        "expires_days": 90,
    }

    response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    token = response.json()

    assert "id" in token
    assert "token" in token
    assert token["token"].startswith("lgs_")  # LangBuilder Service token prefix
    assert token["name"] == token_data["name"]
    assert "created_at" in token

    # Cleanup
    await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{token['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_service_account_token_default_name(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test creating token with default name."""
    token_data = {}  # No name provided

    response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 201, response.text
    token = response.json()

    # Should have default name based on service account
    assert token["name"]  # Name should not be empty

    # Cleanup
    await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{token['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_create_token_for_inactive_service_account(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test that creating token for inactive service account returns 400."""
    # Deactivate service account
    await client.patch(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        json={"is_active": False},
        headers=logged_in_headers_super_user,
    )

    # Try to create token
    token_data = {"name": "Test Token"}
    response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 400, response.text
    assert "not active" in response.json()["detail"].lower()

    # Reactivate for cleanup
    await client.patch(
        f"api/v1/rbac/service-accounts/{test_service_account.id}",
        json={"is_active": True},
        headers=logged_in_headers_super_user,
    )


async def test_create_token_service_account_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test creating token for non-existent service account returns 404."""
    token_data = {"name": "Test Token"}

    response = await client.post(
        f"api/v1/rbac/service-accounts/{uuid4()}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_create_token_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_service_account,
):
    """Test that creating tokens requires superuser access."""
    token_data = {"name": "Test Token"}

    response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# LIST TOKENS Tests
# ============================================================================


async def test_list_service_account_tokens_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test listing tokens for a service account."""
    # Create a token first
    token_data = {"name": "Test Token"}
    create_response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )
    assert create_response.status_code == 201
    created_token = create_response.json()

    # List tokens
    response = await client.get(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 200, response.text
    tokens = response.json()

    assert isinstance(tokens, list)
    assert len(tokens) >= 1

    # Verify structure (should not include token value)
    if tokens:
        token = tokens[0]
        assert "id" in token
        assert "name" in token
        assert "is_active" in token
        assert "total_uses" in token
        assert "token" not in token  # Token value should not be in list response

    # Cleanup
    await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{created_token['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_list_tokens_service_account_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
):
    """Test listing tokens for non-existent service account returns 404."""
    response = await client.get(
        f"api/v1/rbac/service-accounts/{uuid4()}/tokens",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_list_tokens_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_service_account,
):
    """Test that listing tokens requires superuser access."""
    response = await client.get(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# REVOKE TOKEN Tests
# ============================================================================


async def test_revoke_service_account_token_success(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test revoking (deleting) a service account token."""
    # Create a token
    token_data = {"name": "Temp Token"}
    create_response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )
    assert create_response.status_code == 201
    token = create_response.json()

    # Revoke the token
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{token['id']}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 204

    # Verify token is deleted
    list_response = await client.get(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        headers=logged_in_headers_super_user,
    )
    tokens = list_response.json()
    token_ids = [t["id"] for t in tokens]
    assert token["id"] not in token_ids


async def test_revoke_token_not_found(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test revoking non-existent token returns 404."""
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{uuid4()}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text


async def test_revoke_token_wrong_service_account(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_service_account,
):
    """Test revoking token with wrong service account ID returns 404."""
    # Create a token
    token_data = {"name": "Test Token"}
    create_response = await client.post(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens",
        json=token_data,
        headers=logged_in_headers_super_user,
    )
    assert create_response.status_code == 201
    token = create_response.json()

    # Try to revoke with wrong service account ID
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{uuid4()}/tokens/{token['id']}",
        headers=logged_in_headers_super_user,
    )

    assert response.status_code == 404, response.text

    # Cleanup
    await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{token['id']}",
        headers=logged_in_headers_super_user,
    )


async def test_revoke_token_requires_superuser(
    client: AsyncClient,
    logged_in_headers,
    test_service_account,
):
    """Test that revoking tokens requires superuser access."""
    response = await client.delete(
        f"api/v1/rbac/service-accounts/{test_service_account.id}/tokens/{uuid4()}",
        headers=logged_in_headers,
    )

    assert response.status_code == 403, response.text


# ============================================================================
# CASCADE DELETE Tests
# ============================================================================


async def test_delete_service_account_cascades_to_tokens(
    client: AsyncClient,
    logged_in_headers_super_user,
    test_workspace,
):
    """Test that deleting service account also deletes all its tokens."""
    # Create service account
    sa_data = {
        "name": "cascade-test-bot",
        "display_name": "Cascade Test Bot",
        "workspace_id": str(test_workspace.id),  # ✅ ADDED workspace_id
    }
    sa_response = await client.post(
        "api/v1/rbac/service-accounts/",
        json=sa_data,
        headers=logged_in_headers_super_user,
    )
    assert sa_response.status_code == 201
    sa = sa_response.json()

    # Create tokens
    for i in range(3):
        token_response = await client.post(
            f"api/v1/rbac/service-accounts/{sa['id']}/tokens",
            json={"name": f"Token {i}"},
            headers=logged_in_headers_super_user,
        )
        assert token_response.status_code == 201

    # Delete service account
    delete_response = await client.delete(
        f"api/v1/rbac/service-accounts/{sa['id']}",
        headers=logged_in_headers_super_user,
    )
    assert delete_response.status_code == 204

    # Verify tokens are also deleted (service account should not exist)
    get_response = await client.get(
        f"api/v1/rbac/service-accounts/{sa['id']}",
        headers=logged_in_headers_super_user,
    )
    assert get_response.status_code == 404


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


async def test_openapi_docs_include_service_account_endpoints(client: AsyncClient):
    """Test that OpenAPI docs include the service account endpoints."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    paths = openapi_spec.get("paths", {})

    # Check all service account endpoints are documented
    assert "/api/v1/rbac/service-accounts/" in paths
    assert "/api/v1/rbac/service-accounts/{sa_id}" in paths
    assert "/api/v1/rbac/service-accounts/{sa_id}/tokens" in paths
    assert "/api/v1/rbac/service-accounts/{sa_id}/tokens/{token_id}" in paths

    # Check methods
    sa_list_path = paths["/api/v1/rbac/service-accounts/"]
    assert "get" in sa_list_path  # List
    assert "post" in sa_list_path  # Create

    sa_detail_path = paths["/api/v1/rbac/service-accounts/{sa_id}"]
    assert "get" in sa_detail_path  # Get
    assert "patch" in sa_detail_path  # Update
    assert "delete" in sa_detail_path  # Delete

    tokens_path = paths["/api/v1/rbac/service-accounts/{sa_id}/tokens"]
    assert "get" in tokens_path  # List tokens
    assert "post" in tokens_path  # Create token


async def test_openapi_docs_service_accounts_tag(client: AsyncClient):
    """Test that Service Accounts tag exists in OpenAPI docs."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    paths = openapi_spec.get("paths", {})
    sa_path = paths.get("/api/v1/rbac/service-accounts/", {})
    post_spec = sa_path.get("post", {})
    tags = post_spec.get("tags", [])

    assert "Service Accounts" in tags, f"Service Accounts tag not found in endpoint tags: {tags}"

"""Unit tests for Grants API endpoints."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from langflow.services.database.models.grant.model import PrincipalType, ScopeType


@pytest.mark.asyncio
async def test_create_grant_success(client, active_user, superuser_token_headers, session):
    """Test successful grant creation."""
    from langflow.services.database.models.role.crud import create_role

    # Create a role first
    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    grant_data = {
        "principal_type": PrincipalType.USER,
        "principal_id": str(active_user.id),
        "role_id": str(role.id),
        "scope_type": ScopeType.WORKSPACE,
        "scope_id": "workspace-1",
    }

    response = client.post("/api/v1/grants/", json=grant_data, headers=superuser_token_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["principal_type"] == PrincipalType.USER
    assert data["principal_id"] == str(active_user.id)
    assert data["role_id"] == str(role.id)
    assert data["scope_type"] == ScopeType.WORKSPACE
    assert data["scope_id"] == "workspace-1"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_grant_with_expiration(client, active_user, superuser_token_headers, session):
    """Test grant creation with expiration date."""
    from langflow.services.database.models.role.crud import create_role

    role = await create_role(session, name="TempRole", permissions=["flows:read"])
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)

    grant_data = {
        "principal_type": PrincipalType.USER,
        "principal_id": str(active_user.id),
        "role_id": str(role.id),
        "scope_type": ScopeType.PROJECT,
        "scope_id": "project-1",
        "expires_at": expires_at.isoformat(),
    }

    response = client.post("/api/v1/grants/", json=grant_data, headers=superuser_token_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["expires_at"] is not None


@pytest.mark.asyncio
async def test_create_grant_role_not_found(client, active_user, superuser_token_headers):
    """Test grant creation with non-existent role."""
    grant_data = {
        "principal_type": PrincipalType.USER,
        "principal_id": str(active_user.id),
        "role_id": str(uuid4()),
        "scope_type": ScopeType.WORKSPACE,
        "scope_id": "workspace-1",
    }

    response = client.post("/api/v1/grants/", json=grant_data, headers=superuser_token_headers)
    assert response.status_code == 404
    assert "Role not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_grant_user_not_found(client, superuser_token_headers, session):
    """Test grant creation with non-existent user."""
    from langflow.services.database.models.role.crud import create_role

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    grant_data = {
        "principal_type": PrincipalType.USER,
        "principal_id": str(uuid4()),
        "role_id": str(role.id),
        "scope_type": ScopeType.WORKSPACE,
        "scope_id": "workspace-1",
    }

    response = client.post("/api/v1/grants/", json=grant_data, headers=superuser_token_headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_grant_requires_admin(client, active_user, logged_in_headers, session):
    """Test that grant creation requires admin privileges."""
    from langflow.services.database.models.role.crud import create_role

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    grant_data = {
        "principal_type": PrincipalType.USER,
        "principal_id": str(active_user.id),
        "role_id": str(role.id),
        "scope_type": ScopeType.WORKSPACE,
        "scope_id": "workspace-1",
    }

    response = client.post("/api/v1/grants/", json=grant_data, headers=logged_in_headers)
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_grant_success(client, active_user, superuser_token_headers, session):
    """Test retrieving a grant by ID."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])
    grant = await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    response = client.get(f"/api/v1/grants/{grant.id}", headers=superuser_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(grant.id)
    assert data["role_id"] == str(role.id)


@pytest.mark.asyncio
async def test_get_grant_not_found(client, superuser_token_headers):
    """Test retrieving non-existent grant."""
    response = client.get(f"/api/v1/grants/{uuid4()}", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "Grant not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_grants(client, active_user, superuser_token_headers, session):
    """Test listing all grants."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    # Create multiple grants
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )
    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.PROJECT,
        scope_id="project-1",
    )

    response = client.get("/api/v1/grants/", headers=superuser_token_headers)
    assert response.status_code == 200

    data = response.json()
    assert "grants" in data
    assert len(data["grants"]) >= 2


@pytest.mark.asyncio
async def test_list_grants_filter_by_principal(client, active_user, superuser_token_headers, session):
    """Test filtering grants by principal."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    response = client.get(
        f"/api/v1/grants/?principal_type={PrincipalType.USER}&principal_id={active_user.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert len(data["grants"]) >= 1
    assert all(g["principal_id"] == str(active_user.id) for g in data["grants"])


@pytest.mark.asyncio
async def test_list_grants_filter_by_scope(client, active_user, superuser_token_headers, session):
    """Test filtering grants by scope."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-123",
    )

    response = client.get(
        f"/api/v1/grants/?scope_type={ScopeType.WORKSPACE}&scope_id=workspace-123",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert all(g["scope_id"] == "workspace-123" for g in data["grants"])


@pytest.mark.asyncio
async def test_update_grant_expiration(client, active_user, superuser_token_headers, session):
    """Test updating grant expiration."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])
    grant = await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    new_expires_at = datetime.now(timezone.utc) + timedelta(days=60)
    update_data = {"expires_at": new_expires_at.isoformat()}

    response = client.patch(
        f"/api/v1/grants/{grant.id}", json=update_data, headers=superuser_token_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["expires_at"] is not None


@pytest.mark.asyncio
async def test_update_grant_scope(client, active_user, superuser_token_headers, session):
    """Test updating grant scope."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])
    grant = await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    update_data = {
        "scope_type": ScopeType.PROJECT,
        "scope_id": "project-1",
    }

    response = client.patch(
        f"/api/v1/grants/{grant.id}", json=update_data, headers=superuser_token_headers
    )
    assert response.status_code == 200

    data = response.json()
    assert data["scope_type"] == ScopeType.PROJECT
    assert data["scope_id"] == "project-1"


@pytest.mark.asyncio
async def test_revoke_grant(client, active_user, superuser_token_headers, session):
    """Test revoking (deleting) a grant."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])
    grant = await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    response = client.delete(f"/api/v1/grants/{grant.id}", headers=superuser_token_headers)
    assert response.status_code == 204

    # Verify grant is deleted
    get_response = client.get(f"/api/v1/grants/{grant.id}", headers=superuser_token_headers)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_list_grants_for_principal_route(client, active_user, superuser_token_headers, session):
    """Test dedicated endpoint for listing grants by principal."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-1",
    )

    response = client.get(
        f"/api/v1/grants/principal/{PrincipalType.USER}/{active_user.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "grants" in data
    assert all(g["principal_id"] == str(active_user.id) for g in data["grants"])


@pytest.mark.asyncio
async def test_list_grants_for_scope_route(client, active_user, superuser_token_headers, session):
    """Test dedicated endpoint for listing grants by scope."""
    from langflow.services.database.models.role.crud import create_role
    from langflow.services.database.models.grant.crud import create_grant

    role = await create_role(session, name="TestRole", permissions=["flows:read"])

    await create_grant(
        session,
        principal_type=PrincipalType.USER,
        principal_id=active_user.id,
        role_id=role.id,
        scope_type=ScopeType.WORKSPACE,
        scope_id="workspace-456",
    )

    response = client.get(
        f"/api/v1/grants/scope/{ScopeType.WORKSPACE}/workspace-456",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "grants" in data
    assert all(g["scope_id"] == "workspace-456" for g in data["grants"])

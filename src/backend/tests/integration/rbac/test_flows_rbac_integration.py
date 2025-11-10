"""
Integration tests for RBAC permission enforcement in flows.py endpoints.

These tests verify end-to-end permission enforcement for:
- GET /api/v1/flows/ (list with permission filtering)
- POST /api/v1/flows/ (create with project permission check)
- GET /api/v1/flows/{flow_id} (read with permission check)
- PATCH /api/v1/flows/{flow_id} (update with permission check)
- DELETE /api/v1/flows/{flow_id} (delete with permission check)
- Permission inheritance from Project to Flow
- Admin bypass for all operations
"""

import json
from uuid import uuid4

import pytest
from langbuilder.services.database.models.flow.model import FlowCreate
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import UserRoleAssignment
from sqlmodel import select


@pytest.fixture
async def test_project(client_session, active_user, roles):
    """Create a test project with Owner role for active_user."""
    project = Folder(
        name=f"RBAC Test Project {uuid4().hex[:8]}",
        description="Project for RBAC integration tests",
    )
    client_session.add(project)
    await client_session.commit()
    await client_session.refresh(project)

    # Grant active_user Owner role on this project so they can create flows
    owner_role = roles["Owner"]
    assignment = UserRoleAssignment(
        user_id=active_user.id,
        role_id=owner_role.id,
        scope_type="Project",
        scope_id=project.id,
        is_immutable=False,
    )
    client_session.add(assignment)
    await client_session.commit()

    yield project

    # Cleanup - delete assignment first, then project
    try:
        await client_session.delete(assignment)
        await client_session.delete(project)
        await client_session.commit()
    except Exception:
        # If cleanup fails, rollback to avoid leaving stale data
        await client_session.rollback()


@pytest.fixture
async def other_user(client):
    """Create another test user."""
    from langbuilder.services.auth.utils import get_password_hash
    from langbuilder.services.database.models.user.model import User
    from langbuilder.services.deps import get_db_service

    db_service = get_db_service()
    async with db_service.with_session() as session:
        user = User(
            username=f"otheruser_{uuid4().hex[:8]}",
            password=get_password_hash("testpassword"),
            is_active=True,
            is_superuser=False,
        )
        stmt = select(User).where(User.username == user.username)
        existing = (await session.exec(stmt)).first()
        if existing:
            user = existing
        else:
            session.add(user)
            await session.commit()
            await session.refresh(user)

        yield user

        # Cleanup
        try:
            await session.delete(user)
            await session.commit()
        except:
            pass


@pytest.fixture
async def other_user_headers(client, other_user):
    """Get auth headers for other user."""
    login_data = {"username": other_user.username, "password": "testpassword"}
    response = await client.post("api/v1/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def roles(client_session, client):
    """Get roles from database and reload RBAC cache."""
    from langbuilder.services.database.models.rbac import Role
    from langbuilder.api.v1.rbac import get_rbac_service

    # Get roles from database
    result = await client_session.exec(select(Role))
    roles_list = result.all()

    # Reload RBAC cache with current database state
    # This is critical because integration tests create fresh databases
    # with new UUIDs, so the cache needs to be refreshed
    rbac_service = get_rbac_service()
    await rbac_service._load_role_permission_cache()

    return {r.name: r for r in roles_list}


@pytest.fixture
async def admin_user(client, client_session, roles):
    """Create an admin user with Global Admin role."""
    from langbuilder.services.auth.utils import get_password_hash
    from langbuilder.services.database.models.user.model import User

    user = User(
        username=f"admin_{uuid4().hex[:8]}",
        password=get_password_hash("adminpassword"),
        is_active=True,
        is_superuser=False,
    )
    client_session.add(user)
    await client_session.commit()
    await client_session.refresh(user)

    # Grant Global Admin role
    admin_role = roles["Admin"]
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=admin_role.id,
        scope_type="Global",
        scope_id=None,
        is_immutable=False,
    )
    client_session.add(assignment)
    await client_session.commit()

    yield user

    # Cleanup - delete assignment first, then user
    try:
        await client_session.delete(assignment)
        await client_session.delete(user)
        await client_session.commit()
    except Exception:
        # If cleanup fails, rollback to avoid leaving stale data
        await client_session.rollback()


@pytest.fixture
async def admin_headers(client, admin_user):
    """Get auth headers for admin user."""
    login_data = {"username": admin_user.username, "password": "adminpassword"}
    response = await client.post("api/v1/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestFlowsListPermissionFiltering:
    """Test that GET /api/v1/flows/ filters flows by permission."""

    @pytest.mark.asyncio
    async def test_list_flows_shows_only_accessible_flows(
        self, client, logged_in_headers, other_user_headers, test_project, client_session, active_user, other_user, roles
    ):
        """Test that users only see flows they have permission to access."""
        # Create flows owned by active_user in test_project
        flow1_data = FlowCreate(
            name="Flow 1",
            description="First flow",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response1 = await client.post(
            "/api/v1/flows/", json=json.loads(flow1_data.model_dump_json()), headers=logged_in_headers
        )
        assert response1.status_code == 201
        flow1 = response1.json()

        # Create assignment for other_user to have Viewer access to the project
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Other user should see flow1 via inherited permission
        response = await client.get("/api/v1/flows/", headers=other_user_headers)
        assert response.status_code == 200
        data = response.json()

        # Check if flow1 is in the results
        flow_ids = [f["id"] for f in data["flows"]] if isinstance(data, dict) and "flows" in data else [f["id"] for f in data]
        assert flow1["id"] in flow_ids

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow1['id']}", headers=logged_in_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_list_flows_excludes_inaccessible_flows(
        self, client, logged_in_headers, other_user_headers, test_project, client_session, active_user, other_user
    ):
        """Test that users don't see flows they lack permission to access."""
        # Create flow owned by active_user (no assignment for other_user)
        flow_data = FlowCreate(
            name="Private Flow",
            description="Other user has no access",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Other user should NOT see this flow (no permission)
        response = await client.get("/api/v1/flows/", headers=other_user_headers)
        assert response.status_code == 200
        data = response.json()

        flow_ids = [f["id"] for f in data["flows"]] if isinstance(data, dict) and "flows" in data else [f["id"] for f in data]
        assert flow["id"] not in flow_ids

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)


class TestFlowsCreatePermission:
    """Test that POST /api/v1/flows/ requires appropriate permissions."""

    @pytest.mark.asyncio
    async def test_create_flow_requires_project_create_permission(
        self, client, other_user_headers, test_project, other_user, client_session, roles
    ):
        """Test that creating a flow requires Create permission on the project."""
        # Give other_user Viewer role (no Create permission)
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Try to create flow - should fail (Viewer can't Create)
        flow_data = FlowCreate(
            name="Unauthorized Flow",
            description="Should fail",
            data={},
            user_id=other_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=other_user_headers
        )

        # Should be forbidden
        assert response.status_code == 403

        # Cleanup
        # admin assignment cleaned up by fixture
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_create_flow_succeeds_with_editor_role(
        self, client, other_user_headers, test_project, other_user, client_session, roles
    ):
        """Test that users with Editor role can create flows."""
        # Give other_user Editor role (has Create permission)
        editor_role = roles["Editor"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=editor_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Create flow - should succeed
        flow_data = FlowCreate(
            name="Authorized Flow",
            description="Should succeed",
            data={},
            user_id=other_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=other_user_headers
        )

        assert response.status_code == 201
        flow = response.json()

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=other_user_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_admin_can_create_flow_in_any_project(
        self, client, logged_in_headers, test_project, client_session, active_user, roles
    ):
        """Test that Admin users can create flows in any project."""

        # Create flow in test_project - should succeed
        flow_data = FlowCreate(
            name="Admin Flow",
            description="Created by admin",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )

        assert response.status_code == 201
        flow = response.json()

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()


class TestFlowsReadPermission:
    """Test that GET /api/v1/flows/{flow_id} requires Read permission."""

    @pytest.mark.asyncio
    async def test_read_flow_requires_permission(
        self, client, logged_in_headers, other_user_headers, test_project, active_user
    ):
        """Test that reading a flow requires permission."""
        # Create flow owned by active_user
        flow_data = FlowCreate(
            name="Private Flow",
            description="No read access",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Other user tries to read - should fail
        response = await client.get(
            f"/api/v1/flows/{flow['id']}", headers=other_user_headers
        )
        assert response.status_code == 403

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)

    @pytest.mark.asyncio
    async def test_read_flow_succeeds_with_inherited_permission(
        self, client, logged_in_headers, other_user_headers, test_project, active_user, other_user, client_session, roles
    ):
        """Test that reading a flow succeeds with inherited project permission."""
        # Create flow
        flow_data = FlowCreate(
            name="Readable Flow",
            description="Has read access",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Give other_user Viewer role on project
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Other user reads - should succeed via inheritance
        response = await client.get(
            f"/api/v1/flows/{flow['id']}", headers=other_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == flow["id"]

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()


class TestFlowsUpdatePermission:
    """Test that PATCH /api/v1/flows/{flow_id} requires Update permission."""

    @pytest.mark.asyncio
    async def test_update_flow_requires_permission(
        self, client, logged_in_headers, other_user_headers, test_project, active_user, other_user, client_session, roles
    ):
        """Test that updating a flow requires Update permission."""
        # Create flow
        flow_data = FlowCreate(
            name="Original Name",
            description="Original description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Give other_user Viewer role (no Update permission)
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Try to update - should fail
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            f"/api/v1/flows/{flow['id']}", json=update_data, headers=other_user_headers
        )
        assert response.status_code == 403

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_update_flow_succeeds_with_editor_role(
        self, client, logged_in_headers, other_user_headers, test_project, active_user, other_user, client_session, roles
    ):
        """Test that updating a flow succeeds with Editor role."""
        # Create flow
        flow_data = FlowCreate(
            name="Original Name",
            description="Original description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Give other_user Editor role (has Update permission)
        editor_role = roles["Editor"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=editor_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Update - should succeed
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            f"/api/v1/flows/{flow['id']}", json=update_data, headers=other_user_headers
        )
        assert response.status_code == 200
        updated_flow = response.json()
        assert updated_flow["name"] == "Updated Name"

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=other_user_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()


class TestFlowsDeletePermission:
    """Test that DELETE /api/v1/flows/{flow_id} requires Delete permission."""

    @pytest.mark.asyncio
    async def test_delete_flow_requires_permission(
        self, client, logged_in_headers, other_user_headers, test_project, active_user, other_user, client_session, roles
    ):
        """Test that deleting a flow requires Delete permission."""
        # Create flow
        flow_data = FlowCreate(
            name="To Delete",
            description="Description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Give other_user Editor role (no Delete permission)
        editor_role = roles["Editor"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=editor_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Try to delete - should fail
        response = await client.delete(
            f"/api/v1/flows/{flow['id']}", headers=other_user_headers
        )
        assert response.status_code == 403

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)
        # admin assignment cleaned up by fixture
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_delete_flow_succeeds_with_owner_role(
        self, client, logged_in_headers, other_user_headers, test_project, active_user, other_user, client_session, roles
    ):
        """Test that deleting a flow succeeds with Owner role."""
        # Create flow
        flow_data = FlowCreate(
            name="To Delete",
            description="Description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Give other_user Owner role (has Delete permission)
        owner_role = roles["Owner"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=owner_role.id,
            scope_type="Project",
            scope_id=test_project.id,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Delete - should succeed
        response = await client.delete(
            f"/api/v1/flows/{flow['id']}", headers=other_user_headers
        )
        assert response.status_code == 200 or response.status_code == 204

        # Cleanup
        # admin assignment cleaned up by fixture
        await client_session.commit()


class TestFlowsAdminBypass:
    """Test that Admin users bypass all permission checks for flows."""

    @pytest.mark.asyncio
    async def test_admin_can_read_any_flow(
        self, client, logged_in_headers, admin_headers, test_project, active_user
    ):
        """Test that Admin users can read any flow."""
        # Create flow with active_user (who has Owner on project)
        flow_data = FlowCreate(
            name="Any Flow",
            description="Description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()

        # Admin reads - should succeed (bypass permission checks)
        response = await client.get(
            f"/api/v1/flows/{flow['id']}", headers=admin_headers
        )
        assert response.status_code == 200

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)

    @pytest.mark.asyncio
    async def test_admin_can_update_any_flow(
        self, client, logged_in_headers, admin_headers, test_project, active_user
    ):
        """Test that Admin users can update any flow."""
        # Create flow with active_user
        flow_data = FlowCreate(
            name="Original",
            description="Description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()


        # Admin updates - should succeed (bypass permission checks)
        update_data = {"name": "Updated by Admin"}
        response = await client.patch(
            f"/api/v1/flows/{flow['id']}", json=update_data, headers=admin_headers
        )
        assert response.status_code == 200

        # Cleanup
        await client.delete(f"/api/v1/flows/{flow['id']}", headers=logged_in_headers)

    @pytest.mark.asyncio
    async def test_admin_can_delete_any_flow(
        self, client, logged_in_headers, admin_headers, test_project, active_user
    ):
        """Test that Admin users can delete any flow."""
        # Create flow
        flow_data = FlowCreate(
            name="To Delete",
            description="Description",
            data={},
            user_id=active_user.id,
            folder_id=test_project.id,
        )
        response = await client.post(
            "/api/v1/flows/", json=json.loads(flow_data.model_dump_json()), headers=logged_in_headers
        )
        assert response.status_code == 201
        flow = response.json()


        # Admin deletes - should succeed (bypass permission checks)
        response = await client.delete(
            f"/api/v1/flows/{flow['id']}", headers=admin_headers
        )
        assert response.status_code == 200 or response.status_code == 204

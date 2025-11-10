"""
Integration tests for RBAC permission enforcement in projects.py endpoints.

These tests verify end-to-end permission enforcement for:
- GET /api/v1/projects/ (list with permission filtering)
- POST /api/v1/projects/ (create with Global permission check)
- GET /api/v1/projects/{project_id} (read with permission check)
- PATCH /api/v1/projects/{project_id} (update with permission check)
- DELETE /api/v1/projects/{project_id} (delete with permission check)
- Admin bypass for all operations
"""

from uuid import UUID, uuid4

import pytest
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import UserRoleAssignment
from sqlmodel import select


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


class TestProjectsListPermissionFiltering:
    """Test that GET /api/v1/projects/ filters projects by permission."""

    @pytest.mark.asyncio
    async def test_list_projects_shows_only_accessible_projects(
        self, client, logged_in_headers, other_user_headers, client_session, active_user, other_user, roles
    ):
        """Test that users only see projects they have permission to access."""
        # Create project
        project_data = {
            "name": f"Test Project {uuid4().hex[:8]}",
            "description": "Test project",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give other_user Viewer role on this project
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=UUID(project["id"]),
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Other user should see this project
        response = await client.get("/api/v1/projects/", headers=other_user_headers)
        assert response.status_code == 200
        data = response.json()

        project_ids = [p["id"] for p in data["folders"]] if isinstance(data, dict) and "folders" in data else [p["id"] for p in data]
        assert project["id"] in project_ids

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_list_projects_excludes_inaccessible_projects(
        self, client, logged_in_headers, other_user_headers, active_user, other_user
    ):
        """Test that users don't see projects they lack permission to access."""
        # Create project (no assignment for other_user)
        project_data = {
            "name": f"Private Project {uuid4().hex[:8]}",
            "description": "No access",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Other user should NOT see this project
        response = await client.get("/api/v1/projects/", headers=other_user_headers)
        assert response.status_code == 200
        data = response.json()

        project_ids = [p["id"] for p in data["folders"]] if isinstance(data, dict) and "folders" in data else [p["id"] for p in data]
        assert project["id"] not in project_ids

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)


class TestProjectsCreatePermission:
    """Test that POST /api/v1/projects/ requires Global Create permission."""

    @pytest.mark.asyncio
    async def test_create_project_succeeds_for_any_user(
        self, client, other_user_headers, other_user, client_session, roles
    ):
        """Test that any authenticated user can create a project (no RBAC check required)."""
        # Any user should be able to create their own project
        project_data = {
            "name": f"User Project {uuid4().hex[:8]}",
            "description": "Created by regular user",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=other_user_headers
        )

        # Should succeed - any user can create projects
        assert response.status_code == 201
        project = response.json()
        assert project["name"] == project_data["name"]

    @pytest.mark.asyncio
    async def test_create_project_succeeds_with_global_create_permission(
        self, client, other_user_headers, other_user, client_session, roles
    ):
        """Test that users with Global Create permission can create projects."""
        # Give other_user Editor role at Global level (has Create permission)
        editor_role = roles["Editor"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=editor_role.id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Create project - should succeed
        project_data = {
            "name": f"Authorized Project {uuid4().hex[:8]}",
            "description": "Should succeed",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=other_user_headers
        )

        assert response.status_code == 201
        project = response.json()

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=other_user_headers)
        await client_session.delete(assignment)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_admin_can_create_project(
        self, client, logged_in_headers, active_user, client_session, roles
    ):
        """Test that Admin users can create projects."""
        # Give active_user Admin role
        admin_role = roles["Admin"]
        assignment = UserRoleAssignment(
            user_id=active_user.id,
            role_id=admin_role.id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Create project - should succeed
        project_data = {
            "name": f"Admin Project {uuid4().hex[:8]}",
            "description": "Created by admin",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )

        assert response.status_code == 201
        project = response.json()

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()


class TestProjectsReadPermission:
    """Test that GET /api/v1/projects/{project_id} requires Read permission."""

    @pytest.mark.asyncio
    async def test_read_project_requires_permission(
        self, client, logged_in_headers, other_user_headers, active_user
    ):
        """Test that reading a project requires permission."""
        # Create project
        project_data = {
            "name": f"Private Project {uuid4().hex[:8]}",
            "description": "No read access",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Other user tries to read - should fail
        response = await client.get(
            f"/api/v1/projects/{project['id']}", headers=other_user_headers
        )
        assert response.status_code == 403 or response.status_code == 404

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)

    @pytest.mark.asyncio
    async def test_read_project_succeeds_with_permission(
        self, client, logged_in_headers, other_user_headers, other_user, client_session, roles
    ):
        """Test that reading a project succeeds with permission."""
        # Create project
        project_data = {
            "name": f"Readable Project {uuid4().hex[:8]}",
            "description": "Has read access",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give other_user Viewer role
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=UUID(project["id"]),
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Other user reads - should succeed
        response = await client.get(
            f"/api/v1/projects/{project['id']}", headers=other_user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project["id"]

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()


class TestProjectsUpdatePermission:
    """Test that PATCH /api/v1/projects/{project_id} requires Update permission."""

    @pytest.mark.asyncio
    async def test_update_project_requires_permission(
        self, client, logged_in_headers, other_user_headers, other_user, client_session, roles
    ):
        """Test that updating a project requires Update permission."""
        # Create project
        project_data = {
            "name": f"Original Name {uuid4().hex[:8]}",
            "description": "Original description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give other_user Viewer role (no Update permission)
        viewer_role = roles["Viewer"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=viewer_role.id,
            scope_type="Project",
            scope_id=UUID(project["id"]),
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Try to update - should fail
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            f"/api/v1/projects/{project['id']}", json=update_data, headers=other_user_headers
        )
        assert response.status_code == 403

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_update_project_succeeds_with_editor_role(
        self, client, logged_in_headers, other_user_headers, other_user, client_session, roles
    ):
        """Test that updating a project succeeds with Editor role."""
        # Create project
        project_data = {
            "name": f"Original Name {uuid4().hex[:8]}",
            "description": "Original description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give other_user Editor role (has Update permission)
        editor_role = roles["Editor"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=editor_role.id,
            scope_type="Project",
            scope_id=UUID(project["id"]),
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Update - should succeed
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            f"/api/v1/projects/{project['id']}", json=update_data, headers=other_user_headers
        )
        assert response.status_code == 200
        updated_project = response.json()
        assert updated_project["name"] == "Updated Name"

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=other_user_headers)
        await client_session.delete(assignment)
        await client_session.commit()


class TestProjectsDeletePermission:
    """Test that DELETE /api/v1/projects/{project_id} requires Delete permission."""

    @pytest.mark.asyncio
    async def test_delete_project_requires_permission(
        self, client, logged_in_headers, other_user_headers, other_user, client_session, roles
    ):
        """Test that deleting a project requires Delete permission."""
        # Create project
        project_data = {
            "name": f"To Delete {uuid4().hex[:8]}",
            "description": "Description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give other_user Editor role (no Delete permission)
        editor_role = roles["Editor"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=editor_role.id,
            scope_type="Project",
            scope_id=UUID(project["id"]),
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Try to delete - should fail
        response = await client.delete(
            f"/api/v1/projects/{project['id']}", headers=other_user_headers
        )
        assert response.status_code == 403

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_delete_project_succeeds_with_owner_role(
        self, client, logged_in_headers, other_user_headers, other_user, client_session, roles
    ):
        """Test that deleting a project succeeds with Owner role."""
        # Create project
        project_data = {
            "name": f"To Delete {uuid4().hex[:8]}",
            "description": "Description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give other_user Owner role (has Delete permission)
        owner_role = roles["Owner"]
        assignment = UserRoleAssignment(
            user_id=other_user.id,
            role_id=owner_role.id,
            scope_type="Project",
            scope_id=UUID(project["id"]),
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Delete - should succeed
        response = await client.delete(
            f"/api/v1/projects/{project['id']}", headers=other_user_headers
        )
        assert response.status_code == 200 or response.status_code == 204

        # Cleanup
        await client_session.delete(assignment)
        await client_session.commit()


class TestProjectsAdminBypass:
    """Test that Admin users bypass all permission checks for projects."""

    @pytest.mark.asyncio
    async def test_admin_can_read_any_project(
        self, client, logged_in_headers, active_user, client_session, roles
    ):
        """Test that Admin users can read any project."""
        # Create project
        project_data = {
            "name": f"Any Project {uuid4().hex[:8]}",
            "description": "Description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give active_user Admin role
        admin_role = roles["Admin"]
        assignment = UserRoleAssignment(
            user_id=active_user.id,
            role_id=admin_role.id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Admin reads - should succeed
        response = await client.get(
            f"/api/v1/projects/{project['id']}", headers=logged_in_headers
        )
        assert response.status_code == 200

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_admin_can_update_any_project(
        self, client, logged_in_headers, active_user, client_session, roles
    ):
        """Test that Admin users can update any project."""
        # Create project
        project_data = {
            "name": f"Original {uuid4().hex[:8]}",
            "description": "Description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give active_user Admin role
        admin_role = roles["Admin"]
        assignment = UserRoleAssignment(
            user_id=active_user.id,
            role_id=admin_role.id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Admin updates - should succeed
        update_data = {"name": "Updated by Admin"}
        response = await client.patch(
            f"/api/v1/projects/{project['id']}", json=update_data, headers=logged_in_headers
        )
        assert response.status_code == 200

        # Cleanup
        await client.delete(f"/api/v1/projects/{project['id']}", headers=logged_in_headers)
        await client_session.delete(assignment)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_admin_can_delete_any_project(
        self, client, logged_in_headers, active_user, client_session, roles
    ):
        """Test that Admin users can delete any project."""
        # Create project
        project_data = {
            "name": f"To Delete {uuid4().hex[:8]}",
            "description": "Description",
        }
        response = await client.post(
            "/api/v1/projects/", json=project_data, headers=logged_in_headers
        )
        assert response.status_code == 201
        project = response.json()

        # Give active_user Admin role
        admin_role = roles["Admin"]
        assignment = UserRoleAssignment(
            user_id=active_user.id,
            role_id=admin_role.id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
        )
        client_session.add(assignment)
        await client_session.commit()

        # Admin deletes - should succeed
        response = await client.delete(
            f"/api/v1/projects/{project['id']}", headers=logged_in_headers
        )
        assert response.status_code == 200 or response.status_code == 204

        # Cleanup
        await client_session.delete(assignment)
        await client_session.commit()

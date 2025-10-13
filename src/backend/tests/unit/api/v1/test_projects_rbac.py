"""Unit tests for Project (Folder) RBAC Permissions.

Tests Task 4.3 - RBAC Project Endpoints Implementation.

Tests the following RBAC-protected endpoints:
- POST /projects/ (create_project) - project.create permission
- GET /projects/{project_id} (read_project) - project.read permission
- PATCH /projects/{project_id} (update_project) - project.update permission
- DELETE /projects/{project_id} (delete_project) - project.delete permission
- GET /projects/download/{project_id} (download_file) - project.export permission
- POST /projects/upload/ (upload_file) - project.create permission

Each endpoint is tested for:
1. Permission enforcement (user with/without permission)
2. Audit logging (success and denial events)
3. Error handling (403 for no permission, 400 for invalid input)
"""

from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.rbac import AuditLog, Permission, Role, RoleAssignment, RolePermission
from langflow.services.database.models.user import User
from langflow.services.database.models.workspace.model import Workspace
from langflow.services.deps import get_db_service
from sqlmodel import select

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(active_user: User) -> Workspace:
    """Create a test workspace for the active user with membership."""
    from datetime import UTC, datetime

    from langflow.services.database.models.workspace.model import WorkspaceMember

    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name="Test Workspace RBAC",
            slug="test-workspace-rbac",
            description="Workspace for RBAC testing",
            created_by=active_user.id,
        )
        session.add(workspace)
        await session.flush()  # Get workspace.id before creating member

        # Add user as workspace member (owner role)
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=active_user.id,
            role="owner",
            is_active=True,
            joined_at=datetime.now(UTC),
        )
        session.add(member)
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
async def test_project(client: AsyncClient, active_user: User, test_workspace: Workspace) -> Folder:
    """Create a test project/folder for the active user with workspace."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        project = Folder(
            name="Test Project RBAC",
            description="Project for RBAC testing",
            user_id=active_user.id,
            workspace_id=test_workspace.id,  # ✅ Link to workspace
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

    yield project

    # Cleanup
    async with db_manager.with_session() as session:
        project_db = await session.get(Folder, project.id)
        if project_db:
            await session.delete(project_db)
        await session.commit()


@pytest.fixture
async def restricted_user(client: AsyncClient) -> User:
    """Create a user without any RBAC permissions."""
    from langflow.services.auth.utils import get_password_hash

    db_manager = get_db_service()
    user_id = uuid4()

    async with db_manager.with_session() as session:
        user = User(
            id=user_id,
            username=f"restricted_user_{id(client)}",
            password=get_password_hash("testpassword"),
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    yield user

    # Cleanup
    async with db_manager.with_session() as session:
        user_db = await session.get(User, user_id)
        if user_db:
            await session.delete(user_db)
        await session.commit()


@pytest.fixture
async def restricted_user_workspace(restricted_user: User) -> Workspace:
    """Create a workspace for the restricted user with membership."""
    from datetime import UTC, datetime

    from langflow.services.database.models.workspace.model import WorkspaceMember

    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name=f"Restricted User Workspace {id(restricted_user)}",
            slug=f"restricted-workspace-{id(restricted_user)}",
            description="Workspace for restricted user testing",
            created_by=restricted_user.id,
        )
        session.add(workspace)
        await session.flush()  # Get workspace.id before creating member

        # Add user as workspace member (owner role)
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=restricted_user.id,
            role="owner",
            is_active=True,
            joined_at=datetime.now(UTC),
        )
        session.add(member)
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
async def restricted_user_headers(client: AsyncClient, restricted_user: User) -> dict[str, str]:
    """Get authentication headers for the restricted user."""
    login_data = {"username": restricted_user.username, "password": "testpassword"}
    response = await client.post("api/v1/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
async def workspace_create_permission_grant(restricted_user: User, restricted_user_workspace: Workspace) -> None:
    """Grant project.create permission to restricted user in their workspace."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create or get permission
        stmt = select(Permission).where(Permission.name == "project.create")
        permission = (await session.exec(stmt)).first()
        if not permission:
            permission = Permission(
                name="project.create",
                description="Create projects in workspace",
                resource_type="project",  # Fixed: resource_type should be "project" for "project.create"
                action="create",
                display_name="Create Projects",
                scope_level="WORKSPACE",  # But scope_level is still WORKSPACE (permission can be granted at workspace level)
            )
            session.add(permission)
            await session.flush()

        # Create role with permission
        role = Role(
            name=f"workspace_creator_{id(restricted_user)}",
            display_name="Workspace Creator Role",
            description="Role for creating projects",
        )
        session.add(role)
        await session.flush()

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        session.add(role_permission)
        await session.flush()

        # Create role assignment at workspace scope
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=restricted_user.id,
            scope_type="workspace",
            scope_id=restricted_user_workspace.id,  # ✅ Use actual workspace ID
        )
        session.add(assignment)
        await session.commit()

    yield

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(RoleAssignment).where(
            RoleAssignment.user_id == restricted_user.id,
            RoleAssignment.scope_type == "workspace",
        )
        assignments = (await session.exec(stmt)).all()
        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()


@pytest.fixture
async def project_read_permission_grant(test_project: Folder, restricted_user: User) -> None:
    """Grant project.read permission to restricted user on test project."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create or get permission
        stmt = select(Permission).where(Permission.name == "project.read")
        permission = (await session.exec(stmt)).first()
        if not permission:
            permission = Permission(
                name="project.read",
                description="Read/view project",
                resource_type="project",
                action="read",
                display_name="Read Project",
                scope_level="PROJECT",
            )
            session.add(permission)
            await session.flush()

        # Create role with permission
        role = Role(
            name=f"project_reader_{id(test_project)}",
            display_name="Project Reader Role",
            description="Role for reading projects",
        )
        session.add(role)
        await session.flush()

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        session.add(role_permission)
        await session.flush()

        # Create role assignment
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=restricted_user.id,
            scope_type="project",
            scope_id=test_project.id,
        )
        session.add(assignment)
        await session.commit()

    yield

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(RoleAssignment).where(
            RoleAssignment.user_id == restricted_user.id,
            RoleAssignment.scope_type == "project",
            RoleAssignment.scope_id == test_project.id,
        )
        assignments = (await session.exec(stmt)).all()
        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()


@pytest.fixture
async def project_update_permission_grant(test_project: Folder, restricted_user: User) -> None:
    """Grant project.update permission to restricted user on test project."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create or get permission
        stmt = select(Permission).where(Permission.name == "project.update")
        permission = (await session.exec(stmt)).first()
        if not permission:
            permission = Permission(
                name="project.update",
                description="Update/modify project",
                resource_type="project",
                action="update",
                display_name="Update Project",
                scope_level="PROJECT",
            )
            session.add(permission)
            await session.flush()

        # Create role with permission
        role = Role(
            name=f"project_updater_{id(test_project)}",
            display_name="Project Updater Role",
            description="Role for updating projects",
        )
        session.add(role)
        await session.flush()

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        session.add(role_permission)
        await session.flush()

        # Create role assignment
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=restricted_user.id,
            scope_type="project",
            scope_id=test_project.id,
        )
        session.add(assignment)
        await session.commit()

    yield

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(RoleAssignment).where(
            RoleAssignment.user_id == restricted_user.id,
            RoleAssignment.scope_type == "project",
            RoleAssignment.scope_id == test_project.id,
        )
        assignments = (await session.exec(stmt)).all()
        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()


@pytest.fixture
async def project_delete_permission_grant(test_project: Folder, restricted_user: User) -> None:
    """Grant project.delete permission to restricted user on test project."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create or get permission
        stmt = select(Permission).where(Permission.name == "project.delete")
        permission = (await session.exec(stmt)).first()
        if not permission:
            permission = Permission(
                name="project.delete",
                description="Delete project",
                resource_type="project",
                action="delete",
                display_name="Delete Project",
                scope_level="PROJECT",
            )
            session.add(permission)
            await session.flush()

        # Create role with permission
        role = Role(
            name=f"project_deleter_{id(test_project)}",
            display_name="Project Deleter Role",
            description="Role for deleting projects",
        )
        session.add(role)
        await session.flush()

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        session.add(role_permission)
        await session.flush()

        # Create role assignment
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=restricted_user.id,
            scope_type="project",
            scope_id=test_project.id,
        )
        session.add(assignment)
        await session.commit()

    yield

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(RoleAssignment).where(
            RoleAssignment.user_id == restricted_user.id,
            RoleAssignment.scope_type == "project",
            RoleAssignment.scope_id == test_project.id,
        )
        assignments = (await session.exec(stmt)).all()
        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()


@pytest.fixture
async def project_export_permission_grant(test_project: Folder, restricted_user: User) -> None:
    """Grant project.export permission to restricted user on test project."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        # Create or get permission
        stmt = select(Permission).where(Permission.name == "project.export")
        permission = (await session.exec(stmt)).first()
        if not permission:
            permission = Permission(
                name="project.export",
                description="Export/download project",
                resource_type="project",
                action="export",
                display_name="Export Project",
                scope_level="PROJECT",
            )
            session.add(permission)
            await session.flush()

        # Create role with permission
        role = Role(
            name=f"project_exporter_{id(test_project)}",
            display_name="Project Exporter Role",
            description="Role for exporting projects",
        )
        session.add(role)
        await session.flush()

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
        session.add(role_permission)
        await session.flush()

        # Create role assignment
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=restricted_user.id,
            scope_type="project",
            scope_id=test_project.id,
        )
        session.add(assignment)
        await session.commit()

    yield

    # Cleanup
    async with db_manager.with_session() as session:
        stmt = select(RoleAssignment).where(
            RoleAssignment.user_id == restricted_user.id,
            RoleAssignment.scope_type == "project",
            RoleAssignment.scope_id == test_project.id,
        )
        assignments = (await session.exec(stmt)).all()
        for assignment in assignments:
            await session.delete(assignment)
        await session.commit()


# ============================================================================
# CREATE PROJECT RBAC Tests
# ============================================================================


async def test_create_project_with_permission_succeeds(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    restricted_user: User,
    workspace_create_permission_grant: None,
):
    """Test that user with project.create permission can create project."""
    project_data = {
        "name": "Authorized Project",
        "description": "Created by authorized user",
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=restricted_user_headers)

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["name"] == "Authorized Project"
    # Note: user_id is not exposed in FolderRead response model (by design)

    # Verify audit log created
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.created",
            AuditLog.status == "success",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None, "Audit log should be created for successful project creation"
        assert audit_log.resource_type == "project"

    # Cleanup project
    async with db_manager.with_session() as session:
        project_id = UUID(result["id"])
        project = await session.get(Folder, project_id)
        if project:
            await session.delete(project)
        await session.commit()


async def test_create_project_without_permission_denied(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    restricted_user: User,
):
    """Test that user without project.create permission cannot create project."""
    project_data = {
        "name": "Unauthorized Project",
        "description": "Should be denied",
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=restricted_user_headers)

    assert response.status_code == 403, response.text
    assert "insufficient permissions" in response.text.lower()
    assert "project.create" in response.text.lower()

    # Verify denial audit log created
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.create_denied",
            AuditLog.status == "denied",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None, "Audit log should be created for denied project creation"
        assert "insufficient_permissions" in str(audit_log.details)


async def test_create_project_superuser_bypass(
    client: AsyncClient,
    logged_in_headers_super_user: dict[str, str],
):
    """Test that superuser can create project without explicit permission."""
    project_data = {
        "name": "Superuser Project",
        "description": "Created by superuser",
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers_super_user)

    assert response.status_code == 201, response.text
    result = response.json()
    assert result["name"] == "Superuser Project"

    # Cleanup
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        project_id = UUID(result["id"])
        project = await session.get(Folder, project_id)
        if project:
            await session.delete(project)
        await session.commit()


# ============================================================================
# READ PROJECT RBAC Tests
# ============================================================================


async def test_read_project_with_permission_succeeds(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
    project_read_permission_grant: None,
):
    """Test that user with project.read permission can read project."""
    response = await client.get(f"api/v1/projects/{test_project.id}", headers=restricted_user_headers)

    assert response.status_code == 200, response.text
    result = response.json()
    # Check if it's a folder or paginated response
    if "folder" in result:
        assert result["folder"]["id"] == str(test_project.id)
    else:
        assert result["id"] == str(test_project.id)


async def test_read_project_without_permission_denied(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
):
    """Test that user without project.read permission cannot read project."""
    response = await client.get(f"api/v1/projects/{test_project.id}", headers=restricted_user_headers)

    assert response.status_code == 403, response.text
    assert "insufficient permissions" in response.text.lower()
    assert "project.read" in response.text.lower()


# ============================================================================
# UPDATE PROJECT RBAC Tests
# ============================================================================


async def test_update_project_with_permission_succeeds(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
    project_update_permission_grant: None,
):
    """Test that user with project.update permission can update project."""
    update_data = {
        "name": "Updated Project Name",
    }

    response = await client.patch(
        f"api/v1/projects/{test_project.id}", json=update_data, headers=restricted_user_headers
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["name"] == "Updated Project Name"

    # Verify audit log created
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.updated",
            AuditLog.status == "success",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None, "Audit log should be created for successful project update"


async def test_update_project_without_permission_denied(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
):
    """Test that user without project.update permission cannot update project."""
    update_data = {
        "name": "Should Not Update",
    }

    response = await client.patch(
        f"api/v1/projects/{test_project.id}", json=update_data, headers=restricted_user_headers
    )

    assert response.status_code == 403, response.text
    assert "insufficient permissions" in response.text.lower()
    assert "project.update" in response.text.lower()


# ============================================================================
# DELETE PROJECT RBAC Tests
# ============================================================================


async def test_delete_project_with_permission_succeeds(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    restricted_user: User,
    restricted_user_workspace: Workspace,
    project_delete_permission_grant: None,
):
    """Test that user with project.delete permission can delete project."""
    # Create a project to delete
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        project = Folder(
            name="Project To Delete",
            user_id=restricted_user.id,
            workspace_id=restricted_user_workspace.id,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        project_id = project.id

    # Grant delete permission on this specific project
    async with db_manager.with_session() as session:
        stmt = select(Permission).where(Permission.name == "project.delete")
        permission = (await session.exec(stmt)).first()

        stmt_role = select(Role).where(Role.name == f"project_deleter_{id(project)}")
        role = (await session.exec(stmt_role)).first()
        if not role:
            role = Role(
                name=f"project_deleter_{id(project)}",
                display_name="Delete Test Role",
                description="For delete test",
            )
            session.add(role)
            await session.flush()

            if permission:
                role_permission = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                session.add(role_permission)
                await session.flush()

            assignment = RoleAssignment(
                role_id=role.id,
                assignee_type="user",
                user_id=restricted_user.id,
                scope_type="project",
                scope_id=project_id,
            )
            session.add(assignment)
            await session.commit()

    response = await client.delete(f"api/v1/projects/{project_id}", headers=restricted_user_headers)

    assert response.status_code == 204, response.text

    # Verify audit log created
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.deleted",
            AuditLog.status == "success",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None, "Audit log should be created for successful project deletion"


async def test_delete_project_without_permission_denied(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
):
    """Test that user without project.delete permission cannot delete project."""
    response = await client.delete(f"api/v1/projects/{test_project.id}", headers=restricted_user_headers)

    assert response.status_code == 403, response.text
    assert "insufficient permissions" in response.text.lower()
    assert "project.delete" in response.text.lower()


# ============================================================================
# DOWNLOAD/EXPORT PROJECT RBAC Tests
# ============================================================================


async def test_download_project_with_permission_succeeds(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
    project_export_permission_grant: None,
):
    """Test that user with project.export permission can download project."""
    response = await client.get(f"api/v1/projects/download/{test_project.id}", headers=restricted_user_headers)

    # Should get file download (200) or error if no flows (404)
    assert response.status_code in (200, 404), response.text

    if response.status_code == 200:
        # Verify audit log
        db_manager = get_db_service()
        async with db_manager.with_session() as session:
            stmt = select(AuditLog).where(
                AuditLog.actor_id == restricted_user.id,
                AuditLog.action == "project.downloaded",
                AuditLog.status == "success",
            )
            audit_log = (await session.exec(stmt)).first()
            assert audit_log is not None, "Audit log should be created for successful download"


async def test_download_project_without_permission_denied(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    test_project: Folder,
    restricted_user: User,
):
    """Test that user without project.export permission cannot download project."""
    response = await client.get(f"api/v1/projects/download/{test_project.id}", headers=restricted_user_headers)

    assert response.status_code == 403, response.text
    assert "insufficient permissions" in response.text.lower()


# ============================================================================
# UPLOAD PROJECT RBAC Tests
# ============================================================================


async def test_upload_project_with_permission_succeeds(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    restricted_user: User,
    workspace_create_permission_grant: None,
):
    """Test that user with project.create permission can upload project."""
    # Create a simple project file content
    import json

    project_content = {
        "folder_name": "Uploaded Project",
        "folder_description": "Uploaded via test",
        "flows": [
            {
                "name": "Test Flow",
                "description": "Flow in uploaded project",
                "data": {},
            }
        ],
    }

    files = {"file": ("test_project.json", json.dumps(project_content), "application/json")}

    response = await client.post("api/v1/projects/upload/", files=files, headers=restricted_user_headers)

    assert response.status_code == 201, response.text
    result = response.json()
    assert len(result) > 0, "Should create flows from upload"

    # Verify audit log created
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.uploaded",
            AuditLog.status == "success",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None, "Audit log should be created for successful project upload"

        # Cleanup - find and delete uploaded project
        stmt_folder = select(Folder).where(Folder.name == "Uploaded Project", Folder.user_id == restricted_user.id)
        folder = (await session.exec(stmt_folder)).first()
        if folder:
            await session.delete(folder)
            await session.commit()


async def test_upload_project_without_permission_denied(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    restricted_user: User,
):
    """Test that user without project.create permission cannot upload project."""
    import json

    project_content = {
        "folder_name": "Should Not Upload",
        "folder_description": "Should be denied",
        "flows": [],
    }

    files = {"file": ("test_project.json", json.dumps(project_content), "application/json")}

    response = await client.post("api/v1/projects/upload/", files=files, headers=restricted_user_headers)

    assert response.status_code == 403, response.text
    assert "insufficient permissions" in response.text.lower()
    assert "project.create" in response.text.lower()

    # Verify denial audit log created
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.upload_denied",
            AuditLog.status == "denied",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None, "Audit log should be created for denied project upload"


# ============================================================================
# ERROR HANDLING Tests
# ============================================================================


async def test_read_project_invalid_uuid_returns_400(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
):
    """Test that invalid project_id format returns 400 Bad Request."""
    response = await client.get("api/v1/projects/not-a-valid-uuid", headers=restricted_user_headers)

    # Should get 422 (validation error) or 404, not 403
    assert response.status_code in (400, 404, 422), "Invalid UUID should trigger validation error"


async def test_update_project_nonexistent_returns_404(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
):
    """Test that updating nonexistent project returns 404."""
    fake_uuid = uuid4()
    update_data = {"name": "Does Not Exist"}

    response = await client.patch(f"api/v1/projects/{fake_uuid}", json=update_data, headers=restricted_user_headers)

    # Should get 404 (not found), could also get 403 if RBAC checks first
    assert response.status_code in (403, 404), "Nonexistent project should return 404 or 403"


# ============================================================================
# AUDIT LOGGING Tests
# ============================================================================


async def test_audit_log_includes_action_and_resource_type(
    client: AsyncClient,
    restricted_user_headers: dict[str, str],
    restricted_user: User,
):
    """Test that 403 error includes action and resource type in audit log."""
    project_data = {
        "name": "Test Audit Project",
        "description": "For audit logging test",
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=restricted_user_headers)

    assert response.status_code == 403

    # Verify audit log has complete information
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(AuditLog).where(
            AuditLog.actor_id == restricted_user.id,
            AuditLog.action == "project.create_denied",
        )
        audit_log = (await session.exec(stmt)).first()
        assert audit_log is not None
        assert audit_log.resource_type == "project"
        assert audit_log.status == "denied"
        assert "project_name" in str(audit_log.details)
        assert "insufficient_permissions" in str(audit_log.details)

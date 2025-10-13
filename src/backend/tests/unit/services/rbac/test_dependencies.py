"""Unit tests for RBAC FastAPI dependencies.

Tests cover:
- require_permission dependency functionality
- Convenience decorators (require_read, require_update, require_delete, etc.)
- Path parameter extraction
- UUID validation
- Permission checking integration
- Error handling (400, 403)
- Success cases
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Request
from langflow.services.database.models.flow import Flow
from langflow.services.database.models.folder import Folder
from langflow.services.database.models.rbac import Permission, Role, RoleAssignment, RolePermission
from langflow.services.database.models.user import User
from langflow.services.database.models.workspace import Workspace
from langflow.services.rbac.cache import reset_permission_cache
from langflow.services.rbac.dependencies import (
    require_create,
    require_delete,
    require_deploy,
    require_execute,
    require_export,
    require_permission,
    require_read,
    require_update,
)


@pytest.fixture
async def workspace(async_session):
    """Create a test workspace."""
    workspace = Workspace(
        name="Test Workspace",
        slug="test-workspace",
        description="Test workspace for dependency tests",
        created_by=uuid4(),  # Required field
    )
    async_session.add(workspace)
    await async_session.commit()
    await async_session.refresh(workspace)
    return workspace


@pytest.fixture
async def user(async_session):
    """Create a test user."""
    user = User(
        username="testuser",
        password="hashed_password",  # noqa: S106 - Test fixture, not a real password
        is_active=True,
        is_superuser=False,
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def project(async_session, workspace):
    """Create a test project (folder)."""
    project = Folder(
        name="Test Project",
        user_id=uuid4(),  # Placeholder user
        workspace_id=workspace.id,
    )
    async_session.add(project)
    await async_session.commit()
    await async_session.refresh(project)
    return project


@pytest.fixture
async def flow(async_session, project):
    """Create a test flow."""
    flow = Flow(
        name="Test Flow",
        data={},
        folder_id=project.id,
        user_id=uuid4(),  # Placeholder user
    )
    async_session.add(flow)
    await async_session.commit()
    await async_session.refresh(flow)
    return flow


@pytest.fixture
async def flow_read_permission(async_session):
    """Create flow.read permission."""
    permission = Permission(
        name="flow.read",
        resource_type="flow",
        action="read",
        display_name="Read Flow",
        description="Permission to read flows",
        scope_level="FLOW",
    )
    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)
    return permission


@pytest.fixture
async def flow_update_permission(async_session):
    """Create flow.update permission."""
    permission = Permission(
        name="flow.update",
        resource_type="flow",
        action="update",
        display_name="Update Flow",
        description="Permission to update flows",
        scope_level="FLOW",
    )
    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)
    return permission


@pytest.fixture
async def flow_delete_permission(async_session):
    """Create flow.delete permission."""
    permission = Permission(
        name="flow.delete",
        resource_type="flow",
        action="delete",
        display_name="Delete Flow",
        description="Permission to delete flows",
        scope_level="FLOW",
    )
    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)
    return permission


@pytest.fixture
async def flow_export_permission(async_session):
    """Create flow.export permission."""
    permission = Permission(
        name="flow.export",
        resource_type="flow",
        action="export",
        display_name="Export Flow",
        description="Permission to export flows",
        scope_level="FLOW",
    )
    async_session.add(permission)
    await async_session.commit()
    await async_session.refresh(permission)
    return permission


@pytest.fixture
async def role_with_read(async_session, flow_read_permission):
    """Create a role with flow.read permission."""
    role = Role(
        name="reader",
        display_name="Reader",
        description="Read-only role",
    )
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    role_permission = RolePermission(
        role_id=role.id,
        permission_id=flow_read_permission.id,
    )
    async_session.add(role_permission)
    await async_session.commit()

    return role


@pytest.fixture
async def role_with_update(async_session, flow_update_permission):
    """Create a role with flow.update permission."""
    role = Role(
        name="editor",
        display_name="Editor",
        description="Editor role",
    )
    async_session.add(role)
    await async_session.commit()
    await async_session.refresh(role)

    role_permission = RolePermission(
        role_id=role.id,
        permission_id=flow_update_permission.id,
    )
    async_session.add(role_permission)
    await async_session.commit()

    return role


def create_mock_request(path_params: dict):
    """Create a mock FastAPI Request with path params."""
    request = MagicMock(spec=Request)
    request.path_params = path_params
    return request


class TestRequirePermission:
    """Test suite for require_permission dependency."""

    @pytest.mark.asyncio
    async def test_permission_granted_returns_none(
        self,
        async_session,
        user,
        flow,
        role_with_read,
    ):
        """Test dependency returns None when permission granted."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency
        dep = require_permission("flow.read", "flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_permission_denied_raises_403(
        self,
        async_session,
        user,
        flow,
    ):
        """Test dependency raises 403 when permission denied."""
        # Clear cache
        reset_permission_cache()

        # No role assigned - user has no permissions

        # Create dependency
        dep = require_permission("flow.read", "flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency - should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=request, current_user=user, db=async_session)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail
        assert "flow.read" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_missing_resource_id_param_raises_400(
        self,
        async_session,
        user,
    ):
        """Test dependency raises 400 when resource ID param is missing."""
        # Create dependency expecting "flow_id" param
        dep = require_permission("flow.read", "flow", "flow_id")

        # Create request with different param name
        request = create_mock_request({"id": str(uuid4())})

        # Call dependency - should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=request, current_user=user, db=async_session)

        assert exc_info.value.status_code == 400
        assert "Missing resource ID parameter" in exc_info.value.detail
        assert "flow_id" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_uuid_format_raises_400(
        self,
        async_session,
        user,
    ):
        """Test dependency raises 400 when resource ID is not valid UUID."""
        # Create dependency
        dep = require_permission("flow.read", "flow", "flow_id")

        # Create request with invalid UUID
        request = create_mock_request({"flow_id": "not-a-uuid"})

        # Call dependency - should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=request, current_user=user, db=async_session)

        assert exc_info.value.status_code == 400
        assert "Invalid UUID format" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_permission_checked_with_correct_params(
        self,
        async_session,
        user,
        flow,
        role_with_update,
    ):
        """Test dependency calls RBAC engine with correct parameters."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_update.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency
        dep = require_permission("flow.update", "flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None


class TestConvenienceDecorators:
    """Test suite for convenience decorator functions."""

    @pytest.mark.asyncio
    async def test_require_read(
        self,
        async_session,
        user,
        flow,
        role_with_read,
    ):
        """Test require_read convenience decorator."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        dep = require_read("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_update(
        self,
        async_session,
        user,
        flow,
        role_with_update,
    ):
        """Test require_update convenience decorator."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_update.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        dep = require_update("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_delete(
        self,
        async_session,
        user,
        flow,
        flow_delete_permission,
    ):
        """Test require_delete convenience decorator."""
        # Clear cache
        reset_permission_cache()

        # Create role with delete permission
        role = Role(name="deleter", display_name="Deleter")
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=flow_delete_permission.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        dep = require_delete("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_export(
        self,
        async_session,
        user,
        flow,
        flow_export_permission,
    ):
        """Test require_export convenience decorator (PRD Story 1.1 @AC3)."""
        # Clear cache
        reset_permission_cache()

        # Create role with export permission
        role = Role(name="exporter", display_name="Exporter")
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=flow_export_permission.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        dep = require_export("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_create(
        self,
        async_session,
        user,
        project,
    ):
        """Test require_create convenience decorator.

        Note: For create permissions, we check permission on the parent resource
        (project in this case), not on the resource being created (flow).
        """
        # Clear cache
        reset_permission_cache()

        # Create permission - use project resource type since we're checking on parent
        create_perm = Permission(
            name="project.create",
            resource_type="project",
            action="create",
            display_name="Create in Project",
            description="Permission to create items in project",
            scope_level="PROJECT",
        )
        async_session.add(create_perm)
        await async_session.commit()
        await async_session.refresh(create_perm)

        # Create role with create permission
        role = Role(name="creator", display_name="Creator")
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=create_perm.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

        # Assign role to user at project scope
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="project",
            scope_id=project.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        # Check project.create permission on the project resource
        dep = require_create("project", "project_id")

        # Create mock request
        request = create_mock_request({"project_id": str(project.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_execute(
        self,
        async_session,
        user,
        flow,
    ):
        """Test require_execute convenience decorator."""
        # Clear cache
        reset_permission_cache()

        # Create execute permission
        execute_perm = Permission(
            name="flow.execute",
            resource_type="flow",
            action="execute",
            display_name="Execute Flow",
            description="Permission to execute flows",
            scope_level="FLOW",
        )
        async_session.add(execute_perm)
        await async_session.commit()
        await async_session.refresh(execute_perm)

        # Create role with execute permission
        role = Role(name="executor", display_name="Executor")
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=execute_perm.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        dep = require_execute("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_require_deploy(
        self,
        async_session,
        user,
        flow,
    ):
        """Test require_deploy convenience decorator."""
        # Clear cache
        reset_permission_cache()

        # Create deploy permission
        deploy_perm = Permission(
            name="flow.deploy",
            resource_type="flow",
            action="deploy",
            display_name="Deploy Flow",
            description="Permission to deploy flows",
            scope_level="FLOW",
        )
        async_session.add(deploy_perm)
        await async_session.commit()
        await async_session.refresh(deploy_perm)

        # Create role with deploy permission
        role = Role(name="deployer", display_name="Deployer")
        async_session.add(role)
        await async_session.commit()
        await async_session.refresh(role)

        role_permission = RolePermission(
            role_id=role.id,
            permission_id=deploy_perm.id,
        )
        async_session.add(role_permission)
        await async_session.commit()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency using convenience function
        dep = require_deploy("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None


class TestCustomResourceIdParam:
    """Test suite for custom resource_id_param handling."""

    @pytest.mark.asyncio
    async def test_custom_param_name(
        self,
        async_session,
        user,
        flow,
        role_with_read,
    ):
        """Test dependency with custom resource ID parameter name."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency with custom param name
        dep = require_permission("flow.read", "flow", "my_flow_id")

        # Create mock request with custom param
        request = create_mock_request({"my_flow_id": str(flow.id)})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None

    @pytest.mark.asyncio
    async def test_uuid_object_in_path_params(
        self,
        async_session,
        user,
        flow,
        role_with_read,
    ):
        """Test dependency handles UUID object in path params (not just string)."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency
        dep = require_permission("flow.read", "flow", "flow_id")

        # Create mock request with UUID object (not string)
        request = create_mock_request({"flow_id": flow.id})

        # Call dependency
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted)
        assert result is None


class TestIntegrationWithRBACEngine:
    """Test suite for integration with RBAC enforcement engine."""

    @pytest.mark.asyncio
    async def test_permission_inheritance_from_workspace(
        self,
        async_session,
        user,
        flow,
        workspace,
        role_with_read,
    ):
        """Test dependency respects permission inheritance from workspace."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user at workspace scope (should inherit to flow)
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency for flow
        dep = require_read("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency - should succeed due to inheritance
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted via inheritance)
        assert result is None

    @pytest.mark.asyncio
    async def test_group_based_permissions(
        self,
        async_session,
        user,
        flow,
        workspace,
        role_with_read,
    ):
        """Test dependency works with group-based role assignments."""
        from langflow.services.database.models.user_group import UserGroup, UserGroupMember

        # Clear cache
        reset_permission_cache()

        # Create user group
        group = UserGroup(
            workspace_id=workspace.id,
            name="test_group",
            description="Test group",
        )
        async_session.add(group)
        await async_session.commit()
        await async_session.refresh(group)

        # Add user to group
        membership = UserGroupMember(
            group_id=group.id,
            user_id=user.id,
            is_active=True,
        )
        async_session.add(membership)
        await async_session.commit()

        # Assign role to group at workspace scope
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="group",
            group_id=group.id,
            scope_type="workspace",
            scope_id=workspace.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency for flow
        dep = require_read("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency - should succeed due to group membership
        result = await dep(request=request, current_user=user, db=async_session)

        # Should return None (permission granted via group)
        assert result is None

    @pytest.mark.asyncio
    async def test_caching_behavior(
        self,
        async_session,
        user,
        flow,
        role_with_read,
    ):
        """Test dependency leverages permission caching."""
        # Clear cache
        reset_permission_cache()

        # Assign role to user
        assignment = RoleAssignment(
            role_id=role_with_read.id,
            assignee_type="user",
            user_id=user.id,
            scope_type="flow",
            scope_id=flow.id,
        )
        async_session.add(assignment)
        await async_session.commit()

        # Create dependency
        dep = require_read("flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # First call - should hit database
        result1 = await dep(request=request, current_user=user, db=async_session)
        assert result1 is None

        # Second call - should hit cache
        result2 = await dep(request=request, current_user=user, db=async_session)
        assert result2 is None


class TestErrorMessages:
    """Test suite for error message content."""

    @pytest.mark.asyncio
    async def test_403_error_includes_action_and_resource_type(
        self,
        async_session,
        user,
        flow,
    ):
        """Test 403 error message includes action and resource type."""
        # Clear cache
        reset_permission_cache()

        # No role assigned

        # Create dependency
        dep = require_permission("flow.update", "flow", "flow_id")

        # Create mock request
        request = create_mock_request({"flow_id": str(flow.id)})

        # Call dependency - should raise 403
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=request, current_user=user, db=async_session)

        assert exc_info.value.status_code == 403
        assert "flow.update" in exc_info.value.detail
        assert "flow" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_400_error_includes_param_name(
        self,
        async_session,
        user,
    ):
        """Test 400 error message includes missing parameter name."""
        # Create dependency
        dep = require_permission("flow.read", "flow", "my_custom_param")

        # Create request without the required param
        request = create_mock_request({"different_param": "value"})

        # Call dependency - should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await dep(request=request, current_user=user, db=async_session)

        assert exc_info.value.status_code == 400
        assert "my_custom_param" in exc_info.value.detail

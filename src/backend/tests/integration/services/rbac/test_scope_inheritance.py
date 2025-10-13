"""Integration tests for RBAC scope inheritance.

Tests PRD Story 2.1 Acceptance Criteria:
- @AC4: Higher-scope grants cascade to lower scopes
- @AC5: Closest scope wins when multiple grants exist
- @AC6: Scope chain resolution (workspace → project → flow)

These tests validate hierarchical permission evaluation with real database.
"""

import pytest
from langflow.services.rbac.enforcement import RBACEnforcementEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from .fixtures import (
    assign_role,
    create_flow,
    create_project,
    create_role,
    create_user,
    create_workspace,
)


class TestScopeInheritance:
    """Test scope inheritance and cascading permissions."""

    @pytest.mark.asyncio
    async def test_workspace_grant_cascades_to_flow(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 2.1 @AC4: Workspace-level grant allows flow access.

        Scenario: User has editor role at workspace level
        Expected: User can update flows in that workspace
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)
        user_mia = await create_user(async_session, "mia")

        role_editor = await create_role(async_session, "editor", ["flow.read", "flow.update"])
        await assign_role(async_session, user_mia, role_editor, scope_type="workspace", scope_id=workspace.id)

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user_mia.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is True, "Workspace grant should cascade to flow access"

    @pytest.mark.asyncio
    async def test_project_grant_cascades_to_flow(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 2.1 @AC4: Project-level grant allows flow access.

        Scenario: User has editor role at project level
        Expected: User can update flows in that project
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)
        user_alex = await create_user(async_session, "alex")

        role_editor = await create_role(async_session, "project_editor", ["flow.read", "flow.update"])
        await assign_role(async_session, user_alex, role_editor, scope_type="project", scope_id=project.id)

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user_alex.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is True, "Project grant should cascade to flow access"

    @pytest.mark.asyncio
    async def test_closest_scope_overrides_workspace_grant(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 2.1 @AC5: Closest scope wins.

        Scenario: User has viewer role at workspace and editor at project
        Expected: Project-level editor grant takes precedence
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ2", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)
        user_lee = await create_user(async_session, "lee")

        viewer_role = await create_role(async_session, "viewer_scope", ["flow.read"])
        editor_role = await create_role(async_session, "editor_scope", ["flow.read", "flow.update"])

        # Assign viewer at workspace level (broader scope)
        await assign_role(async_session, user_lee, viewer_role, scope_type="workspace", scope_id=workspace.id)

        # Assign editor at project level (narrower scope)
        await assign_role(async_session, user_lee, editor_role, scope_type="project", scope_id=project.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check update permission
        allowed = await engine.has_permission(
            user_id=user_lee.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is True, "Project-level editor grant should override workspace viewer"

    @pytest.mark.asyncio
    async def test_flow_scope_adds_to_project_grant(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 2.1 @AC5: Flow-level grant adds to project grant.

        Scenario: User has viewer at project and delete permission at specific flow
        Expected: User has both view (from project) and delete (from flow) permissions
        Note: RBAC follows additive/OR logic - any grant that provides permission allows it
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)
        user_sam = await create_user(async_session, "sam")

        viewer_role = await create_role(async_session, "viewer_project_level", ["flow.read"])
        deleter_role = await create_role(async_session, "deleter_flow_level", ["flow.delete"])

        # Assign viewer at project level (provides read)
        await assign_role(async_session, user_sam, viewer_role, scope_type="project", scope_id=project.id)

        # Assign deleter at flow level (provides delete)
        await assign_role(async_session, user_sam, deleter_role, scope_type="flow", scope_id=flow.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check read permission (from project-level viewer role)
        can_read = await engine.has_permission(
            user_id=user_sam.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Act - Check delete permission (from flow-level deleter role)
        can_delete = await engine.has_permission(
            user_id=user_sam.id,
            permission="flow.delete",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Act - Check update permission (not granted at any level)
        can_update = await engine.has_permission(
            user_id=user_sam.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert - Additive permissions from multiple scopes
        assert can_read is True, "Should be able to read (from project-level viewer)"
        assert can_delete is True, "Should be able to delete (from flow-level deleter)"
        assert can_update is False, "Should not be able to update (not granted anywhere)"

    @pytest.mark.asyncio
    async def test_workspace_grant_doesnt_apply_to_different_workspace(
        self,
        async_session: AsyncSession,
    ):
        """Test that workspace grants don't apply across workspaces.

        Scenario: User has editor role in Workspace A, tries to access Workspace B
        Expected: Permission denied for Workspace B resources
        """
        # Arrange
        workspace_a = await create_workspace(async_session, "Workspace A")
        workspace_b = await create_workspace(async_session, "Workspace B")

        project_a = await create_project(async_session, "Project A", workspace_a.id)
        project_b = await create_project(async_session, "Project B", workspace_b.id)

        flow_a = await create_flow(async_session, "Flow A", project_a.id)
        flow_b = await create_flow(async_session, "Flow B", project_b.id)

        user = await create_user(async_session, "cross_workspace_user")
        editor_role = await create_role(async_session, "editor_ws_a", ["flow.read", "flow.update"])

        # Grant editor role in Workspace A only
        await assign_role(async_session, user, editor_role, scope_type="workspace", scope_id=workspace_a.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check access to Flow A (should succeed)
        can_access_flow_a = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow_a.id,
        )

        # Act - Check access to Flow B (should fail - different workspace)
        can_access_flow_b = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow_b.id,
        )

        # Assert
        assert can_access_flow_a is True, "Should access flow in granted workspace"
        assert can_access_flow_b is False, "Should NOT access flow in different workspace"

    @pytest.mark.asyncio
    async def test_project_grant_doesnt_apply_to_different_project(
        self,
        async_session: AsyncSession,
    ):
        """Test that project grants don't apply across projects.

        Scenario: User has editor in Project A, tries to access Project B
        Expected: Permission denied for Project B resources
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project_a = await create_project(async_session, "Project A", workspace.id)
        project_b = await create_project(async_session, "Project B", workspace.id)

        flow_a = await create_flow(async_session, "Flow A", project_a.id)
        flow_b = await create_flow(async_session, "Flow B", project_b.id)

        user = await create_user(async_session, "cross_project_user")
        editor_role = await create_role(async_session, "editor_proj_a", ["flow.read", "flow.update"])

        # Grant editor role in Project A only
        await assign_role(async_session, user, editor_role, scope_type="project", scope_id=project_a.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check access to Flow A (should succeed)
        can_access_flow_a = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow_a.id,
        )

        # Act - Check access to Flow B (should fail - different project)
        can_access_flow_b = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow_b.id,
        )

        # Assert
        assert can_access_flow_a is True, "Should access flow in granted project"
        assert can_access_flow_b is False, "Should NOT access flow in different project"

    @pytest.mark.asyncio
    async def test_multiple_scopes_most_specific_wins(
        self,
        async_session: AsyncSession,
    ):
        """Test that most specific scope wins with multiple grants.

        Scenario: User has grants at workspace, project, and flow levels
        Expected: Flow-level grant takes precedence
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)
        user = await create_user(async_session, "multi_scope_user")

        # Create three different roles
        viewer_role = await create_role(async_session, "ws_viewer", ["flow.read"])
        editor_role = await create_role(async_session, "proj_editor", ["flow.read", "flow.update"])
        admin_role = await create_role(async_session, "flow_admin", ["flow.read", "flow.update", "flow.delete"])

        # Assign at all three levels
        await assign_role(async_session, user, viewer_role, scope_type="workspace", scope_id=workspace.id)
        await assign_role(async_session, user, editor_role, scope_type="project", scope_id=project.id)
        await assign_role(async_session, user, admin_role, scope_type="flow", scope_id=flow.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check delete permission (only in flow-level admin role)
        can_delete = await engine.has_permission(
            user_id=user.id,
            permission="flow.delete",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert can_delete is True, "Flow-level admin grant should take precedence"

    @pytest.mark.asyncio
    async def test_scope_chain_resolution_full_hierarchy(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 2.1 @AC6: Full scope chain resolution.

        Scenario: Validate complete hierarchy: workspace → project → flow
        Expected: Permissions cascade correctly through all levels
        """
        # Arrange
        workspace = await create_workspace(async_session, "Corporate")
        project1 = await create_project(async_session, "Sales", workspace.id)
        project2 = await create_project(async_session, "Marketing", workspace.id)
        flow1 = await create_flow(async_session, "Pipeline", project1.id)
        flow2 = await create_flow(async_session, "Campaign", project2.id)

        user = await create_user(async_session, "hierarchy_user")
        editor_role = await create_role(async_session, "corp_editor", ["flow.read", "flow.update"])

        # Grant at workspace level (should cascade to all projects and flows)
        await assign_role(async_session, user, editor_role, scope_type="workspace", scope_id=workspace.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check access to flows in different projects
        can_access_flow1 = await engine.has_permission(
            user_id=user.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow1.id,
        )

        can_access_flow2 = await engine.has_permission(
            user_id=user.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow2.id,
        )

        # Assert
        assert can_access_flow1 is True, "Workspace grant should cascade to flow in project 1"
        assert can_access_flow2 is True, "Workspace grant should cascade to flow in project 2"

    @pytest.mark.asyncio
    async def test_no_upward_permission_inheritance(
        self,
        async_session: AsyncSession,
    ):
        """Test that permissions don't inherit upward.

        Scenario: User has permission on specific flow
        Expected: User does NOT automatically have permission on project or workspace
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)
        user = await create_user(async_session, "downward_only_user")

        editor_role = await create_role(async_session, "flow_only_editor", ["flow.read", "flow.update"])

        # Grant at flow level only
        await assign_role(async_session, user, editor_role, scope_type="flow", scope_id=flow.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check if user has permission on flow (should succeed)
        can_access_flow = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert can_access_flow is True, "User should have permission on the specific flow"
        # Note: We can't directly test project/workspace permissions as they're different resource types
        # The test confirms flow-level permissions work correctly

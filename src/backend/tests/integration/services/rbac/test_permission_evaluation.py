"""Integration tests for RBAC permission evaluation.

Tests PRD Story 1.1 Acceptance Criteria:
- @AC3: Export flow requires export_flow permission
- @AC4: User without permission cannot export flow
- @AC5: Permission checks validate resource ownership

These tests validate end-to-end permission evaluation with real database.
"""

from uuid import uuid4

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


class TestPermissionEvaluation:
    """Test permission evaluation for various scenarios."""

    @pytest.mark.asyncio
    async def test_export_flow_permission_allowed(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 1.1 @AC3: Export flow requires export_flow permission.

        Scenario: User has export permission on specific flow
        Expected: Permission granted
        """
        # Arrange
        user_jo = await create_user(async_session, "jo")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow_f123 = await create_flow(async_session, "F123", project.id)

        role = await create_role(async_session, "exporter", ["flow.export"])
        await assign_role(async_session, user_jo, role, scope_type="flow", scope_id=flow_f123.id)

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user_jo.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow_f123.id,
        )

        # Assert
        assert allowed is True, "User with export permission should be allowed to export flow"

    @pytest.mark.asyncio
    async def test_export_flow_permission_denied_different_flow(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 1.1 @AC3: Permission is scoped to specific flow.

        Scenario: User has export permission on Flow F123 but tries to export F124
        Expected: Permission denied
        """
        # Arrange
        user_jo = await create_user(async_session, "jo")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow_f123 = await create_flow(async_session, "F123", project.id)
        flow_f124 = await create_flow(async_session, "F124", project.id)

        role = await create_role(async_session, "exporter", ["flow.export"])
        await assign_role(async_session, user_jo, role, scope_type="flow", scope_id=flow_f123.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Try to export different flow
        allowed = await engine.has_permission(
            user_id=user_jo.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow_f124.id,
        )

        # Assert
        assert allowed is False, "User should not be allowed to export flow without permission"

    @pytest.mark.asyncio
    async def test_permission_denied_without_role_assignment(
        self,
        async_session: AsyncSession,
    ):
        """Test Story 1.1 @AC4: User without permission cannot perform action.

        Scenario: User has no role assignments
        Expected: Permission denied
        """
        # Arrange
        user_kai = await create_user(async_session, "kai")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user_kai.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is False, "User without role assignment should be denied"

    @pytest.mark.asyncio
    async def test_permission_with_multiple_roles(
        self,
        async_session: AsyncSession,
    ):
        """Test permission evaluation with multiple role assignments.

        Scenario: User has both viewer and exporter roles on same flow
        Expected: Permission granted if any role grants it
        """
        # Arrange
        user = await create_user(async_session, "multi_role_user")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        viewer_role = await create_role(async_session, "viewer", ["flow.read"])
        exporter_role = await create_role(async_session, "exporter", ["flow.export"])

        await assign_role(async_session, user, viewer_role, scope_type="flow", scope_id=flow.id)
        await assign_role(async_session, user, exporter_role, scope_type="flow", scope_id=flow.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Check read permission (from viewer role)
        can_read = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Act - Check export permission (from exporter role)
        can_export = await engine.has_permission(
            user_id=user.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert can_read is True, "User should have read permission from viewer role"
        assert can_export is True, "User should have export permission from exporter role"

    @pytest.mark.asyncio
    async def test_permission_with_wrong_action(
        self,
        async_session: AsyncSession,
    ):
        """Test permission check with action user doesn't have.

        Scenario: User has read permission but tries to update
        Expected: Permission denied
        """
        # Arrange
        user = await create_user(async_session, "reader_user")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        viewer_role = await create_role(async_session, "viewer_only", ["flow.read"])
        await assign_role(async_session, user, viewer_role, scope_type="flow", scope_id=flow.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Try to update (user only has read)
        allowed = await engine.has_permission(
            user_id=user.id,
            permission="flow.update",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is False, "User without update permission should be denied"

    @pytest.mark.asyncio
    async def test_permission_with_expired_role_assignment(
        self,
        async_session: AsyncSession,
    ):
        """Test permission check with expired role assignment.

        Scenario: User had export permission but it expired
        Expected: Permission denied
        """
        # Arrange
        from datetime import datetime, timedelta, timezone

        user = await create_user(async_session, "expired_user")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        role = await create_role(async_session, "exporter_temp", ["flow.export"])

        # Create expired assignment
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        await assign_role(
            async_session,
            user,
            role,
            scope_type="flow",
            scope_id=flow.id,
            expires_at=expired_time,
        )

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is False, "Expired role assignment should not grant permission"

    @pytest.mark.asyncio
    async def test_permission_with_inactive_role_assignment(
        self,
        async_session: AsyncSession,
    ):
        """Test permission check with inactive role assignment.

        Scenario: User has role assignment but it's marked inactive
        Expected: Permission denied
        """
        # Arrange
        user = await create_user(async_session, "inactive_user")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        role = await create_role(async_session, "exporter_inactive", ["flow.export"])

        # Create inactive assignment
        await assign_role(
            async_session,
            user,
            role,
            scope_type="flow",
            scope_id=flow.id,
            is_active=False,
        )

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is False, "Inactive role assignment should not grant permission"

    @pytest.mark.asyncio
    async def test_permission_with_valid_future_expiration(
        self,
        async_session: AsyncSession,
    ):
        """Test permission check with valid future expiration.

        Scenario: User has role that expires in 1 hour
        Expected: Permission granted (not yet expired)
        """
        # Arrange
        from datetime import datetime, timedelta, timezone

        user = await create_user(async_session, "future_exp_user")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        role = await create_role(async_session, "exporter_temp_valid", ["flow.export"])

        # Create assignment that expires in future
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        await assign_role(
            async_session,
            user,
            role,
            scope_type="flow",
            scope_id=flow.id,
            expires_at=future_time,
        )

        engine = RBACEnforcementEngine(async_session)

        # Act
        allowed = await engine.has_permission(
            user_id=user.id,
            permission="flow.export",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is True, "Valid (not yet expired) role assignment should grant permission"

    @pytest.mark.asyncio
    async def test_permission_with_nonexistent_user(
        self,
        async_session: AsyncSession,
    ):
        """Test permission check for non-existent user.

        Scenario: Check permission for user ID that doesn't exist
        Expected: Permission denied
        """
        # Arrange
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        engine = RBACEnforcementEngine(async_session)
        nonexistent_user_id = uuid4()

        # Act
        allowed = await engine.has_permission(
            user_id=nonexistent_user_id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert
        assert allowed is False, "Non-existent user should be denied"

    @pytest.mark.asyncio
    async def test_permission_with_nonexistent_resource(
        self,
        async_session: AsyncSession,
    ):
        """Test permission check for non-existent resource.

        Scenario: Check permission for flow that doesn't exist
        Expected: Permission denied
        """
        # Arrange
        user = await create_user(async_session, "test_user")
        engine = RBACEnforcementEngine(async_session)
        nonexistent_flow_id = uuid4()

        # Act
        allowed = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=nonexistent_flow_id,
        )

        # Assert
        assert allowed is False, "Permission check on non-existent resource should be denied"

    @pytest.mark.asyncio
    async def test_permission_caching_for_repeated_checks(
        self,
        async_session: AsyncSession,
    ):
        """Test that permission checks are cached properly.

        Scenario: Multiple identical permission checks
        Expected: Results should be consistent (cached)
        """
        # Arrange
        user = await create_user(async_session, "cache_test_user")
        workspace = await create_workspace(async_session, "WB1")
        project = await create_project(async_session, "PRJ1", workspace.id)
        flow = await create_flow(async_session, "Flow1", project.id)

        role = await create_role(async_session, "reader_cache", ["flow.read"])
        await assign_role(async_session, user, role, scope_type="flow", scope_id=flow.id)

        engine = RBACEnforcementEngine(async_session)

        # Act - Multiple identical checks
        result1 = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        result2 = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )
        result3 = await engine.has_permission(
            user_id=user.id,
            permission="flow.read",
            resource_type="flow",
            resource_id=flow.id,
        )

        # Assert - All results should be identical
        assert result1 is True, "First check should succeed"
        assert result2 is True, "Second check should succeed (cached)"
        assert result3 is True, "Third check should succeed (cached)"

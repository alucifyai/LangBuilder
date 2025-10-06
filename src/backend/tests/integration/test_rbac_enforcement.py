"""
Integration tests for RBAC enforcement.

Tests acceptance criteria scenarios with actual database and RBAC service.
Covers AC1-AC8 from Story 1.1.
"""

import pytest
from uuid import uuid4
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.rbac import check_permission, SCOPE_HIERARCHY
from langflow.services.database.models.permission.model import Permission
from langflow.services.database.models.permission.crud import get_all_permissions
from langflow.services.database.models.role.model import Role
from langflow.services.database.models.role.crud import create_role, get_role_by_name
from langflow.services.database.models.grant.model import Grant, PrincipalType, ScopeType
from langflow.services.database.models.grant.crud import create_grant


@pytest.mark.asyncio
class TestRBACIntegration:
    """Integration tests for RBAC enforcement scenarios."""

    @pytest.fixture
    async def seed_permissions(self, session: AsyncSession):
        """Seed basic permissions for testing."""
        permissions = [
            Permission(
                id="flows:create",
                resource_type="flows",
                action="create",
                description="Create flows",
            ),
            Permission(
                id="flows:read",
                resource_type="flows",
                action="read",
                description="Read flows",
            ),
            Permission(
                id="flows:export_flow",
                resource_type="flows",
                action="export_flow",
                description="Export flows",
            ),
            Permission(
                id="environments:deploy_environment",
                resource_type="environments",
                action="deploy_environment",
                description="Deploy to environment",
            ),
            Permission(
                id="workspaces:invite_users",
                resource_type="workspaces",
                action="invite_users",
                description="Invite users",
            ),
            Permission(
                id="components:modify_component_settings",
                resource_type="components",
                action="modify_component_settings",
                description="Modify components",
            ),
            Permission(
                id="api_keys:manage_tokens",
                resource_type="api_keys",
                action="manage_tokens",
                description="Manage API tokens",
            ),
        ]

        for perm in permissions:
            session.add(perm)
        await session.commit()

        return permissions

    async def test_ac1_permission_catalog_completeness(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC1: Catalog includes CRUD and the specified extended permissions.

        Verify permission catalog contains all required permissions.
        """
        permissions = await get_all_permissions(session)
        permission_ids = {p.id for p in permissions}

        # Check CRUD permissions exist
        assert "flows:create" in permission_ids
        assert "flows:read" in permission_ids

        # Check extended permissions exist
        assert "flows:export_flow" in permission_ids
        assert "environments:deploy_environment" in permission_ids
        assert "workspaces:invite_users" in permission_ids
        assert "components:modify_component_settings" in permission_ids
        assert "api_keys:manage_tokens" in permission_ids

    async def test_ac2_role_validation_rejects_unknown_permissions(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC2: Role builder only accepts known permission IDs.

        Attempting to create a role with unknown permissions should fail.
        """
        # This should fail - unknown permission
        with pytest.raises(Exception) as exc_info:
            await create_role(
                session,
                name="BadRole",
                permissions=["flows:export_flow", "unknown:permission"],
            )

        assert "Unknown permission id" in str(exc_info.value)

    async def test_ac3_export_flow_permission_enforcement(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC3: Enforcement — export flow requires export_flow permission.

        User with export_flow on Flow=F123 can export F123 but not F124.
        """
        user_id = uuid4()

        # Create role with export_flow permission
        role = await create_role(
            session,
            name="Exporter",
            permissions=["flows:export_flow"],
        )

        # Grant role to user for Flow=F123
        await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=user_id,
            role_id=role.id,
            scope_type=ScopeType.FLOW,
            scope_id="F123",
        )

        # User should be able to export F123
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="export_flow",
            resource_type="flows",
            resource_id="F123",
            scope_type=ScopeType.FLOW,
            scope_id="F123",
        )
        assert has_permission is True

        # User should NOT be able to export F124
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="export_flow",
            resource_type="flows",
            resource_id="F124",
            scope_type=ScopeType.FLOW,
            scope_id="F124",
        )
        assert has_permission is False

    async def test_ac4_deploy_environment_permission_enforcement(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC4: Enforcement — deploy requires deploy_environment permission.

        User with deploy_environment on Environment=Staging can deploy to Staging
        but not Production.
        """
        user_id = uuid4()

        # Create role with deploy_environment permission
        role = await create_role(
            session,
            name="Deployer",
            permissions=["environments:deploy_environment"],
        )

        # Grant role to user for Environment=Staging
        await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=user_id,
            role_id=role.id,
            scope_type=ScopeType.ENVIRONMENT,
            scope_id="Staging",
        )

        # User should be able to deploy to Staging
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="deploy_environment",
            resource_type="environments",
            resource_id="Staging",
            scope_type=ScopeType.ENVIRONMENT,
            scope_id="Staging",
        )
        assert has_permission is True

        # User should NOT be able to deploy to Production
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="deploy_environment",
            resource_type="environments",
            resource_id="Production",
            scope_type=ScopeType.ENVIRONMENT,
            scope_id="Production",
        )
        assert has_permission is False

    async def test_ac5_invite_users_workspace_scoped(
        self, session: AsyncSession, seed_permissions
    ):
        """
        AC5: Enforcement — inviting users requires invite_users at workspace.

        User with invite_users at Workspace=WB1 can invite to projects under WB1
        but not to other workspaces.
        """
        user_id = uuid4()

        # Create role with invite_users permission
        role = await create_role(
            session,
            name="Inviter",
            permissions=["workspaces:invite_users"],
        )

        # Grant role to user for Workspace=WB1
        await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=user_id,
            role_id=role.id,
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB1",
        )

        # User should be able to invite at WB1
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="invite_users",
            resource_type="workspaces",
            resource_id="WB1",
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB1",
        )
        assert has_permission is True

        # User should NOT be able to invite at WB2
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="invite_users",
            resource_type="workspaces",
            resource_id="WB2",
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB2",
        )
        assert has_permission is False

    async def test_scope_hierarchy_inheritance(
        self, session: AsyncSession, seed_permissions
    ):
        """
        Test scope hierarchy inheritance.

        Permission granted at Workspace level should cascade to Projects/Flows below.
        """
        user_id = uuid4()

        # Create role with read permission
        role = await create_role(
            session,
            name="Reader",
            permissions=["flows:read"],
        )

        # Grant role to user at WORKSPACE level
        await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=user_id,
            role_id=role.id,
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB1",
        )

        # User should be able to read flows at PROJECT level (inheritance)
        # Since workspace grant is higher in hierarchy, it applies to lower scopes
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="read",
            resource_type="flows",
            resource_id="some_flow",
            scope_type=ScopeType.PROJECT,
            scope_id="PRJ1_under_WB1",
        )
        assert has_permission is True

    async def test_deny_by_default(self, session: AsyncSession, seed_permissions):
        """
        Test deny-by-default behavior.

        User with no grants should be denied access to all resources.
        """
        user_id = uuid4()  # User with no grants

        # User should NOT have any permissions
        has_permission = await check_permission(
            session,
            user_id=user_id,
            action="export_flow",
            resource_type="flows",
            resource_id="F123",
            scope_type=ScopeType.FLOW,
            scope_id="F123",
        )
        assert has_permission is False

    async def test_scope_hierarchy_constants(self):
        """
        Test scope hierarchy rankings are correctly defined.

        Workspace should have lowest rank (1 = highest priority).
        """
        assert SCOPE_HIERARCHY[ScopeType.WORKSPACE] == 1
        assert SCOPE_HIERARCHY[ScopeType.PROJECT] == 2
        assert SCOPE_HIERARCHY[ScopeType.ENVIRONMENT] == 3
        assert SCOPE_HIERARCHY[ScopeType.FLOW] == 4
        assert SCOPE_HIERARCHY[ScopeType.COMPONENT] == 5

        # Verify hierarchy ordering
        assert SCOPE_HIERARCHY[ScopeType.WORKSPACE] < SCOPE_HIERARCHY[ScopeType.PROJECT]
        assert SCOPE_HIERARCHY[ScopeType.PROJECT] < SCOPE_HIERARCHY[ScopeType.FLOW]

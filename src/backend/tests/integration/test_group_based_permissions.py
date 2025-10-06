"""
Integration test for group-based permissions.

Verifies that users inherit permissions via group membership (Story 2.1).
"""

import pytest
from uuid import uuid4
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.group import (
    create_group,
    add_user_to_group,
    get_user_groups,
)
from langflow.services.database.models.permission.model import Permission
from langflow.services.database.models.role.crud import create_role
from langflow.services.database.models.grant.crud import create_grant
from langflow.services.database.models.grant.model import PrincipalType, ScopeType
from langflow.services.database.models.user import User
from langflow.services.auth.permissions import get_user_grants, has_permission


@pytest.mark.asyncio
class TestGroupBasedPermissions:
    """Integration tests for group-based permission inheritance."""

    @pytest.fixture
    async def seed_permissions(self, session: AsyncSession):
        """Seed basic permissions for testing."""
        permissions = [
            Permission(
                id="flows:read",
                resource_type="flows",
                action="read",
                description="Read flows",
            ),
            Permission(
                id="flows:create",
                resource_type="flows",
                action="create",
                description="Create flows",
            ),
            Permission(
                id="flows:delete",
                resource_type="flows",
                action="delete",
                description="Delete flows",
            ),
        ]

        for perm in permissions:
            session.add(perm)
        await session.commit()

        return permissions

    @pytest.fixture
    async def test_user(self, session: AsyncSession):
        """Create a test user."""
        user = User(
            id=uuid4(),
            username=f"test_user_{uuid4().hex[:8]}",
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def test_user_inherits_permissions_via_group(
        self, session: AsyncSession, seed_permissions, test_user
    ):
        """
        Test that a user inherits permissions from their group membership.

        Scenario:
        1. Create a role "Editor" with flows:read and flows:create permissions
        2. Create a group "Editors"
        3. Grant the "Editor" role to the "Editors" group at Workspace scope
        4. Add test_user to "Editors" group
        5. Verify test_user has flows:read and flows:create permissions
        """
        # 1. Create role
        editor_role = await create_role(
            session,
            name="Editor",
            permissions=["flows:read", "flows:create"],
        )

        # 2. Create group
        editors_group = await create_group(
            session,
            name="Editors",
            description="Editor group for testing",
        )

        # 3. Grant role to group at workspace scope
        workspace_id = str(uuid4())
        grant = await create_grant(
            session,
            principal_type=PrincipalType.GROUP,
            principal_id=str(editors_group.id),
            role_id=str(editor_role.id),
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )

        # 4. Add user to group
        await add_user_to_group(session, editors_group.id, test_user.id)

        # 5. Verify user has permissions via group
        grants = await get_user_grants(session, test_user)

        # Should get the group grant
        assert len(grants) == 1
        assert grants[0].id == grant.id
        assert grants[0].principal_type == PrincipalType.GROUP
        assert grants[0].principal_id == str(editors_group.id)

        # Verify permission check works
        can_read = await has_permission(
            session,
            test_user,
            "flows:read",
            ScopeType.WORKSPACE,
            workspace_id,
        )
        assert can_read is True

        can_create = await has_permission(
            session,
            test_user,
            "flows:create",
            ScopeType.WORKSPACE,
            workspace_id,
        )
        assert can_create is True

        # User should NOT have flows:delete permission
        can_delete = await has_permission(
            session,
            test_user,
            "flows:delete",
            ScopeType.WORKSPACE,
            workspace_id,
        )
        assert can_delete is False

    async def test_user_with_both_direct_and_group_grants(
        self, session: AsyncSession, seed_permissions, test_user
    ):
        """
        Test that a user gets permissions from BOTH direct grants and group membership.

        Scenario:
        1. Create two roles: "Reader" (flows:read) and "Creator" (flows:create)
        2. Grant "Reader" role directly to user
        3. Create group "Creators" with "Creator" role
        4. Add user to "Creators" group
        5. Verify user has both flows:read (direct) and flows:create (via group)
        """
        workspace_id = str(uuid4())

        # 1. Create roles
        reader_role = await create_role(session, name="Reader", permissions=["flows:read"])
        creator_role = await create_role(session, name="Creator", permissions=["flows:create"])

        # 2. Direct grant to user
        direct_grant = await create_grant(
            session,
            principal_type=PrincipalType.USER,
            principal_id=str(test_user.id),
            role_id=str(reader_role.id),
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )

        # 3. Create group with grant
        creators_group = await create_group(session, name="Creators")
        group_grant = await create_grant(
            session,
            principal_type=PrincipalType.GROUP,
            principal_id=str(creators_group.id),
            role_id=str(creator_role.id),
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )

        # 4. Add user to group
        await add_user_to_group(session, creators_group.id, test_user.id)

        # 5. Verify user has grants from both sources
        grants = await get_user_grants(session, test_user)
        assert len(grants) == 2

        grant_ids = {g.id for g in grants}
        assert direct_grant.id in grant_ids
        assert group_grant.id in grant_ids

        # Verify both permissions work
        can_read = await has_permission(
            session, test_user, "flows:read", ScopeType.WORKSPACE, workspace_id
        )
        assert can_read is True

        can_create = await has_permission(
            session, test_user, "flows:create", ScopeType.WORKSPACE, workspace_id
        )
        assert can_create is True

    async def test_user_loses_permissions_when_removed_from_group(
        self, session: AsyncSession, seed_permissions, test_user
    ):
        """
        Test that permissions are removed when user is removed from group.

        Scenario:
        1. Create group with role grant
        2. Add user to group
        3. Verify user has permissions
        4. Remove user from group
        5. Verify user NO LONGER has those permissions
        """
        from langflow.services.database.models.group import remove_user_from_group

        workspace_id = str(uuid4())

        # 1. Create group with role
        editor_role = await create_role(session, name="TestEditor", permissions=["flows:create"])
        editors_group = await create_group(session, name="TestEditors")
        await create_grant(
            session,
            principal_type=PrincipalType.GROUP,
            principal_id=str(editors_group.id),
            role_id=str(editor_role.id),
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )

        # 2. Add user to group
        await add_user_to_group(session, editors_group.id, test_user.id)

        # 3. Verify user has permission
        can_create_before = await has_permission(
            session, test_user, "flows:create", ScopeType.WORKSPACE, workspace_id
        )
        assert can_create_before is True

        # 4. Remove user from group
        await remove_user_from_group(session, editors_group.id, test_user.id)

        # 5. Verify user lost permission
        grants_after = await get_user_grants(session, test_user)
        assert len(grants_after) == 0

        can_create_after = await has_permission(
            session, test_user, "flows:create", ScopeType.WORKSPACE, workspace_id
        )
        assert can_create_after is False

    async def test_multiple_groups_with_overlapping_permissions(
        self, session: AsyncSession, seed_permissions, test_user
    ):
        """
        Test user in multiple groups accumulates all unique permissions.

        Scenario:
        1. Create Group A with flows:read
        2. Create Group B with flows:create
        3. Add user to both groups
        4. Verify user has both permissions
        """
        workspace_id = str(uuid4())

        # Create roles and groups
        reader_role = await create_role(session, name="MultiReader", permissions=["flows:read"])
        creator_role = await create_role(session, name="MultiCreator", permissions=["flows:create"])

        group_a = await create_group(session, name="GroupA")
        group_b = await create_group(session, name="GroupB")

        # Grants to groups
        await create_grant(
            session,
            principal_type=PrincipalType.GROUP,
            principal_id=str(group_a.id),
            role_id=str(reader_role.id),
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )
        await create_grant(
            session,
            principal_type=PrincipalType.GROUP,
            principal_id=str(group_b.id),
            role_id=str(creator_role.id),
            scope_type=ScopeType.WORKSPACE,
            scope_id=workspace_id,
        )

        # Add user to both groups
        await add_user_to_group(session, group_a.id, test_user.id)
        await add_user_to_group(session, group_b.id, test_user.id)

        # Verify user has grants from both groups
        grants = await get_user_grants(session, test_user)
        assert len(grants) == 2

        # Verify both permissions
        can_read = await has_permission(
            session, test_user, "flows:read", ScopeType.WORKSPACE, workspace_id
        )
        assert can_read is True

        can_create = await has_permission(
            session, test_user, "flows:create", ScopeType.WORKSPACE, workspace_id
        )
        assert can_create is True

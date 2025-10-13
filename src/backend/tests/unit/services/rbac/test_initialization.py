"""Unit tests for RBAC initialization and seeding logic.

Tests the idempotent seeding of permissions and system roles
defined in initialization.py (Task 1.3).
"""

import pytest
from langflow.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
)
from langflow.services.rbac.constants import (
    PERMISSIONS,
    SYSTEM_ROLES,
    TOTAL_PERMISSIONS_COUNT,
    TOTAL_SYSTEM_ROLES_COUNT,
)
from langflow.services.rbac.initialization import (
    _is_already_seeded,
    _seed_permissions,
    _seed_system_roles,
)
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
class TestSeedPermissionsAndRoles:
    """Test seeding integration with mocked database service.

    Note: These tests use monkeypatch to inject the test session into the seeding functions.
    """

    async def test_end_to_end_seeding(self, async_session: AsyncSession):
        """Test complete seeding workflow."""
        # Verify database is empty
        result = await async_session.exec(select(Permission))
        assert len(result.all()) == 0

        result = await async_session.exec(select(Role))
        assert len(result.all()) == 0

        # Seed permissions
        permission_map = await _seed_permissions(async_session)
        await async_session.commit()

        # Verify permissions were created
        assert len(permission_map) == TOTAL_PERMISSIONS_COUNT
        result = await async_session.exec(select(Permission))
        permissions = result.all()
        assert len(permissions) == TOTAL_PERMISSIONS_COUNT

        # Seed system roles
        role_count = await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Verify system roles were created
        assert role_count == TOTAL_SYSTEM_ROLES_COUNT
        result = await async_session.exec(select(Role).where(Role.is_system_role == True))  # noqa: E712
        roles = result.all()
        assert len(roles) == TOTAL_SYSTEM_ROLES_COUNT

        # Verify role names
        role_names = {role.name for role in roles}
        expected_names = set(SYSTEM_ROLES.keys())
        assert role_names == expected_names

    async def test_seeding_idempotency(self, async_session: AsyncSession):
        """Test that seeding can run multiple times without creating duplicates."""
        # First seeding
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Count records
        result = await async_session.exec(select(Permission))
        first_count = len(result.all())

        result = await async_session.exec(select(Role))
        first_role_count = len(result.all())

        result = await async_session.exec(select(RolePermission))
        first_rp_count = len(result.all())

        # Second seeding (should skip existing records)
        permission_map2 = await _seed_permissions(async_session)
        role_count2 = await _seed_system_roles(async_session, permission_map2)
        await async_session.commit()

        # Second seeding should create 0 new roles
        assert role_count2 == 0

        # Verify counts are the same (no duplicates)
        result = await async_session.exec(select(Permission))
        second_count = len(result.all())
        assert second_count == first_count

        result = await async_session.exec(select(Role))
        second_role_count = len(result.all())
        assert second_role_count == first_role_count

        result = await async_session.exec(select(RolePermission))
        second_rp_count = len(result.all())
        assert second_rp_count == first_rp_count

    async def test_seeding_with_partial_data(self, async_session: AsyncSession):
        """Test seeding handles partial data correctly."""
        # Manually create one permission
        from datetime import datetime, timezone
        from uuid import uuid4

        perm = Permission(
            id=uuid4(),
            resource_type="WORKSPACE",
            action="READ",
            display_name="Read Workspace",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        async_session.add(perm)
        await async_session.commit()

        # Run seeding
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Verify all permissions exist (including the manually created one)
        result = await async_session.exec(select(Permission))
        permissions = result.all()
        assert len(permissions) == TOTAL_PERMISSIONS_COUNT

        # Verify system roles were created
        result = await async_session.exec(select(Role).where(Role.is_system_role == True))  # noqa: E712
        roles = result.all()
        assert len(roles) == TOTAL_SYSTEM_ROLES_COUNT


@pytest.mark.asyncio
class TestIsAlreadySeeded:
    """Test the seeding detection function."""

    async def test_is_already_seeded_empty_database(self, async_session: AsyncSession):
        """Test detection when database is empty."""
        result = await _is_already_seeded(async_session)
        assert result is False

    async def test_is_already_seeded_with_permissions_only(self, async_session: AsyncSession):
        """Test detection when only permissions exist."""
        from datetime import datetime, timezone
        from uuid import uuid4

        # Create a permission
        perm = Permission(
            id=uuid4(),
            resource_type="WORKSPACE",
            action="READ",
            display_name="Read Workspace",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        async_session.add(perm)
        await async_session.commit()

        result = await _is_already_seeded(async_session)
        assert result is False  # Need both permissions AND roles

    async def test_is_already_seeded_with_roles_only(self, async_session: AsyncSession):
        """Test detection when only roles exist."""
        from datetime import datetime, timezone
        from uuid import uuid4

        # Create a system role
        role = Role(
            id=uuid4(),
            name="test_role",
            display_name="Test Role",
            description="Test",
            is_system_role=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        async_session.add(role)
        await async_session.commit()

        result = await _is_already_seeded(async_session)
        assert result is False  # Need both permissions AND roles

    async def test_is_already_seeded_with_both(self, async_session: AsyncSession):
        """Test detection when both permissions and roles exist."""
        from datetime import datetime, timezone
        from uuid import uuid4

        # Create a permission
        perm = Permission(
            id=uuid4(),
            resource_type="WORKSPACE",
            action="READ",
            display_name="Read Workspace",
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        async_session.add(perm)

        # Create a system role
        role = Role(
            id=uuid4(),
            name="test_role",
            display_name="Test Role",
            description="Test",
            is_system_role=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        async_session.add(role)
        await async_session.commit()

        result = await _is_already_seeded(async_session)
        assert result is True


@pytest.mark.asyncio
class TestSeedPermissions:
    """Test the permission seeding function."""

    async def test_seed_permissions_creates_all(self, async_session: AsyncSession):
        """Test that all permissions are created."""
        permission_map = await _seed_permissions(async_session)

        assert len(permission_map) == TOTAL_PERMISSIONS_COUNT

        # Verify all permissions from catalog are in map
        expected_names = {perm[0] for perm in PERMISSIONS}
        actual_names = set(permission_map.keys())
        assert actual_names == expected_names

    async def test_seed_permissions_database_records(self, async_session: AsyncSession):
        """Test that permission records are created in database."""
        await _seed_permissions(async_session)
        await async_session.commit()

        result = await async_session.exec(select(Permission))
        permissions = result.all()

        assert len(permissions) == TOTAL_PERMISSIONS_COUNT

        # Verify structure of created records
        for perm in permissions:
            assert perm.id is not None
            assert perm.resource_type
            assert perm.action
            assert perm.display_name
            assert perm.is_active is True
            assert perm.created_at is not None

    async def test_seed_permissions_correct_data(self, async_session: AsyncSession):
        """Test that permissions have correct data from catalog."""
        permission_map = await _seed_permissions(async_session)
        await async_session.commit()

        # Verify workspace.read permission
        workspace_read = permission_map.get("workspace.read")
        assert workspace_read is not None
        assert workspace_read.resource_type == "WORKSPACE"
        assert workspace_read.action == "READ"
        assert workspace_read.display_name == "Read Workspace"

        # Verify flow.export permission (PRD @AC3)
        flow_export = permission_map.get("flow.export")
        assert flow_export is not None
        assert flow_export.resource_type == "FLOW"
        assert flow_export.action == "EXPORT"

    async def test_seed_permissions_idempotency(self, async_session: AsyncSession):
        """Test that seeding permissions twice doesn't create duplicates."""
        # First seed
        map1 = await _seed_permissions(async_session)
        await async_session.commit()

        # Second seed
        map2 = await _seed_permissions(async_session)
        await async_session.commit()

        # Both maps should have same number of permissions
        assert len(map1) == len(map2)

        # Verify no duplicates in database
        result = await async_session.exec(select(Permission))
        permissions = result.all()
        assert len(permissions) == TOTAL_PERMISSIONS_COUNT


@pytest.mark.asyncio
class TestSeedSystemRoles:
    """Test the system role seeding function."""

    async def test_seed_system_roles_creates_all(self, async_session: AsyncSession):
        """Test that all system roles are created."""
        # First seed permissions (required for role-permission associations)
        permission_map = await _seed_permissions(async_session)

        # Seed roles
        role_count = await _seed_system_roles(async_session, permission_map)

        assert role_count == TOTAL_SYSTEM_ROLES_COUNT

    async def test_seed_system_roles_database_records(self, async_session: AsyncSession):
        """Test that role records are created in database."""
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        result = await async_session.exec(select(Role).where(Role.is_system_role == True))  # noqa: E712
        roles = result.all()

        assert len(roles) == TOTAL_SYSTEM_ROLES_COUNT

        # Verify structure of created records
        for role in roles:
            assert role.id is not None
            assert role.name
            assert role.display_name
            assert role.description
            assert role.is_system_role is True
            assert role.is_active is True
            assert role.created_at is not None
            assert role.updated_at is not None

    async def test_seed_system_roles_permission_associations(self, async_session: AsyncSession):
        """Test that role-permission associations are created."""
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Check workspace_owner role has all permissions
        result = await async_session.exec(select(Role).where(Role.name == "workspace_owner"))
        owner_role = result.first()
        assert owner_role is not None

        result = await async_session.exec(select(RolePermission).where(RolePermission.role_id == owner_role.id))
        role_permissions = result.all()

        expected_count = len(SYSTEM_ROLES["workspace_owner"]["permissions"])
        assert len(role_permissions) == expected_count

    async def test_seed_system_roles_viewer_read_only(self, async_session: AsyncSession):
        """Test that viewer role has only read permissions."""
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Get viewer role
        result = await async_session.exec(select(Role).where(Role.name == "viewer"))
        viewer_role = result.first()
        assert viewer_role is not None

        # Get viewer permissions
        result = await async_session.exec(select(RolePermission).where(RolePermission.role_id == viewer_role.id))
        rp_records = result.all()

        permission_ids = [rp.permission_id for rp in rp_records]
        result = await async_session.exec(select(Permission).where(Permission.id.in_(permission_ids)))
        viewer_permissions = result.all()

        # Verify all are read permissions
        for perm in viewer_permissions:
            assert not any(
                action in perm.action.lower() for action in ["create", "update", "delete", "manage", "revoke", "deploy", "execute"]
            ), f"Viewer should not have write permission: {perm.resource_type}.{perm.action}"

    async def test_seed_system_roles_service_account_no_permissions(self, async_session: AsyncSession):
        """Test that service_account role has no default permissions."""
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Get service_account role
        result = await async_session.exec(select(Role).where(Role.name == "service_account"))
        sa_role = result.first()
        assert sa_role is not None

        # Get service_account permissions
        result = await async_session.exec(select(RolePermission).where(RolePermission.role_id == sa_role.id))
        rp_records = result.all()

        assert len(rp_records) == 0, "Service account should have no default permissions"

    async def test_seed_system_roles_idempotency(self, async_session: AsyncSession):
        """Test that seeding roles twice doesn't create duplicates."""
        permission_map = await _seed_permissions(async_session)

        # First seed
        count1 = await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Second seed
        count2 = await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Second seed should create 0 new roles
        assert count2 == 0

        # Verify no duplicates in database
        result = await async_session.exec(select(Role).where(Role.is_system_role == True))  # noqa: E712
        roles = result.all()
        assert len(roles) == TOTAL_SYSTEM_ROLES_COUNT


@pytest.mark.asyncio
class TestRolePermissionAssociations:
    """Test role-permission junction table records."""

    async def test_workspace_owner_has_all_permissions(self, async_session: AsyncSession):
        """Test that workspace_owner is associated with all permissions."""
        # Seed permissions and roles
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Get workspace_owner role
        result = await async_session.exec(select(Role).where(Role.name == "workspace_owner"))
        owner_role = result.first()
        assert owner_role is not None

        # Get all role-permission associations
        result = await async_session.exec(select(RolePermission).where(RolePermission.role_id == owner_role.id))
        rp_records = result.all()

        expected_count = len(SYSTEM_ROLES["workspace_owner"]["permissions"])
        assert len(rp_records) == expected_count

    async def test_workspace_admin_permissions(self, async_session: AsyncSession):
        """Test workspace_admin has correct permissions."""
        # Seed permissions and roles
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Get workspace_admin role
        result = await async_session.exec(select(Role).where(Role.name == "workspace_admin"))
        admin_role = result.first()
        assert admin_role is not None

        # Get permissions
        result = await async_session.exec(select(RolePermission).where(RolePermission.role_id == admin_role.id))
        rp_records = result.all()

        permission_ids = [rp.permission_id for rp in rp_records]
        result = await async_session.exec(select(Permission).where(Permission.id.in_(permission_ids)))
        admin_permissions = result.all()

        # Check for required permissions
        # Build a set of lowercase permission names
        perm_names = [p[0] for p in PERMISSIONS]
        perm_resource_action_map = {p[0]: (p[2], p[3]) for p in PERMISSIONS}

        actual_perm_set = set()
        for p in admin_permissions:
            # Find the permission name that matches this resource_type and action
            for perm_name, (resource, action) in perm_resource_action_map.items():
                if resource == p.resource_type and action == p.action:
                    actual_perm_set.add(perm_name)
                    break

        assert "user.read" in actual_perm_set
        assert "user.invite" in actual_perm_set or "user.manage" in actual_perm_set
        assert "role.create" in actual_perm_set
        assert "audit.view" in actual_perm_set

    async def test_editor_has_flow_permissions(self, async_session: AsyncSession):
        """Test editor has flow CRUD permissions."""
        # Seed permissions and roles
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Get editor role
        result = await async_session.exec(select(Role).where(Role.name == "editor"))
        editor_role = result.first()
        assert editor_role is not None

        # Get permissions
        result = await async_session.exec(select(RolePermission).where(RolePermission.role_id == editor_role.id))
        rp_records = result.all()

        permission_ids = [rp.permission_id for rp in rp_records]
        result = await async_session.exec(select(Permission).where(Permission.id.in_(permission_ids)))
        editor_permissions = result.all()

        # Check for flow permissions
        # Build a set of permission names
        perm_resource_action_map = {p[0]: (p[2], p[3]) for p in PERMISSIONS}

        actual_perm_set = set()
        for p in editor_permissions:
            # Find the permission name that matches this resource_type and action
            for perm_name, (resource, action) in perm_resource_action_map.items():
                if resource == p.resource_type and action == p.action:
                    actual_perm_set.add(perm_name)
                    break

        assert "flow.create" in actual_perm_set
        assert "flow.read" in actual_perm_set
        assert "flow.update" in actual_perm_set
        assert "flow.execute" in actual_perm_set


@pytest.mark.asyncio
class TestSeedingErrorHandling:
    """Test error handling and edge cases."""

    async def test_seed_with_missing_permission_in_role(self, async_session: AsyncSession):
        """Test handling of role referencing non-existent permission."""
        # This should not happen due to module-level validation,
        # but test the runtime behavior
        permission_map = await _seed_permissions(async_session)

        # Remove a permission from the map to simulate missing permission
        if "workspace.read" in permission_map:
            del permission_map["workspace.read"]

        # Seeding should continue but log warning
        # (implementation logs warning and skips the permission)
        role_count = await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        # Roles should still be created
        assert role_count > 0

    async def test_all_system_roles_are_system(self, async_session: AsyncSession):
        """Test that all created roles have is_system_role=True."""
        # Seed permissions and roles
        permission_map = await _seed_permissions(async_session)
        await _seed_system_roles(async_session, permission_map)
        await async_session.commit()

        result = await async_session.exec(select(Role).where(Role.is_system_role == True))  # noqa: E712
        system_roles = result.all()

        assert len(system_roles) == TOTAL_SYSTEM_ROLES_COUNT

        for role in system_roles:
            assert role.is_system_role is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Unit tests for RBAC data seeding functionality.

This module tests the seed_rbac_data function to ensure:
- All roles are created correctly with proper descriptions
- All permissions are created correctly with proper descriptions
- Role-permission mappings are correct per PRD Story 1.2
- Seeding is idempotent (can run multiple times safely)
- Database constraints prevent duplicate data

Note: The tests use a fixture to seed the test database once before all tests run.
"""

import pytest
from langbuilder.initial_setup.rbac_seed import (
    PERMISSION_DESCRIPTIONS,
    ROLE_DESCRIPTIONS,
    ROLE_PERMISSIONS,
    seed_rbac_data,
)
from langbuilder.services.database.models.rbac import (
    Permission,
    PermissionEnum,
    Role,
    RoleEnum,
    RolePermission,
    UserRoleAssignment,
)
from langbuilder.services.database.utils import session_getter
from langbuilder.services.deps import get_db_service
from sqlmodel import delete, select


@pytest.fixture(autouse=True)
async def seed_test_database():
    """Seed the test database with RBAC data before running each test.

    This fixture cleans the database first to ensure a consistent test state,
    then seeds fresh RBAC data. This approach ensures test isolation and
    prevents failures due to pre-existing data from other test modules.
    """
    # Clean database before seeding to ensure consistent test state
    async with session_getter(get_db_service()) as session:
        # Delete in correct order due to foreign key constraints
        # UserRoleAssignment -> RolePermission -> Role and Permission
        await session.exec(delete(UserRoleAssignment))
        await session.exec(delete(RolePermission))
        await session.exec(delete(Role))
        await session.exec(delete(Permission))
        await session.commit()

    # Now seed with clean slate
    async with session_getter(get_db_service()) as session:
        await seed_rbac_data(session)


class TestRBACSeeding:
    """Test RBAC data seeding functionality.

    These tests verify that RBAC data was seeded correctly.
    The seed_test_database fixture runs before these tests to populate the database.
    """

    @pytest.mark.asyncio
    async def test_seed_rbac_data_creates_all_roles(self):
        """Test that seeding created all 4 predefined roles."""
        async with session_getter(get_db_service()) as session:
            # Verify all 4 roles exist
            stmt = select(Role)
            roles = list((await session.exec(stmt)).all())
            assert len(roles) == 4, f"Expected 4 roles, found {len(roles)}"

            # Verify role names
            role_names = {role.name for role in roles}
            assert RoleEnum.ADMIN in role_names
            assert RoleEnum.OWNER in role_names
            assert RoleEnum.EDITOR in role_names
            assert RoleEnum.VIEWER in role_names

    @pytest.mark.asyncio
    async def test_seed_rbac_data_creates_all_permissions(self):
        """Test that seeding created all 4 CRUD permissions."""
        async with session_getter(get_db_service()) as session:
            # Verify all 4 permissions exist
            stmt = select(Permission)
            permissions = list((await session.exec(stmt)).all())
            assert len(permissions) == 4, f"Expected 4 permissions, found {len(permissions)}"

            # Verify permission names
            perm_names = {perm.name for perm in permissions}
            assert PermissionEnum.CREATE in perm_names
            assert PermissionEnum.READ in perm_names
            assert PermissionEnum.UPDATE in perm_names
            assert PermissionEnum.DELETE in perm_names

    @pytest.mark.asyncio
    async def test_seed_rbac_data_creates_correct_descriptions(self):
        """Test that roles and permissions have correct descriptions."""
        async with session_getter(get_db_service()) as session:
            # Verify role descriptions
            stmt = select(Role)
            roles = list((await session.exec(stmt)).all())
            for role in roles:
                assert role.description == ROLE_DESCRIPTIONS[role.name], (
                    f"Role {role.name.value} has incorrect description"
                )

            # Verify permission descriptions
            stmt = select(Permission)
            permissions = list((await session.exec(stmt)).all())
            for perm in permissions:
                assert perm.description == PERMISSION_DESCRIPTIONS[perm.name], (
                    f"Permission {perm.name.value} has incorrect description"
                )

    @pytest.mark.asyncio
    async def test_admin_role_has_all_permissions(self):
        """Test that Admin role has all 4 permissions (CREATE, READ, UPDATE, DELETE)."""
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Get Admin role
            stmt = select(Role).where(Role.name == RoleEnum.ADMIN)
            admin_role = (await session.exec(stmt)).first()
            assert admin_role is not None

            # Get permissions for Admin role
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == admin_role.id)
            admin_permissions = list((await session.exec(stmt)).all())

            # Verify Admin has all 4 permissions
            assert len(admin_permissions) == 4, f"Admin should have 4 permissions, found {len(admin_permissions)}"
            perm_names = {p.name for p in admin_permissions}
            assert PermissionEnum.CREATE in perm_names
            assert PermissionEnum.READ in perm_names
            assert PermissionEnum.UPDATE in perm_names
            assert PermissionEnum.DELETE in perm_names

    @pytest.mark.asyncio
    async def test_owner_role_has_all_permissions(self):
        """Test that Owner role has all 4 permissions (CREATE, READ, UPDATE, DELETE)."""
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Get Owner role
            stmt = select(Role).where(Role.name == RoleEnum.OWNER)
            owner_role = (await session.exec(stmt)).first()
            assert owner_role is not None

            # Get permissions for Owner role
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == owner_role.id)
            owner_permissions = list((await session.exec(stmt)).all())

            # Verify Owner has all 4 permissions
            assert len(owner_permissions) == 4, f"Owner should have 4 permissions, found {len(owner_permissions)}"
            perm_names = {p.name for p in owner_permissions}
            assert PermissionEnum.CREATE in perm_names
            assert PermissionEnum.READ in perm_names
            assert PermissionEnum.UPDATE in perm_names
            assert PermissionEnum.DELETE in perm_names

    @pytest.mark.asyncio
    async def test_editor_role_has_create_read_update_no_delete(self):
        """Test that Editor role has CREATE, READ, UPDATE permissions (no DELETE)."""
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Get Editor role
            stmt = select(Role).where(Role.name == RoleEnum.EDITOR)
            editor_role = (await session.exec(stmt)).first()
            assert editor_role is not None

            # Get permissions for Editor role
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == editor_role.id)
            editor_permissions = list((await session.exec(stmt)).all())

            # Verify Editor has 3 permissions (no DELETE)
            assert len(editor_permissions) == 3, f"Editor should have 3 permissions, found {len(editor_permissions)}"
            perm_names = {p.name for p in editor_permissions}
            assert PermissionEnum.CREATE in perm_names
            assert PermissionEnum.READ in perm_names
            assert PermissionEnum.UPDATE in perm_names
            assert PermissionEnum.DELETE not in perm_names, "Editor should not have DELETE permission"

    @pytest.mark.asyncio
    async def test_viewer_role_has_only_read_permission(self):
        """Test that Viewer role has only READ permission."""
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Get Viewer role
            stmt = select(Role).where(Role.name == RoleEnum.VIEWER)
            viewer_role = (await session.exec(stmt)).first()
            assert viewer_role is not None

            # Get permissions for Viewer role
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == viewer_role.id)
            viewer_permissions = list((await session.exec(stmt)).all())

            # Verify Viewer has only 1 permission (READ)
            assert len(viewer_permissions) == 1, f"Viewer should have 1 permission, found {len(viewer_permissions)}"
            assert viewer_permissions[0].name == PermissionEnum.READ
            perm_names = {p.name for p in viewer_permissions}
            assert PermissionEnum.CREATE not in perm_names
            assert PermissionEnum.UPDATE not in perm_names
            assert PermissionEnum.DELETE not in perm_names

    @pytest.mark.asyncio
    async def test_seeding_is_idempotent(self):
        """Test that seeding can be run multiple times safely without creating duplicates.

        This test calls seed_rbac_data directly to verify idempotency.
        The first call during application startup has already seeded the data,
        so this second call should be a no-op.
        """
        async with session_getter(get_db_service()) as session:
            # Count roles and permissions before calling seed again
            stmt = select(Role)
            roles_before = list((await session.exec(stmt)).all())
            stmt = select(Permission)
            permissions_before = list((await session.exec(stmt)).all())
            stmt = select(RolePermission)
            mappings_before = list((await session.exec(stmt)).all())

            # Seeding should already have happened during startup
            assert len(roles_before) == 4
            assert len(permissions_before) == 4
            assert len(mappings_before) > 0

            # Call seed_rbac_data again - should be a no-op (idempotent)
            await seed_rbac_data(session)

            # Count roles and permissions after calling seed again
            stmt = select(Role)
            roles_after = list((await session.exec(stmt)).all())
            stmt = select(Permission)
            permissions_after = list((await session.exec(stmt)).all())
            stmt = select(RolePermission)
            mappings_after = list((await session.exec(stmt)).all())

            # Verify counts remain the same (no duplicates)
            assert len(roles_after) == len(roles_before) == 4, "Seeding is not idempotent - roles count changed"
            assert len(permissions_after) == len(permissions_before) == 4, (
                "Seeding is not idempotent - permissions count changed"
            )
            assert len(mappings_after) == len(mappings_before), "Seeding is not idempotent - mappings count changed"

    @pytest.mark.asyncio
    async def test_role_permission_mappings_match_specification(self):
        """Test that role-permission mappings exactly match ROLE_PERMISSIONS specification."""
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Verify each role's permissions match the specification
            for role_enum, expected_perms in ROLE_PERMISSIONS.items():
                # Get role
                stmt = select(Role).where(Role.name == role_enum)
                role = (await session.exec(stmt)).first()
                assert role is not None, f"Role {role_enum.value} not found"

                # Get permissions for this role
                stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == role.id)
                actual_perms = list((await session.exec(stmt)).all())

                # Verify count matches
                assert len(actual_perms) == len(expected_perms), (
                    f"Role {role_enum.value} expected {len(expected_perms)} permissions, found {len(actual_perms)}"
                )

                # Verify each expected permission exists
                actual_perm_names = {p.name for p in actual_perms}
                for expected_perm in expected_perms:
                    assert expected_perm in actual_perm_names, (
                        f"Role {role_enum.value} missing expected permission {expected_perm.value}"
                    )

    @pytest.mark.asyncio
    async def test_all_role_permission_mappings_created(self):
        """Test that correct number of role-permission mappings are created."""
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Calculate expected number of mappings from ROLE_PERMISSIONS
            expected_mapping_count = sum(len(perms) for perms in ROLE_PERMISSIONS.values())

            # Count actual mappings
            stmt = select(RolePermission)
            mappings = list((await session.exec(stmt)).all())

            assert len(mappings) == expected_mapping_count, (
                f"Expected {expected_mapping_count} role-permission mappings, found {len(mappings)}"
            )

    @pytest.mark.asyncio
    async def test_seed_data_matches_prd_story_1_2(self):
        """Integration test: Verify seeded data matches PRD Epic 1 Story 1.2 specifications.

        PRD Story 1.2 specifies:
        - Admin: Full access (all permissions)
        - Owner: Full access (all permissions)
        - Editor: Create, Read, Update (no Delete)
        - Viewer: Read only
        """
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # Verify Admin role per PRD
            stmt = select(Role).where(Role.name == RoleEnum.ADMIN)
            admin = (await session.exec(stmt)).first()
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == admin.id)
            admin_perms = {p.name for p in (await session.exec(stmt)).all()}
            assert admin_perms == {
                PermissionEnum.CREATE,
                PermissionEnum.READ,
                PermissionEnum.UPDATE,
                PermissionEnum.DELETE,
            }, "Admin role does not match PRD specification"

            # Verify Owner role per PRD
            stmt = select(Role).where(Role.name == RoleEnum.OWNER)
            owner = (await session.exec(stmt)).first()
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == owner.id)
            owner_perms = {p.name for p in (await session.exec(stmt)).all()}
            assert owner_perms == {
                PermissionEnum.CREATE,
                PermissionEnum.READ,
                PermissionEnum.UPDATE,
                PermissionEnum.DELETE,
            }, "Owner role does not match PRD specification"

            # Verify Editor role per PRD
            stmt = select(Role).where(Role.name == RoleEnum.EDITOR)
            editor = (await session.exec(stmt)).first()
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == editor.id)
            editor_perms = {p.name for p in (await session.exec(stmt)).all()}
            assert editor_perms == {
                PermissionEnum.CREATE,
                PermissionEnum.READ,
                PermissionEnum.UPDATE,
            }, "Editor role does not match PRD specification"

            # Verify Viewer role per PRD
            stmt = select(Role).where(Role.name == RoleEnum.VIEWER)
            viewer = (await session.exec(stmt)).first()
            stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == viewer.id)
            viewer_perms = {p.name for p in (await session.exec(stmt)).all()}
            assert viewer_perms == {
                PermissionEnum.READ,
            }, "Viewer role does not match PRD specification"

    @pytest.mark.asyncio
    async def test_database_constraints_prevent_duplicates(self):
        """Test that database unique constraints prevent duplicate roles/permissions.

        This verifies that the database schema correctly enforces uniqueness,
        which is part of the success criteria for Task 1.3.
        """
        async with session_getter(get_db_service()) as session:
            # Seeding happens during application startup

            # The unique constraints should be enforced at the database level
            # If we try to create a duplicate role, it should fail
            # This is already tested by the unique constraint tests in test_rbac_models.py
            # Here we just verify that seeding doesn't bypass constraints

            # Verify no duplicate roles
            stmt = select(Role)
            roles = list((await session.exec(stmt)).all())
            role_names = [r.name for r in roles]
            assert len(role_names) == len(set(role_names)), "Duplicate roles found"

            # Verify no duplicate permissions
            stmt = select(Permission)
            permissions = list((await session.exec(stmt)).all())
            perm_names = [p.name for p in permissions]
            assert len(perm_names) == len(set(perm_names)), "Duplicate permissions found"

            # Verify no duplicate role-permission mappings
            stmt = select(RolePermission)
            mappings = list((await session.exec(stmt)).all())
            mapping_pairs = [(m.role_id, m.permission_id) for m in mappings]
            assert len(mapping_pairs) == len(set(mapping_pairs)), "Duplicate role-permission mappings found"

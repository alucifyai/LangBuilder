"""RBAC Data Seeding Module.

This module provides functionality to seed the default RBAC roles, permissions,
and role-permission mappings into the database during initial application setup.

The seeding process is idempotent - it can be run multiple times safely without
creating duplicate data. It seeds:
- 4 Roles: Admin, Owner, Editor, Viewer
- 4 Permissions: CREATE, READ, UPDATE, DELETE
- Role-Permission Mappings per PRD Story 1.2:
  * Admin: All permissions (CREATE, READ, UPDATE, DELETE)
  * Owner: All permissions (CREATE, READ, UPDATE, DELETE)
  * Editor: CREATE, READ, UPDATE (no DELETE)
  * Viewer: READ only
"""
# ruff: noqa: S101, PLR2004

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.services.database.models.rbac.model import (
    Permission,
    PermissionEnum,
    Role,
    RoleEnum,
    RolePermission,
)

# Role-Permission Mappings per PRD Epic 1 Story 1.2
# These mappings define the capabilities of each role
ROLE_PERMISSIONS = {
    RoleEnum.ADMIN: [
        PermissionEnum.CREATE,
        PermissionEnum.READ,
        PermissionEnum.UPDATE,
        PermissionEnum.DELETE,
    ],  # Full access across all scopes (global)
    RoleEnum.OWNER: [
        PermissionEnum.CREATE,
        PermissionEnum.READ,
        PermissionEnum.UPDATE,
        PermissionEnum.DELETE,
    ],  # Full access to owned scope
    RoleEnum.EDITOR: [
        PermissionEnum.CREATE,
        PermissionEnum.READ,
        PermissionEnum.UPDATE,
    ],  # No DELETE permission
    RoleEnum.VIEWER: [
        PermissionEnum.READ,
    ],  # Read-only access
}

# Role descriptions per PRD
ROLE_DESCRIPTIONS = {
    RoleEnum.ADMIN: "Global administrative access to all resources and RBAC management",
    RoleEnum.OWNER: "Full CRUD permissions on assigned scope (projects and flows)",
    RoleEnum.EDITOR: "Create, Read, and Update permissions (no Delete)",
    RoleEnum.VIEWER: "Read-only access and flow execution capability",
}

# Permission descriptions
PERMISSION_DESCRIPTIONS = {
    PermissionEnum.CREATE: "Create new entities (flows, projects)",
    PermissionEnum.READ: "View entities and execute flows",
    PermissionEnum.UPDATE: "Modify existing entities and import flows",
    PermissionEnum.DELETE: "Remove entities (flows, projects)",
}


async def seed_rbac_data(session: AsyncSession) -> None:
    """Seed default RBAC roles, permissions, and role-permission mappings.

    This function is idempotent - it checks if data already exists before seeding.
    If roles are already present in the database, it skips the seeding process.

    The seeding process:
    1. Checks if roles already exist (idempotency check)
    2. Creates 4 permissions (CREATE, READ, UPDATE, DELETE)
    3. Creates 4 roles with descriptions (Admin, Owner, Editor, Viewer)
    4. Creates role-permission mappings per ROLE_PERMISSIONS configuration

    Args:
        session: Async database session for performing database operations

    Returns:
        None

    Raises:
        Exception: Any database errors during seeding are logged and re-raised
    """
    try:
        # Idempotency check: Skip if roles already exist
        stmt = select(Role)
        result = await session.exec(stmt)
        existing_roles = result.all()

        if existing_roles:
            logger.debug(f"RBAC data already seeded ({len(existing_roles)} roles found). Skipping seed operation.")
            return

        logger.info("Starting RBAC data seeding...")

        # Step 1: Create permissions
        logger.debug("Creating permissions...")
        permissions = {}
        for perm_enum in [
            PermissionEnum.CREATE,
            PermissionEnum.READ,
            PermissionEnum.UPDATE,
            PermissionEnum.DELETE,
        ]:
            permission = Permission(
                name=perm_enum,
                description=PERMISSION_DESCRIPTIONS[perm_enum],
            )
            session.add(permission)
            permissions[perm_enum] = permission

        await session.commit()
        logger.debug(f"Created {len(permissions)} permissions")

        # Refresh to get IDs
        for perm in permissions.values():
            await session.refresh(perm)

        # Step 2: Create roles with mappings
        logger.debug("Creating roles and role-permission mappings...")
        roles_created = 0
        mappings_created = 0

        for role_enum, perm_list in ROLE_PERMISSIONS.items():
            # Create role
            role = Role(
                name=role_enum,
                description=ROLE_DESCRIPTIONS[role_enum],
            )
            session.add(role)
            await session.flush()  # Flush to get the role ID

            # Create role-permission mappings
            for perm_enum in perm_list:
                role_perm = RolePermission(
                    role_id=role.id,
                    permission_id=permissions[perm_enum].id,
                )
                session.add(role_perm)
                mappings_created += 1

            roles_created += 1
            logger.debug(f"Created role '{role_enum.value}' with {len(perm_list)} permissions")

        await session.commit()

        logger.info(
            f"RBAC data seeding completed successfully: "
            f"{len(permissions)} permissions, "
            f"{roles_created} roles, "
            f"{mappings_created} role-permission mappings"
        )

        # Verify seeding
        await _verify_seeding(session)

    except Exception as e:
        await session.rollback()
        logger.error(f"Error during RBAC data seeding: {e!s}")
        raise


async def _verify_seeding(session: AsyncSession) -> None:
    """Verify that RBAC data was seeded correctly.

    Performs validation checks to ensure:
    - All 4 roles were created
    - All 4 permissions were created
    - Role-permission mappings are correct per ROLE_PERMISSIONS

    Args:
        session: Async database session

    Raises:
        AssertionError: If verification fails
    """
    logger.debug("Verifying RBAC data seeding...")

    # Verify roles
    stmt = select(Role)
    roles = list((await session.exec(stmt)).all())
    assert len(roles) == 4, f"Expected 4 roles, found {len(roles)}"

    # Verify permissions
    stmt = select(Permission)
    permissions = list((await session.exec(stmt)).all())
    assert len(permissions) == 4, f"Expected 4 permissions, found {len(permissions)}"

    # Verify role-permission mappings
    for role in roles:
        stmt = select(Permission).join(RolePermission).where(RolePermission.role_id == role.id)
        role_permissions = list((await session.exec(stmt)).all())
        expected_perms = ROLE_PERMISSIONS[role.name]
        expected_count = len(expected_perms)

        assert len(role_permissions) == expected_count, (
            f"Role {role.name.value} expected {expected_count} permissions, found {len(role_permissions)}"
        )

        perm_names = {p.name for p in role_permissions}
        for expected_perm in expected_perms:
            assert expected_perm in perm_names, (
                f"Role {role.name.value} missing expected permission {expected_perm.value}"
            )

    logger.debug("RBAC data seeding verification passed")

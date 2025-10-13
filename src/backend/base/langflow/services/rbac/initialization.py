"""RBAC Initialization and Seeding Logic.

This module provides idempotent seeding of permissions and system roles
into the database on first application startup (Task 1.3).

AppGraph Impact Subgraph:
- system_initialization_flow (LSN-065): Application startup orchestration
- permission_catalog_seeder (LSN-066): Permission table population
- system_role_seeder (LSN-067): System role and role-permission creation
"""

from datetime import datetime, timezone
from uuid import uuid4

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
)
from langflow.services.deps import get_db_service, get_settings_service
from langflow.services.rbac.constants import (
    PERMISSIONS,
    SYSTEM_ROLES,
    TOTAL_PERMISSIONS_COUNT,
    TOTAL_SYSTEM_ROLES_COUNT,
)


async def seed_permissions_and_roles() -> None:
    """Seed permission catalog and system roles into the database.

    AppGraph Node: system_initialization_flow (LSN-065)

    This function is idempotent and safe to call multiple times.
    It will:
    1. Check if seeding has already been done
    2. Seed permissions from PERMISSIONS constant
    3. Seed system roles from SYSTEM_ROLES constant
    4. Create role-permission associations

    The function logs progress and completion status.

    Note: RBAC initialization is automatically skipped when running in testing mode
    (LANGFLOW_TESTING=true) to avoid conflicts with test fixtures.
    """
    # Skip RBAC initialization in testing mode to avoid conflicts with test fixtures
    settings_service = get_settings_service()
    if settings_service.settings.testing:
        logger.debug("Running in testing mode, skipping RBAC initialization to avoid fixture conflicts")
        return

    db_service = get_db_service()

    try:
        async with db_service.with_session() as session:
            # Check if already seeded (idempotency check)
            if await _is_already_seeded(session):
                logger.debug("RBAC permissions and roles already seeded, skipping initialization")
                return

            logger.info("Starting RBAC initialization: seeding permissions and system roles")
            start_time = datetime.now(timezone.utc)

            # Seed permissions
            permission_map = await _seed_permissions(session)
            logger.info(f"✓ Seeded {len(permission_map)} permissions")

            # Seed system roles
            role_count = await _seed_system_roles(session, permission_map)
            logger.info(f"✓ Seeded {role_count} system roles")

            # Commit the transaction
            await session.commit()

            elapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(
                f"✓ RBAC initialization complete in {elapsed_time:.2f}s "
                f"({TOTAL_PERMISSIONS_COUNT} permissions, {TOTAL_SYSTEM_ROLES_COUNT} roles)"
            )

    except Exception as e:
        logger.exception(f"Error during RBAC initialization: {e}")
        raise


async def _is_already_seeded(session: AsyncSession) -> bool:
    """Check if permissions and roles have already been seeded.

    Args:
        session: Database session

    Returns:
        True if seeding has been completed, False otherwise
    """
    # Check if any permissions exist
    result = await session.exec(select(Permission).limit(1))
    permission_exists = result.first() is not None

    # Check if any system roles exist
    result = await session.exec(select(Role).where(Role.is_system_role == True).limit(1))  # noqa: E712
    role_exists = result.first() is not None

    return permission_exists and role_exists


async def _seed_permissions(session: AsyncSession) -> dict[str, Permission]:
    """Seed permissions from the permission catalog.

    AppGraph Node: permission_catalog_seeder (LSN-066)

    Args:
        session: Database session

    Returns:
        Dictionary mapping permission names to Permission objects
    """
    permission_map: dict[str, Permission] = {}

    for perm_tuple in PERMISSIONS:
        name, display_name, resource_type, action, scope_level = perm_tuple

        # Check if permission already exists
        result = await session.exec(select(Permission).where(Permission.resource_type == resource_type, Permission.action == action))
        existing = result.first()

        if existing:
            permission_map[name] = existing
            logger.debug(f"Permission already exists: {name}")
            continue

        # Create new permission
        permission = Permission(
            id=uuid4(),
            name=name,  # ✅ ADDED: Permission identifier (e.g., "flow.create")
            resource_type=resource_type,
            action=action,
            display_name=display_name,
            description=None,  # Can be added later if needed
            scope_level=scope_level,  # ✅ ADDED: Hierarchical scope level
            is_active=True,
            is_system_permission=True,  # ✅ ADDED: Mark as system permission
            created_at=datetime.now(timezone.utc),
        )
        session.add(permission)
        permission_map[name] = permission
        logger.debug(f"Created permission: {name}")

    # Flush to get IDs
    await session.flush()

    return permission_map


async def _seed_system_roles(session: AsyncSession, permission_map: dict[str, Permission]) -> int:
    """Seed system roles and their permission associations.

    AppGraph Node: system_role_seeder (LSN-067)

    Args:
        session: Database session
        permission_map: Dictionary mapping permission names to Permission objects

    Returns:
        Number of roles created
    """
    role_count = 0

    for role_name, role_data in SYSTEM_ROLES.items():
        # Check if role already exists
        result = await session.exec(select(Role).where(Role.name == role_name))
        existing_role = result.first()

        if existing_role:
            logger.debug(f"System role already exists: {role_name}")
            continue

        # Create new role
        role = Role(
            id=uuid4(),
            name=role_name,
            display_name=role_data["display_name"],
            description=role_data["description"],
            is_system_role=True,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(role)
        await session.flush()  # Flush to get role ID
        role_count += 1

        # Create role-permission associations
        permission_count = 0
        for perm_name in role_data["permissions"]:
            if perm_name not in permission_map:
                logger.warning(f"Permission '{perm_name}' not found in permission_map for role '{role_name}'")
                continue

            permission = permission_map[perm_name]

            # Check if association already exists
            result = await session.exec(
                select(RolePermission).where(
                    RolePermission.role_id == role.id, RolePermission.permission_id == permission.id
                )
            )
            if result.first():
                continue

            # Create role-permission association
            role_permission = RolePermission(
                id=uuid4(), role_id=role.id, permission_id=permission.id
            )
            session.add(role_permission)
            permission_count += 1

        logger.debug(f"Created system role '{role_name}' with {permission_count} permissions")

    return role_count

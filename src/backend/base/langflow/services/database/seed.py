"""Database seeding utilities for RBAC system.

Implements GAP #4 and GAP #5 from RBAC_PHASE1_AUDIT_REPORT:
- Permission catalog seeding (GAP #4)
- System role seeding (GAP #5)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


async def seed_permissions(session: AsyncSession) -> None:
    """Seed permission catalog into the database.

    Implements GAP #4 from audit report.
    Uses upsert logic to avoid duplicates on repeated runs.

    Args:
        session: Async database session
    """
    from langflow.services.database.models.rbac.permission import PERMISSION_CATALOG, Permission
    from sqlmodel import select

    logger.info("Seeding permission catalog")

    for perm_data in PERMISSION_CATALOG:
        # Check if permission already exists
        perm_id = f"{perm_data['resource_type']}:{perm_data['action']}"
        result = await session.exec(select(Permission).where(Permission.id == perm_id))
        existing = result.first()

        if existing:
            # Update description if changed
            if existing.description != perm_data.get("description"):
                existing.description = perm_data.get("description")
                session.add(existing)
                logger.debug(f"Updated permission: {perm_id}")
        else:
            # Create new permission
            perm = Permission(**perm_data)
            session.add(perm)
            logger.debug(f"Created permission: {perm_id}")

    await session.commit()
    logger.info(f"Successfully seeded {len(PERMISSION_CATALOG)} permissions")


async def seed_system_roles(session: AsyncSession) -> None:
    """Seed system roles into the database.

    Implements GAP #5 from audit report.
    Creates the 4 predefined system roles: Admin, Editor, Viewer, Deployer.
    Uses upsert logic to avoid duplicates on repeated runs.

    Args:
        session: Async database session
    """
    from langflow.services.database.models.rbac.role import SYSTEM_ROLES, Role
    from sqlmodel import select

    logger.info("Seeding system roles")

    for role_data in SYSTEM_ROLES:
        # Check if role already exists
        result = await session.exec(select(Role).where(Role.name == role_data["name"]))
        existing = result.first()

        if existing:
            # Update permissions and description if changed
            if existing.permissions != role_data["permissions"] or existing.description != role_data.get(
                "description"
            ):
                existing.permissions = role_data["permissions"]
                existing.description = role_data.get("description")
                existing.version += 1  # Increment version on update
                session.add(existing)
                logger.debug(f"Updated system role: {role_data['name']}")
        else:
            # Create new role
            role = Role(
                name=role_data["name"],
                description=role_data.get("description"),
                permissions=role_data["permissions"],
                is_system_role=True,
            )
            session.add(role)
            logger.debug(f"Created system role: {role_data['name']}")

    await session.commit()
    logger.info(f"Successfully seeded {len(SYSTEM_ROLES)} system roles")


async def seed_rbac_data(session: AsyncSession) -> None:
    """Seed all RBAC data (permissions and system roles).

    This is the main entry point for seeding RBAC data.
    Should be called during application initialization.

    Args:
        session: Async database session
    """
    logger.info("Starting RBAC data seeding")
    await seed_permissions(session)
    await seed_system_roles(session)
    logger.info("RBAC data seeding completed")

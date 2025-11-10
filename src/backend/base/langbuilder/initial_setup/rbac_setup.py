"""
RBAC seed data initialization.

This module provides functionality to populate the database with predefined roles,
permissions, and role-permission mappings for the RBAC system. The initialization
is idempotent and can be run multiple times safely.

Predefined Roles (per PRD 1.2):
- Admin: All permissions on all scopes (global assignment)
- Owner: Create, Read, Update, Delete on assigned scope
- Editor: Create, Read, Update (no Delete) on assigned scope
- Viewer: Read only on assigned scope

Permissions (per PRD 1.1, 1.2):
- CRUD operations (Create, Read, Update, Delete) for Flow and Project scopes
- Total: 8 permissions (4 CRUD × 2 entity types)

Special Permission Rules (per PRD 1.2):
- Read permission enables: Flow execution, saving, exporting, downloading
- Update permission enables: Flow/Project import
"""

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
)


# Predefined roles as per PRD 1.2
PREDEFINED_ROLES = [
    {
        "name": "Admin",
        "description": "Full access to all resources and actions across all scopes",
        "is_system": True,
    },
    {
        "name": "Owner",
        "description": "Full CRUD access to assigned scope (Flow or Project)",
        "is_system": True,
    },
    {
        "name": "Editor",
        "description": "Create, Read, and Update access to assigned scope (no Delete)",
        "is_system": True,
    },
    {
        "name": "Viewer",
        "description": "Read-only access to assigned scope",
        "is_system": True,
    },
]


# Predefined permissions as per PRD 1.1, 1.2
# CRUD operations for Flow and Project scopes
# Permission names are generic (Create, Read, Update, Delete) with uniqueness enforced by (name, scope_type)
PREDEFINED_PERMISSIONS = [
    # Flow permissions
    {
        "name": "Create",
        "scope_type": "Flow",
        "description": "Create new flows",
    },
    {
        "name": "Read",
        "scope_type": "Flow",
        "description": "View flows, execute flows, save flows, export flows, download flows",
    },
    {
        "name": "Update",
        "scope_type": "Flow",
        "description": "Modify existing flows, import flows",
    },
    {
        "name": "Delete",
        "scope_type": "Flow",
        "description": "Delete flows",
    },
    # Project permissions
    {
        "name": "Create",
        "scope_type": "Project",
        "description": "Create new projects",
    },
    {
        "name": "Read",
        "scope_type": "Project",
        "description": "View projects and their contents",
    },
    {
        "name": "Update",
        "scope_type": "Project",
        "description": "Modify existing projects, import projects",
    },
    {
        "name": "Delete",
        "scope_type": "Project",
        "description": "Delete projects",
    },
]


# Role-permission mappings as per PRD 1.2
# Admin: All permissions (8 total)
# Owner: All CRUD permissions (8 total)
# Editor: Create, Read, Update only (6 total - 3 per scope)
# Viewer: Read only (2 total - 1 per scope)
# Format: List of tuples (permission_name, scope_type)
ROLE_PERMISSION_MAPPINGS = {
    "Admin": [
        ("Create", "Flow"),
        ("Read", "Flow"),
        ("Update", "Flow"),
        ("Delete", "Flow"),
        ("Create", "Project"),
        ("Read", "Project"),
        ("Update", "Project"),
        ("Delete", "Project"),
    ],
    "Owner": [
        ("Create", "Flow"),
        ("Read", "Flow"),
        ("Update", "Flow"),
        ("Delete", "Flow"),
        ("Create", "Project"),
        ("Read", "Project"),
        ("Update", "Project"),
        ("Delete", "Project"),
    ],
    "Editor": [
        ("Create", "Flow"),
        ("Read", "Flow"),
        ("Update", "Flow"),
        ("Create", "Project"),
        ("Read", "Project"),
        ("Update", "Project"),
    ],
    "Viewer": [
        ("Read", "Flow"),
        ("Read", "Project"),
    ],
}


async def initialize_rbac_data(session: AsyncSession) -> None:
    """
    Initialize RBAC data: roles, permissions, and role-permission mappings.

    This function is idempotent and can be run multiple times safely.
    It checks for existing data before inserting to avoid duplicates.

    Args:
        session: Active database session for executing queries

    Raises:
        Exception: If there are issues creating RBAC data
    """
    try:
        logger.debug("Initializing RBAC data...")

        # Step 1: Create predefined permissions (idempotent)
        permissions_created = await _create_permissions(session)
        logger.debug(f"Created {permissions_created} new permissions")

        # Step 2: Create predefined roles (idempotent)
        roles_created = await _create_roles(session)
        logger.debug(f"Created {roles_created} new roles")

        # Step 3: Create role-permission mappings (idempotent)
        mappings_created = await _create_role_permission_mappings(session)
        logger.debug(f"Created {mappings_created} new role-permission mappings")

        # Commit all changes
        await session.commit()
        logger.info(
            f"RBAC initialization complete: {permissions_created} permissions, "
            f"{roles_created} roles, {mappings_created} role-permission mappings"
        )

    except Exception as e:
        await session.rollback()
        logger.exception("Error initializing RBAC data")
        raise


async def _create_permissions(session: AsyncSession) -> int:
    """
    Create predefined permissions if they don't exist.

    Args:
        session: Active database session

    Returns:
        Number of permissions created
    """
    created_count = 0

    for perm_data in PREDEFINED_PERMISSIONS:
        # Check if permission already exists (by name AND scope_type for uniqueness)
        stmt = select(Permission).where(
            Permission.name == perm_data["name"],
            Permission.scope_type == perm_data["scope_type"],
        )
        existing = (await session.exec(stmt)).first()

        if not existing:
            # Create new permission
            permission = Permission(
                name=perm_data["name"],
                scope_type=perm_data["scope_type"],
                description=perm_data["description"],
            )
            session.add(permission)
            created_count += 1
            logger.debug(f"Created permission: {perm_data['name']} ({perm_data['scope_type']})")
        else:
            logger.debug(f"Permission already exists: {perm_data['name']} ({perm_data['scope_type']})")

    return created_count


async def _create_roles(session: AsyncSession) -> int:
    """
    Create predefined roles if they don't exist.

    Args:
        session: Active database session

    Returns:
        Number of roles created
    """
    created_count = 0

    for role_data in PREDEFINED_ROLES:
        # Check if role already exists (by name)
        stmt = select(Role).where(Role.name == role_data["name"])
        existing = (await session.exec(stmt)).first()

        if not existing:
            # Create new role
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                is_system=role_data["is_system"],
            )
            session.add(role)
            created_count += 1
            logger.debug(f"Created role: {role_data['name']}")
        else:
            logger.debug(f"Role already exists: {role_data['name']}")

    return created_count


async def _create_role_permission_mappings(session: AsyncSession) -> int:
    """
    Create role-permission mappings if they don't exist.

    Args:
        session: Active database session

    Returns:
        Number of role-permission mappings created
    """
    created_count = 0

    # First, fetch all roles and permissions for efficient lookup
    roles_stmt = select(Role)
    roles = (await session.exec(roles_stmt)).all()
    roles_map = {role.name: role for role in roles}

    permissions_stmt = select(Permission)
    permissions = (await session.exec(permissions_stmt)).all()
    # Index by (name, scope_type) tuple since names are not unique
    permissions_map = {(perm.name, perm.scope_type): perm for perm in permissions}

    # Create mappings for each role
    for role_name, perm_tuples in ROLE_PERMISSION_MAPPINGS.items():
        role = roles_map.get(role_name)
        if not role:
            logger.warning(f"Role not found: {role_name}, skipping mappings")
            continue

        for perm_name, scope_type in perm_tuples:
            permission = permissions_map.get((perm_name, scope_type))
            if not permission:
                logger.warning(f"Permission not found: {perm_name} ({scope_type}), skipping mapping")
                continue

            # Check if mapping already exists
            mapping_stmt = select(RolePermission).where(
                RolePermission.role_id == role.id,
                RolePermission.permission_id == permission.id,
            )
            existing_mapping = (await session.exec(mapping_stmt)).first()

            if not existing_mapping:
                # Create new mapping
                mapping = RolePermission(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                session.add(mapping)
                created_count += 1
                logger.debug(f"Created mapping: {role_name} -> {perm_name} ({scope_type})")
            else:
                logger.debug(f"Mapping already exists: {role_name} -> {perm_name} ({scope_type})")

    return created_count

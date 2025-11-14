"""
Data migration script for RBAC role assignments.

This script migrates existing users, projects, and flows to the RBAC system by
assigning appropriate roles based on current ownership. It ensures backward
compatibility by granting:
- Superusers: Global Admin role
- Regular users: Owner role for their flows and projects
- Starter Project: Immutable Owner assignment

The script is idempotent and can be safely run multiple times.
"""

import asyncio
from typing import Any

from loguru import logger
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.services.database.models.flow.model import Flow
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from langbuilder.services.database.models.user.model import User


async def migrate_existing_users_to_rbac(
    session: AsyncSession,
    dry_run: bool = True
) -> dict[str, Any]:
    """
    Migrate existing users/projects/flows to RBAC assignments.

    This function assigns RBAC roles to all existing users based on their current
    ownership of flows and projects. Superusers receive global Admin role, while
    regular users receive Owner role for each flow and project they own.

    Args:
        session: Active database session for executing queries
        dry_run: If True, rolls back changes and returns what would be created.
                 If False, commits changes to the database.

    Returns:
        Dictionary with migration results:
        - status: "success", "dry_run", or "error"
        - created/would_create: Number of assignments created
        - skipped/would_skip: Number of assignments skipped (already exist)
        - errors: List of error messages encountered

    Raises:
        ValueError: If Admin or Owner roles are not found in database
        Exception: For database or other unexpected errors
    """
    created_count = 0
    skipped_count = 0
    errors = []

    try:
        logger.info(f"Starting RBAC migration (dry_run={dry_run})...")

        # Get all users
        users_stmt = select(User)
        users_result = await session.exec(users_stmt)
        users_list = users_result.all()
        logger.debug(f"Found {len(users_list)} users to migrate")

        # Get Admin and Owner roles
        admin_role_stmt = select(Role).where(Role.name == "Admin")
        admin_role_result = await session.exec(admin_role_stmt)
        admin_role = admin_role_result.first()

        owner_role_stmt = select(Role).where(Role.name == "Owner")
        owner_role_result = await session.exec(owner_role_stmt)
        owner_role = owner_role_result.first()

        if not admin_role or not owner_role:
            msg = "Admin and Owner roles not found. Run RBAC seed data initialization first."
            raise ValueError(msg)

        logger.debug(f"Admin role ID: {admin_role.id}, Owner role ID: {owner_role.id}")

        # Process each user
        for user in users_list:
            try:
                if user.is_superuser:
                    # Superusers get global Admin role
                    logger.debug(f"Processing superuser: {user.username} (ID: {user.id})")

                    existing_stmt = select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.role_id == admin_role.id,
                        UserRoleAssignment.scope_type == "global",
                    )
                    existing_result = await session.exec(existing_stmt)

                    if not existing_result.first():
                        assignment = UserRoleAssignment(
                            user_id=user.id,
                            role_id=admin_role.id,
                            scope_type="global",
                            scope_id=None,
                        )
                        session.add(assignment)
                        created_count += 1
                        logger.debug(f"Created global Admin assignment for superuser {user.username}")
                    else:
                        skipped_count += 1
                        logger.debug(f"Skipped superuser {user.username} (already has Admin role)")
                else:
                    # Regular users: Owner of their flows and projects
                    logger.debug(f"Processing regular user: {user.username} (ID: {user.id})")

                    # Process flows owned by this user
                    flows_stmt = select(Flow).where(Flow.user_id == user.id)
                    flows_result = await session.exec(flows_stmt)
                    flows_list = flows_result.all()

                    logger.debug(f"Found {len(flows_list)} flows for user {user.username}")

                    for flow in flows_list:
                        existing_stmt = select(UserRoleAssignment).where(
                            UserRoleAssignment.user_id == user.id,
                            UserRoleAssignment.role_id == owner_role.id,
                            UserRoleAssignment.scope_type == "flow",
                            UserRoleAssignment.scope_id == flow.id,
                        )
                        existing_result = await session.exec(existing_stmt)

                        if not existing_result.first():
                            assignment = UserRoleAssignment(
                                user_id=user.id,
                                role_id=owner_role.id,
                                scope_type="flow",
                                scope_id=flow.id,
                            )
                            session.add(assignment)
                            created_count += 1
                            logger.debug(f"Created flow Owner assignment for {user.username} on flow {flow.name}")
                        else:
                            skipped_count += 1

                    # Process projects/folders owned by this user
                    folders_stmt = select(Folder).where(Folder.user_id == user.id)
                    folders_result = await session.exec(folders_stmt)
                    folders_list = folders_result.all()

                    logger.debug(f"Found {len(folders_list)} projects for user {user.username}")

                    for folder in folders_list:
                        existing_stmt = select(UserRoleAssignment).where(
                            UserRoleAssignment.user_id == user.id,
                            UserRoleAssignment.role_id == owner_role.id,
                            UserRoleAssignment.scope_type == "project",
                            UserRoleAssignment.scope_id == folder.id,
                        )
                        existing_result = await session.exec(existing_stmt)
                        existing_assignment = existing_result.first()

                        if not existing_assignment:
                            # Check if this is the Starter Project
                            is_starter = folder.name == "Starter Project"

                            assignment = UserRoleAssignment(
                                user_id=user.id,
                                role_id=owner_role.id,
                                scope_type="project",
                                scope_id=folder.id,
                                is_immutable=is_starter,
                            )
                            session.add(assignment)
                            created_count += 1
                            logger.debug(
                                f"Created project Owner assignment for {user.username} "
                                f"on project {folder.name} (immutable={is_starter})"
                            )
                        else:
                            # Check if we need to update immutability for Starter Project
                            if folder.name == "Starter Project" and not existing_assignment.is_immutable:
                                existing_assignment.is_immutable = True
                                session.add(existing_assignment)
                                logger.debug(
                                    f"Updated Starter Project assignment to immutable "
                                    f"for user {user.username}"
                                )
                            skipped_count += 1

            except Exception as e:
                error_msg = f"Error migrating user {user.username} (ID: {user.id}): {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        # Commit or rollback based on dry_run flag
        if not dry_run:
            await session.commit()
            logger.info(
                f"RBAC migration complete: {created_count} assignments created, "
                f"{skipped_count} skipped"
            )
            return {
                "status": "success",
                "created": created_count,
                "skipped": skipped_count,
                "errors": errors,
            }
        else:
            await session.rollback()
            logger.info(
                f"RBAC migration dry run complete: {created_count} assignments would be created, "
                f"{skipped_count} would be skipped"
            )
            return {
                "status": "dry_run",
                "would_create": created_count,
                "would_skip": skipped_count,
                "errors": errors,
            }

    except Exception as e:
        await session.rollback()
        error_msg = f"Fatal error during RBAC migration: {str(e)}"
        logger.exception(error_msg)
        return {
            "status": "error",
            "error": str(e),
            "created": created_count,
            "skipped": skipped_count,
            "errors": errors,
        }


async def main():
    """
    Main entry point for running the migration script standalone.

    This function sets up the database connection and runs the migration.
    Use --dry-run flag to preview changes without committing.
    """
    import sys

    from langbuilder.services.database.utils import session_getter

    # Check for dry-run flag
    dry_run = "--dry-run" in sys.argv

    logger.info("=" * 60)
    logger.info("RBAC Data Migration Script")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN (no changes will be committed)' if dry_run else 'LIVE (changes will be committed)'}")
    logger.info("=" * 60)

    # Get database session
    async with session_getter() as session:
        result = await migrate_existing_users_to_rbac(session, dry_run=dry_run)

        logger.info("")
        logger.info("=" * 60)
        logger.info("Migration Results")
        logger.info("=" * 60)
        logger.info(f"Status: {result['status']}")

        if result["status"] == "dry_run":
            logger.info(f"Would create: {result['would_create']} assignments")
            logger.info(f"Would skip: {result['would_skip']} assignments")
        elif result["status"] == "success":
            logger.info(f"Created: {result['created']} assignments")
            logger.info(f"Skipped: {result['skipped']} assignments")
        elif result["status"] == "error":
            logger.error(f"Error: {result['error']}")
            logger.info(f"Partial created: {result['created']} assignments")

        if result["errors"]:
            logger.warning(f"Errors encountered: {len(result['errors'])}")
            for error in result["errors"]:
                logger.warning(f"  - {error}")

        logger.info("=" * 60)

        if dry_run:
            logger.info("")
            logger.info("To apply these changes, run the script without --dry-run flag:")
            logger.info("  python -m langbuilder.scripts.migrate_rbac_data")


if __name__ == "__main__":
    asyncio.run(main())

"""Migrate existing users to RBAC

Revision ID: d73ae349cf9c
Revises: c62fe238bf8b
Create Date: 2025-11-05 10:00:00.000000

This data migration assigns RBAC roles to all existing users based on their
current ownership of flows and projects. It ensures backward compatibility
by granting appropriate roles:
- Superusers: Global Admin role
- Regular users: Owner role for their flows and projects
- Starter Project: Immutable Owner assignment
"""

from typing import Optional, Sequence, Union
from uuid import uuid4

from alembic import op
from loguru import logger
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "d73ae349cf9c"
down_revision: Union[str, None] = "c62fe238bf8b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Run the RBAC data migration.

    This migration assigns RBAC roles using synchronous SQL operations
    to avoid event loop conflicts with Alembic's async environment.
    """
    logger.info("Running RBAC data migration...")

    # Get the current database connection from Alembic
    connection = op.get_bind()

    created_count = 0
    skipped_count = 0

    try:
        # Get Admin and Owner role IDs
        admin_role = connection.execute(text("SELECT id FROM role WHERE name = 'Admin'")).fetchone()
        owner_role = connection.execute(text("SELECT id FROM role WHERE name = 'Owner'")).fetchone()

        if not admin_role or not owner_role:
            logger.error("Admin and Owner roles not found. Run RBAC seed data initialization first.")
            raise ValueError("Required roles not found in database")

        admin_role_id = admin_role[0]
        owner_role_id = owner_role[0]

        logger.debug(f"Admin role ID: {admin_role_id}, Owner role ID: {owner_role_id}")

        # Get all users
        users = connection.execute(text("SELECT id, username, is_superuser FROM user")).fetchall()
        logger.debug(f"Found {len(users)} users to migrate")

        for user in users:
            user_id, username, is_superuser = user

            if is_superuser:
                # Superusers get global Admin role
                logger.debug(f"Processing superuser: {username} (ID: {user_id})")

                # Check if assignment already exists
                existing = connection.execute(text(
                    "SELECT id FROM user_role_assignment WHERE user_id = :user_id "
                    "AND role_id = :role_id AND scope_type = 'Global'"
                ), {"user_id": user_id, "role_id": admin_role_id}).fetchone()

                if not existing:
                    connection.execute(text(
                        "INSERT INTO user_role_assignment (id, user_id, role_id, scope_type, scope_id, is_immutable) "
                        "VALUES (:id, :user_id, :role_id, :scope_type, NULL, :is_immutable)"
                    ), {
                        "id": str(uuid4()),
                        "user_id": user_id,
                        "role_id": admin_role_id,
                        "scope_type": "Global",
                        "is_immutable": False
                    })
                    created_count += 1
                    logger.debug(f"  Created global Admin assignment for superuser {username}")
                else:
                    skipped_count += 1
                    logger.debug(f"  Skipped (already exists): global Admin for {username}")

            # Process user's flows (both superusers and regular users)
            flows = connection.execute(text(
                "SELECT f.id, f.name, f.folder_id, fo.name as folder_name "
                "FROM flow f LEFT JOIN folder fo ON f.folder_id = fo.id "
                "WHERE f.user_id = :user_id"
            ), {"user_id": user_id}).fetchall()

            for flow in flows:
                flow_id, flow_name, folder_id, folder_name = flow

                # Check if this flow is in a Starter Project folder
                # (supports both "Starter Project" and "Starter Project - username")
                is_in_starter_project = False
                if folder_name:
                    # Check exact match or pattern match
                    is_in_starter_project = (
                        folder_name == "Starter Project" or
                        folder_name.startswith("Starter Project - ")
                    )

                # Check if assignment already exists
                existing = connection.execute(text(
                    "SELECT id FROM user_role_assignment WHERE user_id = :user_id "
                    "AND role_id = :role_id AND scope_type = 'Flow' AND scope_id = :scope_id"
                ), {"user_id": user_id, "role_id": owner_role_id, "scope_id": flow_id}).fetchone()

                if not existing:
                    connection.execute(text(
                        "INSERT INTO user_role_assignment (id, user_id, role_id, scope_type, scope_id, is_immutable) "
                        "VALUES (:id, :user_id, :role_id, :scope_type, :scope_id, :is_immutable)"
                    ), {
                        "id": str(uuid4()),
                        "user_id": user_id,
                        "role_id": owner_role_id,
                        "scope_type": "Flow",
                        "scope_id": flow_id,
                        "is_immutable": is_in_starter_project  # Mark Starter Project flows as immutable
                    })
                    created_count += 1
                    immutable_tag = " (immutable)" if is_in_starter_project else ""
                    logger.debug(f"  Created Owner assignment for flow '{flow_name}'{immutable_tag}")
                else:
                    skipped_count += 1

            # Process user's projects (folders)
            projects = connection.execute(text(
                "SELECT id, name FROM folder WHERE user_id = :user_id"
            ), {"user_id": user_id}).fetchall()

            for project in projects:
                project_id, project_name = project

                # Check if this is a Starter Project
                # (supports both "Starter Project" and "Starter Project - username")
                is_starter = (
                    project_name == "Starter Project" or
                    project_name.startswith("Starter Project - ")
                )

                # Check if assignment already exists
                existing = connection.execute(text(
                    "SELECT id FROM user_role_assignment WHERE user_id = :user_id "
                    "AND role_id = :role_id AND scope_type = 'Project' AND scope_id = :scope_id"
                ), {"user_id": user_id, "role_id": owner_role_id, "scope_id": project_id}).fetchone()

                if not existing:
                    connection.execute(text(
                        "INSERT INTO user_role_assignment (id, user_id, role_id, scope_type, scope_id, is_immutable) "
                        "VALUES (:id, :user_id, :role_id, :scope_type, :scope_id, :is_immutable)"
                    ), {
                        "id": str(uuid4()),
                        "user_id": user_id,
                        "role_id": owner_role_id,
                        "scope_type": "Project",
                        "scope_id": project_id,
                        "is_immutable": is_starter
                    })
                    created_count += 1
                    immutable_note = " (immutable)" if is_starter else ""
                    logger.debug(f"  Created Owner assignment for project '{project_name}'{immutable_note}")
                else:
                    skipped_count += 1
                    # Update is_immutable if this is a Starter Project
                    if is_starter:
                        connection.execute(text(
                            "UPDATE user_role_assignment SET is_immutable = :is_immutable "
                            "WHERE user_id = :user_id AND role_id = :role_id "
                            "AND scope_type = 'Project' AND scope_id = :scope_id"
                        ), {
                            "is_immutable": True,
                            "user_id": user_id,
                            "role_id": owner_role_id,
                            "scope_id": project_id
                        })
                        logger.debug(f"  Updated Starter Project '{project_name}' to immutable")

        logger.info(
            f"RBAC migration successful: {created_count} assignments created, "
            f"{skipped_count} skipped (already existed)"
        )

    except Exception as e:
        logger.exception("Error during RBAC data migration")
        raise


def downgrade() -> None:
    """
    Rollback the RBAC data migration.

    This removes all UserRoleAssignment records that were created by the migration.
    Note: This is a destructive operation and should be used with caution.
    """
    logger.info("Rolling back RBAC data migration...")

    # Import here to avoid circular dependencies
    from sqlalchemy import text

    connection = op.get_bind()

    # Delete all user role assignments
    # Note: This is a simple rollback that removes all assignments.
    # In a more sophisticated scenario, you might want to track which
    # assignments were created by the migration and only delete those.
    connection.execute(text("DELETE FROM user_role_assignment"))

    logger.info("RBAC data migration rolled back successfully")

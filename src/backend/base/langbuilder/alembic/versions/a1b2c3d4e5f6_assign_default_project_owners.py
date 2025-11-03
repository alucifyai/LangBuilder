"""Assign Owner role to all users for their Default Project.

Revision ID: a1b2c3d4e5f6
Revises: d6c803ed2d15
Create Date: 2025-11-01 13:49:45.000000

This data migration implements PRD Epic 1 Story 1.4 requirement for protecting
existing user ownership by auto-assigning Owner role to all existing users for
their Default Project with is_immutable=True.

The migration is idempotent - it can be run multiple times safely without
creating duplicate assignments or errors.
"""
# ruff: noqa: TRY003, EM101, EM102, INP001

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import uuid4

from alembic import op
from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "d6c803ed2d15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Default folder name constant (from folder/constants.py)
DEFAULT_FOLDER_NAME = "Starter Project"


def upgrade() -> None:
    """Assign Owner role to all users for their Default Project.

    This migration:
    1. Gets Owner role ID from the role table
    2. Finds all users and their Default Project (folder with name "Starter Project")
    3. Creates immutable Owner role assignments for each user-project pair
    4. Is idempotent - checks for existing assignments before creating
    5. Logs progress and results
    """
    conn = op.get_bind()

    # Verify required tables exist
    inspector = Inspector.from_engine(conn)
    table_names = inspector.get_table_names()

    required_tables = ["role", "user", "folder", "userroleassignment"]
    missing_tables = [t for t in required_tables if t not in table_names]

    if missing_tables:
        logger.warning(
            f"Skipping migration: Required tables missing: {missing_tables}. "
            "This is expected if running migrations in development."
        )
        return

    try:
        # Step 1: Get Owner role ID
        owner_role_result = conn.execute(text("SELECT id FROM role WHERE name = 'OWNER'")).fetchone()

        if not owner_role_result:
            raise RuntimeError(
                "Owner role not found in database. Ensure RBAC seed migration (rbac_seed.py) has been executed."
            )

        owner_role_id = owner_role_result[0]
        logger.info(f"Found Owner role with ID: {owner_role_id}")

        # Step 2: Get all users and their Default Projects
        # Join users with their "Starter Project" folders
        users_folders_result = conn.execute(
            text("""
                SELECT u.id as user_id, f.id as folder_id
                FROM "user" u
                INNER JOIN folder f ON f.user_id = u.id AND f.name = :default_folder_name
            """),
            {"default_folder_name": DEFAULT_FOLDER_NAME},
        ).fetchall()

        total_users = len(users_folders_result)
        logger.info(f"Found {total_users} users with Default Project ({DEFAULT_FOLDER_NAME})")

        if total_users == 0:
            logger.warning("No users found with Default Project. This might be expected in a fresh installation.")
            return

        # Step 3: Create assignments (with idempotency check)
        assignments_created = 0
        assignments_skipped = 0

        for user_id, folder_id in users_folders_result:
            # Check if assignment already exists (idempotency)
            existing_assignment = conn.execute(
                text("""
                    SELECT id FROM userroleassignment
                    WHERE user_id = :user_id
                    AND scope_type = 'PROJECT'
                    AND scope_id = :scope_id
                """),
                {"user_id": str(user_id), "scope_id": str(folder_id)},
            ).fetchone()

            if existing_assignment:
                assignments_skipped += 1
                logger.debug(f"Assignment already exists for user {user_id} on project {folder_id}, skipping")
                continue

            # Create new assignment with is_immutable=True
            conn.execute(
                text("""
                    INSERT INTO userroleassignment
                    (id, user_id, role_id, scope_type, scope_id, is_immutable, created_at)
                    VALUES (
                        :id,
                        :user_id,
                        :role_id,
                        'PROJECT',
                        :scope_id,
                        true,
                        :created_at
                    )
                """),
                {
                    "id": str(uuid4()),
                    "user_id": str(user_id),
                    "role_id": str(owner_role_id),
                    "scope_id": str(folder_id),
                    "created_at": datetime.now(timezone.utc),
                },
            )
            assignments_created += 1

        # Log summary
        logger.info(
            f"Data migration completed successfully: "
            f"{assignments_created} assignments created, "
            f"{assignments_skipped} assignments skipped (already existed)"
        )

        # Verify all users now have assignments
        verification_result = conn.execute(
            text("""
                SELECT COUNT(DISTINCT u.id) as users_with_assignment
                FROM "user" u
                INNER JOIN folder f ON f.user_id = u.id AND f.name = :default_folder_name
                INNER JOIN userroleassignment ura ON ura.user_id = u.id
                    AND ura.scope_type = 'PROJECT'
                    AND ura.scope_id = f.id
            """),
            {"default_folder_name": DEFAULT_FOLDER_NAME},
        ).fetchone()

        users_with_assignment = verification_result[0] if verification_result else 0

        if users_with_assignment != total_users:
            logger.error(
                f"Verification failed: Expected {total_users} users with assignments, but found {users_with_assignment}"
            )
            raise RuntimeError("Assignment verification failed")

        logger.info(f"Verification passed: All {total_users} users have Owner role on Default Project")

    except Exception as e:
        logger.error(f"Error during data migration: {e!s}")
        raise


def downgrade() -> None:
    """Remove all immutable role assignments (Default Project Owner assignments).

    WARNING: This will remove all immutable assignments created by this migration.
    Only use in development/testing scenarios.
    """
    conn = op.get_bind()

    # Verify table exists
    inspector = Inspector.from_engine(conn)
    table_names = inspector.get_table_names()

    if "userroleassignment" not in table_names:
        logger.warning("userroleassignment table not found, skipping downgrade")
        return

    try:
        # Get count before deletion
        count_before = conn.execute(
            text("SELECT COUNT(*) FROM userroleassignment WHERE is_immutable = true")
        ).fetchone()[0]

        logger.info(f"Removing {count_before} immutable role assignments")

        # Remove all immutable assignments
        conn.execute(text("DELETE FROM userroleassignment WHERE is_immutable = true"))

        # Verify deletion
        count_after = conn.execute(
            text("SELECT COUNT(*) FROM userroleassignment WHERE is_immutable = true")
        ).fetchone()[0]

        if count_after > 0:
            raise RuntimeError(f"Downgrade verification failed: {count_after} immutable assignments still exist")

        logger.info(f"Downgrade completed successfully: Removed {count_before} immutable assignments")

    except Exception as e:
        logger.error(f"Error during downgrade: {e!s}")
        raise

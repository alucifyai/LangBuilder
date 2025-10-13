"""Test RBAC migration on existing database with data (Test Scenario 2)."""

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .conftest import column_exists, table_exists


class TestExistingDatabaseMigration:
    """Test RBAC migration on existing database with users, folders, and flows."""

    def test_existing_database_creates_default_workspace(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that migration creates 'Default Workspace' for existing users."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Verify we have existing users before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM user"))
            user_count_before = result.scalar()

        assert user_count_before > 0, "Test database should have existing users"

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify default workspace was created
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM workspace WHERE slug = 'default'")
            )
            default_workspace = result.fetchone()

        assert default_workspace is not None, "Default workspace was not created"
        assert default_workspace[1] == "Default Workspace"  # name column

    def test_existing_users_assigned_as_workspace_owners(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that all existing users are assigned as owners of default workspace."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get user count before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM user"))
            user_count = result.scalar()

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify all users are workspace members with 'owner' role
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) FROM workspace_member
                WHERE workspace_id = (SELECT id FROM workspace WHERE slug = 'default')
                AND role = 'owner'
            """
                )
            )
            owner_count = result.scalar()

        assert (
            owner_count == user_count
        ), f"Expected {user_count} owners, but found {owner_count}"

    def test_all_existing_folders_assigned_to_workspace(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that all existing folders are assigned to default workspace."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get folder count before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM folder"))
            folder_count = result.scalar()

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify all folders have workspace_id set
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) FROM folder
                WHERE workspace_id = (SELECT id FROM workspace WHERE slug = 'default')
            """
                )
            )
            folders_with_workspace = result.scalar()

        assert (
            folders_with_workspace == folder_count
        ), f"Expected {folder_count} folders in workspace, but found {folders_with_workspace}"

    def test_folder_workspace_id_not_nullable_after_migration(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that folder.workspace_id is NOT NULL after migration."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Try to insert folder without workspace_id (should fail)
        import pytest

        with existing_db_engine.connect() as conn:
            with pytest.raises(Exception):  # Should raise IntegrityError
                conn.execute(
                    text(
                        """
                    INSERT INTO folder (id, name, user_id, created_at, updated_at)
                    VALUES ('test-folder', 'Test', 'user-1', '2024-01-01', '2024-01-01')
                """
                    )
                )
                conn.commit()

    def test_existing_flows_preserved(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that all existing flows are preserved after migration."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get flow count and IDs before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), GROUP_CONCAT(id) FROM flow"))
            flow_data_before = result.fetchone()
            flow_count_before = flow_data_before[0]
            flow_ids_before = set(flow_data_before[1].split(",")) if flow_data_before[1] else set()

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Get flow count and IDs after migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*), GROUP_CONCAT(id) FROM flow"))
            flow_data_after = result.fetchone()
            flow_count_after = flow_data_after[0]
            flow_ids_after = set(flow_data_after[1].split(",")) if flow_data_after[1] else set()

        assert (
            flow_count_before == flow_count_after
        ), f"Flow count changed: {flow_count_before} -> {flow_count_after}"
        assert (
            flow_ids_before == flow_ids_after
        ), f"Flow IDs changed: {flow_ids_before} != {flow_ids_after}"

    def test_api_key_columns_added(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that new RBAC columns are added to api_key table."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify new columns exist
        expected_columns = [
            "workspace_id",
            "scope_type",
            "scope_id",
            "scoped_permissions",
            "service_account_id",
        ]

        for column in expected_columns:
            assert column_exists(
                existing_db_engine, "api_key", column
            ), f"Column {column} not added to api_key table"

    def test_flow_environment_id_added_and_nullable(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that environment_id column is added to flow table and is nullable."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify column exists
        assert column_exists(
            existing_db_engine, "flow", "environment_id"
        ), "environment_id column not added to flow table"

        # Verify existing flows have NULL environment_id
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM flow WHERE environment_id IS NULL")
            )
            null_environment_count = result.scalar()
            result = conn.execute(text("SELECT COUNT(*) FROM flow"))
            total_flow_count = result.scalar()

        assert (
            null_environment_count == total_flow_count
        ), "All existing flows should have NULL environment_id"

    def test_existing_api_keys_preserved(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that existing API keys are preserved with new columns as NULL."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get API key count before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM api_key"))
            key_count_before = result.scalar()

        assert key_count_before > 0, "Test database should have existing API keys"

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Get API key count after migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM api_key"))
            key_count_after = result.scalar()

        assert (
            key_count_before == key_count_after
        ), f"API key count changed: {key_count_before} -> {key_count_after}"

        # Verify new columns are NULL for existing keys
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT COUNT(*) FROM api_key
                WHERE workspace_id IS NULL
                AND scope_type IS NULL
                AND scope_id IS NULL
                AND service_account_id IS NULL
            """
                )
            )
            keys_with_null_rbac_fields = result.scalar()

        assert (
            keys_with_null_rbac_fields == key_count_before
        ), "Existing API keys should have NULL RBAC fields"

    def test_data_migration_idempotency(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that running migration twice doesn't create duplicate data."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration first time
        command.upgrade(alembic_config, "0b4b33664011")

        # Get counts after first migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM workspace"))
            workspace_count_1 = result.scalar()
            result = conn.execute(text("SELECT COUNT(*) FROM workspace_member"))
            member_count_1 = result.scalar()

        # Downgrade
        command.downgrade(alembic_config, "fd531f8868b1")

        # Run migration second time
        command.upgrade(alembic_config, "0b4b33664011")

        # Get counts after second migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM workspace"))
            workspace_count_2 = result.scalar()
            result = conn.execute(text("SELECT COUNT(*) FROM workspace_member"))
            member_count_2 = result.scalar()

        # Counts should be the same
        assert (
            workspace_count_1 == workspace_count_2
        ), "Workspace count changed on second migration"
        assert (
            member_count_1 == member_count_2
        ), "Member count changed on second migration"

    def test_all_rbac_tables_created(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that all 13 RBAC tables are created even with existing data."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify all RBAC tables exist
        expected_tables = [
            "workspace",
            "workspace_member",
            "user_group",
            "user_group_member",
            "role",
            "permission",
            "role_permission",
            "role_assignment",
            "service_account",
            "audit_log",
            "sso_integration",
            "environment",
            "invitation",
        ]

        for table_name in expected_tables:
            assert table_exists(
                existing_db_engine, table_name
            ), f"Table {table_name} was not created"

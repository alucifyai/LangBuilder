"""Test RBAC migration rollback (Test Scenario 3)."""

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .conftest import column_exists, get_table_names, table_exists


class TestMigrationRollback:
    """Test RBAC migration rollback (downgrade) functionality."""

    def test_rollback_removes_all_rbac_tables(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade removes all 13 RBAC tables."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify tables exist
        rbac_tables = [
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

        for table_name in rbac_tables:
            assert table_exists(
                existing_db_engine, table_name
            ), f"Table {table_name} should exist after upgrade"

        # Run rollback
        command.downgrade(alembic_config, "fd531f8868b1")

        # Verify tables are removed
        tables_after_downgrade = get_table_names(existing_db_engine)

        for table_name in rbac_tables:
            assert (
                table_name not in tables_after_downgrade
            ), f"Table {table_name} was not removed by downgrade"

    def test_rollback_removes_api_key_columns(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade removes RBAC columns from api_key table."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify columns exist
        rbac_columns = [
            "workspace_id",
            "scope_type",
            "scope_id",
            "scoped_permissions",
            "service_account_id",
        ]

        for column in rbac_columns:
            assert column_exists(
                existing_db_engine, "api_key", column
            ), f"Column {column} should exist after upgrade"

        # Run rollback
        command.downgrade(alembic_config, "fd531f8868b1")

        # Verify columns are removed
        for column in rbac_columns:
            assert not column_exists(
                existing_db_engine, "api_key", column
            ), f"Column {column} was not removed from api_key table"

    def test_rollback_removes_folder_workspace_id(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade removes workspace_id from folder table."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify column exists
        assert column_exists(
            existing_db_engine, "folder", "workspace_id"
        ), "workspace_id should exist after upgrade"

        # Run rollback
        command.downgrade(alembic_config, "fd531f8868b1")

        # Verify column is removed
        assert not column_exists(
            existing_db_engine, "folder", "workspace_id"
        ), "workspace_id was not removed from folder table"

    def test_rollback_removes_flow_environment_id(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade removes environment_id from flow table."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify column exists
        assert column_exists(
            existing_db_engine, "flow", "environment_id"
        ), "environment_id should exist after upgrade"

        # Run rollback
        command.downgrade(alembic_config, "fd531f8868b1")

        # Verify column is removed
        assert not column_exists(
            existing_db_engine, "flow", "environment_id"
        ), "environment_id was not removed from flow table"

    def test_rollback_preserves_user_data(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade preserves existing user data."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get user data before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT id, username FROM user ORDER BY id"))
            users_before = [(row[0], row[1]) for row in result.fetchall()]

        # Run migration and rollback
        command.upgrade(alembic_config, "0b4b33664011")
        command.downgrade(alembic_config, "fd531f8868b1")

        # Get user data after rollback
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT id, username FROM user ORDER BY id"))
            users_after = [(row[0], row[1]) for row in result.fetchall()]

        assert users_before == users_after, "User data was modified by rollback"

    def test_rollback_preserves_folder_data(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade preserves existing folder data."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get folder data before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT id, name, user_id FROM folder ORDER BY id"))
            folders_before = [(row[0], row[1], row[2]) for row in result.fetchall()]

        # Run migration and rollback
        command.upgrade(alembic_config, "0b4b33664011")
        command.downgrade(alembic_config, "fd531f8868b1")

        # Get folder data after rollback
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT id, name, user_id FROM folder ORDER BY id"))
            folders_after = [(row[0], row[1], row[2]) for row in result.fetchall()]

        assert folders_before == folders_after, "Folder data was modified by rollback"

    def test_rollback_preserves_flow_data(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade preserves existing flow data."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get flow data before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, user_id, folder_id FROM flow ORDER BY id")
            )
            flows_before = [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]

        # Run migration and rollback
        command.upgrade(alembic_config, "0b4b33664011")
        command.downgrade(alembic_config, "fd531f8868b1")

        # Get flow data after rollback
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, user_id, folder_id FROM flow ORDER BY id")
            )
            flows_after = [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]

        assert flows_before == flows_after, "Flow data was modified by rollback"

    def test_rollback_preserves_api_key_data(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that downgrade preserves existing API key data."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Get API key data before migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, api_key, user_id FROM api_key ORDER BY id")
            )
            keys_before = [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]

        # Run migration and rollback
        command.upgrade(alembic_config, "0b4b33664011")
        command.downgrade(alembic_config, "fd531f8868b1")

        # Get API key data after rollback
        with existing_db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, api_key, user_id FROM api_key ORDER BY id")
            )
            keys_after = [(row[0], row[1], row[2], row[3]) for row in result.fetchall()]

        assert keys_before == keys_after, "API key data was modified by rollback"

    def test_upgrade_after_rollback_succeeds(
        self, alembic_config: Config, existing_db_engine: Engine
    ):
        """Test that migration can be re-applied after rollback."""
        alembic_config.attributes["connection"] = existing_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Get counts after first migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM workspace"))
            workspace_count_1 = result.scalar()
            result = conn.execute(text("SELECT COUNT(*) FROM workspace_member"))
            member_count_1 = result.scalar()

        # Rollback
        command.downgrade(alembic_config, "fd531f8868b1")

        # Verify RBAC tables are gone
        assert not table_exists(existing_db_engine, "workspace")

        # Re-apply migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify tables are recreated
        assert table_exists(existing_db_engine, "workspace")
        assert table_exists(existing_db_engine, "workspace_member")

        # Get counts after second migration
        with existing_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM workspace"))
            workspace_count_2 = result.scalar()
            result = conn.execute(text("SELECT COUNT(*) FROM workspace_member"))
            member_count_2 = result.scalar()

        # Counts should be the same
        assert (
            workspace_count_1 == workspace_count_2
        ), "Workspace count different after re-apply"
        assert (
            member_count_1 == member_count_2
        ), "Member count different after re-apply"

    def test_rollback_on_fresh_database(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test that downgrade works on fresh database (no existing data)."""
        alembic_config.attributes["connection"] = fresh_db_engine

        # Run migration
        command.upgrade(alembic_config, "0b4b33664011")

        # Verify tables exist
        assert table_exists(fresh_db_engine, "workspace")

        # Run rollback
        command.downgrade(alembic_config, "fd531f8868b1")

        # Verify tables are removed
        assert not table_exists(fresh_db_engine, "workspace")
        assert not table_exists(fresh_db_engine, "role")
        assert not table_exists(fresh_db_engine, "permission")

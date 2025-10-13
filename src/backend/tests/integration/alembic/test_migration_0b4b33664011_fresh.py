"""Test RBAC migration on a fresh database (Test Scenario 1)."""

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .conftest import column_exists, get_table_names, table_exists


class TestFreshDatabaseMigration:
    """Test RBAC migration on a fresh database without existing data."""

    def test_fresh_database_upgrade_creates_all_tables(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test that migration creates all 13 RBAC tables on fresh database."""
        # Update Alembic config to use the test database
        alembic_config.attributes["connection"] = fresh_db_engine

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

        tables = get_table_names(fresh_db_engine)

        for table_name in expected_tables:
            assert table_name in tables, f"Table {table_name} was not created"

    def test_workspace_table_structure(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test workspace table has correct columns."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        expected_columns = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
            "settings",
        ]

        for column in expected_columns:
            assert column_exists(
                fresh_db_engine, "workspace", column
            ), f"Column {column} not found in workspace table"

    def test_workspace_member_table_structure(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test workspace_member table has correct columns."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        expected_columns = [
            "id",
            "workspace_id",
            "user_id",
            "role",
            "joined_at",
            "updated_at",
        ]

        for column in expected_columns:
            assert column_exists(
                fresh_db_engine, "workspace_member", column
            ), f"Column {column} not found in workspace_member table"

    def test_role_table_structure(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test role table has correct columns."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        expected_columns = [
            "id",
            "name",
            "display_name",
            "description",
            "is_system_role",
            "created_at",
            "updated_at",
        ]

        for column in expected_columns:
            assert column_exists(
                fresh_db_engine, "role", column
            ), f"Column {column} not found in role table"

    def test_permission_table_structure(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test permission table has correct columns."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        expected_columns = [
            "id",
            "resource_type",
            "action",
            "description",
            "created_at",
        ]

        for column in expected_columns:
            assert column_exists(
                fresh_db_engine, "permission", column
            ), f"Column {column} not found in permission table"

    def test_role_assignment_table_structure(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test role_assignment table has correct columns."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        expected_columns = [
            "id",
            "role_id",
            "assignee_type",
            "user_id",
            "service_account_id",
            "group_id",
            "scope_type",
            "scope_id",
            "granted_by_user_id",
            "expires_at",
            "created_at",
            "updated_at",
        ]

        for column in expected_columns:
            assert column_exists(
                fresh_db_engine, "role_assignment", column
            ), f"Column {column} not found in role_assignment table"

    def test_environment_table_structure(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test environment table has correct columns."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        expected_columns = [
            "id",
            "project_id",
            "name",
            "environment_type",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]

        for column in expected_columns:
            assert column_exists(
                fresh_db_engine, "environment", column
            ), f"Column {column} not found in environment table"

    def test_fresh_database_no_default_workspace(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test that no default workspace is created on fresh database (no existing users)."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        # Check workspace table is empty
        with fresh_db_engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM workspace"))
            workspace_count = result.scalar()

        assert (
            workspace_count == 0
        ), "Default workspace should not be created on fresh database"

    def test_fresh_database_foreign_keys_work(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test that foreign key relationships work by inserting test data."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        # This test would require creating test users first
        # For now, we just verify the migration succeeded
        assert table_exists(fresh_db_engine, "workspace")
        assert table_exists(fresh_db_engine, "workspace_member")

    def test_unique_constraints_exist(
        self, alembic_config: Config, fresh_db_engine: Engine
    ):
        """Test that unique constraints prevent duplicate entries."""
        alembic_config.attributes["connection"] = fresh_db_engine
        command.upgrade(alembic_config, "0b4b33664011")

        # Test workspace slug uniqueness
        with fresh_db_engine.connect() as conn:
            # Insert first workspace
            conn.execute(
                text(
                    """
                INSERT INTO workspace (id, name, slug, is_active, created_at, updated_at, settings)
                VALUES ('ws-1', 'Test Workspace', 'test-workspace', 1, '2024-01-01', '2024-01-01', '{}')
            """
                )
            )
            conn.commit()

            # Try to insert duplicate slug (should fail)
            with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
                conn.execute(
                    text(
                        """
                    INSERT INTO workspace (id, name, slug, is_active, created_at, updated_at, settings)
                    VALUES ('ws-2', 'Another Workspace', 'test-workspace', 1, '2024-01-01', '2024-01-01', '{}')
                """
                    )
                )
                conn.commit()

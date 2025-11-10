"""
Unit tests for RBAC migration (c62fe238bf8b_add_rbac_tables).

These tests verify that the migration:
- Creates all RBAC tables correctly
- Applies cleanly to empty and existing databases
- Can be rolled back without data loss
- Creates all indexes and constraints properly
"""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from langbuilder.services.auth.utils import get_password_hash
from langbuilder.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
)
from langbuilder.services.database.models.user.model import User
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import Session, SQLModel, select


def get_alembic_config(db_url: str) -> Config:
    """Create an Alembic configuration for testing."""
    # Get the path to alembic directory
    # From test file: .../tests/unit/services/database/test_rbac_migration.py
    # To alembic dir: .../base/langbuilder/alembic
    test_root = Path(__file__).parents[5]  # Gets to LangBuilder/src
    base_dir = test_root / "backend" / "base"
    alembic_dir = base_dir / "langbuilder" / "alembic"
    alembic_ini_path = base_dir / "langbuilder" / "alembic.ini"

    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(alembic_dir))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def test_migration_creates_all_tables():
    """Test that the migration creates all four RBAC tables."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        # Use sync URL for creating base tables
        sync_db_url = f"sqlite:///{db_path}"
        # Use async URL for alembic (required by env.py)
        async_db_url = f"sqlite+aiosqlite:///{db_path}"

        # Create base tables (user table must exist for foreign keys)
        engine = create_engine(sync_db_url)
        SQLModel.metadata.create_all(engine)

        # Run migration
        config = get_alembic_config(async_db_url)
        command.upgrade(config, "c62fe238bf8b")

        # Verify tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "role" in tables, "role table should be created"
        assert "permission" in tables, "permission table should be created"
        assert "role_permission" in tables, "role_permission table should be created"
        assert "user_role_assignment" in tables, "user_role_assignment table should be created"

        engine.dispose()
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_migration_creates_correct_columns():
    """Test that all tables have the correct columns."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        inspector = inspect(engine)

        # Check role table columns
        role_columns = {col["name"] for col in inspector.get_columns("role")}
        assert role_columns == {"id", "name", "description", "is_system"}

        # Check permission table columns
        permission_columns = {col["name"] for col in inspector.get_columns("permission")}
        assert permission_columns == {"id", "name", "description", "scope_type"}

        # Check role_permission table columns
        role_permission_columns = {col["name"] for col in inspector.get_columns("role_permission")}
        assert role_permission_columns == {"id", "role_id", "permission_id"}

        # Check user_role_assignment table columns
        assignment_columns = {col["name"] for col in inspector.get_columns("user_role_assignment")}
        assert assignment_columns == {
            "id", "user_id", "role_id", "scope_type",
            "scope_id", "is_immutable", "created_at", "created_by"
        }

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_creates_indexes():
    """Test that all required indexes are created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        inspector = inspect(engine)

        # Check role indexes
        role_indexes = {idx["name"] for idx in inspector.get_indexes("role")}
        assert "ix_role_name" in role_indexes

        # Check permission indexes
        permission_indexes = {idx["name"] for idx in inspector.get_indexes("permission")}
        assert "ix_permission_name" in permission_indexes
        assert "ix_permission_scope_type" in permission_indexes

        # Check role_permission indexes
        role_permission_indexes = {idx["name"] for idx in inspector.get_indexes("role_permission")}
        assert "ix_role_permission_role_id" in role_permission_indexes
        assert "ix_role_permission_permission_id" in role_permission_indexes

        # Check user_role_assignment indexes (including composite index)
        assignment_indexes = {idx["name"] for idx in inspector.get_indexes("user_role_assignment")}
        assert "ix_user_role_assignment_user_id" in assignment_indexes
        assert "ix_user_role_assignment_role_id" in assignment_indexes
        assert "ix_user_role_assignment_scope_type" in assignment_indexes
        assert "ix_user_role_assignment_scope_id" in assignment_indexes
        assert "idx_scope_lookup" in assignment_indexes, "Composite index for permission checks should exist"

        # Verify composite index columns
        for idx in inspector.get_indexes("user_role_assignment"):
            if idx["name"] == "idx_scope_lookup":
                assert idx["column_names"] == ["user_id", "scope_type", "scope_id"]

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_creates_unique_constraints():
    """Test that unique constraints are properly created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        inspector = inspect(engine)

        # Check role unique constraints
        role_constraints = inspector.get_unique_constraints("role")
        role_constraint_columns = {tuple(sorted(c["column_names"])) for c in role_constraints}
        assert ("name",) in role_constraint_columns or any("name" in idx["column_names"] and idx["unique"] for idx in inspector.get_indexes("role"))

        # Check permission unique constraints
        permission_constraints = inspector.get_unique_constraints("permission")
        permission_constraint_columns = {tuple(sorted(c["column_names"])) for c in permission_constraints}
        assert ("name",) in permission_constraint_columns or any("name" in idx["column_names"] and idx["unique"] for idx in inspector.get_indexes("permission"))

        # Check role_permission composite unique constraint
        role_permission_constraints = inspector.get_unique_constraints("role_permission")
        role_permission_constraint_columns = [sorted(c["column_names"]) for c in role_permission_constraints]
        assert ["permission_id", "role_id"] in role_permission_constraint_columns

        # Check user_role_assignment composite unique constraint
        assignment_constraints = inspector.get_unique_constraints("user_role_assignment")
        assignment_constraint_columns = [sorted(c["column_names"]) for c in assignment_constraints]
        assert ["role_id", "scope_id", "scope_type", "user_id"] in assignment_constraint_columns

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_creates_foreign_keys():
    """Test that all foreign key constraints are created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        inspector = inspect(engine)

        # Check role_permission foreign keys
        role_permission_fks = inspector.get_foreign_keys("role_permission")
        role_permission_fk_tables = {fk["referred_table"] for fk in role_permission_fks}
        assert "role" in role_permission_fk_tables
        assert "permission" in role_permission_fk_tables

        # Check user_role_assignment foreign keys
        assignment_fks = inspector.get_foreign_keys("user_role_assignment")
        assignment_fk_tables = {fk["referred_table"] for fk in assignment_fks}
        assert "user" in assignment_fk_tables
        assert "role" in assignment_fk_tables

        # Verify foreign key columns
        for fk in assignment_fks:
            if fk["referred_table"] == "user":
                assert "user_id" in fk["constrained_columns"] or "created_by" in fk["constrained_columns"]
            elif fk["referred_table"] == "role":
                assert "role_id" in fk["constrained_columns"]

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_rollback():
    """Test that the migration can be rolled back cleanly."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Get original tables
        inspector = inspect(engine)
        original_tables = set(inspector.get_table_names())

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        # Verify RBAC tables exist
        inspector = inspect(engine)
        tables_after_upgrade = set(inspector.get_table_names())
        assert "role" in tables_after_upgrade
        assert "permission" in tables_after_upgrade
        assert "role_permission" in tables_after_upgrade
        assert "user_role_assignment" in tables_after_upgrade

        # Rollback migration
        command.downgrade(config, "fd531f8868b1")

        # Verify RBAC tables are removed
        inspector = inspect(engine)
        tables_after_downgrade = set(inspector.get_table_names())
        assert "role" not in tables_after_downgrade, "role table should be removed after rollback"
        assert "permission" not in tables_after_downgrade, "permission table should be removed after rollback"
        assert "role_permission" not in tables_after_downgrade, "role_permission table should be removed after rollback"
        assert "user_role_assignment" not in tables_after_downgrade, "user_role_assignment table should be removed after rollback"

        # Verify original tables still exist
        assert original_tables.issubset(tables_after_downgrade), "Original tables should still exist after rollback"

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_rollback_with_data():
    """Test that rollback works correctly even with data in RBAC tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Create a user to reference
        with Session(engine) as session:
            user = User(
                username="testuser",
                password=get_password_hash("password"),
                is_active=True,
            )
            session.add(user)
            session.commit()
            user_id = user.id

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        # Add RBAC data
        with Session(engine) as session:
            role = Role(name="TestRole", is_system=False)
            session.add(role)
            session.commit()
            session.refresh(role)

            permission = Permission(name="TestPermission", scope_type="Flow")
            session.add(permission)
            session.commit()
            session.refresh(permission)

            role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
            session.add(role_permission)
            session.commit()

            assignment = UserRoleAssignment(
                user_id=user_id,
                role_id=role.id,
                scope_type="global",
                scope_id=None,
                is_immutable=False,
            )
            session.add(assignment)
            session.commit()

        # Verify data exists
        with Session(engine) as session:
            roles = session.exec(select(Role)).all()
            assert len(roles) == 1

        # Rollback migration
        command.downgrade(config, "fd531f8868b1")

        # Verify RBAC tables are removed
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "role" not in tables
        assert "permission" not in tables
        assert "role_permission" not in tables
        assert "user_role_assignment" not in tables

        # Verify user table still exists and data is intact
        assert "user" in tables
        with Session(engine) as session:
            user = session.exec(select(User).where(User.id == user_id)).first()
            assert user is not None
            assert user.username == "testuser"

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_applies_to_existing_database():
    """Test that migration applies cleanly to a database with existing data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables with some data
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Add existing users
        with Session(engine) as session:
            users = [
                User(username=f"user{i}", password=get_password_hash("password"), is_active=True)
                for i in range(5)
            ]
            for user in users:
                session.add(user)
            session.commit()

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        # Verify RBAC tables exist
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "role" in tables
        assert "permission" in tables
        assert "role_permission" in tables
        assert "user_role_assignment" in tables

        # Verify existing users are intact
        with Session(engine) as session:
            users_count = len(session.exec(select(User)).all())
            assert users_count == 5, "Existing users should be preserved"

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_idempotency():
    """Test that running the migration multiple times doesn't cause errors."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Run migration first time
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        inspector = inspect(engine)
        tables_first = set(inspector.get_table_names())

        # Running upgrade again to same revision should be a no-op
        command.upgrade(config, "c62fe238bf8b")

        inspector = inspect(engine)
        tables_second = set(inspector.get_table_names())

        assert tables_first == tables_second, "Multiple upgrades should not change table structure"

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_rollback_multiple_times():
    """Test that rollback can be performed multiple times without errors."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        config = get_alembic_config(db_url)

        # Upgrade and downgrade cycle 1
        command.upgrade(config, "c62fe238bf8b")
        inspector = inspect(engine)
        assert "role" in inspector.get_table_names()

        command.downgrade(config, "fd531f8868b1")
        inspector = inspect(engine)
        assert "role" not in inspector.get_table_names()

        # Upgrade and downgrade cycle 2
        command.upgrade(config, "c62fe238bf8b")
        inspector = inspect(engine)
        assert "role" in inspector.get_table_names()

        command.downgrade(config, "fd531f8868b1")
        inspector = inspect(engine)
        assert "role" not in inspector.get_table_names()

        # Upgrade and downgrade cycle 3
        command.upgrade(config, "c62fe238bf8b")
        inspector = inspect(engine)
        assert "role" in inspector.get_table_names()

        command.downgrade(config, "fd531f8868b1")
        inspector = inspect(engine)
        assert "role" not in inspector.get_table_names()

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)



def test_migration_preserves_user_table_structure():
    """Test that the migration doesn't modify the user table structure."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"

        # Create base tables
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        # Get user table structure before migration
        inspector = inspect(engine)
        user_columns_before = {col["name"] for col in inspector.get_columns("user")}
        user_indexes_before = {idx["name"] for idx in inspector.get_indexes("user")}

        # Run migration
        config = get_alembic_config(db_url)
        command.upgrade(config, "c62fe238bf8b")

        # Get user table structure after migration
        inspector = inspect(engine)
        user_columns_after = {col["name"] for col in inspector.get_columns("user")}
        user_indexes_after = {idx["name"] for idx in inspector.get_indexes("user")}

        # Verify user table is unchanged
        assert user_columns_before == user_columns_after, "User table columns should not change"
        assert user_indexes_before == user_indexes_after, "User table indexes should not change"

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

"""
Simplified tests for RBAC migration.

These tests verify the migration file structure and that the RBAC models
work correctly when tables are created through SQLModel.metadata.create_all().
"""

import os
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from langbuilder.services.auth.utils import get_password_hash
from langbuilder.services.database.models.rbac import (
    Permission,
    Role,
    RolePermission,
    UserRoleAssignment,
)
from langbuilder.services.database.models.user.model import User
from sqlalchemy import create_engine, inspect
from sqlmodel import Session, SQLModel, select


def test_migration_file_exists():
    """Test that the RBAC migration file exists."""
    # Get path to migration file
    migration_dir = Path(__file__).parents[5] / "backend" / "base" / "langbuilder" / "alembic" / "versions"
    migration_file = migration_dir / "c62fe238bf8b_add_rbac_tables.py"

    assert migration_file.exists(), f"Migration file should exist at {migration_file}"


def test_migration_file_structure():
    """Test that the migration file has correct structure."""
    migration_dir = Path(__file__).parents[5] / "backend" / "base" / "langbuilder" / "alembic" / "versions"
    migration_file = migration_dir / "c62fe238bf8b_add_rbac_tables.py"

    content = migration_file.read_text()

    # Check required attributes
    assert 'revision: str = "c62fe238bf8b"' in content
    assert 'down_revision: Union[str, None] = "fd531f8868b1"' in content

    # Check upgrade and downgrade functions exist
    assert "def upgrade() -> None:" in content
    assert "def downgrade() -> None:" in content

    # Check all tables are created in upgrade
    assert "create_table" in content
    assert '"role"' in content
    assert '"permission"' in content
    assert '"role_permission"' in content
    assert '"user_role_assignment"' in content


def test_rbac_tables_creation_via_metadata():
    """Test that RBAC tables can be created using SQLModel.metadata."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)

        # Create all tables including RBAC
        SQLModel.metadata.create_all(engine)

        # Verify RBAC tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "role" in tables
        assert "permission" in tables
        assert "role_permission" in tables
        assert "user_role_assignment" in tables

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_rbac_tables_have_correct_columns():
    """Test that all RBAC tables have the correct columns."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

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


def test_rbac_tables_have_indexes():
    """Test that all required indexes are created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

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
                assert set(idx["column_names"]) == {"user_id", "scope_type", "scope_id"}

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_rbac_tables_have_foreign_keys():
    """Test that all foreign key constraints are created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

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

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_rbac_data_operations():
    """Test basic CRUD operations on RBAC tables."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            # Create a user
            user = User(
                username="testuser",
                password=get_password_hash("password"),
                is_active=True,
            )
            session.add(user)
            session.commit()
            session.refresh(user)

            # Create a role
            role = Role(name="Owner", description="Project owner", is_system=True)
            session.add(role)
            session.commit()
            session.refresh(role)

            # Create a permission
            permission = Permission(name="Create", description="Create resources", scope_type="Project")
            session.add(permission)
            session.commit()
            session.refresh(permission)

            # Create role-permission mapping
            role_permission = RolePermission(role_id=role.id, permission_id=permission.id)
            session.add(role_permission)
            session.commit()
            session.refresh(role_permission)

            # Create user role assignment
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="project",
                scope_id=uuid4(),
                is_immutable=False,
            )
            session.add(assignment)
            session.commit()
            session.refresh(assignment)

            # Verify data exists
            assert session.exec(select(Role)).first() is not None
            assert session.exec(select(Permission)).first() is not None
            assert session.exec(select(RolePermission)).first() is not None
            assert session.exec(select(UserRoleAssignment)).first() is not None

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_user_role_assignment_global_scope():
    """Test creating a global scope assignment."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = User(username="admin", password=get_password_hash("password"), is_active=True)
            role = Role(name="Admin", is_system=True)
            session.add_all([user, role])
            session.commit()
            session.refresh(user)
            session.refresh(role)

            # Create global assignment
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="global",
                scope_id=None,
                is_immutable=False,
            )
            session.add(assignment)
            session.commit()
            session.refresh(assignment)

            assert assignment.scope_type == "global"
            assert assignment.scope_id is None

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_user_role_assignment_project_scope():
    """Test creating a project scope assignment."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = User(username="owner", password=get_password_hash("password"), is_active=True)
            role = Role(name="Owner", is_system=True)
            session.add_all([user, role])
            session.commit()
            session.refresh(user)
            session.refresh(role)

            project_id = uuid4()

            # Create project assignment
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="project",
                scope_id=project_id,
                is_immutable=False,
            )
            session.add(assignment)
            session.commit()
            session.refresh(assignment)

            assert assignment.scope_type == "project"
            assert assignment.scope_id == project_id

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_user_role_assignment_flow_scope():
    """Test creating a flow scope assignment."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = User(username="editor", password=get_password_hash("password"), is_active=True)
            role = Role(name="Editor", is_system=True)
            session.add_all([user, role])
            session.commit()
            session.refresh(user)
            session.refresh(role)

            flow_id = uuid4()

            # Create flow assignment
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="flow",
                scope_id=flow_id,
                is_immutable=False,
            )
            session.add(assignment)
            session.commit()
            session.refresh(assignment)

            assert assignment.scope_type == "flow"
            assert assignment.scope_id == flow_id

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_user_role_assignment_immutability():
    """Test that immutable assignments are properly flagged."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = User(username="owner", password=get_password_hash("password"), is_active=True)
            role = Role(name="Owner", is_system=True)
            session.add_all([user, role])
            session.commit()
            session.refresh(user)
            session.refresh(role)

            # Create immutable assignment (for Starter Project Owner)
            assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="project",
                scope_id=uuid4(),
                is_immutable=True,  # Immutable flag set
            )
            session.add(assignment)
            session.commit()
            session.refresh(assignment)

            assert assignment.is_immutable is True

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_user_role_assignment_composite_index_query():
    """Test that the composite index works for permission check queries."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            user = User(username="testuser", password=get_password_hash("password"), is_active=True)
            role = Role(name="TestRole", is_system=False)
            session.add_all([user, role])
            session.commit()
            session.refresh(user)
            session.refresh(role)

            project_id = uuid4()

            # Create multiple assignments
            assignment1 = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="global",
                scope_id=None,
                is_immutable=False,
            )
            assignment2 = UserRoleAssignment(
                user_id=user.id,
                role_id=role.id,
                scope_type="project",
                scope_id=project_id,
                is_immutable=False,
            )
            session.add_all([assignment1, assignment2])
            session.commit()

            # Test composite index query (user_id + scope_type + scope_id)
            stmt = select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == user.id,
                UserRoleAssignment.scope_type == "project",
                UserRoleAssignment.scope_id == project_id,
            )
            result = session.exec(stmt).first()

            assert result is not None
            assert result.scope_type == "project"
            assert result.scope_id == project_id

        engine.dispose()
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

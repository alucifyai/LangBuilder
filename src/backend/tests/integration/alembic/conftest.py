"""Pytest fixtures for Alembic migration tests."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


@pytest.fixture
def alembic_config() -> Config:
    """Create Alembic configuration for testing."""
    # Get the path to the alembic directory
    alembic_dir = Path(__file__).parent.parent.parent.parent.parent / "base" / "langflow" / "alembic"

    config = Config(str(alembic_dir / "alembic.ini"))
    config.set_main_option("script_location", str(alembic_dir))

    return config


@pytest.fixture
def fresh_db_engine() -> Generator[Engine, None, None]:
    """Create a fresh SQLite database engine for testing."""
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")
        yield engine
        engine.dispose()
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def existing_db_engine() -> Generator[Engine, None, None]:
    """Create a database with existing users, folders, and flows for testing data migration."""
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        # Create engine
        engine = create_engine(f"sqlite:///{db_path}")

        # Create minimal schema (user, folder, flow, api_key tables)
        # These would normally exist before RBAC migration
        with engine.connect() as conn:
            # Create user table
            conn.execute(text("""
                CREATE TABLE user (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    is_superuser INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))

            # Create folder table
            conn.execute(text("""
                CREATE TABLE folder (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            """))

            # Create flow table
            conn.execute(text("""
                CREATE TABLE flow (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    data TEXT,
                    user_id TEXT,
                    folder_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (folder_id) REFERENCES folder(id)
                )
            """))

            # Create api_key table
            conn.execute(text("""
                CREATE TABLE api_key (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    total_uses INTEGER DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            """))

            # Create alembic_version table and set to revision before RBAC
            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))

            # Set version to the revision before RBAC migration
            conn.execute(text("""
                INSERT INTO alembic_version (version_num) VALUES ('fd531f8868b1')
            """))

            # Insert test users
            conn.execute(text("""
                INSERT INTO user (id, username, password, is_active, is_superuser, created_at, updated_at)
                VALUES
                    ('user-1', 'testuser1', 'hashed_password_1', 1, 0, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
                    ('user-2', 'testuser2', 'hashed_password_2', 1, 0, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
                    ('user-3', 'admin', 'hashed_password_3', 1, 1, '2024-01-01 00:00:00', '2024-01-01 00:00:00')
            """))

            # Insert test folders
            conn.execute(text("""
                INSERT INTO folder (id, name, description, user_id, created_at, updated_at)
                VALUES
                    ('folder-1', 'User 1 Folder', 'Test folder 1', 'user-1', '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
                    ('folder-2', 'User 2 Folder', 'Test folder 2', 'user-2', '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
                    ('folder-3', 'Admin Folder', 'Admin test folder', 'user-3', '2024-01-01 00:00:00', '2024-01-01 00:00:00')
            """))

            # Insert test flows
            conn.execute(text("""
                INSERT INTO flow (id, name, description, data, user_id, folder_id, created_at, updated_at)
                VALUES
                    ('flow-1', 'Test Flow 1', 'Description 1', '{}', 'user-1', 'folder-1', '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
                    ('flow-2', 'Test Flow 2', 'Description 2', '{}', 'user-2', 'folder-2', '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
                    ('flow-3', 'Admin Flow', 'Admin flow', '{}', 'user-3', 'folder-3', '2024-01-01 00:00:00', '2024-01-01 00:00:00')
            """))

            # Insert test API keys
            conn.execute(text("""
                INSERT INTO api_key (id, name, api_key, user_id, created_at, total_uses, is_active)
                VALUES
                    ('key-1', 'User 1 Key', 'sk-test-key-1', 'user-1', '2024-01-01 00:00:00', 0, 1),
                    ('key-2', 'User 2 Key', 'sk-test-key-2', 'user-2', '2024-01-01 00:00:00', 0, 1)
            """))

            conn.commit()

        yield engine
        engine.dispose()
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def db_session(fresh_db_engine: Engine) -> Generator[Session, None, None]:
    """Create a database session for testing."""
    session = Session(fresh_db_engine)
    try:
        yield session
    finally:
        session.close()


def get_table_names(engine: Engine) -> list[str]:
    """Get all table names from the database."""
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ))
        else:  # PostgreSQL
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public'"
            ))
        return [row[0] for row in result]


def get_column_names(engine: Engine, table_name: str) -> list[str]:
    """Get all column names from a table."""
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            return [row[1] for row in result]
        # PostgreSQL
        result = conn.execute(text(
            f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='{table_name}'
                """
        ))
        return [row[0] for row in result]


def table_exists(engine: Engine, table_name: str) -> bool:
    """Check if a table exists in the database."""
    return table_name in get_table_names(engine)


def column_exists(engine: Engine, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    return column_name in get_column_names(engine, table_name)

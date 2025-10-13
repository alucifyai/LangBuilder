"""Manual migration test runner that bypasses pytest fixtures."""

import os
import tempfile
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text


def get_alembic_config(db_url: str) -> Config:
    """Create Alembic configuration."""
    # Get the correct path to alembic directory
    # From: src/backend/tests/integration/alembic/run_manual_tests.py
    # To: src/backend/base/langflow/
    langflow_dir = Path(__file__).parent.parent.parent.parent / "base" / "langflow"
    alembic_dir = langflow_dir / "alembic"

    config = Config(str(langflow_dir / "alembic.ini"))
    config.set_main_option("script_location", str(alembic_dir))
    config.set_main_option("sqlalchemy.url", db_url)

    return config


def test_fresh_database_migration():
    """Test 1: Fresh database migration."""
    print("\n" + "=" * 80)
    print("TEST 1: Fresh Database Migration")
    print("=" * 80)

    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_engine(f"sqlite:///{db_path}")

        # Create Alembic config
        config = get_alembic_config(db_url)
        config.attributes["connection"] = engine

        print(f"✓ Created temporary database: {db_path}")

        # Run migration to RBAC revision
        print("✓ Running migration to 0b4b33664011...")
        command.upgrade(config, "0b4b33664011")

        # Verify tables exist
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

        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic_%'"
            ))
            tables = [row[0] for row in result.fetchall()]

        print(f"✓ Found {len(tables)} tables")

        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"✗ FAIL: Missing tables: {missing_tables}")
            return False

        print("✓ All 13 RBAC tables created successfully")

        # Verify no default workspace on fresh database
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM workspace"))
            workspace_count = result.scalar()

        if workspace_count == 0:
            print("✓ No default workspace created (expected for fresh database)")
        else:
            print(f"✗ FAIL: Unexpected workspace count: {workspace_count}")
            return False

        print("✓ TEST 1 PASSED\n")
        return True

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_existing_database_migration():
    """Test 2: Existing database with data migration."""
    print("\n" + "=" * 80)
    print("TEST 2: Existing Database Migration with Data")
    print("=" * 80)

    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_engine(f"sqlite:///{db_path}")

        print(f"✓ Created temporary database: {db_path}")

        # Create minimal existing schema
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

            # Create alembic_version table
            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('fd531f8868b1')"))

            # Insert test data
            now = datetime.now().isoformat()
            conn.execute(text("""
                INSERT INTO user (id, username, password, is_active, is_superuser, created_at, updated_at)
                VALUES
                    ('user-1', 'testuser1', 'hashed_password_1', 1, 0, :now, :now),
                    ('user-2', 'testuser2', 'hashed_password_2', 1, 0, :now, :now),
                    ('user-3', 'admin', 'hashed_password_3', 1, 1, :now, :now)
            """), {"now": now})

            conn.execute(text("""
                INSERT INTO folder (id, name, description, user_id, created_at, updated_at)
                VALUES
                    ('folder-1', 'User 1 Folder', 'Test folder 1', 'user-1', :now, :now),
                    ('folder-2', 'User 2 Folder', 'Test folder 2', 'user-2', :now, :now)
            """), {"now": now})

            conn.execute(text("""
                INSERT INTO flow (id, name, description, data, user_id, folder_id, created_at, updated_at)
                VALUES
                    ('flow-1', 'Test Flow 1', 'Description 1', '{}', 'user-1', 'folder-1', :now, :now)
            """), {"now": now})

            conn.commit()

        print("✓ Created existing schema with 3 users, 2 folders, 1 flow")

        # Create Alembic config
        config = get_alembic_config(db_url)
        config.attributes["connection"] = engine

        # Run migration
        print("✓ Running migration to 0b4b33664011...")
        command.upgrade(config, "0b4b33664011")

        # Verify default workspace created
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM workspace WHERE slug = 'default'"))
            default_workspace = result.fetchone()

        if default_workspace is None:
            print("✗ FAIL: Default workspace was not created")
            return False

        print("✓ Default workspace created")

        # Verify all users are workspace owners
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM workspace_member
                WHERE workspace_id = (SELECT id FROM workspace WHERE slug = 'default')
                AND role = 'owner'
            """))
            owner_count = result.scalar()

        if owner_count == 3:
            print("✓ All 3 users assigned as workspace owners")
        else:
            print(f"✗ FAIL: Expected 3 owners, found {owner_count}")
            return False

        # Verify all folders assigned to workspace
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) FROM folder
                WHERE workspace_id = (SELECT id FROM workspace WHERE slug = 'default')
            """))
            folder_count = result.scalar()

        if folder_count == 2:
            print("✓ All 2 folders assigned to default workspace")
        else:
            print(f"✗ FAIL: Expected 2 folders in workspace, found {folder_count}")
            return False

        # Verify flows preserved
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM flow"))
            flow_count = result.scalar()

        if flow_count == 1:
            print("✓ All flows preserved")
        else:
            print(f"✗ FAIL: Expected 1 flow, found {flow_count}")
            return False

        print("✓ TEST 2 PASSED\n")
        return True

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_rollback():
    """Test 3: Migration rollback."""
    print("\n" + "=" * 80)
    print("TEST 3: Migration Rollback")
    print("=" * 80)

    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_engine(f"sqlite:///{db_path}")

        print(f"✓ Created temporary database: {db_path}")

        # Create minimal existing schema
        with engine.connect() as conn:
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

            conn.execute(text("""
                CREATE TABLE folder (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))

            conn.execute(text("""
                CREATE TABLE flow (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    user_id TEXT,
                    folder_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """))

            conn.execute(text("""
                CREATE TABLE api_key (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """))

            conn.execute(text("""
                CREATE TABLE alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                )
            """))
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('fd531f8868b1')"))

            # Insert test data
            now = datetime.now().isoformat()
            conn.execute(text("INSERT INTO user (id, username, password, is_active, is_superuser, created_at, updated_at) VALUES ('user-1', 'test', 'pass', 1, 0, :now, :now)"), {"now": now})
            conn.commit()

        print("✓ Created existing schema with test data")

        # Create Alembic config
        config = get_alembic_config(db_url)
        config.attributes["connection"] = engine

        # Run migration
        print("✓ Running migration to 0b4b33664011...")
        command.upgrade(config, "0b4b33664011")

        # Verify RBAC tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='workspace'"))
            workspace_exists = result.fetchone() is not None

        if not workspace_exists:
            print("✗ FAIL: Workspace table not created after upgrade")
            return False

        print("✓ RBAC tables created")

        # Run rollback
        print("✓ Running rollback to fd531f8868b1...")
        command.downgrade(config, "fd531f8868b1")

        # Verify RBAC tables removed
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='workspace'"))
            workspace_exists = result.fetchone() is not None

        if workspace_exists:
            print("✗ FAIL: Workspace table still exists after rollback")
            return False

        print("✓ All RBAC tables removed")

        # Verify original data preserved
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM user"))
            user_count = result.scalar()

        if user_count == 1:
            print("✓ User data preserved after rollback")
        else:
            print(f"✗ FAIL: User count changed: {user_count}")
            return False

        print("✓ TEST 3 PASSED\n")
        return True

    finally:
        engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def main():
    """Run all tests and generate summary."""
    print("\n" + "=" * 80)
    print("RBAC MIGRATION TEST SUITE")
    print("Migration: 0b4b33664011_add_rbac_models_with_workspace_groups")
    print("=" * 80)

    results = {
        "Test 1: Fresh Database Migration": test_fresh_database_migration(),
        "Test 2: Existing Database Migration": test_existing_database_migration(),
        "Test 3: Migration Rollback": test_rollback(),
    }

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    print(f"\n✗ {total - passed} TEST(S) FAILED")
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())

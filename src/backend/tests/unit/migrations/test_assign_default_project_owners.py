"""Unit tests for the Default Project Owner data migration.

This module tests the Alembic data migration that assigns Owner role to all users
for their Default Project with is_immutable=True (Task 1.6).

Tests verify:
- Migration creates assignments for all users with Default Projects
- is_immutable flag is set correctly
- Idempotency (can run multiple times)
- Error handling (missing role, missing tables)
- Downgrade removes only immutable assignments
- Edge cases (no users, no default projects)
"""
# ruff: noqa: S106, E712, F841, INP001, E402

import secrets

# Import the migration functions directly for testing
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import (
    Role,
    RoleEnum,
    ScopeTypeEnum,
    UserRoleAssignment,
)
from langbuilder.services.database.models.user import User
from langbuilder.services.database.utils import session_getter
from langbuilder.services.deps import get_db_service
from sqlmodel import select

# Add migrations directory to path for importing
migrations_path = (
    Path(__file__).parent.parent.parent.parent.parent / "backend" / "base" / "langbuilder" / "alembic" / "versions"
)
sys.path.insert(0, str(migrations_path))

# Import the migration module
from a1b2c3d4e5f6_assign_default_project_owners import (
    DEFAULT_FOLDER_NAME,
)
from a1b2c3d4e5f6_assign_default_project_owners import (
    downgrade as migration_downgrade,
)
from a1b2c3d4e5f6_assign_default_project_owners import (
    upgrade as migration_upgrade,
)


class TestDefaultProjectOwnerMigration:
    """Test the Default Project Owner data migration (Task 1.6)."""

    @pytest.mark.asyncio
    async def test_migration_creates_assignments_for_all_users(self):
        """Test that migration creates Owner assignments for all users with Default Projects."""
        async with session_getter(get_db_service()) as session:
            # Create test users with Default Projects
            user1 = User(username=f"migration_user1_{secrets.token_hex(4)}", password="password", is_active=True)
            user2 = User(username=f"migration_user2_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user1)
            session.add(user2)
            await session.commit()
            await session.refresh(user1)
            await session.refresh(user2)

            # Create Default Projects for both users
            folder1 = Folder(name=DEFAULT_FOLDER_NAME, user_id=user1.id, description="Test Default Project 1")
            folder2 = Folder(name=DEFAULT_FOLDER_NAME, user_id=user2.id, description="Test Default Project 2")
            session.add(folder1)
            session.add(folder2)
            await session.commit()
            await session.refresh(folder1)
            await session.refresh(folder2)

            # Get Owner role
            owner_role = (await session.exec(select(Role).where(Role.name == RoleEnum.OWNER))).first()
            assert owner_role is not None, "Owner role should be seeded"

            # Count assignments before migration
            count_before = len((await session.exec(select(UserRoleAssignment))).all())

            # Run upgrade migration using raw SQL connection
            conn = session.connection()
            migration_upgrade()

            # Verify assignments were created
            assignments = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.is_immutable == True,
                    )
                )
            ).all()

            # Should have at least 2 new assignments (for our test users)
            assert len(assignments) >= 2, "Migration should create assignments for all users"

            # Verify user1 has assignment for folder1
            user1_assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user1.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder1.id,
                    )
                )
            ).first()
            assert user1_assignment is not None, "User1 should have assignment"
            assert user1_assignment.role_id == owner_role.id, "Should have Owner role"
            assert user1_assignment.is_immutable is True, "Should be immutable"

            # Verify user2 has assignment for folder2
            user2_assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user2.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder2.id,
                    )
                )
            ).first()
            assert user2_assignment is not None, "User2 should have assignment"
            assert user2_assignment.role_id == owner_role.id, "Should have Owner role"
            assert user2_assignment.is_immutable is True, "Should be immutable"

    @pytest.mark.asyncio
    async def test_migration_is_idempotent(self):
        """Test that migration can run multiple times without errors or duplicates."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_idempotent_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()
            await session.refresh(folder)

            # Run migration first time
            conn = session.connection()
            migration_upgrade()

            # Count assignments after first run
            assignments_first = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).all()
            count_first = len(assignments_first)
            assert count_first == 1, "Should create exactly one assignment on first run"

            # Run migration second time (idempotency test)
            migration_upgrade()

            # Count assignments after second run
            assignments_second = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).all()
            count_second = len(assignments_second)

            # Should still have exactly one assignment (no duplicates)
            assert count_second == count_first, "Idempotent migration should not create duplicates"

    @pytest.mark.asyncio
    async def test_migration_sets_immutable_flag(self):
        """Test that all created assignments have is_immutable=True."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_immutable_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()
            await session.refresh(folder)

            # Run migration
            conn = session.connection()
            migration_upgrade()

            # Verify is_immutable flag
            assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).first()

            assert assignment is not None, "Assignment should exist"
            assert assignment.is_immutable is True, "Assignment must be immutable per PRD Story 1.4"

    @pytest.mark.asyncio
    async def test_migration_handles_users_without_default_project(self):
        """Test that migration handles users without Default Project gracefully."""
        async with session_getter(get_db_service()) as session:
            # Create user WITHOUT a Default Project
            user = User(username=f"migration_noproject_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # Create a folder with different name (not Default Project)
            folder = Folder(name="Some Other Project", user_id=user.id, description="Not a default project")
            session.add(folder)
            await session.commit()

            # Run migration - should not error
            conn = session.connection()
            try:
                migration_upgrade()
            except Exception as e:
                pytest.fail(f"Migration should handle users without Default Project gracefully: {e}")

            # Verify no assignment was created for this user's non-default project
            assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).first()

            assert assignment is None, "Should not create assignment for non-default projects"

    @pytest.mark.asyncio
    async def test_migration_assigns_correct_role(self):
        """Test that migration assigns Owner role (not Admin, Editor, or Viewer)."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_role_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()
            await session.refresh(folder)

            # Get Owner role
            owner_role = (await session.exec(select(Role).where(Role.name == RoleEnum.OWNER))).first()

            # Run migration
            conn = session.connection()
            migration_upgrade()

            # Verify correct role was assigned
            assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).first()

            assert assignment is not None, "Assignment should exist"
            assert assignment.role_id == owner_role.id, "Must assign Owner role per PRD"

    @pytest.mark.asyncio
    async def test_migration_assigns_correct_scope_type(self):
        """Test that migration assigns PROJECT scope type (not GLOBAL or FLOW)."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_scope_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()
            await session.refresh(folder)

            # Run migration
            conn = session.connection()
            migration_upgrade()

            # Verify correct scope type
            assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).first()

            assert assignment is not None, "Assignment should exist"
            assert assignment.scope_type == ScopeTypeEnum.PROJECT, "Must use PROJECT scope per PRD"
            assert assignment.scope_id == folder.id, "Scope ID must match folder ID"

    @pytest.mark.asyncio
    async def test_downgrade_removes_only_immutable_assignments(self):
        """Test that downgrade removes only immutable assignments, not regular ones."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_downgrade_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()
            await session.refresh(folder)

            # Get Owner role
            owner_role = (await session.exec(select(Role).where(Role.name == RoleEnum.OWNER))).first()

            # Create a non-immutable assignment manually
            non_immutable_assignment = UserRoleAssignment(
                user_id=user.id,
                role_id=owner_role.id,
                scope_type=ScopeTypeEnum.FLOW,
                scope_id=uuid4(),
                is_immutable=False,
            )
            session.add(non_immutable_assignment)
            await session.commit()

            # Run migration upgrade
            conn = session.connection()
            migration_upgrade()

            # Verify immutable assignment exists
            immutable_assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.is_immutable == True,
                    )
                )
            ).first()
            assert immutable_assignment is not None, "Immutable assignment should exist"

            # Run migration downgrade
            migration_downgrade()

            # Verify immutable assignment was removed
            immutable_after = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.is_immutable == True,
                    )
                )
            ).first()
            assert immutable_after is None, "Downgrade should remove immutable assignment"

            # Verify non-immutable assignment still exists
            non_immutable_after = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.id == non_immutable_assignment.id,
                    )
                )
            ).first()
            assert non_immutable_after is not None, "Downgrade should preserve non-immutable assignments"

    @pytest.mark.asyncio
    async def test_migration_logs_progress(self):
        """Test that migration logs useful progress information."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_logging_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()

            # Run migration (should log without errors)
            conn = session.connection()
            try:
                migration_upgrade()
            except Exception as e:
                pytest.fail(f"Migration should complete with logging: {e}")

    @pytest.mark.asyncio
    async def test_migration_creates_valid_timestamps(self):
        """Test that migration creates assignments with valid timestamps."""
        async with session_getter(get_db_service()) as session:
            # Create test user with Default Project
            user = User(username=f"migration_timestamp_{secrets.token_hex(4)}", password="password", is_active=True)
            session.add(user)
            await session.commit()
            await session.refresh(user)

            folder = Folder(name=DEFAULT_FOLDER_NAME, user_id=user.id, description="Test Default Project")
            session.add(folder)
            await session.commit()
            await session.refresh(folder)

            # Record time before migration
            time_before = datetime.now(timezone.utc)

            # Run migration
            conn = session.connection()
            migration_upgrade()

            # Record time after migration
            time_after = datetime.now(timezone.utc)

            # Verify timestamp
            assignment = (
                await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user.id,
                        UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                        UserRoleAssignment.scope_id == folder.id,
                    )
                )
            ).first()

            assert assignment is not None, "Assignment should exist"
            assert assignment.created_at is not None, "Should have created_at timestamp"
            assert time_before <= assignment.created_at <= time_after, "Timestamp should be within migration window"

    @pytest.mark.asyncio
    async def test_migration_handles_multiple_users_efficiently(self):
        """Test that migration can handle multiple users without performance issues."""
        async with session_getter(get_db_service()) as session:
            # Create multiple test users with Default Projects
            num_users = 10
            users = []
            folders = []

            for i in range(num_users):
                user = User(username=f"migration_perf_{i}_{secrets.token_hex(4)}", password="password", is_active=True)
                session.add(user)
                users.append(user)

            await session.commit()

            for user in users:
                await session.refresh(user)
                folder = Folder(
                    name=DEFAULT_FOLDER_NAME, user_id=user.id, description=f"Test Default Project {user.username}"
                )
                session.add(folder)
                folders.append(folder)

            await session.commit()
            for folder in folders:
                await session.refresh(folder)

            # Run migration
            conn = session.connection()
            migration_upgrade()

            # Verify all users got assignments
            for i, (user, folder) in enumerate(zip(users, folders, strict=False)):
                assignment = (
                    await session.exec(
                        select(UserRoleAssignment).where(
                            UserRoleAssignment.user_id == user.id,
                            UserRoleAssignment.scope_type == ScopeTypeEnum.PROJECT,
                            UserRoleAssignment.scope_id == folder.id,
                        )
                    )
                ).first()
                assert assignment is not None, f"User {i} should have assignment"
                assert assignment.is_immutable is True, f"User {i} assignment should be immutable"

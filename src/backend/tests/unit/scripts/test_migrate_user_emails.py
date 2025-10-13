"""Tests for user email migration script.

This test file validates the email migration script functionality for Task 3.9 gap fix.
"""

import pytest
from langflow.scripts.migrate_user_emails import (
    derive_email_from_username,
    is_valid_email,
    migrate_user_emails,
    sanitize_username_for_email,
)
from langflow.services.database.models.user.model import User
from sqlmodel import select


class TestEmailValidation:
    """Test email validation functions."""

    def test_is_valid_email_valid_cases(self):
        """Test valid email addresses."""
        assert is_valid_email("user@example.com")
        assert is_valid_email("user.name@example.com")
        assert is_valid_email("user+tag@example.com")
        assert is_valid_email("user_name@example.co.uk")
        assert is_valid_email("123@example.com")
        assert is_valid_email("user@subdomain.example.com")

    def test_is_valid_email_invalid_cases(self):
        """Test invalid email addresses."""
        assert not is_valid_email("invalid")
        assert not is_valid_email("@example.com")
        assert not is_valid_email("user@")
        assert not is_valid_email("user @example.com")
        assert not is_valid_email("user@example")
        assert not is_valid_email("")


class TestUsernameSanitization:
    """Test username sanitization for email generation."""

    def test_sanitize_username_simple(self):
        """Test sanitization of simple usernames."""
        assert sanitize_username_for_email("user") == "user"
        assert sanitize_username_for_email("User") == "user"
        assert sanitize_username_for_email("USER") == "user"

    def test_sanitize_username_with_spaces(self):
        """Test sanitization of usernames with spaces."""
        assert sanitize_username_for_email("user name") == "user.name"
        assert sanitize_username_for_email("first last") == "first.last"

    def test_sanitize_username_with_special_chars(self):
        """Test sanitization of usernames with special characters."""
        assert sanitize_username_for_email("user@name") == "user.name"
        assert sanitize_username_for_email("user#name") == "user.name"
        assert sanitize_username_for_email("user*name") == "user.name"

    def test_sanitize_username_with_dots(self):
        """Test sanitization preserves valid dots."""
        assert sanitize_username_for_email("user.name") == "user.name"
        assert sanitize_username_for_email("first.middle.last") == "first.middle.last"

    def test_sanitize_username_removes_consecutive_dots(self):
        """Test sanitization removes consecutive dots."""
        assert sanitize_username_for_email("user..name") == "user.name"
        assert sanitize_username_for_email("user...name") == "user.name"

    def test_sanitize_username_trims_dots(self):
        """Test sanitization trims leading/trailing dots."""
        assert sanitize_username_for_email(".user") == "user"
        assert sanitize_username_for_email("user.") == "user"
        assert sanitize_username_for_email(".user.") == "user"

    def test_sanitize_username_empty_fallback(self):
        """Test sanitization handles empty or invalid input."""
        assert sanitize_username_for_email("") == "user"
        assert sanitize_username_for_email("...") == "user"
        assert sanitize_username_for_email("@@@") == "user"


class TestEmailDerivation:
    """Test email derivation from username."""

    def test_derive_email_from_email_username(self):
        """Test derivation when username is already a valid email."""
        assert derive_email_from_username("user@example.com") == "user@example.com"
        assert derive_email_from_username("USER@EXAMPLE.COM") == "user@example.com"

    def test_derive_email_from_simple_username(self):
        """Test derivation from simple username."""
        assert derive_email_from_username("user") == "user@example.com"
        assert derive_email_from_username("john") == "john@example.com"

    def test_derive_email_with_custom_domain(self):
        """Test derivation with custom domain."""
        assert derive_email_from_username("user", "company.com") == "user@company.com"
        assert derive_email_from_username("admin", "test.org") == "admin@test.org"

    def test_derive_email_from_username_with_spaces(self):
        """Test derivation from username with spaces."""
        assert derive_email_from_username("first last") == "first.last@example.com"
        assert derive_email_from_username("john doe") == "john.doe@example.com"

    def test_derive_email_from_invalid_email_username(self):
        """Test derivation when username contains @ but isn't valid email."""
        result = derive_email_from_username("user@invalid")
        assert "@" in result
        assert result.startswith("user@")
        assert result.endswith("example.com")


@pytest.mark.asyncio
class TestMigrationScript:
    """Test the migration script functionality."""

    async def test_migrate_user_emails_dry_run(self, session):
        """Test migration in dry run mode."""
        # Create test users without email
        user1 = User(username="testuser1", email=None, password="hashed")
        user2 = User(username="test.user2", email=None, password="hashed")
        user3 = User(username="existing@example.com", email=None, password="hashed")

        session.add(user1)
        session.add(user2)
        session.add(user3)
        await session.commit()

        # Get database URL from session
        database_url = str(session.bind.engine.url)
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # Run migration in dry run mode
        stats = await migrate_user_emails(
            database_url=database_url, dry_run=True, domain="test.com", verbose=False
        )

        # Verify statistics
        assert stats["total_users"] >= 3
        assert stats["users_without_email"] >= 3
        assert stats["migrated_users"] >= 3
        assert stats["failed_users"] == 0
        assert stats["dry_run"] is True

        # Verify no changes were made (dry run)
        await session.refresh(user1)
        await session.refresh(user2)
        await session.refresh(user3)
        assert user1.email is None
        assert user2.email is None
        assert user3.email is None

    async def test_migrate_user_emails_actual(self, session):
        """Test actual migration (not dry run)."""
        # Create test users without email
        user1 = User(username="actualuser1", email=None, password="hashed")
        user2 = User(username="actual user2", email=None, password="hashed")

        session.add(user1)
        session.add(user2)
        await session.commit()

        user1_id = user1.id
        user2_id = user2.id

        # Get database URL from session
        database_url = str(session.bind.engine.url)
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # Run actual migration
        stats = await migrate_user_emails(
            database_url=database_url, dry_run=False, domain="migration.com", verbose=False
        )

        # Verify statistics
        assert stats["migrated_users"] >= 2
        assert stats["failed_users"] == 0
        assert stats["dry_run"] is False

        # Verify changes were made
        stmt = select(User).where(User.id == user1_id)
        result = await session.exec(stmt)
        migrated_user1 = result.first()
        assert migrated_user1.email == "actualuser1@migration.com"

        stmt = select(User).where(User.id == user2_id)
        result = await session.exec(stmt)
        migrated_user2 = result.first()
        assert migrated_user2.email == "actual.user2@migration.com"

    async def test_migrate_user_emails_preserves_existing(self, session):
        """Test migration preserves users who already have email."""
        # Create user with existing email
        user_with_email = User(
            username="userwithemail", email="existing@example.com", password="hashed"
        )

        session.add(user_with_email)
        await session.commit()

        original_email = user_with_email.email

        # Get database URL from session
        database_url = str(session.bind.engine.url)
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # Run migration
        stats = await migrate_user_emails(
            database_url=database_url, dry_run=False, domain="test.com", verbose=False
        )

        # Verify user with existing email was not modified
        await session.refresh(user_with_email)
        assert user_with_email.email == original_email

    async def test_migrate_user_emails_no_users_without_email(self, session):
        """Test migration when all users have email."""
        # Create users with email
        user1 = User(username="user1", email="user1@example.com", password="hashed")
        user2 = User(username="user2", email="user2@example.com", password="hashed")

        session.add(user1)
        session.add(user2)
        await session.commit()

        # Get database URL from session
        database_url = str(session.bind.engine.url)
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # Run migration
        stats = await migrate_user_emails(
            database_url=database_url, dry_run=False, domain="test.com", verbose=False
        )

        # Verify no migration needed
        assert stats["users_without_email"] == 0
        assert stats["migrated_users"] == 0

    async def test_migrate_user_emails_with_email_formatted_username(self, session):
        """Test migration for users whose username is already email-formatted."""
        # Create user with email-formatted username but null email field
        user = User(username="valid.user@company.com", email=None, password="hashed")

        session.add(user)
        await session.commit()

        user_id = user.id

        # Get database URL from session
        database_url = str(session.bind.engine.url)
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # Run migration
        stats = await migrate_user_emails(
            database_url=database_url, dry_run=False, domain="test.com", verbose=False
        )

        # Verify user email was set to lowercase username
        stmt = select(User).where(User.id == user_id)
        result = await session.exec(stmt)
        migrated_user = result.first()
        assert migrated_user.email == "valid.user@company.com"

    async def test_migrate_user_emails_statistics(self, session):
        """Test migration statistics are correct."""
        # Create mixed set of users
        user_with_email = User(username="hasemail", email="has@example.com", password="hashed")
        user_without_1 = User(username="needsemail1", email=None, password="hashed")
        user_without_2 = User(username="needsemail2", email=None, password="hashed")

        session.add(user_with_email)
        session.add(user_without_1)
        session.add(user_without_2)
        await session.commit()

        # Get database URL from session
        database_url = str(session.bind.engine.url)
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

        # Run migration
        stats = await migrate_user_emails(
            database_url=database_url, dry_run=False, domain="stats.com", verbose=False
        )

        # Verify statistics
        assert stats["total_users"] >= 3
        assert stats["users_with_email"] >= 1
        assert stats["users_without_email"] >= 2
        assert stats["migrated_users"] >= 2
        assert stats["failed_users"] == 0
        assert "errors" in stats
        assert isinstance(stats["errors"], list)

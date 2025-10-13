"""Data migration script for user email field.

This script populates the email field for existing users who have null email values.
Required before production deployment of Task 3.9 (Invitation Management API).

Background:
-----------
Task 3.9 added an email field to the User model (migration b73646cee5b2) to enable
email-based invitation matching as required by PRD Story 1.1 @AC6. The field is
nullable for backward compatibility with existing users.

This script ensures all users have valid email addresses by:
1. Using username as email if it's email-formatted (contains @)
2. Deriving email from username if not email-formatted
3. Handling special characters and edge cases

Usage:
------
# Dry run (preview changes without committing)
python -m langflow.scripts.migrate_user_emails --dry-run

# Execute migration
python -m langflow.scripts.migrate_user_emails

# Execute with custom email domain
python -m langflow.scripts.migrate_user_emails --domain company.com

# Verbose output
python -m langflow.scripts.migrate_user_emails --verbose

Environment Variables:
---------------------
LANGFLOW_DATABASE_URL - Database connection string (required)

Example:
--------
export LANGFLOW_DATABASE_URL="postgresql://user:pass@localhost/langflow"
python -m langflow.scripts.migrate_user_emails --dry-run
python -m langflow.scripts.migrate_user_emails

Author: Claude Code (Generated for Task 3.9 Gap Fix)
Date: 2025-10-12
"""

import argparse
import asyncio
import re
import sys
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from langflow.services.database.models.user.model import User


def is_valid_email(email: str) -> bool:
    """Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid format, False otherwise
    """
    # RFC 5322 simplified email regex
    pattern = r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    return bool(re.match(pattern, email))


def sanitize_username_for_email(username: str) -> str:
    """Sanitize username to create valid email local part.

    Removes or replaces invalid characters for email local part.

    Args:
        username: Username to sanitize

    Returns:
        Sanitized username suitable for email local part
    """
    # Replace spaces and special chars with dots
    sanitized = re.sub(r"[^a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]", ".", username)
    # Remove consecutive dots
    sanitized = re.sub(r"\.+", ".", sanitized)
    # Remove leading/trailing dots
    sanitized = sanitized.strip(".")
    # Ensure not empty
    if not sanitized:
        sanitized = "user"
    return sanitized.lower()


def derive_email_from_username(username: str, domain: str = "example.com") -> str:
    """Derive email address from username.

    Args:
        username: Username to derive email from
        domain: Email domain to use (default: example.com)

    Returns:
        Derived email address
    """
    # If username is already email-formatted, use it
    if "@" in username and is_valid_email(username):
        return username.lower()

    # If username contains @ but isn't valid, extract local part
    if "@" in username:
        local_part = username.split("@")[0]
        sanitized = sanitize_username_for_email(local_part)
        return f"{sanitized}@{domain}"

    # Sanitize username and create email
    sanitized = sanitize_username_for_email(username)
    return f"{sanitized}@{domain}"


async def migrate_user_emails(
    database_url: str,
    dry_run: bool = False,
    domain: str = "example.com",
    verbose: bool = False,
) -> dict[str, Any]:
    """Migrate user email fields for users with null email.

    Args:
        database_url: Database connection string
        dry_run: If True, preview changes without committing
        domain: Email domain to use for derived emails
        verbose: If True, log detailed information

    Returns:
        Migration statistics dictionary
    """
    # Configure logging
    if verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Create async engine
    engine = create_async_engine(database_url, echo=verbose)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    stats = {
        "total_users": 0,
        "users_with_email": 0,
        "users_without_email": 0,
        "migrated_users": 0,
        "failed_users": 0,
        "dry_run": dry_run,
        "errors": [],
    }

    try:
        async with async_session() as session:
            # Count total users
            result = await session.exec(select(User))
            all_users = result.all()
            stats["total_users"] = len(all_users)

            logger.info(f"Found {stats['total_users']} total users in database")

            # Find users without email
            stmt = select(User).where(User.email.is_(None))
            result = await session.exec(stmt)
            users_without_email = result.all()
            stats["users_without_email"] = len(users_without_email)
            stats["users_with_email"] = stats["total_users"] - stats["users_without_email"]

            logger.info(f"Users with email: {stats['users_with_email']}")
            logger.info(f"Users without email: {stats['users_without_email']}")

            if stats["users_without_email"] == 0:
                logger.success("✅ All users already have email addresses. No migration needed.")
                return stats

            if dry_run:
                logger.warning("🔍 DRY RUN MODE - No changes will be committed")

            # Migrate each user
            for user in users_without_email:
                try:
                    # Derive email from username
                    derived_email = derive_email_from_username(user.username, domain)

                    # Validate derived email
                    if not is_valid_email(derived_email):
                        error_msg = f"Failed to derive valid email for user {user.id} (username: {user.username})"
                        logger.error(error_msg)
                        stats["failed_users"] += 1
                        stats["errors"].append(
                            {
                                "user_id": str(user.id),
                                "username": user.username,
                                "error": "invalid_derived_email",
                            }
                        )
                        continue

                    # Log the migration
                    if verbose:
                        logger.debug(
                            f"User {user.id}: username='{user.username}' → email='{derived_email}'"
                        )
                    else:
                        logger.info(
                            f"Migrating user {user.id}: '{user.username}' → '{derived_email}'"
                        )

                    # Update user email (if not dry run)
                    if not dry_run:
                        user.email = derived_email
                        session.add(user)

                    stats["migrated_users"] += 1

                except Exception as e:
                    error_msg = f"Error migrating user {user.id}: {e!s}"
                    logger.error(error_msg)
                    stats["failed_users"] += 1
                    stats["errors"].append(
                        {
                            "user_id": str(user.id),
                            "username": user.username if hasattr(user, "username") else "unknown",
                            "error": str(e),
                        }
                    )

            # Commit changes (if not dry run)
            if not dry_run:
                await session.commit()
                logger.success(f"✅ Committed {stats['migrated_users']} user email updates")
            else:
                logger.info(f"🔍 Would migrate {stats['migrated_users']} users (dry run)")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e!s}")
        stats["errors"].append({"error": "migration_failed", "message": str(e)})
        raise

    finally:
        await engine.dispose()

    return stats


def print_stats(stats: dict[str, Any]) -> None:
    """Print migration statistics.

    Args:
        stats: Migration statistics dictionary
    """
    print("\n" + "=" * 60)
    print("MIGRATION STATISTICS")
    print("=" * 60)
    print(f"Total Users:          {stats['total_users']}")
    print(f"Users with Email:     {stats['users_with_email']}")
    print(f"Users without Email:  {stats['users_without_email']}")
    print(f"Migrated Users:       {stats['migrated_users']}")
    print(f"Failed Users:         {stats['failed_users']}")
    print(f"Dry Run:              {stats['dry_run']}")
    print("=" * 60)

    if stats["errors"]:
        print("\nERRORS:")
        for error in stats["errors"]:
            if "user_id" in error:
                print(f"  User {error['user_id']} ({error.get('username', 'N/A')}): {error['error']}")
            else:
                print(f"  {error.get('error', 'Unknown error')}: {error.get('message', 'N/A')}")
        print("=" * 60)


async def main_async(args: argparse.Namespace) -> int:
    """Async main function.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import os

    # Get database URL from environment or args
    database_url = args.database_url or os.getenv("LANGFLOW_DATABASE_URL")

    if not database_url:
        logger.error("❌ Database URL not provided")
        logger.info("Set LANGFLOW_DATABASE_URL environment variable or use --database-url")
        return 1

    # Convert sync database URL to async if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("sqlite:///"):
        database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)

    logger.info("=" * 60)
    logger.info("USER EMAIL MIGRATION SCRIPT")
    logger.info("=" * 60)
    logger.info(f"Database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    logger.info(f"Domain: {args.domain}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info(f"Verbose: {args.verbose}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.warning("🔍 DRY RUN MODE - Preview only, no changes will be made")

    try:
        stats = await migrate_user_emails(
            database_url=database_url,
            dry_run=args.dry_run,
            domain=args.domain,
            verbose=args.verbose,
        )

        print_stats(stats)

        if stats["failed_users"] > 0:
            logger.warning(f"⚠️ Migration completed with {stats['failed_users']} failures")
            return 1

        if stats["migrated_users"] > 0:
            if args.dry_run:
                logger.success("✅ Dry run completed successfully")
                logger.info("Run without --dry-run to apply changes")
            else:
                logger.success("✅ Migration completed successfully")
        else:
            logger.info("✅ No migration needed")

        return 0

    except Exception as e:
        logger.error(f"❌ Migration failed: {e!s}")
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Migrate user email fields for existing users",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview changes)
  python -m langflow.scripts.migrate_user_emails --dry-run

  # Execute migration
  export LANGFLOW_DATABASE_URL="postgresql://user:pass@localhost/langflow"
  python -m langflow.scripts.migrate_user_emails

  # Use custom email domain
  python -m langflow.scripts.migrate_user_emails --domain company.com

  # Verbose output
  python -m langflow.scripts.migrate_user_emails --verbose --dry-run
        """,
    )

    parser.add_argument(
        "--database-url",
        type=str,
        help="Database connection string (defaults to LANGFLOW_DATABASE_URL env var)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to database",
    )

    parser.add_argument(
        "--domain",
        type=str,
        default="example.com",
        help="Email domain to use for derived emails (default: example.com)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Run async main
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())

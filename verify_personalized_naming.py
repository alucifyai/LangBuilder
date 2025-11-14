"""Verification script for personalized Starter Project naming feature.

This script tests:
1. Helper functions work correctly
2. New folders get personalized names
3. Pattern matching works for both old and new naming conventions
"""
import asyncio
from uuid import uuid4

from langbuilder.services.database.models.folder.constants import (
    DEFAULT_FOLDER_NAME,
    get_starter_project_name,
    is_starter_project,
)
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from langbuilder.services.database.models.user.model import User
from langbuilder.services.auth.utils import get_password_hash
from langbuilder.services.deps import get_db_service
from langbuilder.initial_setup.setup import get_or_create_default_folder, session_scope
from sqlmodel import select


async def verify_helper_functions():
    """Test helper functions work correctly."""
    print("=" * 60)
    print("Testing Helper Functions")
    print("=" * 60)

    # Test get_starter_project_name
    assert get_starter_project_name("arnab") == "Starter Project - arnab"
    assert get_starter_project_name("testuser") == "Starter Project - testuser"
    print("✓ get_starter_project_name() works correctly")

    # Test is_starter_project with old naming
    assert is_starter_project("Starter Project") is True
    print("✓ is_starter_project() recognizes old naming: 'Starter Project'")

    # Test is_starter_project with new naming
    assert is_starter_project("Starter Project - arnab") is True
    assert is_starter_project("Starter Project - testuser") is True
    print("✓ is_starter_project() recognizes new naming: 'Starter Project - <username>'")

    # Test is_starter_project with non-starter names
    assert is_starter_project("My Project") is False
    assert is_starter_project("Project - Starter") is False
    assert is_starter_project("") is False
    assert is_starter_project(None) is False
    print("✓ is_starter_project() correctly rejects non-Starter Project names")

    print()


async def verify_new_user_gets_personalized_folder():
    """Test that new users get personalized Starter Projects."""
    print("=" * 60)
    print("Testing New User Creation")
    print("=" * 60)

    db_service = get_db_service()

    # Create a test user
    test_username = f"testuser_{uuid4().hex[:8]}"
    test_user_id = uuid4()

    async with db_service.with_session() as session:
        # Create user
        test_user = User(
            id=test_user_id,
            username=test_username,
            password=get_password_hash("testpass123"),
            is_active=True,
            is_superuser=False,
        )
        session.add(test_user)
        await session.commit()

        print(f"✓ Created test user: {test_username}")

    # Create default folder using the setup function
    async with session_scope() as session:
        folder = await get_or_create_default_folder(session, test_user_id)

        # Verify personalized name
        expected_name = get_starter_project_name(test_username)
        assert folder.name == expected_name, \
            f"Expected '{expected_name}', got '{folder.name}'"
        print(f"✓ Default folder has personalized name: '{folder.name}'")

        # Verify it's recognized as a Starter Project
        assert is_starter_project(folder.name), \
            "Folder should be recognized as a Starter Project"
        print(f"✓ Folder is recognized as a Starter Project")

        # Verify immutable Owner assignment exists
        owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()
        if owner_role:
            assignment = (await session.exec(
                select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == test_user_id,
                    UserRoleAssignment.role_id == owner_role.id,
                    UserRoleAssignment.scope_type == "Project",
                    UserRoleAssignment.scope_id == folder.id
                )
            )).first()

            assert assignment is not None, "Owner assignment should exist"
            assert assignment.is_immutable is True, "Assignment should be immutable"
            print(f"✓ Owner role assignment is immutable")

    # Cleanup
    async with db_service.with_session() as session:
        user_to_delete = (await session.exec(
            select(User).where(User.id == test_user_id)
        )).first()
        if user_to_delete:
            await session.delete(user_to_delete)
            await session.commit()
            print(f"✓ Cleaned up test user")

    print()


async def verify_existing_folders():
    """Verify existing Starter Projects have correct names and immutability."""
    print("=" * 60)
    print("Verifying Existing Starter Projects")
    print("=" * 60)

    db_service = get_db_service()

    async with db_service.with_session() as session:
        # Get all folders
        all_folders = (await session.exec(select(Folder))).all()

        # Filter for Starter Projects
        starter_projects = [f for f in all_folders if is_starter_project(f.name)]

        print(f"✓ Found {len(starter_projects)} Starter Project folders")

        if len(starter_projects) == 0:
            print("  (No existing Starter Projects to verify)")
            print()
            return

        owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()

        for folder in starter_projects:
            # Check naming format
            if folder.name == DEFAULT_FOLDER_NAME:
                name_status = "OLD naming"
            elif folder.name.startswith(f"{DEFAULT_FOLDER_NAME} - "):
                name_status = "NEW personalized naming"
            else:
                name_status = "UNKNOWN format"

            # Check immutability
            if owner_role and folder.user_id:
                assignment = (await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == folder.user_id,
                        UserRoleAssignment.role_id == owner_role.id,
                        UserRoleAssignment.scope_type == "Project",
                        UserRoleAssignment.scope_id == folder.id
                    )
                )).first()

                immutable_status = "✓ IMMUTABLE" if assignment and assignment.is_immutable else "✗ MUTABLE"
            else:
                immutable_status = "? NO ASSIGNMENT"

            print(f"  - '{folder.name}': {name_status}, {immutable_status}")

    print()


async def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("PERSONALIZED STARTER PROJECT NAMING VERIFICATION")
    print("=" * 60)
    print()

    try:
        await verify_helper_functions()
        await verify_existing_folders()
        await verify_new_user_gets_personalized_folder()

        print("=" * 60)
        print("✅ ALL VERIFICATION TESTS PASSED")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)

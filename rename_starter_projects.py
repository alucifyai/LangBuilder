"""Script to rename existing Starter Projects to personalized naming structure.

This script finds all folders named "Starter Project" (old naming convention)
and renames them to "Starter Project - <username>" (new personalized naming).
"""
import asyncio
from sqlmodel import select

from langbuilder.services.database.models.folder.constants import DEFAULT_FOLDER_NAME, get_starter_project_name
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.user.model import User
from langbuilder.services.deps import get_db_service


async def rename_starter_projects():
    """Rename all Starter Project folders to use personalized naming."""
    db_service = get_db_service()

    async with db_service.with_session() as session:
        # Get all folders with the old "Starter Project" naming
        old_name_folders = (await session.exec(
            select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME)
        )).all()

        if not old_name_folders:
            print("✅ No folders found with old 'Starter Project' naming")
            return True

        print(f"✓ Found {len(old_name_folders)} folders to rename")

        renamed_count = 0
        skipped_count = 0

        for folder in old_name_folders:
            # Skip folders without a user_id (shouldn't happen for Starter Projects)
            if folder.user_id is None:
                print(f"  - Skipping folder '{folder.name}' (ID: {folder.id}) - no user_id")
                skipped_count += 1
                continue

            # Get the user to obtain username
            user = (await session.exec(
                select(User).where(User.id == folder.user_id)
            )).first()

            if not user:
                print(f"  ⚠️  WARNING: User {folder.user_id} not found for folder {folder.id}")
                skipped_count += 1
                continue

            # Get the personalized name
            new_name = get_starter_project_name(user.username)

            # Check if a folder with the new name already exists for this user
            existing_folder = (await session.exec(
                select(Folder).where(
                    Folder.user_id == user.id,
                    Folder.name == new_name
                )
            )).first()

            if existing_folder and existing_folder.id != folder.id:
                print(f"  ⚠️  WARNING: Folder '{new_name}' already exists for user {user.username} (ID: {user.id})")
                skipped_count += 1
                continue

            # Rename the folder
            folder.name = new_name
            session.add(folder)
            print(f"  ✓ Renamed folder for user '{user.username}': '{DEFAULT_FOLDER_NAME}' → '{new_name}'")
            renamed_count += 1

        if renamed_count > 0:
            await session.commit()
            print(f"\n✅ SUCCESS: Renamed {renamed_count} Starter Project folders")
            if skipped_count > 0:
                print(f"   Skipped {skipped_count} folders (see warnings above)")
        else:
            print(f"\n✅ No folders needed renaming")
            if skipped_count > 0:
                print(f"   Skipped {skipped_count} folders (see warnings above)")

        return True


if __name__ == "__main__":
    result = asyncio.run(rename_starter_projects())
    exit(0 if result else 1)

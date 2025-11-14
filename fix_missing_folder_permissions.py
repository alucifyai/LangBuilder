"""Script to fix missing Owner role assignments for existing user folders."""
import asyncio
from sqlmodel import select

from langbuilder.services.database.models.folder.constants import is_starter_project
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from langbuilder.services.deps import get_db_service


async def fix_missing_folder_permissions():
    """Find folders without Owner role assignments and create them, mark Starter Project ownership as immutable."""
    db_service = get_db_service()

    async with db_service.with_session() as session:
        # Get the Owner role
        owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()
        if not owner_role:
            print("❌ ERROR: Owner role not found in database")
            return False

        print(f"✓ Found Owner role (ID: {owner_role.id})")

        # Get all folders
        folders = (await session.exec(select(Folder))).all()
        print(f"✓ Found {len(folders)} folders in database")

        fixed_count = 0
        updated_count = 0
        for folder in folders:
            # Skip folders without a user_id (shared/global folders)
            if folder.user_id is None:
                print(f"  - Skipping folder '{folder.name}' (no user_id - shared folder)")
                continue

            # Check if Owner role assignment exists for this folder
            existing_assignment = (await session.exec(
                select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == folder.user_id,
                    UserRoleAssignment.role_id == owner_role.id,
                    UserRoleAssignment.scope_type == "Project",
                    UserRoleAssignment.scope_id == folder.id
                )
            )).first()

            # Determine if this is a Starter Project folder (supports both old and new naming)
            is_starter = is_starter_project(folder.name)

            if not existing_assignment:
                # Create the missing Owner role assignment
                assignment = UserRoleAssignment(
                    user_id=folder.user_id,
                    role_id=owner_role.id,
                    scope_type="Project",
                    scope_id=folder.id,
                    is_immutable=is_starter  # Mark Starter Project ownership as immutable
                )
                session.add(assignment)
                immutable_status = " (immutable)" if is_starter else ""
                print(f"  + Created Owner assignment for folder '{folder.name}'{immutable_status} (user: {folder.user_id})")
                fixed_count += 1
            elif is_starter and not existing_assignment.is_immutable:
                # Update existing Starter Project assignment to be immutable
                existing_assignment.is_immutable = True
                session.add(existing_assignment)
                print(f"  * Updated Owner assignment for folder '{folder.name}' to immutable (user: {folder.user_id})")
                updated_count += 1

        if fixed_count > 0 or updated_count > 0:
            await session.commit()
            print(f"\n✅ SUCCESS: Created {fixed_count} missing Owner role assignments, updated {updated_count} to immutable")
        else:
            print(f"\n✅ All folders already have correct Owner role assignments")

        return True


if __name__ == "__main__":
    result = asyncio.run(fix_missing_folder_permissions())
    exit(0 if result else 1)

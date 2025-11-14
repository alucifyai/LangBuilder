"""Script to mark all Starter Project folder and flow ownership assignments as immutable."""
import asyncio
from sqlmodel import select

from langbuilder.services.database.models.flow.model import Flow
from langbuilder.services.database.models.folder.constants import is_starter_project
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from langbuilder.services.deps import get_db_service


async def fix_starter_project_immutability():
    """Mark all Starter Project folder and flow ownership assignments as immutable."""
    db_service = get_db_service()

    async with db_service.with_session() as session:
        # Get the Owner role
        owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()
        if not owner_role:
            print("❌ ERROR: Owner role not found in database")
            return False

        print(f"✓ Found Owner role (ID: {owner_role.id})")

        folder_updated_count = 0
        flow_updated_count = 0

        # Get all folders and filter for Starter Projects
        all_folders = (await session.exec(select(Folder))).all()
        folders = [f for f in all_folders if is_starter_project(f.name)]

        print(f"✓ Found {len(folders)} Starter Project folders in database")

        for folder in folders:
            if folder.user_id is None:
                continue

            # Update folder owner assignment to be immutable
            folder_assignment = (await session.exec(
                select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == folder.user_id,
                    UserRoleAssignment.role_id == owner_role.id,
                    UserRoleAssignment.scope_type == "Project",
                    UserRoleAssignment.scope_id == folder.id
                )
            )).first()

            if folder_assignment and not folder_assignment.is_immutable:
                folder_assignment.is_immutable = True
                session.add(folder_assignment)
                print(f"  * Updated folder '{folder.name}' ownership to immutable (user: {folder.user_id})")
                folder_updated_count += 1

            # Get all flows in this Starter Project folder
            flows = (await session.exec(
                select(Flow).where(Flow.folder_id == folder.id)
            )).all()

            for flow in flows:
                # Update flow owner assignment to be immutable
                flow_assignment = (await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == flow.user_id,
                        UserRoleAssignment.role_id == owner_role.id,
                        UserRoleAssignment.scope_type == "Flow",
                        UserRoleAssignment.scope_id == flow.id
                    )
                )).first()

                if flow_assignment and not flow_assignment.is_immutable:
                    flow_assignment.is_immutable = True
                    session.add(flow_assignment)
                    print(f"    + Updated flow '{flow.name}' ownership to immutable (user: {flow.user_id})")
                    flow_updated_count += 1

        if folder_updated_count > 0 or flow_updated_count > 0:
            await session.commit()
            print(f"\n✅ SUCCESS: Updated {folder_updated_count} folder assignments and {flow_updated_count} flow assignments to immutable")
        else:
            print(f"\n✅ All Starter Project assignments are already immutable")

        return True


if __name__ == "__main__":
    result = asyncio.run(fix_starter_project_immutability())
    exit(0 if result else 1)

from uuid import UUID

from sqlmodel import and_, select, update
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.initial_setup.setup import get_or_create_default_folder
from langbuilder.services.database.models.flow.model import Flow

from .constants import DEFAULT_FOLDER_DESCRIPTION, DEFAULT_FOLDER_NAME
from .model import Folder


async def create_default_folder_if_it_doesnt_exist(session: AsyncSession, user_id: UUID):
    from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
    from langbuilder.services.database.models.user.model import User
    from loguru import logger
    from .constants import get_starter_project_name, is_starter_project

    # Check if a Starter Project folder already exists (with any naming convention)
    stmt = select(Folder).where(Folder.user_id == user_id)
    all_folders = (await session.exec(stmt)).all()

    # Find existing Starter Project (old or new naming convention)
    folder = None
    for f in all_folders:
        if is_starter_project(f.name):
            folder = f
            break

    if not folder:
        # Get the user to obtain username for personalized folder name
        user_result = await session.exec(select(User).where(User.id == user_id))
        user = user_result.first()
        if not user:
            msg = f"User with ID {user_id} not found"
            raise ValueError(msg)

        # Get personalized Starter Project name
        personalized_name = get_starter_project_name(user.username)

        folder = Folder(
            name=personalized_name,
            user_id=user_id,
            description=DEFAULT_FOLDER_DESCRIPTION,
        )
        session.add(folder)
        await session.commit()
        await session.refresh(folder)
        await session.exec(
            update(Flow)
            .where(
                and_(
                    Flow.folder_id is None,
                    Flow.user_id == user_id,
                )
            )
            .values(folder_id=folder.id)
        )
        await session.commit()

        # Create Owner role assignment for the default folder
        try:
            owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()
            if owner_role:
                # Check if assignment already exists
                existing_assignment = (await session.exec(
                    select(UserRoleAssignment).where(
                        UserRoleAssignment.user_id == user_id,
                        UserRoleAssignment.role_id == owner_role.id,
                        UserRoleAssignment.scope_type == "Project",
                        UserRoleAssignment.scope_id == folder.id
                    )
                )).first()

                if not existing_assignment:
                    assignment = UserRoleAssignment(
                        user_id=user_id,
                        role_id=owner_role.id,
                        scope_type="Project",
                        scope_id=folder.id,
                        is_immutable=True  # Starter Project ownership is immutable
                    )
                    session.add(assignment)
                    await session.commit()
                    logger.debug(f"Created immutable Owner role assignment for default folder {folder.id}")
            else:
                logger.warning("Owner role not found - cannot assign to default folder")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to assign Owner role to default folder: {e}")
            # Don't fail folder creation if RBAC assignment fails

    return folder


async def get_default_folder_id(session: AsyncSession, user_id: UUID):
    from .constants import is_starter_project

    # Find Starter Project folder (supports both old and new naming conventions)
    all_folders = (await session.exec(select(Folder).where(Folder.user_id == user_id))).all()

    folder = None
    for f in all_folders:
        if is_starter_project(f.name):
            folder = f
            break

    if not folder:
        folder = await get_or_create_default_folder(session, user_id)
    return folder.id

import asyncio
from uuid import uuid4

import pytest
from langbuilder.initial_setup.setup import DEFAULT_FOLDER_NAME, get_or_create_default_folder, session_scope
from langbuilder.services.database.models.folder.model import FolderRead


@pytest.mark.usefixtures("client")
async def test_get_or_create_default_folder_creation() -> None:
    """Test that a default project is created for a new user.

    This test verifies that when no default project exists for a given user,
    get_or_create_default_folder creates one with the expected name and assigns it an ID.
    """
    test_user_id = uuid4()
    async with session_scope() as session:
        folder = await get_or_create_default_folder(session, test_user_id)
        assert folder.name == DEFAULT_FOLDER_NAME, "The project name should match the default."
        assert hasattr(folder, "id"), "The project should have an 'id' attribute after creation."


@pytest.mark.usefixtures("client")
async def test_get_or_create_default_folder_idempotency() -> None:
    """Test that subsequent calls to get_or_create_default_folder return the same project.

    The function should be idempotent such that if a default project already exists,
    calling the function again does not create a new one.
    """
    test_user_id = uuid4()
    async with session_scope() as session:
        folder_first = await get_or_create_default_folder(session, test_user_id)
        folder_second = await get_or_create_default_folder(session, test_user_id)
        assert folder_first.id == folder_second.id, "Both calls should return the same folder instance."


@pytest.mark.usefixtures("client")
async def test_get_or_create_default_folder_concurrent_calls() -> None:
    """Test concurrent invocations of get_or_create_default_folder.

    This test ensures that when multiple concurrent calls are made for the same user,
    only one default project is created, demonstrating idempotency under concurrent access.
    """
    test_user_id = uuid4()

    async def get_folder() -> FolderRead:
        async with session_scope() as session:
            return await get_or_create_default_folder(session, test_user_id)

    results = await asyncio.gather(get_folder(), get_folder(), get_folder())
    folder_ids = {folder.id for folder in results}
    assert len(folder_ids) == 1, "Concurrent calls must return a single, consistent folder instance."


@pytest.mark.usefixtures("client")
async def test_get_or_create_default_folder_creates_immutable_owner_assignment() -> None:
    """Test that get_or_create_default_folder creates an immutable Owner role assignment.

    This test verifies that when a default Starter Project folder is created,
    an Owner role assignment is automatically created with is_immutable=True.
    """
    from sqlmodel import select
    from langbuilder.services.database.models.rbac import Role, UserRoleAssignment

    test_user_id = uuid4()
    async with session_scope() as session:
        # Create the default folder
        folder = await get_or_create_default_folder(session, test_user_id)

        # Get the Owner role
        owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()
        assert owner_role is not None, "Owner role should exist in database"

        # Verify Owner role assignment was created
        assignment = (await session.exec(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == test_user_id,
                UserRoleAssignment.role_id == owner_role.id,
                UserRoleAssignment.scope_type == "Project",
                UserRoleAssignment.scope_id == folder.id
            )
        )).first()

        assert assignment is not None, "Owner role assignment should be created for default folder"
        assert assignment.is_immutable is True, "Starter Project Owner assignment should be immutable"


@pytest.mark.usefixtures("client")
async def test_get_or_create_default_folder_doesnt_duplicate_assignment() -> None:
    """Test that get_or_create_default_folder doesn't create duplicate Owner assignments.

    This test verifies that when a default folder already exists with an Owner assignment,
    subsequent calls don't create duplicate assignments.
    """
    from sqlmodel import select
    from langbuilder.services.database.models.rbac import Role, UserRoleAssignment

    test_user_id = uuid4()
    async with session_scope() as session:
        # Create the default folder twice
        folder_first = await get_or_create_default_folder(session, test_user_id)
        folder_second = await get_or_create_default_folder(session, test_user_id)

        # Get the Owner role
        owner_role = (await session.exec(select(Role).where(Role.name == "Owner"))).first()
        assert owner_role is not None, "Owner role should exist in database"

        # Count Owner role assignments for this folder
        assignments = (await session.exec(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == test_user_id,
                UserRoleAssignment.role_id == owner_role.id,
                UserRoleAssignment.scope_type == "Project",
                UserRoleAssignment.scope_id == folder_first.id
            )
        )).all()

        assert len(assignments) == 1, "Should have exactly one Owner assignment, not duplicates"
        assert assignments[0].is_immutable is True, "The assignment should be immutable"

"""Unit tests for folder utility functions, especially Starter Project immutability."""

from uuid import uuid4

import pytest
from sqlmodel import select

from langbuilder.services.database.models.folder.constants import DEFAULT_FOLDER_NAME
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.folder.utils import create_default_folder_if_it_doesnt_exist
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from langbuilder.services.deps import get_db_service


@pytest.mark.usefixtures("client")
async def test_create_default_folder_creates_immutable_owner_assignment():
    """Test that create_default_folder_if_it_doesnt_exist creates immutable Owner role assignment.

    This test verifies that when a default Starter Project folder is created,
    an Owner role assignment is automatically created with is_immutable=True.
    """
    db_service = get_db_service()
    test_user_id = uuid4()

    async with db_service.with_session() as session:
        # Create the default folder
        folder = await create_default_folder_if_it_doesnt_exist(session, test_user_id)

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
        assert folder.name == DEFAULT_FOLDER_NAME, "Folder should be named 'Starter Project'"


@pytest.mark.usefixtures("client")
async def test_create_default_folder_doesnt_duplicate_assignment():
    """Test that create_default_folder_if_it_doesnt_exist doesn't create duplicate assignments.

    This test verifies that when a default folder already exists,
    subsequent calls don't create duplicate Owner assignments.
    """
    db_service = get_db_service()
    test_user_id = uuid4()

    async with db_service.with_session() as session:
        # Create the default folder twice
        folder_first = await create_default_folder_if_it_doesnt_exist(session, test_user_id)
        folder_second = await create_default_folder_if_it_doesnt_exist(session, test_user_id)

        assert folder_first.id == folder_second.id, "Both calls should return the same folder"

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


@pytest.mark.usefixtures("client")
async def test_create_default_folder_returns_existing_folder():
    """Test that create_default_folder_if_it_doesnt_exist returns existing folder if it exists.

    This test verifies idempotency of folder creation.
    """
    db_service = get_db_service()
    test_user_id = uuid4()

    async with db_service.with_session() as session:
        # Create folder first time
        folder_first = await create_default_folder_if_it_doesnt_exist(session, test_user_id)
        first_id = folder_first.id

        # Try to create again - should return the same folder
        folder_second = await create_default_folder_if_it_doesnt_exist(session, test_user_id)
        second_id = folder_second.id

        assert first_id == second_id, "Should return the same folder on subsequent calls"
        assert folder_second.name == DEFAULT_FOLDER_NAME, "Folder name should be preserved"

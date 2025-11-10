"""
Integration tests for Starter Project immutability.

These tests verify end-to-end behavior for:
- New users getting Starter Project with immutable Owner assignment
- Flows created in Starter Project get immutable Owner assignments
- Immutable assignments don't appear in GET /api/v1/rbac/assignments response
- Attempting to delete immutable assignment fails appropriately
"""

import json
from uuid import uuid4

import pytest
from langbuilder.services.database.models.flow.model import FlowCreate
from langbuilder.services.database.models.folder.constants import DEFAULT_FOLDER_NAME, get_starter_project_name, is_starter_project
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from sqlmodel import select


@pytest.fixture
async def roles(client_session, client):
    """Get roles from database and reload RBAC cache."""
    from langbuilder.api.v1.rbac import get_rbac_service

    # Get roles from database
    result = await client_session.exec(select(Role))
    roles_list = result.all()

    # Reload RBAC cache with current database state
    rbac_service = get_rbac_service()
    await rbac_service._load_role_permission_cache()

    return {r.name: r for r in roles_list}


@pytest.fixture
async def superuser_headers(client):
    """Get auth headers for superuser."""
    from langbuilder.services.auth.utils import get_password_hash
    from langbuilder.services.database.models.user.model import User
    from langbuilder.services.deps import get_db_service

    db_service = get_db_service()
    async with db_service.with_session() as session:
        # Check if superuser exists
        superuser_result = await session.exec(
            select(User).where(User.is_superuser == True)
        )
        superuser = superuser_result.first()

        if not superuser:
            # Create a superuser for testing
            superuser = User(
                username=f"superuser_{uuid4().hex[:8]}",
                password=get_password_hash("testpass123"),
                is_active=True,
                is_superuser=True,
            )
            session.add(superuser)
            await session.commit()
            await session.refresh(superuser)

    # Login and get token
    login_data = {"username": superuser.username, "password": "testpass123"}
    response = await client.post("api/v1/login", data=login_data)
    assert response.status_code == 200
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


class TestStarterProjectImmutability:
    """Test suite for Starter Project immutability feature."""

    @pytest.mark.asyncio
    async def test_new_user_gets_starter_project_with_immutable_owner(self, client, client_session, roles):
        """Test that a new user automatically gets a Starter Project with immutable Owner assignment.

        This test verifies that when a user is created, they automatically receive:
        1. A "Starter Project" folder
        2. An Owner role assignment for that folder
        3. That assignment is marked as immutable
        """
        from langbuilder.services.auth.utils import get_password_hash
        from langbuilder.services.database.models.user.model import User
        from langbuilder.initial_setup.setup import get_or_create_default_folder, session_scope

        # Create a new user
        new_user_id = uuid4()
        username = f"testuser_{uuid4().hex[:8]}"
        new_user = User(
            id=new_user_id,
            username=username,
            password=get_password_hash("testpass123"),
            is_active=True,
            is_superuser=False,
        )
        client_session.add(new_user)
        await client_session.commit()

        # Trigger default folder creation
        async with session_scope() as session:
            folder_read = await get_or_create_default_folder(session, new_user_id)

            # Verify folder was created with personalized Starter Project name
            expected_name = get_starter_project_name(username)
            assert folder_read.name == expected_name, f"Should create personalized Starter Project: expected '{expected_name}', got '{folder_read.name}'"
            assert is_starter_project(folder_read.name), "Folder should be recognized as a Starter Project"

            # Get the actual Folder object from database
            db_folder = (await session.exec(
                select(Folder).where(Folder.id == folder_read.id)
            )).first()

            assert db_folder is not None, "Folder should exist in database"
            assert db_folder.user_id == new_user_id, "Folder should belong to the new user"

            # Verify immutable Owner assignment was created
            owner_role = roles["Owner"]
            assignment = (await session.exec(
                select(UserRoleAssignment).where(
                    UserRoleAssignment.user_id == new_user_id,
                    UserRoleAssignment.role_id == owner_role.id,
                    UserRoleAssignment.scope_type == "Project",
                    UserRoleAssignment.scope_id == folder_read.id
                )
            )).first()

            assert assignment is not None, "Owner assignment should be created"
            assert assignment.is_immutable is True, "Starter Project Owner assignment should be immutable"

        # Cleanup
        await client_session.delete(new_user)
        await client_session.commit()

    @pytest.mark.asyncio
    async def test_flows_in_starter_project_get_immutable_owner_assignment(
        self, client, logged_in_headers, client_session, roles, active_user
    ):
        """Test that flows created in Starter Project get immutable Owner assignments.

        This test verifies that when a flow is created in a user's Starter Project folder,
        the Owner role assignment for that flow is marked as immutable.
        """
        # Get or create Starter Project for active_user
        # Search for any folder that is a Starter Project (old or new naming convention)
        all_folders = (await client_session.exec(
            select(Folder).where(Folder.user_id == active_user.id)
        )).all()

        starter_project = None
        for f in all_folders:
            if is_starter_project(f.name):
                starter_project = f
                break

        # If no Starter Project exists, create one
        if not starter_project:
            from langbuilder.initial_setup.setup import get_or_create_default_folder, session_scope
            async with session_scope() as session:
                folder_read = await get_or_create_default_folder(session, active_user.id)
                starter_project = (await client_session.exec(
                    select(Folder).where(Folder.id == folder_read.id)
                )).first()

        assert starter_project is not None, "Starter Project should exist"

        # Create a flow in the Starter Project
        flow_data = {
            "name": f"Test Flow {uuid4().hex[:8]}",
            "description": "Test flow for immutability check",
            "data": {"nodes": []},
            "folder_id": str(starter_project.id),
        }

        response = await client.post(
            "api/v1/flows/",
            json=flow_data,
            headers=logged_in_headers,
        )

        assert response.status_code == 201, f"Flow creation should succeed: {response.text}"
        flow_response = response.json()
        flow_id = flow_response["id"]

        # Verify the flow Owner assignment is immutable
        owner_role = roles["Owner"]
        assignment = (await client_session.exec(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == active_user.id,
                UserRoleAssignment.role_id == owner_role.id,
                UserRoleAssignment.scope_type == "Flow",
                UserRoleAssignment.scope_id == flow_id
            )
        )).first()

        assert assignment is not None, "Flow Owner assignment should be created"
        assert assignment.is_immutable is True, "Flow in Starter Project should have immutable Owner assignment"

        # Cleanup - delete the flow
        await client.delete(f"api/v1/flows/{flow_id}", headers=logged_in_headers)

    @pytest.mark.asyncio
    async def test_immutable_assignments_filtered_from_api_response(
        self, client, logged_in_headers, client_session, roles, active_user, superuser_headers
    ):
        """Test that immutable assignments don't appear in GET /api/v1/rbac/assignments.

        This test verifies that when listing role assignments via the API,
        immutable assignments (like Starter Project ownership) are filtered out
        and don't appear in the response.
        """
        # Get Starter Project for active_user
        # Search for any folder that is a Starter Project (old or new naming convention)
        all_folders_for_user = (await client_session.exec(
            select(Folder).where(Folder.user_id == active_user.id)
        )).all()

        starter_project = None
        for f in all_folders_for_user:
            if is_starter_project(f.name):
                starter_project = f
                break

        if not starter_project:
            from langbuilder.initial_setup.setup import get_or_create_default_folder, session_scope
            async with session_scope() as session:
                folder_read = await get_or_create_default_folder(session, active_user.id)
                starter_project = (await client_session.exec(
                    select(Folder).where(Folder.id == folder_read.id)
                )).first()

        # Verify immutable assignment exists in database
        owner_role = roles["Owner"]
        immutable_assignment = (await client_session.exec(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == active_user.id,
                UserRoleAssignment.role_id == owner_role.id,
                UserRoleAssignment.scope_type == "Project",
                UserRoleAssignment.scope_id == starter_project.id,
                UserRoleAssignment.is_immutable == True
            )
        )).first()

        assert immutable_assignment is not None, "Immutable assignment should exist in database"

        # Get assignments list from API (using superuser for admin access)
        response = await client.get(
            f"api/v1/rbac/assignments?user_id={active_user.id}",
            headers=superuser_headers,
        )

        assert response.status_code == 200, f"Should get assignments successfully: {response.text}"
        assignments = response.json()

        # Verify immutable assignment is NOT in the response
        assignment_ids = [a["id"] for a in assignments]
        assert str(immutable_assignment.id) not in assignment_ids, \
            "Immutable assignments should be filtered out from API response"

        # Verify all returned assignments are mutable
        for assignment in assignments:
            # The response should only contain mutable assignments
            # We verify this by checking the database directly
            db_assignment = (await client_session.exec(
                select(UserRoleAssignment).where(UserRoleAssignment.id == assignment["id"])
            )).first()
            if db_assignment:
                assert db_assignment.is_immutable is False, \
                    f"Assignment {assignment['id']} in response should be mutable"

    @pytest.mark.asyncio
    async def test_cannot_delete_immutable_assignment_via_api(
        self, client, logged_in_headers, client_session, roles, active_user, superuser_headers
    ):
        """Test that attempting to delete an immutable assignment via API fails.

        This test verifies that the DELETE /api/v1/rbac/assignments/{id} endpoint
        properly rejects attempts to delete immutable assignments.
        """
        # Get Starter Project for active_user
        # Search for any folder that is a Starter Project (old or new naming convention)
        all_folders_for_user = (await client_session.exec(
            select(Folder).where(Folder.user_id == active_user.id)
        )).all()

        starter_project = None
        for f in all_folders_for_user:
            if is_starter_project(f.name):
                starter_project = f
                break

        if not starter_project:
            from langbuilder.initial_setup.setup import get_or_create_default_folder, session_scope
            async with session_scope() as session:
                folder_read = await get_or_create_default_folder(session, active_user.id)
                starter_project = (await client_session.exec(
                    select(Folder).where(Folder.id == folder_read.id)
                )).first()

        # Get the immutable assignment
        owner_role = roles["Owner"]
        immutable_assignment = (await client_session.exec(
            select(UserRoleAssignment).where(
                UserRoleAssignment.user_id == active_user.id,
                UserRoleAssignment.role_id == owner_role.id,
                UserRoleAssignment.scope_type == "Project",
                UserRoleAssignment.scope_id == starter_project.id,
                UserRoleAssignment.is_immutable == True
            )
        )).first()

        assert immutable_assignment is not None, "Immutable assignment should exist"

        # Attempt to delete the immutable assignment via API (using superuser)
        response = await client.delete(
            f"api/v1/rbac/assignments/{immutable_assignment.id}",
            headers=superuser_headers,
        )

        # Should fail with appropriate error
        assert response.status_code == 400, "Deleting immutable assignment should fail with 400"
        assert "immutable" in response.text.lower(), "Error message should mention immutability"

        # Verify assignment still exists in database
        still_exists = (await client_session.exec(
            select(UserRoleAssignment).where(UserRoleAssignment.id == immutable_assignment.id)
        )).first()

        assert still_exists is not None, "Immutable assignment should still exist after failed delete"
        assert still_exists.is_immutable is True, "Assignment should still be immutable"

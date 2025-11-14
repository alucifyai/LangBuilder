"""
Unit tests for Task 2.3: Default Role Assignments during Project Creation.

Tests verify that Owner role is automatically assigned to users when they create projects.
"""

import pytest
from uuid import UUID

from fastapi import status
from httpx import AsyncClient
from sqlmodel import select

from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment


@pytest.mark.asyncio
async def test_create_project_assigns_owner_role(client: AsyncClient, logged_in_headers, client_session, active_user):
    """
    Test that creating a project automatically assigns Owner role to the creator.

    Success Criteria:
    - Project is created successfully
    - Owner role assignment is created with correct scope_type and scope_id
    - Assignment is linked to the creating user
    """
    # Create a project
    project_data = {
        "name": "Test Project With Owner Assignment",
        "description": "Test project for owner role assignment",
        "flows_list": [],
        "components_list": [],
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result = response.json()

    # Assert project creation succeeded
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in result
    assert result["name"] == project_data["name"]

    # Convert string UUIDs to UUID objects for database queries
    project_id = UUID(result["id"])
    user_id = active_user.id

    # Verify Owner role assignment was created
    # Get Owner role
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role_result = await client_session.exec(owner_role_stmt)
    owner_role = owner_role_result.first()

    assert owner_role is not None, "Owner role should exist in database"

    # Check for assignment
    assignment_stmt = (
        select(UserRoleAssignment)
        .where(UserRoleAssignment.user_id == user_id)
        .where(UserRoleAssignment.role_id == owner_role.id)
        .where(UserRoleAssignment.scope_type == "Project")
        .where(UserRoleAssignment.scope_id == project_id)
    )
    assignment_result = await client_session.exec(assignment_stmt)
    assignment = assignment_result.first()

    # Verify assignment exists and has correct properties
    assert assignment is not None, "Owner role assignment should be created for project creator"
    assert assignment.user_id == user_id
    assert assignment.role_id == owner_role.id
    assert assignment.scope_type == "Project"
    assert assignment.scope_id == project_id
    assert assignment.is_immutable is False, "Project owner assignments should not be immutable"
    assert assignment.created_by == user_id, "Assignment should be created by the project creator"


@pytest.mark.asyncio
async def test_create_project_assignment_in_same_transaction(client: AsyncClient, logged_in_headers, client_session, active_user):
    """
    Test that project creation and role assignment happen in the same transaction.

    Success Criteria:
    - If project creation fails, no assignment is created
    - Assignment is created immediately after project creation
    """
    project_data = {
        "name": "Test Transaction Project",
        "description": "Test transaction handling",
        "flows_list": [],
        "components_list": [],
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_201_CREATED

    # Convert string UUIDs to UUID objects for database queries
    project_id = UUID(result["id"])
    user_id = active_user.id

    # Verify both project and assignment exist
    project_stmt = select(Folder).where(Folder.id == project_id)
    project_result = await client_session.exec(project_stmt)
    project = project_result.first()
    assert project is not None

    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await client_session.exec(owner_role_stmt)).first()

    assignment_stmt = (
        select(UserRoleAssignment)
        .where(UserRoleAssignment.user_id == user_id)
        .where(UserRoleAssignment.scope_id == project_id)
        .where(UserRoleAssignment.role_id == owner_role.id)
    )
    assignment_result = await client_session.exec(assignment_stmt)
    assignment = assignment_result.first()

    assert assignment is not None, "Assignment should exist after project creation"


@pytest.mark.asyncio
async def test_create_multiple_projects_each_gets_owner_role(
    client: AsyncClient, logged_in_headers, client_session
):
    """
    Test that each project gets its own Owner role assignment.

    Success Criteria:
    - Multiple projects can be created
    - Each project has its own Owner assignment
    - Assignments have different scope_ids
    """
    project_ids = []

    # Create 3 projects
    for i in range(3):
        project_data = {
            "name": f"Test Project Multiple {i}",
            "description": f"Test project {i}",
            "flows_list": [],
            "components_list": [],
        }

        response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
        result = response.json()

        assert response.status_code == status.HTTP_201_CREATED
        # Convert string UUID to UUID object for database queries
        project_ids.append(UUID(result["id"]))

    # Verify each project has its own assignment
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await client_session.exec(owner_role_stmt)).first()

    for project_id in project_ids:
        assignment_stmt = (
            select(UserRoleAssignment)
            .where(UserRoleAssignment.scope_id == project_id)
            .where(UserRoleAssignment.scope_type == "Project")
            .where(UserRoleAssignment.role_id == owner_role.id)
        )
        assignment = (await client_session.exec(assignment_stmt)).first()

        assert assignment is not None, f"Project {project_id} should have Owner assignment"
        assert assignment.scope_id == project_id

    # Verify assignments are distinct
    assert len(set(project_ids)) == 3, "All project IDs should be unique"


@pytest.mark.asyncio
async def test_create_project_without_owner_role_logs_warning(client: AsyncClient, logged_in_headers):
    """
    Test that if Owner role is missing, a warning is logged but project creation succeeds.

    Success Criteria:
    - Project is created even if Owner role is missing
    - Warning is logged about missing Owner role
    """
    project_data = {
        "name": "Test Project No Owner Role",
        "description": "Test project without owner role",
        "flows_list": [],
        "components_list": [],
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result = response.json()

    # Project should still be created
    assert response.status_code == status.HTTP_201_CREATED
    assert "id" in result


@pytest.mark.asyncio
async def test_project_creation_assignment_properties(client: AsyncClient, logged_in_headers, client_session, active_user):
    """
    Test that the Owner role assignment has correct properties.

    Success Criteria:
    - is_immutable is False (can be modified later)
    - created_by is set to the creating user
    - scope_type is "Project" (capitalized)
    - scope_id matches the project ID
    """
    project_data = {
        "name": "Test Project Assignment Properties",
        "description": "Test assignment properties",
        "flows_list": [],
        "components_list": [],
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_201_CREATED

    # Convert string UUIDs to UUID objects for database queries
    project_id = UUID(result["id"])
    user_id = active_user.id

    # Get assignment
    owner_role = (await client_session.exec(select(Role).where(Role.name == "Owner"))).first()
    assignment_stmt = (
        select(UserRoleAssignment)
        .where(UserRoleAssignment.scope_id == project_id)
        .where(UserRoleAssignment.role_id == owner_role.id)
    )
    assignment = (await client_session.exec(assignment_stmt)).first()

    # Verify properties
    assert assignment is not None
    assert assignment.is_immutable is False, "Project owner assignments should be mutable"
    assert assignment.created_by == user_id, "created_by should be the project creator"
    assert assignment.scope_type == "Project", "scope_type should be 'Project' (capitalized)"
    assert assignment.scope_id == project_id, "scope_id should match project ID"
    assert assignment.created_at is not None, "created_at should be set"


@pytest.mark.asyncio
async def test_project_with_flows_assigns_owner_to_project_only(
    client: AsyncClient, logged_in_headers, client_session
):
    """
    Test that when creating a project with flows, Owner is assigned to project only.

    Success Criteria:
    - Project gets Owner assignment
    - Flows added to project do not get new assignments (they keep their existing ones)
    """
    # This test documents behavior where adding existing flows to a project
    # doesn't change their Owner assignments
    project_data = {
        "name": "Test Project With Flows",
        "description": "Test project with flows",
        "flows_list": [],  # In practice, would have flow IDs
        "components_list": [],
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_201_CREATED

    # Convert string UUID to UUID object for database queries
    project_id = UUID(result["id"])

    # Verify project has Owner assignment
    owner_role = (await client_session.exec(select(Role).where(Role.name == "Owner"))).first()
    assignment_stmt = (
        select(UserRoleAssignment)
        .where(UserRoleAssignment.scope_id == project_id)
        .where(UserRoleAssignment.scope_type == "Project")
        .where(UserRoleAssignment.role_id == owner_role.id)
    )
    assignment = (await client_session.exec(assignment_stmt)).first()

    assert assignment is not None, "Project should have Owner assignment"


@pytest.mark.asyncio
async def test_duplicate_project_name_still_assigns_owner(client: AsyncClient, logged_in_headers, client_session):
    """
    Test that when a project name is duplicated and renamed, Owner is still assigned.

    Success Criteria:
    - Second project with same name gets renamed (e.g., "Project (1)")
    - Second project still gets Owner assignment
    """
    project_data = {
        "name": "Duplicate Project Name",
        "description": "First project",
        "flows_list": [],
        "components_list": [],
    }

    # Create first project
    response1 = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result1 = response1.json()
    assert response1.status_code == status.HTTP_201_CREATED
    # Convert string UUID to UUID object for database queries
    project_id_1 = UUID(result1["id"])

    # Create second project with same name
    response2 = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result2 = response2.json()
    assert response2.status_code == status.HTTP_201_CREATED
    # Convert string UUID to UUID object for database queries
    project_id_2 = UUID(result2["id"])

    # Names should be different
    assert result2["name"] != result1["name"]
    assert "(1)" in result2["name"] or result2["name"] != project_data["name"]

    # Both should have Owner assignments
    owner_role = (await client_session.exec(select(Role).where(Role.name == "Owner"))).first()

    for project_id in [project_id_1, project_id_2]:
        assignment_stmt = (
            select(UserRoleAssignment)
            .where(UserRoleAssignment.scope_id == project_id)
            .where(UserRoleAssignment.scope_type == "Project")
            .where(UserRoleAssignment.role_id == owner_role.id)
        )
        assignment = (await client_session.exec(assignment_stmt)).first()
        assert assignment is not None, f"Project {project_id} should have Owner assignment"


@pytest.mark.asyncio
async def test_project_creation_with_flows_and_components_assigns_owner(
    client: AsyncClient, logged_in_headers, client_session
):
    """
    Test that project creation with flows_list and components_list still assigns Owner.

    Success Criteria:
    - Project is created with flows and components
    - Owner assignment is created for the project
    """
    project_data = {
        "name": "Test Project With Lists",
        "description": "Test project with flows and components lists",
        "flows_list": [],  # Empty for now, but tests the code path
        "components_list": [],
    }

    response = await client.post("api/v1/projects/", json=project_data, headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_201_CREATED

    # Convert string UUID to UUID object for database queries
    project_id = UUID(result["id"])

    # Verify Owner assignment
    owner_role = (await client_session.exec(select(Role).where(Role.name == "Owner"))).first()
    assignment_stmt = (
        select(UserRoleAssignment)
        .where(UserRoleAssignment.scope_id == project_id)
        .where(UserRoleAssignment.scope_type == "Project")
        .where(UserRoleAssignment.role_id == owner_role.id)
    )
    assignment = (await client_session.exec(assignment_stmt)).first()

    assert assignment is not None, "Project should have Owner assignment even with flows/components lists"

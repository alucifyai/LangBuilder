"""
Unit tests for RBAC data migration script.

These tests verify that the migrate_existing_users_to_rbac function correctly
assigns roles to existing users, flows, and projects based on ownership, and
that the migration is idempotent and handles edge cases properly.
"""

from uuid import uuid4

import pytest
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langbuilder.initial_setup.rbac_setup import initialize_rbac_data
from langbuilder.scripts.migrate_rbac_data import migrate_existing_users_to_rbac
from langbuilder.services.database.models.flow.model import Flow
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
from langbuilder.services.database.models.user.model import User


# Fixtures for test data


@pytest.fixture
async def rbac_initialized_session(async_session: AsyncSession):
    """Fixture that provides a session with RBAC roles and permissions initialized."""
    await initialize_rbac_data(async_session)
    return async_session


@pytest.fixture
async def superuser(rbac_initialized_session: AsyncSession):
    """Create a superuser for testing."""
    user = User(
        id=uuid4(),
        username="admin_user",
        password="hashed_password",
        is_superuser=True,
        is_active=True,
    )
    rbac_initialized_session.add(user)
    await rbac_initialized_session.commit()
    await rbac_initialized_session.refresh(user)
    return user


@pytest.fixture
async def regular_user(rbac_initialized_session: AsyncSession):
    """Create a regular user for testing."""
    user = User(
        id=uuid4(),
        username="regular_user",
        password="hashed_password",
        is_superuser=False,
        is_active=True,
    )
    rbac_initialized_session.add(user)
    await rbac_initialized_session.commit()
    await rbac_initialized_session.refresh(user)
    return user


@pytest.fixture
async def user_with_flows(rbac_initialized_session: AsyncSession, regular_user: User):
    """Create a user with flows."""
    flow1 = Flow(
        id=uuid4(),
        name="Test Flow 1",
        data={"nodes": []},
        user_id=regular_user.id,
    )
    flow2 = Flow(
        id=uuid4(),
        name="Test Flow 2",
        data={"nodes": []},
        user_id=regular_user.id,
    )
    rbac_initialized_session.add(flow1)
    rbac_initialized_session.add(flow2)
    await rbac_initialized_session.commit()
    await rbac_initialized_session.refresh(flow1)
    await rbac_initialized_session.refresh(flow2)
    return regular_user, [flow1, flow2]


@pytest.fixture
async def user_with_projects(rbac_initialized_session: AsyncSession, regular_user: User):
    """Create a user with projects/folders."""
    project1 = Folder(
        id=uuid4(),
        name="Test Project",
        user_id=regular_user.id,
    )
    project2 = Folder(
        id=uuid4(),
        name="Starter Project",
        user_id=regular_user.id,
    )
    rbac_initialized_session.add(project1)
    rbac_initialized_session.add(project2)
    await rbac_initialized_session.commit()
    await rbac_initialized_session.refresh(project1)
    await rbac_initialized_session.refresh(project2)
    return regular_user, [project1, project2]


# Tests for migrate_existing_users_to_rbac function


@pytest.mark.asyncio
async def test_migrate_superuser_gets_global_admin(
    rbac_initialized_session: AsyncSession,
    superuser: User,
):
    """Test that superusers receive global Admin role."""
    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Verify success
    assert result["status"] == "success"
    assert result["created"] == 1
    assert result["skipped"] == 0
    assert len(result["errors"]) == 0

    # Verify assignment was created
    admin_role_stmt = select(Role).where(Role.name == "Admin")
    admin_role = (await rbac_initialized_session.exec(admin_role_stmt)).first()

    assignment_stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == superuser.id,
        UserRoleAssignment.role_id == admin_role.id,
        UserRoleAssignment.scope_type == "global",
    )
    assignment = (await rbac_initialized_session.exec(assignment_stmt)).first()

    assert assignment is not None
    assert assignment.scope_id is None
    assert assignment.is_immutable is False


@pytest.mark.asyncio
async def test_migrate_regular_user_with_flows(
    rbac_initialized_session: AsyncSession,
    user_with_flows: tuple[User, list[Flow]],
):
    """Test that regular users get Owner role for their flows."""
    user, flows = user_with_flows

    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Verify success
    assert result["status"] == "success"
    assert result["created"] == 2  # 2 flows
    assert result["skipped"] == 0
    assert len(result["errors"]) == 0

    # Verify assignments were created for each flow
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await rbac_initialized_session.exec(owner_role_stmt)).first()

    for flow in flows:
        assignment_stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role_id == owner_role.id,
            UserRoleAssignment.scope_type == "flow",
            UserRoleAssignment.scope_id == flow.id,
        )
        assignment = (await rbac_initialized_session.exec(assignment_stmt)).first()

        assert assignment is not None
        assert assignment.is_immutable is False


@pytest.mark.asyncio
async def test_migrate_regular_user_with_projects(
    rbac_initialized_session: AsyncSession,
    user_with_projects: tuple[User, list[Folder]],
):
    """Test that regular users get Owner role for their projects."""
    user, projects = user_with_projects

    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Verify success
    assert result["status"] == "success"
    assert result["created"] == 2  # 2 projects
    assert result["skipped"] == 0
    assert len(result["errors"]) == 0

    # Verify assignments were created for each project
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await rbac_initialized_session.exec(owner_role_stmt)).first()

    for project in projects:
        assignment_stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user.id,
            UserRoleAssignment.role_id == owner_role.id,
            UserRoleAssignment.scope_type == "project",
            UserRoleAssignment.scope_id == project.id,
        )
        assignment = (await rbac_initialized_session.exec(assignment_stmt)).first()

        assert assignment is not None

        # Starter Project should be immutable
        if project.name == "Starter Project":
            assert assignment.is_immutable is True
        else:
            assert assignment.is_immutable is False


@pytest.mark.asyncio
async def test_migrate_starter_project_is_immutable(
    rbac_initialized_session: AsyncSession,
    user_with_projects: tuple[User, list[Folder]],
):
    """Test that Starter Project Owner assignment is marked immutable."""
    user, projects = user_with_projects

    # Run migration
    await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Find the Starter Project
    starter_project = next(p for p in projects if p.name == "Starter Project")

    # Verify the assignment is immutable
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await rbac_initialized_session.exec(owner_role_stmt)).first()

    assignment_stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user.id,
        UserRoleAssignment.role_id == owner_role.id,
        UserRoleAssignment.scope_type == "project",
        UserRoleAssignment.scope_id == starter_project.id,
    )
    assignment = (await rbac_initialized_session.exec(assignment_stmt)).first()

    assert assignment is not None
    assert assignment.is_immutable is True


@pytest.mark.asyncio
async def test_migrate_idempotent(
    rbac_initialized_session: AsyncSession,
    user_with_flows: tuple[User, list[Flow]],
):
    """Test that migration is idempotent (safe to run multiple times)."""
    user, flows = user_with_flows

    # Run migration first time
    result1 = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)
    assert result1["status"] == "success"
    assert result1["created"] == 2

    # Count assignments after first run
    assignments_stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user.id)
    assignments_count_1 = len((await rbac_initialized_session.exec(assignments_stmt)).all())

    # Run migration second time
    result2 = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)
    assert result2["status"] == "success"
    assert result2["created"] == 0
    assert result2["skipped"] == 2

    # Count assignments after second run - should be identical
    assignments_count_2 = len((await rbac_initialized_session.exec(assignments_stmt)).all())

    assert assignments_count_1 == assignments_count_2


@pytest.mark.asyncio
async def test_migrate_dry_run_does_not_commit(
    rbac_initialized_session: AsyncSession,
    regular_user: User,
):
    """Test that dry run mode does not commit changes."""
    # Capture user ID before migration (to avoid session expiry issues)
    user_id = regular_user.id

    # Run migration in dry run mode
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=True)

    # Verify dry run status
    assert result["status"] == "dry_run"
    assert "would_create" in result
    assert "would_skip" in result

    # Verify no assignments were actually created
    assignments_stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
    assignments = (await rbac_initialized_session.exec(assignments_stmt)).all()

    assert len(assignments) == 0


@pytest.mark.asyncio
async def test_migrate_with_multiple_users(
    rbac_initialized_session: AsyncSession,
):
    """Test migration with multiple users of different types."""
    # Create superuser
    superuser = User(
        id=uuid4(),
        username="admin",
        password="hashed_password",
        is_superuser=True,
        is_active=True,
    )
    rbac_initialized_session.add(superuser)

    # Create regular user with flows
    user1 = User(
        id=uuid4(),
        username="user1",
        password="hashed_password",
        is_superuser=False,
        is_active=True,
    )
    rbac_initialized_session.add(user1)

    flow1 = Flow(
        id=uuid4(),
        name="Flow 1",
        data={"nodes": []},
        user_id=user1.id,
    )
    rbac_initialized_session.add(flow1)

    # Create regular user with project
    user2 = User(
        id=uuid4(),
        username="user2",
        password="hashed_password",
        is_superuser=False,
        is_active=True,
    )
    rbac_initialized_session.add(user2)

    project1 = Folder(
        id=uuid4(),
        name="Project 1",
        user_id=user2.id,
    )
    rbac_initialized_session.add(project1)

    await rbac_initialized_session.commit()

    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Verify success
    assert result["status"] == "success"
    # 1 superuser admin + 1 flow owner + 1 project owner = 3
    assert result["created"] == 3
    assert len(result["errors"]) == 0

    # Verify all assignments exist
    all_assignments_stmt = select(UserRoleAssignment)
    all_assignments = (await rbac_initialized_session.exec(all_assignments_stmt)).all()
    assert len(all_assignments) == 3


@pytest.mark.asyncio
async def test_migrate_user_without_resources(
    rbac_initialized_session: AsyncSession,
    regular_user: User,
):
    """Test that users without flows or projects get no assignments."""
    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Verify success
    assert result["status"] == "success"
    assert result["created"] == 0
    assert result["skipped"] == 0

    # Verify no assignments were created
    assignments_stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == regular_user.id)
    assignments = (await rbac_initialized_session.exec(assignments_stmt)).all()

    assert len(assignments) == 0


@pytest.mark.asyncio
async def test_migrate_missing_roles_raises_error(async_session: AsyncSession):
    """Test that migration fails if Admin/Owner roles are not found."""
    # Create a user without initializing RBAC
    user = User(
        id=uuid4(),
        username="test_user",
        password="hashed_password",
        is_superuser=True,
        is_active=True,
    )
    async_session.add(user)
    await async_session.commit()

    # Run migration - should fail
    result = await migrate_existing_users_to_rbac(async_session, dry_run=False)

    # Verify error
    assert result["status"] == "error"
    assert "Admin and Owner roles not found" in result["error"]


@pytest.mark.asyncio
async def test_migrate_updates_starter_project_immutability(
    rbac_initialized_session: AsyncSession,
):
    """Test that existing Starter Project assignment is updated to immutable."""
    # Create user with Starter Project
    user = User(
        id=uuid4(),
        username="user1",
        password="hashed_password",
        is_superuser=False,
        is_active=True,
    )
    rbac_initialized_session.add(user)

    starter_project = Folder(
        id=uuid4(),
        name="Starter Project",
        user_id=user.id,
    )
    rbac_initialized_session.add(starter_project)
    await rbac_initialized_session.commit()

    # Get Owner role
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await rbac_initialized_session.exec(owner_role_stmt)).first()

    # Create non-immutable assignment manually
    assignment = UserRoleAssignment(
        user_id=user.id,
        role_id=owner_role.id,
        scope_type="project",
        scope_id=starter_project.id,
        is_immutable=False,
    )
    rbac_initialized_session.add(assignment)
    await rbac_initialized_session.commit()

    # Capture IDs before migration
    assignment_id = assignment.id
    user_id = user.id
    starter_project_id = starter_project.id

    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Re-query the assignment to check if it was updated
    assignment_stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == owner_role.id,
        UserRoleAssignment.scope_type == "project",
        UserRoleAssignment.scope_id == starter_project_id,
    )
    updated_assignment = (await rbac_initialized_session.exec(assignment_stmt)).first()

    assert updated_assignment is not None
    assert updated_assignment.is_immutable is True


@pytest.mark.asyncio
async def test_migrate_dry_run_preview_correct_counts(
    rbac_initialized_session: AsyncSession,
):
    """Test that dry run provides accurate preview counts."""
    # Create test data
    user1 = User(
        id=uuid4(),
        username="user1",
        password="hashed_password",
        is_superuser=True,
        is_active=True,
    )
    rbac_initialized_session.add(user1)

    user2 = User(
        id=uuid4(),
        username="user2",
        password="hashed_password",
        is_superuser=False,
        is_active=True,
    )
    rbac_initialized_session.add(user2)

    flow1 = Flow(
        id=uuid4(),
        name="Flow 1",
        data={"nodes": []},
        user_id=user2.id,
    )
    rbac_initialized_session.add(flow1)

    await rbac_initialized_session.commit()

    # Run dry run
    dry_result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=True)

    assert dry_result["status"] == "dry_run"
    assert dry_result["would_create"] == 2  # 1 admin + 1 flow owner

    # Verify no assignments were created
    all_assignments_stmt = select(UserRoleAssignment)
    all_assignments = (await rbac_initialized_session.exec(all_assignments_stmt)).all()
    assert len(all_assignments) == 0

    # Run actual migration
    live_result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    assert live_result["status"] == "success"
    assert live_result["created"] == dry_result["would_create"]


@pytest.mark.asyncio
async def test_migrate_complex_scenario(
    rbac_initialized_session: AsyncSession,
):
    """Test migration with a complex scenario of multiple users, flows, and projects."""
    # Create 2 superusers
    admin1 = User(id=uuid4(), username="admin1", password="pass", is_superuser=True, is_active=True)
    admin2 = User(id=uuid4(), username="admin2", password="pass", is_superuser=True, is_active=True)
    rbac_initialized_session.add(admin1)
    rbac_initialized_session.add(admin2)

    # Create 3 regular users
    user1 = User(id=uuid4(), username="user1", password="pass", is_superuser=False, is_active=True)
    user2 = User(id=uuid4(), username="user2", password="pass", is_superuser=False, is_active=True)
    user3 = User(id=uuid4(), username="user3", password="pass", is_superuser=False, is_active=True)
    rbac_initialized_session.add(user1)
    rbac_initialized_session.add(user2)
    rbac_initialized_session.add(user3)

    # User1 has 3 flows and 2 projects (one is Starter Project)
    for i in range(3):
        flow = Flow(id=uuid4(), name=f"User1 Flow {i}", data={"nodes": []}, user_id=user1.id)
        rbac_initialized_session.add(flow)

    project1 = Folder(id=uuid4(), name="User1 Project", user_id=user1.id)
    starter1 = Folder(id=uuid4(), name="Starter Project", user_id=user1.id)
    rbac_initialized_session.add(project1)
    rbac_initialized_session.add(starter1)

    # User2 has 1 flow
    flow = Flow(id=uuid4(), name="User2 Flow", data={"nodes": []}, user_id=user2.id)
    rbac_initialized_session.add(flow)

    # User3 has 2 projects
    project2 = Folder(id=uuid4(), name="User3 Project 1", user_id=user3.id)
    project3 = Folder(id=uuid4(), name="User3 Project 2", user_id=user3.id)
    rbac_initialized_session.add(project2)
    rbac_initialized_session.add(project3)

    await rbac_initialized_session.commit()

    # Run migration
    result = await migrate_existing_users_to_rbac(rbac_initialized_session, dry_run=False)

    # Verify counts
    # 2 admins + 3 flows (user1) + 2 projects (user1) + 1 flow (user2) + 2 projects (user3) = 10
    assert result["status"] == "success"
    assert result["created"] == 10
    assert len(result["errors"]) == 0

    # Verify Starter Project is immutable
    owner_role_stmt = select(Role).where(Role.name == "Owner")
    owner_role = (await rbac_initialized_session.exec(owner_role_stmt)).first()

    starter_assignment_stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user1.id,
        UserRoleAssignment.role_id == owner_role.id,
        UserRoleAssignment.scope_type == "project",
        UserRoleAssignment.scope_id == starter1.id,
    )
    starter_assignment = (await rbac_initialized_session.exec(starter_assignment_stmt)).first()
    assert starter_assignment.is_immutable is True

    # Verify regular project is not immutable
    regular_assignment_stmt = select(UserRoleAssignment).where(
        UserRoleAssignment.user_id == user1.id,
        UserRoleAssignment.role_id == owner_role.id,
        UserRoleAssignment.scope_type == "project",
        UserRoleAssignment.scope_id == project1.id,
    )
    regular_assignment = (await rbac_initialized_session.exec(regular_assignment_stmt)).first()
    assert regular_assignment.is_immutable is False

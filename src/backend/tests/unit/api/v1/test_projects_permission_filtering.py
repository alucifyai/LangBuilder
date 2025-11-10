"""
Unit tests for Task 3.1: Project List Permission Filtering.

Tests cover:
- read_projects endpoint filters by Read permission
- Users only see projects they have Read permission for
- Admin users bypass permission checks (see all projects)
- Error handling when permission check fails
- Projects are sorted correctly after filtering
- Starter folder is excluded from results
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from langbuilder.api.v1.projects import read_projects
from langbuilder.services.database.models.folder.model import Folder
from langbuilder.services.database.models.user.model import User


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user."""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "adminuser"
    user.is_active = True
    user.is_superuser = True
    return user


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def mock_rbac_service():
    """Create a mock RBACService."""
    service = AsyncMock()
    return service


@pytest.fixture
def sample_projects():
    """Create sample projects for testing."""
    projects = []

    # Create default project
    default_project = Mock(spec=Folder)
    default_project.id = uuid4()
    default_project.name = "My Collection"
    default_project.description = "Default project"
    default_project.user_id = uuid4()
    projects.append(default_project)

    # Create starter project (should be excluded)
    starter_project = Mock(spec=Folder)
    starter_project.id = uuid4()
    starter_project.name = "Starter Projects"
    starter_project.description = "Starter examples"
    starter_project.user_id = None
    projects.append(starter_project)

    # Create regular projects
    for i in range(3):
        project = Mock(spec=Folder)
        project.id = uuid4()
        project.name = f"Project {i}"
        project.description = f"Description {i}"
        project.user_id = uuid4()
        projects.append(project)

    return projects


# ============================================================================
# Test read_projects Permission Filtering
# ============================================================================


@pytest.mark.asyncio
async def test_read_projects_filters_by_permission(mock_user, mock_session, mock_rbac_service, sample_projects):
    """Test that read_projects filters projects by Read permission."""
    # Setup mock session to return projects (excluding starter)
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=sample_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to allow access to projects at indices 0, 2, 4
    # (indices 0=default, 1=starter, 2=Project 0, 3=Project 1, 4=Project 2)
    async def mock_can_access(user_id, permission_name, scope_type, scope_id):
        project_index = next((i for i, p in enumerate(sample_projects) if p.id == scope_id), -1)
        # Allow indices 0, 2, 4 (deny 1, 3)
        return project_index in [0, 2, 4]

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Should exclude starter project (index 1) and project at index 3
    # Should return projects at indices 0 (default), 2 (Project 0), 4 (Project 2)
    assert len(result) == 3

    # Verify can_access was called for each non-starter project
    # (1 call for index 0, skip 1 (starter), 1 call each for 2, 3, 4)
    assert mock_rbac_service.can_access.call_count == 4


@pytest.mark.asyncio
async def test_read_projects_denies_all_when_no_permissions(
    mock_user, mock_session, mock_rbac_service, sample_projects
):
    """Test that read_projects returns empty list when user has no Read permissions."""
    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=sample_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to deny all access
    mock_rbac_service.can_access = AsyncMock(return_value=False)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Should return empty list
    assert len(result) == 0

    # Should have checked permissions for all non-starter projects (4 projects)
    assert mock_rbac_service.can_access.call_count == 4


@pytest.mark.asyncio
async def test_read_projects_allows_all_for_admin(
    mock_admin_user, mock_session, mock_rbac_service, sample_projects
):
    """Test that admin users can see all projects (bypass permission check via service)."""
    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=sample_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to always allow access (admin bypass)
    mock_rbac_service.can_access = AsyncMock(return_value=True)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_admin_user,
        rbac_service=mock_rbac_service,
    )

    # Should return all projects except starter (4 projects)
    assert len(result) == 4

    # Should have checked permissions for all non-starter projects
    assert mock_rbac_service.can_access.call_count == 4


@pytest.mark.asyncio
async def test_read_projects_excludes_starter_folder(mock_user, mock_session, mock_rbac_service, sample_projects):
    """Test that read_projects always excludes Starter Projects folder."""
    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=sample_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to allow all
    mock_rbac_service.can_access = AsyncMock(return_value=True)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Should not include "Starter Projects"
    assert all(p.name != "Starter Projects" for p in result)

    # Should return 4 projects (exclude starter project at index 1)
    assert len(result) == 4


@pytest.mark.asyncio
async def test_read_projects_handles_permission_check_error(
    mock_user, mock_session, mock_rbac_service, sample_projects
):
    """Test that read_projects gracefully handles errors during permission check."""
    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=sample_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to throw error for some projects
    async def mock_can_access_with_error(user_id, permission_name, scope_type, scope_id):
        project_index = next((i for i, p in enumerate(sample_projects) if p.id == scope_id), -1)
        if project_index == 2:  # Throw error for project at index 2
            raise Exception("Permission check failed")
        # Allow even indices
        return project_index % 2 == 0

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access_with_error)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Should skip project 2 (error) and project 3 (denied)
    # Should return projects at indices 0 (default) and 4 (Project 2)
    assert len(result) == 2

    # Verify can_access was called for non-starter projects
    assert mock_rbac_service.can_access.call_count == 4


@pytest.mark.asyncio
async def test_read_projects_sorts_default_first(mock_user, mock_session, mock_rbac_service, sample_projects):
    """Test that read_projects sorts results with default project first."""
    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=sample_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to allow all
    mock_rbac_service.can_access = AsyncMock(return_value=True)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # First project should be "My Collection" (default)
    assert len(result) > 0
    assert result[0].name == "My Collection"


@pytest.mark.asyncio
async def test_read_projects_with_mixed_ownership(mock_user, mock_session, mock_rbac_service):
    """Test that read_projects handles projects with different ownership correctly."""
    # Create projects with different ownership
    user_project = Mock(spec=Folder)
    user_project.id = uuid4()
    user_project.name = "User Project"
    user_project.user_id = mock_user.id

    shared_project = Mock(spec=Folder)
    shared_project.id = uuid4()
    shared_project.name = "Shared Project"
    shared_project.user_id = None  # Shared/public project

    other_user_project = Mock(spec=Folder)
    other_user_project.id = uuid4()
    other_user_project.name = "Other User Project"
    other_user_project.user_id = uuid4()  # Different user

    projects = [user_project, shared_project, other_user_project]

    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service to allow user's own project and shared project, deny other user's project
    async def mock_can_access(user_id, permission_name, scope_type, scope_id):
        if scope_id == user_project.id or scope_id == shared_project.id:
            return True
        return False

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Should return user's project and shared project (2 projects)
    assert len(result) == 2
    assert user_project in result
    assert shared_project in result
    assert other_user_project not in result


@pytest.mark.asyncio
async def test_read_projects_calls_rbac_service_correctly(
    mock_user, mock_session, mock_rbac_service, sample_projects
):
    """Test that read_projects calls RBACService with correct parameters."""
    # Setup mock session
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    # Only return non-starter projects for this test
    non_starter_projects = [p for p in sample_projects if p.name != "Starter Projects"]
    projects_result.all = Mock(return_value=non_starter_projects)
    mock_session.exec.return_value = projects_result

    # Mock RBAC service
    mock_rbac_service.can_access = AsyncMock(return_value=True)

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify can_access was called with correct parameters for each project
    for project in non_starter_projects:
        mock_rbac_service.can_access.assert_any_call(
            user_id=mock_user.id,
            permission_name="Read",
            scope_type="Project",
            scope_id=project.id,
        )

    # Should have been called once per project
    assert mock_rbac_service.can_access.call_count == len(non_starter_projects)


@pytest.mark.asyncio
async def test_read_projects_empty_database(mock_user, mock_session, mock_rbac_service):
    """Test that read_projects handles empty database correctly."""
    # Setup mock session to return no projects
    mock_session.exec = AsyncMock()
    projects_result = AsyncMock()
    projects_result.all = Mock(return_value=[])
    mock_session.exec.return_value = projects_result

    # Call read_projects
    result = await read_projects(
        session=mock_session,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Should return empty list
    assert len(result) == 0

    # Should not call can_access
    assert mock_rbac_service.can_access.call_count == 0


@pytest.mark.asyncio
async def test_read_projects_raises_http_exception_on_error(mock_user, mock_session, mock_rbac_service):
    """Test that read_projects raises HTTPException on database error."""
    # Setup mock session to throw error
    mock_session.exec = AsyncMock(side_effect=Exception("Database connection failed"))

    # Call read_projects and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await read_projects(
            session=mock_session,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    # Should raise 500 error
    assert exc_info.value.status_code == 500
    assert "Database connection failed" in str(exc_info.value.detail)

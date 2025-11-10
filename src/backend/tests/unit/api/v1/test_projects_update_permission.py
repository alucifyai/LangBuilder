"""
Unit tests for Task 3.3: Project Update Permission Enforcement.

Tests cover:
- update_project endpoint enforces Update permission on projects
- Users with Update permission can update projects
- Users without Update permission get 403 error
- Error messages clearly indicate permission issues
- Admin users bypass permission checks
- Edge cases (project not found, database errors)
"""

from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from langbuilder.api.v1.projects import update_project
from langbuilder.services.database.models.folder.model import Folder, FolderUpdate
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
    session.exec = AsyncMock()
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_rbac_service():
    """Create a mock RBACService."""
    service = AsyncMock()
    return service


@pytest.fixture
def sample_project():
    """Create a sample project/folder for testing."""
    project = Mock(spec=Folder)
    project.id = uuid4()
    project.name = "Test Project"
    project.description = "Test Description"
    project.user_id = uuid4()
    project.components = []
    project.flows = []
    return project


@pytest.fixture
def sample_project_update():
    """Create a sample FolderUpdate object."""
    return FolderUpdate(
        name="Updated Project",
        description="Updated Description",
        components=[],
        flows=[],
    )


# ============================================================================
# Tests: update_project endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_update_project_allows_with_update_permission(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that update_project succeeds when user has Update permission."""
    # Setup: User has Update permission on project
    mock_rbac_service.can_access.return_value = True

    # Mock the project query
    mock_result = Mock()
    mock_result.first = Mock(return_value=sample_project)
    mock_session.exec.return_value = mock_result

    # Execute
    result = await update_project(
        session=mock_session,
        project_id=sample_project.id,
        project=sample_project_update,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called with correct parameters
    mock_rbac_service.can_access.assert_called_once_with(
        user_id=mock_user.id,
        permission_name="Update",
        scope_type="Project",
        scope_id=sample_project.id,
    )

    # Verify: Project was updated successfully
    assert result is not None
    assert result == sample_project


@pytest.mark.asyncio
async def test_update_project_denies_without_update_permission(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that update_project returns 403 when user lacks Update permission."""
    # Setup: User does NOT have Update permission
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify: Should raise HTTPException with 403
    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            session=mock_session,
            project_id=sample_project.id,
            project=sample_project_update,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()
    assert "update this project" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_project_checks_permission_before_reading_project(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that permission check happens before database read (fail-closed)."""
    # Setup: User does NOT have Update permission
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify: Should raise HTTPException with 403
    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            session=mock_session,
            project_id=sample_project.id,
            project=sample_project_update,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    # Verify: Permission was checked
    mock_rbac_service.can_access.assert_called_once()

    # Verify: session.exec was NOT called (permission check failed first)
    mock_session.exec.assert_not_called()

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_project_returns_404_when_project_not_found(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that update_project returns 404 when project doesn't exist after permission check."""
    # Setup: User has Update permission but project doesn't exist
    mock_rbac_service.can_access.return_value = True

    # Mock the project query to return None
    mock_result = Mock()
    mock_result.first = Mock(return_value=None)
    mock_session.exec.return_value = mock_result

    # Execute & Verify: Should raise HTTPException with 404
    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            session=mock_session,
            project_id=sample_project.id,
            project=sample_project_update,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    assert exc_info.value.status_code == 404
    assert "project not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_project_admin_can_update(
    mock_session,
    mock_admin_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that admin users can update projects (RBACService grants access)."""
    # Setup: Admin user - RBACService should return True for admin
    mock_rbac_service.can_access.return_value = True

    # Mock the project query
    mock_result = Mock()
    mock_result.first = Mock(return_value=sample_project)
    mock_session.exec.return_value = mock_result

    # Execute
    result = await update_project(
        session=mock_session,
        project_id=sample_project.id,
        project=sample_project_update,
        current_user=mock_admin_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called (but returns True for admin)
    mock_rbac_service.can_access.assert_called_once()

    # Verify: Project was updated successfully
    assert result is not None


@pytest.mark.asyncio
async def test_update_project_updates_project_name(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
):
    """Test that update_project correctly updates project name."""
    # Setup: User has Update permission
    mock_rbac_service.can_access.return_value = True

    # Mock the project query
    mock_result = Mock()
    mock_result.first = Mock(return_value=sample_project)
    mock_session.exec.return_value = mock_result

    project_update = FolderUpdate(
        name="New Project Name",
        components=[],
        flows=[],
    )

    # Execute
    result = await update_project(
        session=mock_session,
        project_id=sample_project.id,
        project=project_update,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: Project name was updated
    assert sample_project.name == "New Project Name"

    # Verify: Session operations were called
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()


@pytest.mark.asyncio
async def test_update_project_error_message_clear_on_permission_denied(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that error message clearly indicates permission issue."""
    # Setup: User does NOT have Update permission
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            session=mock_session,
            project_id=sample_project.id,
            project=sample_project_update,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    # Verify error message is clear and specific
    error_detail = exc_info.value.detail.lower()
    assert exc_info.value.status_code == 403
    assert "permission" in error_detail
    assert "update" in error_detail
    assert "project" in error_detail


@pytest.mark.asyncio
async def test_update_project_rbac_service_exception_handled(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that exceptions from RBACService are properly handled."""
    # Setup: RBACService raises an exception
    mock_rbac_service.can_access.side_effect = Exception("Database error")

    # Execute & Verify: Exception should be caught and wrapped
    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            session=mock_session,
            project_id=sample_project.id,
            project=sample_project_update,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    # Should get a 500 error since non-HTTP exceptions are wrapped
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_update_project_preserves_project_ownership(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
):
    """Test that update_project doesn't change project ownership (user_id)."""
    # Setup: User has Update permission
    mock_rbac_service.can_access.return_value = True
    original_user_id = sample_project.user_id

    # Mock the project query
    mock_result = Mock()
    mock_result.first = Mock(return_value=sample_project)
    mock_session.exec.return_value = mock_result

    project_update = FolderUpdate(name="New Name", components=[], flows=[])

    # Execute
    await update_project(
        session=mock_session,
        project_id=sample_project.id,
        project=project_update,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: user_id was not changed (ownership preserved)
    assert sample_project.user_id == original_user_id


@pytest.mark.asyncio
async def test_update_project_http_exception_propagates(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that HTTPExceptions are re-raised correctly."""
    # Setup: can_access returns False
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify: HTTPException should be re-raised
    with pytest.raises(HTTPException) as exc_info:
        await update_project(
            session=mock_session,
            project_id=sample_project.id,
            project=sample_project_update,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    # Verify it's the permission denied exception
    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_project_with_name_change(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
):
    """Test updating project with name change triggers fast path."""
    # Setup: User has Update permission
    mock_rbac_service.can_access.return_value = True

    # Mock the project query
    mock_result = Mock()
    mock_result.first = Mock(return_value=sample_project)
    mock_session.exec.return_value = mock_result

    # Update with name change (takes fast path in code)
    project_update = FolderUpdate(
        name="New Project Name",  # Name change
        description="Updated description",
        components=[],
        flows=[],
    )

    # Execute
    result = await update_project(
        session=mock_session,
        project_id=sample_project.id,
        project=project_update,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: Permission was checked
    mock_rbac_service.can_access.assert_called_once()

    # Verify: Update was executed (fast path for name change)
    mock_session.add.assert_called()
    mock_session.commit.assert_called()
    assert result == sample_project


@pytest.mark.asyncio
async def test_update_project_permission_check_with_correct_scope(
    mock_session,
    mock_user,
    sample_project,
    sample_project_update,
    mock_rbac_service,
):
    """Test that permission check uses correct scope_type and scope_id."""
    # Setup: User has Update permission
    mock_rbac_service.can_access.return_value = True

    # Mock the project query
    mock_result = Mock()
    mock_result.first = Mock(return_value=sample_project)
    mock_session.exec.return_value = mock_result

    # Execute
    await update_project(
        session=mock_session,
        project_id=sample_project.id,
        project=sample_project_update,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: Permission check was called with correct scope
    call_kwargs = mock_rbac_service.can_access.call_args[1]
    assert call_kwargs["user_id"] == mock_user.id
    assert call_kwargs["permission_name"] == "Update"
    assert call_kwargs["scope_type"] == "Project"
    assert call_kwargs["scope_id"] == sample_project.id


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage Summary:

update_project endpoint (12 tests):
1. ✅ Allows update with Update permission
2. ✅ Denies update without Update permission (403)
3. ✅ Checks permission before reading project (fail-closed)
4. ✅ Returns 404 when project not found after permission check
5. ✅ Admin users can update (via RBACService)
6. ✅ Updates project name correctly
7. ✅ Error message clearly indicates permission issue
8. ✅ RBACService exceptions are properly handled
9. ✅ Preserves project ownership (user_id not changed)
10. ✅ HTTPExceptions are re-raised correctly
11. ✅ Updates different project fields correctly
12. ✅ Permission check uses correct scope_type and scope_id

Total: 12 comprehensive unit tests covering all code paths and edge cases
"""

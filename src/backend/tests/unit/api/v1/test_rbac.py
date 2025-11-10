"""
Unit tests for RBAC API endpoints.

Tests cover:
- Admin access enforcement
- List roles endpoint
- List assignments with filters
- Create assignment (success and validation errors)
- Update assignment (success, immutable rejection, not found)
- Delete assignment (success, immutable rejection, not found)
- Check single permission (allowed and denied)
- Batch permission check (multiple resources)
- Error responses (400, 403, 404, 500)
- Pydantic schema validation
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from langbuilder.api.v1.rbac import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    BatchResource,
    PermissionCheckBatchRequest,
    PermissionCheckBatchResponse,
    PermissionCheckRequest,
    PermissionCheckResponse,
    RoleResponse,
    check_permission,
    check_permissions_batch,
    create_assignment,
    delete_assignment,
    get_rbac_service,
    list_assignments,
    list_roles,
    require_admin,
    update_assignment,
)
from langbuilder.services.database.models.rbac import Role, UserRoleAssignment
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
def sample_role():
    """Create a sample role."""
    return Role(
        id=uuid4(),
        name="Admin",
        description="Administrator role",
        is_system=True,
    )


@pytest.fixture
def sample_assignment():
    """Create a sample assignment."""
    return UserRoleAssignment(
        id=uuid4(),
        user_id=uuid4(),
        role_id=uuid4(),
        scope_type="Global",
        scope_id=None,
        is_immutable=False,
        created_at=datetime.now(timezone.utc),
        created_by=uuid4(),
    )


@pytest.fixture
def immutable_assignment():
    """Create an immutable assignment."""
    return UserRoleAssignment(
        id=uuid4(),
        user_id=uuid4(),
        role_id=uuid4(),
        scope_type="Project",
        scope_id=uuid4(),
        is_immutable=True,
        created_at=datetime.now(timezone.utc),
        created_by=uuid4(),
    )


# ============================================================================
# Test Dependencies
# ============================================================================


@pytest.mark.asyncio
async def test_require_admin_allows_admin(mock_admin_user, mock_session):
    """Test that require_admin allows admin users."""
    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        # Mock get_user_assignments to return a Global scope assignment
        global_assignment = Mock()
        global_assignment.scope_type = "Global"
        mock_service.get_user_assignments = AsyncMock(return_value=[global_assignment])
        mock_get_service.return_value = mock_service

        result = await require_admin(mock_admin_user, mock_session)

        assert result == mock_admin_user
        mock_service.get_user_assignments.assert_called_once_with(mock_admin_user.id)


@pytest.mark.asyncio
async def test_require_admin_rejects_non_admin(mock_user, mock_session):
    """Test that require_admin rejects non-admin users."""
    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        # Mock get_user_assignments to return no Global scope assignments
        non_global_assignment = Mock()
        non_global_assignment.scope_type = "Flow"  # Not Global
        mock_service.get_user_assignments = AsyncMock(return_value=[non_global_assignment])
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await require_admin(mock_user, mock_session)

        assert exc_info.value.status_code == 403
        assert "Admin access required" in exc_info.value.detail


def test_get_rbac_service_success():
    """Test that get_rbac_service returns service successfully."""
    with patch("langbuilder.api.v1.rbac.get_service") as mock_get_service:
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        result = get_rbac_service()

        assert result == mock_service


def test_get_rbac_service_failure():
    """Test that get_rbac_service raises HTTPException on failure."""
    with patch("langbuilder.api.v1.rbac.get_service") as mock_get_service:
        mock_get_service.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_rbac_service()

        assert exc_info.value.status_code == 500
        assert "RBAC service not available" in exc_info.value.detail


# ============================================================================
# Test List Roles Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_list_roles_success(mock_admin_user, sample_role):
    """Test list_roles endpoint returns roles successfully."""
    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.list_roles = AsyncMock(return_value=[sample_role])
        mock_get_service.return_value = mock_service

        result = await list_roles(mock_admin_user)

        assert len(result) == 1
        assert result[0] == sample_role
        mock_service.list_roles.assert_called_once()


@pytest.mark.asyncio
async def test_list_roles_error():
    """Test list_roles endpoint handles errors."""
    mock_admin_user = Mock()

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.list_roles = AsyncMock(side_effect=Exception("Database error"))
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await list_roles(mock_admin_user)

        assert exc_info.value.status_code == 500
        assert "Failed to list roles" in exc_info.value.detail


# ============================================================================
# Test List Assignments Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_list_assignments_no_filters(mock_admin_user, sample_assignment):
    """Test list_assignments without filters."""
    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.get_assignments = AsyncMock(return_value=[sample_assignment])
        mock_get_service.return_value = mock_service

        result = await list_assignments(mock_admin_user)

        assert len(result) == 1
        assert result[0] == sample_assignment
        mock_service.get_assignments.assert_called_once_with(
            user_id=None, role_id=None, scope_type=None
        )


@pytest.mark.asyncio
async def test_list_assignments_with_filters(mock_admin_user, sample_assignment):
    """Test list_assignments with filters."""
    user_id = uuid4()
    role_id = uuid4()
    scope_type = "project"

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.get_assignments = AsyncMock(return_value=[sample_assignment])
        mock_get_service.return_value = mock_service

        result = await list_assignments(
            mock_admin_user,
            user_id=user_id,
            role_id=role_id,
            scope_type=scope_type,
        )

        assert len(result) == 1
        mock_service.get_assignments.assert_called_once_with(
            user_id=user_id, role_id=role_id, scope_type=scope_type
        )


@pytest.mark.asyncio
async def test_list_assignments_filters_immutable_assignments(mock_admin_user, sample_assignment, immutable_assignment):
    """Test that list_assignments filters out immutable assignments (Starter Project ownership).

    This test verifies that when the RBAC service returns a mix of mutable and immutable
    assignments, the list_assignments endpoint filters out the immutable ones so they
    don't appear in the Role Assignment management UI.
    """
    from langbuilder.services.database.models.user.model import User

    # Create mock user and role objects for the enrichment
    mock_user = Mock(spec=User)
    mock_user.id = sample_assignment.user_id
    mock_user.username = "testuser"

    mock_role = Mock(spec=Role)
    mock_role.id = sample_assignment.role_id
    mock_role.name = "Owner"

    # Create mock session with proper async mocking for execute()
    mock_session = AsyncMock()

    # Mock the execute() calls for users, roles, folders, and flows
    # Each execute() should return an object with scalars().all()
    mock_users_result = Mock()
    mock_users_scalars = Mock()
    mock_users_scalars.all.return_value = [mock_user]
    mock_users_result.scalars.return_value = mock_users_scalars

    mock_roles_result = Mock()
    mock_roles_scalars = Mock()
    mock_roles_scalars.all.return_value = [mock_role]
    mock_roles_result.scalars.return_value = mock_roles_scalars

    mock_folders_result = Mock()
    mock_folders_scalars = Mock()
    mock_folders_scalars.all.return_value = []
    mock_folders_result.scalars.return_value = mock_folders_scalars

    mock_flows_result = Mock()
    mock_flows_scalars = Mock()
    mock_flows_scalars.all.return_value = []
    mock_flows_result.scalars.return_value = mock_flows_scalars

    # Setup session.execute to return different results based on the query
    mock_session.execute = AsyncMock(side_effect=[
        mock_users_result,
        mock_roles_result,
        mock_folders_result,
        mock_flows_result,
    ])

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        # Mock get_assignments to return both mutable and immutable assignments
        mock_service.get_assignments = AsyncMock(
            return_value=[sample_assignment, immutable_assignment]
        )
        mock_get_service.return_value = mock_service

        result = await list_assignments(mock_admin_user, mock_session)

        # Should only return the mutable assignment, immutable should be filtered out
        assert len(result) == 1, "Should filter out immutable assignments"
        assert result[0].user_id == str(sample_assignment.user_id), "Should only include mutable assignments"
        assert result[0].is_immutable is False, "Returned assignment should be mutable"


@pytest.mark.asyncio
async def test_list_assignments_error():
    """Test list_assignments handles errors."""
    mock_admin_user = Mock()

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.get_assignments = AsyncMock(
            side_effect=Exception("Database error")
        )
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await list_assignments(mock_admin_user)

        assert exc_info.value.status_code == 500
        assert "Failed to list assignments" in exc_info.value.detail


# ============================================================================
# Test Create Assignment Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_create_assignment_success(
    mock_admin_user, mock_session, sample_assignment
):
    """Test create_assignment endpoint successfully creates assignment."""
    user_id = uuid4()
    role_id = uuid4()

    assignment_data = AssignmentCreate(
        user_id=user_id,
        role_id=role_id,
        scope_type="Global",
        scope_id=None,
        is_immutable=False,
    )

    # Mock session.get for user and role
    async def mock_get(model, id):
        if model == User:
            user = Mock()
            user.id = id
            return user
        elif model == Role:
            role = Mock()
            role.id = id
            return role
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.create_assignment = AsyncMock(return_value=sample_assignment)
        mock_get_service.return_value = mock_service

        result = await create_assignment(assignment_data, mock_admin_user, mock_session)

        assert result == sample_assignment
        mock_service.create_assignment.assert_called_once_with(
            user_id=user_id,
            role_id=role_id,
            scope_type="Global",
            scope_id=None,
            is_immutable=False,
            created_by=mock_admin_user.id,
        )


@pytest.mark.asyncio
async def test_create_assignment_user_not_found(mock_admin_user, mock_session):
    """Test create_assignment fails when user not found."""
    assignment_data = AssignmentCreate(
        user_id=uuid4(),
        role_id=uuid4(),
        scope_type="Global",
        scope_id=None,
    )

    # Mock session.get to return None for User
    async def mock_get(model, id):
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await create_assignment(assignment_data, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "User" in exc_info.value.detail
        assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_assignment_role_not_found(mock_admin_user, mock_session):
    """Test create_assignment fails when role not found."""
    assignment_data = AssignmentCreate(
        user_id=uuid4(),
        role_id=uuid4(),
        scope_type="Global",
        scope_id=None,
    )

    # Mock session.get to return user but not role
    async def mock_get(model, id):
        if model == User:
            user = Mock()
            user.id = id
            return user
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await create_assignment(assignment_data, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "Role" in exc_info.value.detail
        assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_assignment_duplicate(mock_admin_user, mock_session):
    """Test create_assignment fails when assignment already exists."""
    user_id = uuid4()
    role_id = uuid4()

    assignment_data = AssignmentCreate(
        user_id=user_id,
        role_id=role_id,
        scope_type="Global",
        scope_id=None,
    )

    # Mock session.get for user and role
    async def mock_get(model, id):
        if model == User:
            user = Mock()
            user.id = id
            return user
        elif model == Role:
            role = Mock()
            role.id = id
            return role
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.create_assignment = AsyncMock(
            side_effect=ValueError("Assignment already exists")
        )
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await create_assignment(assignment_data, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "already exists" in exc_info.value.detail


# ============================================================================
# Test Update Assignment Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_update_assignment_success(
    mock_admin_user, mock_session, sample_assignment
):
    """Test update_assignment endpoint successfully updates assignment."""
    assignment_id = sample_assignment.id
    new_role_id = uuid4()

    update_data = AssignmentUpdate(role_id=new_role_id)

    # Mock session.get for assignment and role
    async def mock_get(model, id):
        if model == UserRoleAssignment:
            return sample_assignment
        elif model == Role:
            role = Mock()
            role.id = id
            return role
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        updated_assignment = sample_assignment
        updated_assignment.role_id = new_role_id
        mock_service.update_assignment = AsyncMock(return_value=updated_assignment)
        mock_get_service.return_value = mock_service

        result = await update_assignment(
            assignment_id, update_data, mock_admin_user, mock_session
        )

        assert result.role_id == new_role_id
        mock_service.update_assignment.assert_called_once_with(
            assignment_id=assignment_id, role_id=new_role_id
        )


@pytest.mark.asyncio
async def test_update_assignment_not_found(mock_admin_user, mock_session):
    """Test update_assignment fails when assignment not found."""
    assignment_id = uuid4()
    update_data = AssignmentUpdate(role_id=uuid4())

    # Mock session.get to return None
    mock_session.get = AsyncMock(return_value=None)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await update_assignment(assignment_id, update_data, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_assignment_immutable(
    mock_admin_user, mock_session, immutable_assignment
):
    """Test update_assignment fails when assignment is immutable."""
    assignment_id = immutable_assignment.id
    update_data = AssignmentUpdate(role_id=uuid4())

    # Mock session.get to return immutable assignment
    async def mock_get(model, id):
        if model == UserRoleAssignment:
            return immutable_assignment
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await update_assignment(assignment_id, update_data, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "immutable" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_update_assignment_role_not_found(
    mock_admin_user, mock_session, sample_assignment
):
    """Test update_assignment fails when new role not found."""
    assignment_id = sample_assignment.id
    update_data = AssignmentUpdate(role_id=uuid4())

    # Mock session.get to return assignment but not role
    async def mock_get(model, id):
        if model == UserRoleAssignment:
            return sample_assignment
        return None

    mock_session.get = AsyncMock(side_effect=mock_get)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await update_assignment(assignment_id, update_data, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "Role" in exc_info.value.detail
        assert "not found" in exc_info.value.detail


# ============================================================================
# Test Delete Assignment Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_delete_assignment_success(
    mock_admin_user, mock_session, sample_assignment
):
    """Test delete_assignment endpoint successfully deletes assignment."""
    assignment_id = sample_assignment.id

    # Mock session.get to return assignment
    mock_session.get = AsyncMock(return_value=sample_assignment)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.delete_assignment = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service

        result = await delete_assignment(assignment_id, mock_admin_user, mock_session)

        assert result is None
        mock_service.delete_assignment.assert_called_once_with(assignment_id)


@pytest.mark.asyncio
async def test_delete_assignment_not_found(mock_admin_user, mock_session):
    """Test delete_assignment fails when assignment not found."""
    assignment_id = uuid4()

    # Mock session.get to return None
    mock_session.get = AsyncMock(return_value=None)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await delete_assignment(assignment_id, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_assignment_immutable(
    mock_admin_user, mock_session, immutable_assignment
):
    """Test delete_assignment fails when assignment is immutable."""
    assignment_id = immutable_assignment.id

    # Mock session.get to return immutable assignment
    mock_session.get = AsyncMock(return_value=immutable_assignment)

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await delete_assignment(assignment_id, mock_admin_user, mock_session)

        assert exc_info.value.status_code == 400
        assert "immutable" in exc_info.value.detail.lower()


# ============================================================================
# Test Check Permission Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_check_permission_allowed(mock_user):
    """Test check_permission returns allowed=True when user has permission."""
    permission = "Read"
    scope_type = "Flow"
    scope_id = uuid4()

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.can_access = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service

        result = await check_permission(permission, scope_type, mock_user, scope_id)

        assert isinstance(result, PermissionCheckResponse)
        assert result.allowed is True
        mock_service.can_access.assert_called_once_with(
            user_id=mock_user.id,
            permission_name=permission,
            scope_type=scope_type,
            scope_id=scope_id,
        )


@pytest.mark.asyncio
async def test_check_permission_denied(mock_user):
    """Test check_permission returns allowed=False when user lacks permission."""
    permission = "Delete"
    scope_type = "Project"
    scope_id = uuid4()

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.can_access = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service

        result = await check_permission(permission, scope_type, mock_user, scope_id)

        assert isinstance(result, PermissionCheckResponse)
        assert result.allowed is False


@pytest.mark.asyncio
async def test_check_permission_error():
    """Test check_permission handles errors."""
    mock_user = Mock()
    mock_user.id = uuid4()

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.can_access = AsyncMock(side_effect=Exception("Service error"))
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await check_permission("Read", "Flow", mock_user, uuid4())

        assert exc_info.value.status_code == 500
        assert "Failed to check permission" in exc_info.value.detail


# ============================================================================
# Test Batch Permission Check Endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_check_permissions_batch_success(mock_user):
    """Test batch permission check returns results for all resources."""
    flow1_id = str(uuid4())
    flow2_id = str(uuid4())
    flow3_id = str(uuid4())

    request = PermissionCheckBatchRequest(
        permission="Read",
        resources=[
            BatchResource(id=flow1_id, scope_type="Flow", scope_id=flow1_id),
            BatchResource(id=flow2_id, scope_type="Flow", scope_id=flow2_id),
            BatchResource(id=flow3_id, scope_type="Flow", scope_id=flow3_id),
        ],
    )

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        # User has access to flow1 and flow3, but not flow2
        mock_service.can_access = AsyncMock(
            side_effect=[True, False, True]
        )
        mock_get_service.return_value = mock_service

        result = await check_permissions_batch(request, mock_user)

        assert isinstance(result, PermissionCheckBatchResponse)
        assert len(result.results) == 3
        assert result.results[flow1_id] is True
        assert result.results[flow2_id] is False
        assert result.results[flow3_id] is True
        assert mock_service.can_access.call_count == 3


@pytest.mark.asyncio
async def test_check_permissions_batch_empty():
    """Test batch permission check with empty resources list."""
    mock_user = Mock()
    mock_user.id = uuid4()

    request = PermissionCheckBatchRequest(
        permission="Read",
        resources=[],
    )

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_get_service.return_value = mock_service

        result = await check_permissions_batch(request, mock_user)

        assert isinstance(result, PermissionCheckBatchResponse)
        assert len(result.results) == 0


@pytest.mark.asyncio
async def test_check_permissions_batch_error():
    """Test batch permission check handles errors."""
    mock_user = Mock()
    mock_user.id = uuid4()

    request = PermissionCheckBatchRequest(
        permission="Read",
        resources=[
            BatchResource(id=str(uuid4()), scope_type="Flow", scope_id=str(uuid4())),
        ],
    )

    with patch("langbuilder.api.v1.rbac.get_rbac_service") as mock_get_service:
        mock_service = AsyncMock()
        mock_service.can_access = AsyncMock(side_effect=Exception("Service error"))
        mock_get_service.return_value = mock_service

        with pytest.raises(HTTPException) as exc_info:
            await check_permissions_batch(request, mock_user)

        assert exc_info.value.status_code == 500
        assert "Failed to check permissions batch" in exc_info.value.detail


# ============================================================================
# Test Pydantic Schema Validation
# ============================================================================


def test_role_response_schema():
    """Test RoleResponse schema."""
    role_data = {
        "id": str(uuid4()),
        "name": "Admin",
        "description": "Administrator role",
        "is_system": True,
    }

    response = RoleResponse(**role_data)

    assert response.id == role_data["id"]
    assert response.name == role_data["name"]
    assert response.description == role_data["description"]
    assert response.is_system == role_data["is_system"]


def test_assignment_response_schema():
    """Test AssignmentResponse schema."""
    assignment_data = {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "role_id": str(uuid4()),
        "scope_type": "global",
        "scope_id": None,
        "is_immutable": False,
        "created_at": datetime.now(timezone.utc),
        "created_by": str(uuid4()),
    }

    response = AssignmentResponse(**assignment_data)

    assert response.id == assignment_data["id"]
    assert response.user_id == assignment_data["user_id"]
    assert response.role_id == assignment_data["role_id"]
    assert response.scope_type == assignment_data["scope_type"]


def test_assignment_create_schema():
    """Test AssignmentCreate schema."""
    user_id = uuid4()
    role_id = uuid4()
    scope_id = uuid4()

    request = AssignmentCreate(
        user_id=user_id,
        role_id=role_id,
        scope_type="Project",
        scope_id=scope_id,
        is_immutable=True,
    )

    assert request.user_id == user_id
    assert request.role_id == role_id
    assert request.scope_type == "Project"
    assert request.scope_id == scope_id
    assert request.is_immutable is True


def test_assignment_create_schema_defaults():
    """Test AssignmentCreate schema with defaults."""
    user_id = uuid4()
    role_id = uuid4()

    request = AssignmentCreate(
        user_id=user_id,
        role_id=role_id,
        scope_type="Global",
    )

    assert request.scope_id is None
    assert request.is_immutable is False


def test_permission_check_request_schema():
    """Test PermissionCheckRequest schema."""
    scope_id = uuid4()

    request = PermissionCheckRequest(
        permission="Read",
        scope_type="Flow",
        scope_id=scope_id,
    )

    assert request.permission == "Read"
    assert request.scope_type == "Flow"
    assert request.scope_id == scope_id


def test_batch_resource_schema():
    """Test BatchResource schema."""
    resource_id = str(uuid4())
    scope_id = str(uuid4())

    resource = BatchResource(
        id=resource_id,
        scope_type="Project",
        scope_id=scope_id,
    )

    assert resource.id == resource_id
    assert resource.scope_type == "Project"
    assert resource.scope_id == scope_id


def test_permission_check_batch_request_schema():
    """Test PermissionCheckBatchRequest schema."""
    resources = [
        BatchResource(id=str(uuid4()), scope_type="Flow", scope_id=str(uuid4())),
        BatchResource(id=str(uuid4()), scope_type="Flow", scope_id=str(uuid4())),
    ]

    request = PermissionCheckBatchRequest(
        permission="Update",
        resources=resources,
    )

    assert request.permission == "Update"
    assert len(request.resources) == 2
    assert request.resources[0].scope_type == "Flow"

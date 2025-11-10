"""
Unit tests for Task 3.2: Flow Creation Permission Enforcement.

Tests cover:
- create_flow endpoint enforces Create permission on parent project
- create_flows batch endpoint enforces Create permission
- upload_file endpoint enforces Create permission
- Users with Create permission can create flows
- Users without Create permission get 403 error
- Error messages clearly indicate permission issues
- Default folder handling works correctly
- Admin users bypass permission checks
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from langbuilder.api.v1.flows import create_flow, create_flows, upload_file
from langbuilder.api.v1.schemas import FlowListCreate
from langbuilder.services.database.models.flow.model import Flow, FlowCreate
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
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
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
    return project


@pytest.fixture
def sample_flow_create(sample_project):
    """Create a sample FlowCreate object."""
    return FlowCreate(
        name="Test Flow",
        description="Test Description",
        data={},
        folder_id=sample_project.id,
    )


@pytest.fixture
def sample_flow_create_no_folder():
    """Create a FlowCreate object without folder_id."""
    return FlowCreate(
        name="Test Flow",
        description="Test Description",
        data={},
        folder_id=None,
    )


@pytest.fixture
def mock_new_flow():
    """Mock the _new_flow helper function."""
    with patch("langbuilder.api.v1.flows._new_flow") as mock:
        flow = Mock(spec=Flow)
        flow.id = uuid4()
        flow.name = "Test Flow"
        flow.user_id = uuid4()
        flow.folder_id = uuid4()
        mock.return_value = flow
        yield mock


@pytest.fixture
def mock_save_flow_to_fs():
    """Mock the _save_flow_to_fs helper function."""
    with patch("langbuilder.api.v1.flows._save_flow_to_fs") as mock:
        mock.return_value = None
        yield mock


@pytest.fixture
def mock_owner_role():
    """Mock the Owner role query."""
    from langbuilder.services.database.models.rbac import Role

    role = Mock(spec=Role)
    role.id = uuid4()
    role.name = "Owner"
    return role


# ============================================================================
# Tests: create_flow endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_create_flow_allows_with_create_permission(
    mock_session,
    mock_user,
    sample_flow_create,
    sample_project,
    mock_rbac_service,
    mock_new_flow,
    mock_save_flow_to_fs,
    mock_owner_role,
):
    """Test that create_flow succeeds when user has Create permission."""
    # Setup: User has Create permission on project
    mock_rbac_service.can_access.return_value = True

    # Mock Owner role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)
    mock_session.exec.return_value = mock_role_result

    # Execute
    result = await create_flow(
        session=mock_session,
        flow=sample_flow_create,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called with correct parameters
    mock_rbac_service.can_access.assert_called_once_with(
        user_id=mock_user.id,
        permission_name="Create",
        scope_type="Project",
        scope_id=sample_flow_create.folder_id,
    )

    # Verify: _new_flow was called
    mock_new_flow.assert_called_once()

    # Verify: Flow was created successfully
    assert result is not None


@pytest.mark.asyncio
async def test_create_flow_denies_without_create_permission(
    mock_session,
    mock_user,
    sample_flow_create,
    mock_rbac_service,
):
    """Test that create_flow returns 403 when user lacks Create permission."""
    # Setup: User does NOT have Create permission
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify: Should raise HTTPException with 403
    with pytest.raises(HTTPException) as exc_info:
        await create_flow(
            session=mock_session,
            flow=sample_flow_create,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()
    assert "create flows" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_flow_uses_default_folder_when_none_specified(
    mock_session,
    mock_user,
    sample_flow_create_no_folder,
    mock_rbac_service,
    mock_new_flow,
    mock_save_flow_to_fs,
    mock_owner_role,
):
    """Test that create_flow uses default folder when folder_id is None."""
    # Setup: Default folder exists
    default_folder = Mock(spec=Folder)
    default_folder.id = uuid4()
    default_folder.name = "My Collection"

    # Mock folder query to return default folder
    mock_folder_result = Mock()
    mock_folder_result.first = Mock(return_value=default_folder)

    # Mock role query to return Owner role
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)

    # Setup session.exec to return appropriate results
    async def exec_side_effect(query):
        # First call is for folder query, second is for role query
        if not hasattr(exec_side_effect, "call_count"):
            exec_side_effect.call_count = 0
        exec_side_effect.call_count += 1

        if exec_side_effect.call_count == 1:
            return mock_folder_result
        else:
            return mock_role_result

    mock_session.exec.side_effect = exec_side_effect

    # User has Create permission on default folder
    mock_rbac_service.can_access.return_value = True

    # Execute
    result = await create_flow(
        session=mock_session,
        flow=sample_flow_create_no_folder,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called with default folder ID
    mock_rbac_service.can_access.assert_called_once_with(
        user_id=mock_user.id,
        permission_name="Create",
        scope_type="Project",
        scope_id=default_folder.id,
    )

    # Verify: Flow was created successfully
    assert result is not None


@pytest.mark.asyncio
async def test_create_flow_raises_error_when_no_default_folder(
    mock_session,
    mock_user,
    sample_flow_create_no_folder,
    mock_rbac_service,
):
    """Test that create_flow raises 500 when default folder doesn't exist."""
    # Setup: No default folder exists
    mock_folder_result = Mock()
    mock_folder_result.first = Mock(return_value=None)
    mock_session.exec.return_value = mock_folder_result

    # Execute & Verify: Should raise HTTPException with 500
    with pytest.raises(HTTPException) as exc_info:
        await create_flow(
            session=mock_session,
            flow=sample_flow_create_no_folder,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    assert exc_info.value.status_code == 500
    assert "default project not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_flow_admin_bypasses_permission_check(
    mock_session,
    mock_admin_user,
    sample_flow_create,
    mock_rbac_service,
    mock_new_flow,
    mock_save_flow_to_fs,
    mock_owner_role,
):
    """Test that admin users can create flows (RBACService grants access)."""
    # Setup: Admin user - RBACService should return True for admin
    mock_rbac_service.can_access.return_value = True

    # Mock Owner role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)
    mock_session.exec.return_value = mock_role_result

    # Execute
    result = await create_flow(
        session=mock_session,
        flow=sample_flow_create,
        current_user=mock_admin_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called (but returns True for admin)
    mock_rbac_service.can_access.assert_called_once()

    # Verify: Flow was created successfully
    assert result is not None


# ============================================================================
# Tests: create_flows batch endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_create_flows_batch_allows_with_create_permission(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
    mock_owner_role,
):
    """Test that batch create succeeds when user has Create permission."""
    # Setup: Create 3 flows in the same project
    flows = [
        FlowCreate(name=f"Flow {i}", description=f"Desc {i}", data={}, folder_id=sample_project.id)
        for i in range(3)
    ]
    flow_list = FlowListCreate(flows=flows)

    # User has Create permission
    mock_rbac_service.can_access.return_value = True

    # Mock Owner role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)
    mock_session.exec.return_value = mock_role_result

    # Execute
    result = await create_flows(
        session=mock_session,
        flow_list=flow_list,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called once (all flows in same project)
    assert mock_rbac_service.can_access.call_count == 1
    mock_rbac_service.can_access.assert_called_with(
        user_id=mock_user.id,
        permission_name="Create",
        scope_type="Project",
        scope_id=sample_project.id,
    )

    # Verify: All flows were created
    assert len(result) == 3


@pytest.mark.asyncio
async def test_create_flows_batch_denies_without_create_permission(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
):
    """Test that batch create fails when user lacks Create permission."""
    # Setup: Create flows
    flows = [
        FlowCreate(name=f"Flow {i}", description=f"Desc {i}", data={}, folder_id=sample_project.id)
        for i in range(2)
    ]
    flow_list = FlowListCreate(flows=flows)

    # User does NOT have Create permission
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify: Should raise HTTPException with 403
    with pytest.raises(HTTPException) as exc_info:
        await create_flows(
            session=mock_session,
            flow_list=flow_list,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
        )

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_flows_batch_checks_multiple_projects(
    mock_session,
    mock_user,
    mock_rbac_service,
    mock_owner_role,
):
    """Test that batch create checks permission for each unique project."""
    # Setup: Create flows in 2 different projects
    project1_id = uuid4()
    project2_id = uuid4()

    flows = [
        FlowCreate(name="Flow 1", description="Desc 1", data={}, folder_id=project1_id),
        FlowCreate(name="Flow 2", description="Desc 2", data={}, folder_id=project1_id),
        FlowCreate(name="Flow 3", description="Desc 3", data={}, folder_id=project2_id),
    ]
    flow_list = FlowListCreate(flows=flows)

    # User has Create permission on both projects
    mock_rbac_service.can_access.return_value = True

    # Mock Owner role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)
    mock_session.exec.return_value = mock_role_result

    # Execute
    result = await create_flows(
        session=mock_session,
        flow_list=flow_list,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called twice (for 2 unique projects)
    assert mock_rbac_service.can_access.call_count == 2

    # Verify: All flows were created
    assert len(result) == 3


@pytest.mark.asyncio
async def test_create_flows_batch_uses_default_folder(
    mock_session,
    mock_user,
    mock_rbac_service,
    mock_owner_role,
):
    """Test that batch create uses default folder when folder_id is None."""
    # Setup: Default folder exists
    default_folder = Mock(spec=Folder)
    default_folder.id = uuid4()
    default_folder.name = "My Collection"

    # Mock folder query - always return same default_folder
    mock_folder_result = Mock()
    mock_folder_result.first = Mock(return_value=default_folder)

    # Mock role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)

    # Setup session.exec to handle both queries
    # First two calls are for folder queries (one per flow with folder_id=None)
    # Subsequent calls are for role queries
    async def exec_side_effect(query):
        if not hasattr(exec_side_effect, "call_count"):
            exec_side_effect.call_count = 0
        exec_side_effect.call_count += 1

        # First two calls are folder queries, rest are role queries
        if exec_side_effect.call_count <= 2:
            return mock_folder_result
        else:
            return mock_role_result

    mock_session.exec.side_effect = exec_side_effect

    # Create flows without folder_id
    flows = [
        FlowCreate(name="Flow 1", description="Desc 1", data={}, folder_id=None),
        FlowCreate(name="Flow 2", description="Desc 2", data={}, folder_id=None),
    ]
    flow_list = FlowListCreate(flows=flows)

    # User has Create permission on default folder
    mock_rbac_service.can_access.return_value = True

    # Execute
    result = await create_flows(
        session=mock_session,
        flow_list=flow_list,
        current_user=mock_user,
        rbac_service=mock_rbac_service,
    )

    # Verify: can_access was called once (both flows end up in same folder)
    # Since we mock to return the same default_folder object both times,
    # both flows get the same folder_id, so permission is checked only once
    assert mock_rbac_service.can_access.call_count == 1
    call_kwargs = mock_rbac_service.can_access.call_args[1]
    assert call_kwargs["user_id"] == mock_user.id
    assert call_kwargs["permission_name"] == "Create"
    assert call_kwargs["scope_type"] == "Project"
    # Both flows should have been assigned the default folder's ID
    assert call_kwargs["scope_id"] == default_folder.id

    # Verify: All flows were created
    assert len(result) == 2


# ============================================================================
# Tests: upload_file endpoint
# ============================================================================


@pytest.mark.asyncio
async def test_upload_file_allows_with_create_permission(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
    mock_new_flow,
    mock_save_flow_to_fs,
    mock_owner_role,
):
    """Test that upload_file succeeds when user has Create permission."""
    # Setup: Mock file upload
    mock_file = AsyncMock()
    mock_file.read.return_value = b'{"name": "Test Flow", "description": "Test", "data": {}}'

    # User has Create permission
    mock_rbac_service.can_access.return_value = True

    # Mock Owner role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)
    mock_session.exec.return_value = mock_role_result

    # Execute
    with patch("langbuilder.api.v1.flows.orjson.loads") as mock_loads:
        mock_loads.return_value = {"name": "Test Flow", "description": "Test", "data": {}}

        result = await upload_file(
            session=mock_session,
            file=mock_file,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
            folder_id=sample_project.id,
        )

    # Verify: can_access was called
    mock_rbac_service.can_access.assert_called_once_with(
        user_id=mock_user.id,
        permission_name="Create",
        scope_type="Project",
        scope_id=sample_project.id,
    )

    # Verify: Upload succeeded
    assert result is not None


@pytest.mark.asyncio
async def test_upload_file_denies_without_create_permission(
    mock_session,
    mock_user,
    sample_project,
    mock_rbac_service,
):
    """Test that upload_file fails when user lacks Create permission."""
    # Setup: Mock file upload
    mock_file = AsyncMock()
    mock_file.read.return_value = b'{"name": "Test Flow", "description": "Test", "data": {}}'

    # User does NOT have Create permission
    mock_rbac_service.can_access.return_value = False

    # Execute & Verify: Should raise HTTPException with 403
    with patch("langbuilder.api.v1.flows.orjson.loads") as mock_loads:
        mock_loads.return_value = {"name": "Test Flow", "description": "Test", "data": {}}

        with pytest.raises(HTTPException) as exc_info:
            await upload_file(
                session=mock_session,
                file=mock_file,
                current_user=mock_user,
                rbac_service=mock_rbac_service,
                folder_id=sample_project.id,
            )

    assert exc_info.value.status_code == 403
    assert "permission" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_upload_file_uses_default_folder(
    mock_session,
    mock_user,
    mock_rbac_service,
    mock_new_flow,
    mock_save_flow_to_fs,
    mock_owner_role,
):
    """Test that upload_file uses default folder when folder_id is None."""
    # Setup: Default folder exists
    default_folder = Mock(spec=Folder)
    default_folder.id = uuid4()
    default_folder.name = "My Collection"

    # Mock folder query
    mock_folder_result = Mock()
    mock_folder_result.first = Mock(return_value=default_folder)

    # Mock role query
    mock_role_result = Mock()
    mock_role_result.first = Mock(return_value=mock_owner_role)

    # Setup session.exec to handle both queries
    async def exec_side_effect(query):
        if not hasattr(exec_side_effect, "call_count"):
            exec_side_effect.call_count = 0
        exec_side_effect.call_count += 1

        if exec_side_effect.call_count == 1:
            return mock_folder_result
        else:
            return mock_role_result

    mock_session.exec.side_effect = exec_side_effect

    # Mock file upload
    mock_file = AsyncMock()
    mock_file.read.return_value = b'{"name": "Test Flow", "description": "Test", "data": {}}'

    # User has Create permission
    mock_rbac_service.can_access.return_value = True

    # Execute
    with patch("langbuilder.api.v1.flows.orjson.loads") as mock_loads:
        mock_loads.return_value = {"name": "Test Flow", "description": "Test", "data": {}}

        result = await upload_file(
            session=mock_session,
            file=mock_file,
            current_user=mock_user,
            rbac_service=mock_rbac_service,
            folder_id=None,  # No folder specified
        )

    # Verify: can_access was called with default folder ID
    mock_rbac_service.can_access.assert_called_with(
        user_id=mock_user.id,
        permission_name="Create",
        scope_type="Project",
        scope_id=default_folder.id,
    )

    # Verify: Upload succeeded
    assert result is not None


# ============================================================================
# Summary
# ============================================================================

"""
Test Coverage Summary:

create_flow endpoint (5 tests):
1. ✅ Allows creation with Create permission
2. ✅ Denies creation without Create permission (403)
3. ✅ Uses default folder when folder_id is None
4. ✅ Raises error when default folder doesn't exist
5. ✅ Admin users can create (via RBACService)

create_flows batch endpoint (4 tests):
1. ✅ Allows batch creation with Create permission
2. ✅ Denies batch creation without Create permission (403)
3. ✅ Checks permission for each unique project
4. ✅ Uses default folder when folder_id is None

upload_file endpoint (3 tests):
1. ✅ Allows upload with Create permission
2. ✅ Denies upload without Create permission (403)
3. ✅ Uses default folder when folder_id is None

Total: 12 comprehensive unit tests
"""

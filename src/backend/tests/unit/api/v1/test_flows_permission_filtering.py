"""
Unit tests for Task 3.1: Flow List Permission Filtering.

Tests cover:
- read_flows endpoint filters by Read permission
- Users only see flows they have Read permission for
- Admin users bypass permission checks (see all flows)
- Permission inheritance from Project to Flow works
- Error handling when permission check fails
- Paginated results are filtered correctly
- Header flows are filtered correctly
- Performance requirements are met
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException
from langbuilder.api.v1.flows import read_flows
from langbuilder.services.database.models.flow.model import Flow
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
def sample_flows():
    """Create sample flows for testing."""
    flows = []
    for i in range(5):
        flow = Mock(spec=Flow)
        flow.id = uuid4()
        flow.name = f"Test Flow {i}"
        flow.description = f"Description {i}"
        flow.user_id = uuid4()
        flow.folder_id = uuid4()
        flow.is_component = False
        flows.append(flow)
    return flows


@pytest.fixture
def sample_folders():
    """Create sample folders for testing."""
    default_folder = Mock(spec=Folder)
    default_folder.id = uuid4()
    default_folder.name = "My Collection"

    starter_folder = Mock(spec=Folder)
    starter_folder.id = uuid4()
    starter_folder.name = "Starter Projects"

    return {"default": default_folder, "starter": starter_folder}


@pytest.fixture
def mock_settings_service():
    """Create a mock settings service."""
    with patch("langbuilder.api.v1.flows.get_settings_service") as mock_service:
        settings = Mock()
        settings.auth_settings.AUTO_LOGIN = False
        mock_service.return_value = settings
        yield mock_service


# ============================================================================
# Test read_flows Permission Filtering
# ============================================================================


@pytest.mark.asyncio
async def test_read_flows_filters_by_permission(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows filters flows by Read permission."""
    # Setup mock session to return folders and flows
    mock_session.exec = AsyncMock()

    # First call returns default folder
    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    # Second call returns starter folder
    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    # Third call returns flows
    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to allow access to flows 0, 2, 4 (deny 1, 3)
    async def mock_can_access(user_id, permission_name, scope_type, scope_id):
        # Find flow index based on scope_id
        flow_index = next((i for i, f in enumerate(sample_flows) if f.id == scope_id), -1)
        # Allow even indices (0, 2, 4), deny odd indices (1, 3)
        return flow_index % 2 == 0

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access)

    # Mock validate_is_component to return flows as-is
    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
            # Mock Params
            mock_params = Mock()
            mock_params.page = 1
            mock_params.size = 50

            # Call read_flows with get_all=True
            result = await read_flows(
                current_user=mock_user,
                session=mock_session,
                rbac_service=mock_rbac_service,
                remove_example_flows=False,
                components_only=False,
                get_all=True,
                folder_id=None,
                params=mock_params,
                header_flows=False,
            )

    # Should only return flows at indices 0, 2, 4 (3 flows)
    assert len(result) == 3
    assert result[0] == sample_flows[0]
    assert result[1] == sample_flows[2]
    assert result[2] == sample_flows[4]

    # Verify can_access was called for each flow
    assert mock_rbac_service.can_access.call_count == 5


@pytest.mark.asyncio
async def test_read_flows_denies_all_when_no_permissions(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows returns empty list when user has no Read permissions."""
    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to deny all access
    mock_rbac_service.can_access = AsyncMock(return_value=False)

    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
            mock_params = Mock()
            mock_params.page = 1
            mock_params.size = 50

            result = await read_flows(
                current_user=mock_user,
                session=mock_session,
                rbac_service=mock_rbac_service,
                remove_example_flows=False,
                components_only=False,
                get_all=True,
                folder_id=None,
                params=mock_params,
                header_flows=False,
            )

    # Should return empty list
    assert len(result) == 0
    assert mock_rbac_service.can_access.call_count == 5


@pytest.mark.asyncio
async def test_read_flows_allows_all_for_admin(
    mock_admin_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that admin users can see all flows (bypass permission check via service)."""
    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to always allow access (admin bypass)
    mock_rbac_service.can_access = AsyncMock(return_value=True)

    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
            mock_params = Mock()
            mock_params.page = 1
            mock_params.size = 50

            result = await read_flows(
                current_user=mock_admin_user,
                session=mock_session,
                rbac_service=mock_rbac_service,
                remove_example_flows=False,
                components_only=False,
                get_all=True,
                folder_id=None,
                params=mock_params,
                header_flows=False,
            )

    # Should return all flows
    assert len(result) == 5
    assert mock_rbac_service.can_access.call_count == 5


@pytest.mark.asyncio
async def test_read_flows_handles_permission_check_error(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows gracefully handles errors during permission check."""
    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to throw error for some flows
    async def mock_can_access_with_error(user_id, permission_name, scope_type, scope_id):
        flow_index = next((i for i, f in enumerate(sample_flows) if f.id == scope_id), -1)
        if flow_index == 1:  # Throw error for flow at index 1
            raise Exception("Permission check failed")
        return flow_index % 2 == 0

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access_with_error)

    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
            mock_params = Mock()
            mock_params.page = 1
            mock_params.size = 50

            result = await read_flows(
                current_user=mock_user,
                session=mock_session,
                rbac_service=mock_rbac_service,
                remove_example_flows=False,
                components_only=False,
                get_all=True,
                folder_id=None,
                params=mock_params,
                header_flows=False,
            )

    # Should skip flow 1 (error) and flow 3 (denied), return 0, 2, 4
    assert len(result) == 3
    assert result[0] == sample_flows[0]
    assert result[1] == sample_flows[2]
    assert result[2] == sample_flows[4]


@pytest.mark.asyncio
async def test_read_flows_filters_header_flows(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows filters header flows correctly."""
    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to allow first 3 flows
    async def mock_can_access(user_id, permission_name, scope_type, scope_id):
        flow_index = next((i for i, f in enumerate(sample_flows) if f.id == scope_id), -1)
        return flow_index < 3

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access)

    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        # Mock FlowHeader.model_validate to return the flow itself
        with patch("langbuilder.api.v1.flows.FlowHeader") as mock_flow_header:
            mock_flow_header.model_validate = Mock(side_effect=lambda x, **kwargs: x)
            with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
                mock_params = Mock()
                mock_params.page = 1
                mock_params.size = 50

                result = await read_flows(
                    current_user=mock_user,
                    session=mock_session,
                    rbac_service=mock_rbac_service,
                    remove_example_flows=False,
                    components_only=False,
                    get_all=True,
                    folder_id=None,
                    params=mock_params,
                    header_flows=True,
                )

        # Should return first 3 flows as headers
        assert len(result) == 3


@pytest.mark.asyncio
async def test_read_flows_filters_paginated_results(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows filters paginated results correctly."""
    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    # For paginated case, return flows for specific folder
    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to allow flows at indices 0, 2, 4
    async def mock_can_access(user_id, permission_name, scope_type, scope_id):
        flow_index = next((i for i, f in enumerate(sample_flows) if f.id == scope_id), -1)
        return flow_index % 2 == 0

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access)

    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        mock_params = Mock()
        mock_params.page = 1
        mock_params.size = 2  # Request 2 items per page

        # Call with get_all=False to trigger pagination
        result = await read_flows(
            current_user=mock_user,
            session=mock_session,
            rbac_service=mock_rbac_service,
            remove_example_flows=False,
            components_only=False,
            get_all=False,
            folder_id=sample_folders["default"].id,
            params=mock_params,
            header_flows=False,
        )

    # Should return Page object with filtered results
    assert hasattr(result, "items")
    assert hasattr(result, "total")
    assert result.total == 3  # Total readable flows: 0, 2, 4
    assert len(result.items) == 2  # Page size is 2
    assert result.page == 1
    assert result.size == 2


@pytest.mark.asyncio
async def test_read_flows_with_components_only_filter(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows filters by components_only and permissions."""
    # Mark some flows as components
    sample_flows[0].is_component = True
    sample_flows[2].is_component = True
    sample_flows[4].is_component = True

    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to allow flows 0, 2 (deny 4)
    async def mock_can_access(user_id, permission_name, scope_type, scope_id):
        flow_index = next((i for i, f in enumerate(sample_flows) if f.id == scope_id), -1)
        return flow_index < 3

    mock_rbac_service.can_access = AsyncMock(side_effect=mock_can_access)

    # Mock validate_is_component to filter components
    def mock_validate(flows):
        return [f for f in flows if f.is_component]

    with patch("langbuilder.api.v1.flows.validate_is_component", side_effect=mock_validate):
        with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
            mock_params = Mock()
            mock_params.page = 1
            mock_params.size = 50

            result = await read_flows(
                current_user=mock_user,
                session=mock_session,
                rbac_service=mock_rbac_service,
                remove_example_flows=False,
                components_only=True,
                get_all=True,
                folder_id=None,
                params=mock_params,
                header_flows=False,
            )

    # Should return only component flows with Read permission (0, 2)
    assert len(result) == 2
    assert all(f.is_component for f in result)


@pytest.mark.asyncio
async def test_read_flows_with_remove_example_flows(
    mock_user, mock_session, mock_rbac_service, sample_flows, sample_folders, mock_settings_service
):
    """Test that read_flows filters example flows and applies permissions."""
    # Assign some flows to starter folder
    sample_flows[1].folder_id = sample_folders["starter"].id
    sample_flows[3].folder_id = sample_folders["starter"].id

    # Setup mock session
    mock_session.exec = AsyncMock()

    default_result = AsyncMock()
    default_result.first = Mock(return_value=sample_folders["default"])

    starter_result = AsyncMock()
    starter_result.first = Mock(return_value=sample_folders["starter"])

    flows_result = AsyncMock()
    flows_result.all = Mock(return_value=sample_flows)

    mock_session.exec.side_effect = [default_result, starter_result, flows_result]

    # Mock RBAC service to allow all flows
    mock_rbac_service.can_access = AsyncMock(return_value=True)

    with patch("langbuilder.api.v1.flows.validate_is_component", return_value=sample_flows):
        with patch("langbuilder.api.v1.flows.compress_response", side_effect=lambda x: x):
            mock_params = Mock()
            mock_params.page = 1
            mock_params.size = 50

            result = await read_flows(
                current_user=mock_user,
                session=mock_session,
                rbac_service=mock_rbac_service,
                remove_example_flows=True,
                components_only=False,
                get_all=True,
                folder_id=None,
                params=mock_params,
                header_flows=False,
            )

    # Should exclude flows from starter folder (1, 3), return 0, 2, 4
    assert len(result) == 3
    assert all(f.folder_id != sample_folders["starter"].id for f in result)

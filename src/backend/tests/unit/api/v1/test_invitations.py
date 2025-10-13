"""Unit tests for Invitation Management API.

Tests PRD Story 1.1 @AC6 - Invitation Management
- Accept workspace invitation via token
- Reject workspace invitation
- List pending invitations for user

Implements Task 3.9 from RBAC Implementation Plan.
"""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from langflow.services.database.models.invitation.model import Invitation, InvitationStatus
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_assignment import RoleAssignment
from langflow.services.database.models.user.model import User
from langflow.services.database.models.workspace.model import Workspace, WorkspaceMember
from langflow.services.deps import get_db_service
from sqlmodel import select

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_workspace(client, active_user):
    """Create test workspace in the database."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        workspace = Workspace(
            name="Test Workspace",
            slug="test-workspace",
            description="Workspace for API testing",
            created_by=active_user.id,
            is_active=True,
        )
        session.add(workspace)
        await session.commit()
        await session.refresh(workspace)

    yield workspace

    # Cleanup
    async with db_manager.with_session() as session:
        workspace_db = await session.get(Workspace, workspace.id)
        if workspace_db:
            await session.delete(workspace_db)
        await session.commit()


@pytest.fixture
async def test_role(client):
    """Create test role in the database."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        role = Role(
            name="Test Role",
            display_name="Test Role",
            description="Role for API testing",
            scope_type="workspace",
            is_active=True,
        )
        session.add(role)
        await session.commit()
        await session.refresh(role)

    yield role

    # Cleanup
    async with db_manager.with_session() as session:
        role_db = await session.get(Role, role.id)
        if role_db:
            await session.delete(role_db)
        await session.commit()


@pytest.fixture
async def test_invitation(client, test_workspace, active_user):
    """Create test invitation in the database."""
    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)

    yield invitation

    # Cleanup
    async with db_manager.with_session() as session:
        inv_db = await session.get(Invitation, invitation.id)
        if inv_db:
            await session.delete(inv_db)
        await session.commit()


@pytest.fixture
async def second_user(client):
    """Create a second test user."""
    from langflow.services.auth.utils import get_password_hash

    db_manager = get_db_service()

    async with db_manager.with_session() as session:
        user = User(
            username="seconduser",
            email="seconduser@example.com",
            password=get_password_hash("testpassword"),
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    yield user

    # Cleanup
    async with db_manager.with_session() as session:
        user_db = await session.get(User, user.id)
        if user_db:
            await session.delete(user_db)
        await session.commit()


# ============================================================================
# ACCEPT INVITATION Tests
# ============================================================================


async def test_accept_invitation_success(
    client: AsyncClient, logged_in_headers, test_invitation, active_user, test_workspace
):
    """Test PRD Story 1.1 @AC6: Accept workspace invitation."""
    response = await client.post(
        f"api/v1/invitations/{test_invitation.token}/accept",
        headers=logged_in_headers,
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "accepted"
    assert result["workspace_id"] == str(test_workspace.id)
    assert result.get("role_granted") is False  # No role specified in invitation

    # Verify user is now a workspace member
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == test_workspace.id,
            WorkspaceMember.user_id == active_user.id,
        )
        result = await session.exec(stmt)
        member = result.first()
        assert member is not None, "User should be a workspace member"
        assert member.role == "member"

        # Verify invitation status updated
        inv_db = await session.get(Invitation, test_invitation.id)
        assert inv_db.status == InvitationStatus.ACCEPTED.value
        assert inv_db.invited_user_id == active_user.id
        assert inv_db.accepted_at is not None

        # Cleanup
        await session.delete(member)
        await session.commit()


async def test_accept_invitation_with_role(
    client: AsyncClient, logged_in_headers, test_workspace, test_role, active_user
):
    """Test accepting invitation that includes role assignment."""
    db_manager = get_db_service()

    # Create invitation with role
    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            role_id=test_role.id,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        response = await client.post(
            f"api/v1/invitations/{inv_token}/accept",
            headers=logged_in_headers,
        )

        assert response.status_code == 200, response.text
        result = response.json()
        assert result["status"] == "accepted"
        assert result["role_granted"] is True

        # Verify role assignment created
        async with db_manager.with_session() as session:
            stmt = select(RoleAssignment).where(
                RoleAssignment.user_id == active_user.id,
                RoleAssignment.role_id == test_role.id,
            )
            result = await session.exec(stmt)
            assignment = result.first()
            assert assignment is not None, "Role assignment should exist"
            assert assignment.scope_type == "workspace"
            assert assignment.scope_id == test_workspace.id

            # Cleanup role assignment
            await session.delete(assignment)

            # Cleanup workspace member
            stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == test_workspace.id,
                WorkspaceMember.user_id == active_user.id,
            )
            result = await session.exec(stmt)
            member = result.first()
            if member:
                await session.delete(member)

            await session.commit()

    finally:
        # Cleanup invitation
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)
            await session.commit()


async def test_accept_invitation_expired(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test accepting expired invitation fails."""
    db_manager = get_db_service()

    # Create expired invitation
    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        response = await client.post(
            f"api/v1/invitations/{inv_token}/accept",
            headers=logged_in_headers,
        )

        assert response.status_code == 400, response.text
        assert "expired" in response.text.lower()

        # Verify invitation status updated to expired
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            assert inv_db.status == InvitationStatus.EXPIRED.value

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)
            await session.commit()


async def test_accept_invitation_wrong_user(
    client: AsyncClient, logged_in_headers, test_workspace, active_user, second_user
):
    """Test PRD @AC6: Only invited user can accept (email mismatch)."""
    db_manager = get_db_service()

    # Create invitation for second user
    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=second_user.email,  # Different email
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        # Try to accept with active_user (wrong email)
        response = await client.post(
            f"api/v1/invitations/{inv_token}/accept",
            headers=logged_in_headers,
        )

        assert response.status_code == 403, response.text
        assert "invite_not_for_user" in response.text
        assert "different user" in response.text.lower()

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)
            await session.commit()


async def test_accept_invitation_not_found(
    client: AsyncClient, logged_in_headers
):
    """Test accepting non-existent invitation fails."""
    fake_token = "nonexistent-token-12345"

    response = await client.post(
        f"api/v1/invitations/{fake_token}/accept",
        headers=logged_in_headers,
    )

    assert response.status_code == 404
    assert "not found" in response.text.lower()


async def test_accept_invitation_already_accepted(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test accepting already accepted invitation fails."""
    db_manager = get_db_service()

    # Create already accepted invitation
    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.ACCEPTED.value,  # Already accepted
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
            accepted_at=datetime.now(timezone.utc),
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        response = await client.post(
            f"api/v1/invitations/{inv_token}/accept",
            headers=logged_in_headers,
        )

        assert response.status_code == 404, response.text
        assert "already processed" in response.text.lower()

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)
            await session.commit()


async def test_accept_invitation_already_member(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test accepting invitation when already a workspace member."""
    db_manager = get_db_service()

    # Add user as workspace member first
    async with db_manager.with_session() as session:
        member = WorkspaceMember(
            workspace_id=test_workspace.id,
            user_id=active_user.id,
            role="member",
            is_active=True,
        )
        session.add(member)

        # Create invitation
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        response = await client.post(
            f"api/v1/invitations/{inv_token}/accept",
            headers=logged_in_headers,
        )

        assert response.status_code == 200, response.text
        result = response.json()
        assert result["status"] == "accepted"
        assert result.get("already_member") is True

        # Verify invitation marked as accepted
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            assert inv_db.status == InvitationStatus.ACCEPTED.value

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)

            stmt = select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == test_workspace.id,
                WorkspaceMember.user_id == active_user.id,
            )
            result = await session.exec(stmt)
            member = result.first()
            if member:
                await session.delete(member)

            await session.commit()


async def test_accept_invitation_requires_authentication(
    client: AsyncClient, test_invitation
):
    """Test that accepting invitation requires authentication."""
    response = await client.post(
        f"api/v1/invitations/{test_invitation.token}/accept",
    )

    assert response.status_code == 403, "Should require authentication"


# ============================================================================
# REJECT INVITATION Tests
# ============================================================================


async def test_reject_invitation_success(
    client: AsyncClient, logged_in_headers, test_invitation, active_user, test_workspace
):
    """Test rejecting workspace invitation."""
    response = await client.post(
        f"api/v1/invitations/{test_invitation.token}/reject",
        headers=logged_in_headers,
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "rejected"
    assert result["workspace_id"] == str(test_workspace.id)

    # Verify invitation status updated
    db_manager = get_db_service()
    async with db_manager.with_session() as session:
        inv_db = await session.get(Invitation, test_invitation.id)
        assert inv_db.status == InvitationStatus.REJECTED.value
        assert inv_db.invited_user_id == active_user.id

    # Verify user is NOT a workspace member
    async with db_manager.with_session() as session:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == test_workspace.id,
            WorkspaceMember.user_id == active_user.id,
        )
        result = await session.exec(stmt)
        member = result.first()
        assert member is None, "User should NOT be a workspace member"


async def test_reject_invitation_expired(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test rejecting expired invitation fails."""
    db_manager = get_db_service()

    # Create expired invitation
    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        response = await client.post(
            f"api/v1/invitations/{inv_token}/reject",
            headers=logged_in_headers,
        )

        assert response.status_code == 400, response.text
        assert "expired" in response.text.lower()

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)
            await session.commit()


async def test_reject_invitation_wrong_user(
    client: AsyncClient, logged_in_headers, test_workspace, active_user, second_user
):
    """Test only invited user can reject (email mismatch)."""
    db_manager = get_db_service()

    # Create invitation for second user
    async with db_manager.with_session() as session:
        invitation = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=second_user.email,  # Different email
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(invitation)
        await session.commit()
        await session.refresh(invitation)
        inv_token = invitation.token
        inv_id = invitation.id

    try:
        # Try to reject with active_user (wrong email)
        response = await client.post(
            f"api/v1/invitations/{inv_token}/reject",
            headers=logged_in_headers,
        )

        assert response.status_code == 403, response.text
        assert "invite_not_for_user" in response.text

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            inv_db = await session.get(Invitation, inv_id)
            if inv_db:
                await session.delete(inv_db)
            await session.commit()


async def test_reject_invitation_requires_authentication(
    client: AsyncClient, test_invitation
):
    """Test that rejecting invitation requires authentication."""
    response = await client.post(
        f"api/v1/invitations/{test_invitation.token}/reject",
    )

    assert response.status_code == 403, "Should require authentication"


# ============================================================================
# LIST INVITATIONS Tests
# ============================================================================


async def test_list_pending_invitations_success(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test listing pending invitations for current user."""
    db_manager = get_db_service()

    # Create multiple invitations for active user
    async with db_manager.with_session() as session:
        invitations = [
            Invitation(
                workspace_id=test_workspace.id,
                invited_by_user_id=active_user.id,
                email=active_user.email,
                status=InvitationStatus.PENDING.value,
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                token=Invitation.generate_token(),
                scope_type="workspace",
                scope_id=test_workspace.id,
            ),
            Invitation(
                workspace_id=test_workspace.id,
                invited_by_user_id=active_user.id,
                email=active_user.email,
                status=InvitationStatus.PENDING.value,
                expires_at=datetime.now(timezone.utc) + timedelta(days=5),
                token=Invitation.generate_token(),
                scope_type="workspace",
                scope_id=test_workspace.id,
            ),
        ]
        for inv in invitations:
            session.add(inv)
        await session.commit()
        for inv in invitations:
            await session.refresh(inv)
        inv_ids = [inv.id for inv in invitations]

    try:
        response = await client.get(
            "api/v1/invitations/pending",
            headers=logged_in_headers,
        )

        assert response.status_code == 200, response.text
        result = response.json()
        assert isinstance(result, list)
        assert len(result) >= 2  # At least our 2 invitations

        # Check they're for the correct email
        for inv in result:
            if inv["id"] in [str(i) for i in inv_ids]:
                assert inv["email"] == active_user.email
                assert inv["status"] == InvitationStatus.PENDING.value

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            for inv_id in inv_ids:
                inv_db = await session.get(Invitation, inv_id)
                if inv_db:
                    await session.delete(inv_db)
            await session.commit()


async def test_list_pending_invitations_excludes_expired(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test that list excludes expired invitations."""
    db_manager = get_db_service()

    # Create pending and expired invitations
    async with db_manager.with_session() as session:
        pending_inv = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        expired_inv = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # Expired
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        session.add(pending_inv)
        session.add(expired_inv)
        await session.commit()
        await session.refresh(pending_inv)
        await session.refresh(expired_inv)
        pending_id = pending_inv.id
        expired_id = expired_inv.id

    try:
        response = await client.get(
            "api/v1/invitations/pending",
            headers=logged_in_headers,
        )

        assert response.status_code == 200, response.text
        result = response.json()

        # Check pending invitation is included
        pending_ids = [inv["id"] for inv in result]
        assert str(pending_id) in pending_ids
        # Check expired invitation is NOT included
        assert str(expired_id) not in pending_ids

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            for inv_id in [pending_id, expired_id]:
                inv_db = await session.get(Invitation, inv_id)
                if inv_db:
                    await session.delete(inv_db)
            await session.commit()


async def test_list_pending_invitations_excludes_accepted(
    client: AsyncClient, logged_in_headers, test_workspace, active_user
):
    """Test that list excludes accepted invitations."""
    db_manager = get_db_service()

    # Create pending and accepted invitations
    async with db_manager.with_session() as session:
        pending_inv = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.PENDING.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
        )
        accepted_inv = Invitation(
            workspace_id=test_workspace.id,
            invited_by_user_id=active_user.id,
            email=active_user.email,
            status=InvitationStatus.ACCEPTED.value,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            token=Invitation.generate_token(),
            scope_type="workspace",
            scope_id=test_workspace.id,
            accepted_at=datetime.now(timezone.utc),
        )
        session.add(pending_inv)
        session.add(accepted_inv)
        await session.commit()
        await session.refresh(pending_inv)
        await session.refresh(accepted_inv)
        pending_id = pending_inv.id
        accepted_id = accepted_inv.id

    try:
        response = await client.get(
            "api/v1/invitations/pending",
            headers=logged_in_headers,
        )

        assert response.status_code == 200, response.text
        result = response.json()

        # Check pending invitation is included
        pending_ids = [inv["id"] for inv in result]
        assert str(pending_id) in pending_ids
        # Check accepted invitation is NOT included
        assert str(accepted_id) not in pending_ids

    finally:
        # Cleanup
        async with db_manager.with_session() as session:
            for inv_id in [pending_id, accepted_id]:
                inv_db = await session.get(Invitation, inv_id)
                if inv_db:
                    await session.delete(inv_db)
            await session.commit()


async def test_list_pending_invitations_empty(
    client: AsyncClient, logged_in_headers
):
    """Test listing invitations when there are none."""
    response = await client.get(
        "api/v1/invitations/pending",
        headers=logged_in_headers,
    )

    assert response.status_code == 200, response.text
    result = response.json()
    assert isinstance(result, list)
    # May be empty or contain invitations from other tests


async def test_list_pending_invitations_requires_authentication(
    client: AsyncClient
):
    """Test that listing invitations requires authentication."""
    response = await client.get(
        "api/v1/invitations/pending",
    )

    assert response.status_code == 403, "Should require authentication"


# ============================================================================
# OpenAPI Documentation Tests
# ============================================================================


async def test_openapi_docs_include_invitations_endpoints(client: AsyncClient):
    """Test that OpenAPI docs are generated correctly for Invitations endpoints."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    openapi_spec = response.json()

    # Check that Invitations endpoints are documented
    paths = openapi_spec.get("paths", {})

    # Check for invitation paths
    inv_paths = [p for p in paths.keys() if "invitations" in p]
    assert len(inv_paths) >= 3, f"Expected at least 3 invitation endpoints, found: {inv_paths}"

"""
Unit tests for RBAC models (Permission, Role, Grant, Invite).

Tests model validation, business logic, and data integrity.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from langflow.services.database.models.permission.model import Permission
from langflow.services.database.models.role.model import Role
from langflow.services.database.models.grant.model import Grant, PrincipalType, ScopeType
from langflow.services.database.models.invite.model import Invite, InviteStatus


class TestPermissionModel:
    """Test Permission model."""

    def test_permission_creation(self):
        """Test creating a permission with valid data."""
        permission = Permission(
            id="flows:create",
            resource_type="flows",
            action="create",
            description="Create new flows",
        )

        assert permission.id == "flows:create"
        assert permission.resource_type == "flows"
        assert permission.action == "create"
        assert permission.description == "Create new flows"

    def test_permission_id_format(self):
        """Test permission ID follows resource_type:action format."""
        permission = Permission(
            id="components:modify_component_settings",
            resource_type="components",
            action="modify_component_settings",
            description="Modify component settings",
        )

        assert ":" in permission.id
        assert permission.id.startswith(permission.resource_type)


class TestRoleModel:
    """Test Role model with permission validation."""

    def test_role_creation(self):
        """Test creating a role with permissions."""
        role = Role(
            name="Editor",
            permissions=["flows:create", "flows:read", "flows:update"],
            version=1,
        )

        assert role.name == "Editor"
        assert len(role.permissions) == 3
        assert role.version == 1

    def test_role_validate_permissions_success(self):
        """Test permission validation succeeds with known permissions."""
        role = Role(
            name="Editor",
            permissions=["flows:create", "flows:read"],
        )

        valid_permission_ids = {"flows:create", "flows:read", "flows:delete"}
        is_valid, unknown = role.validate_permissions(valid_permission_ids)

        assert is_valid is True
        assert unknown == []

    def test_role_validate_permissions_failure(self):
        """Test permission validation fails with unknown permissions."""
        role = Role(
            name="BadRole",
            permissions=["flows:create", "unknown:permission", "another:bad"],
        )

        valid_permission_ids = {"flows:create", "flows:read"}
        is_valid, unknown = role.validate_permissions(valid_permission_ids)

        assert is_valid is False
        assert "unknown:permission" in unknown
        assert "another:bad" in unknown
        assert len(unknown) == 2

    def test_role_empty_permissions(self):
        """Test role with no permissions is valid."""
        role = Role(name="EmptyRole", permissions=[])

        valid_permission_ids = {"flows:create"}
        is_valid, unknown = role.validate_permissions(valid_permission_ids)

        assert is_valid is True
        assert unknown == []

    def test_role_none_permissions(self):
        """Test role with None permissions."""
        role = Role(name="NoneRole", permissions=None)

        valid_permission_ids = {"flows:create"}
        is_valid, unknown = role.validate_permissions(valid_permission_ids)

        assert is_valid is True
        assert unknown == []


class TestGrantModel:
    """Test Grant model for role assignments."""

    def test_grant_creation(self):
        """Test creating a grant with all required fields."""
        grant = Grant(
            principal_type=PrincipalType.USER,
            principal_id=str(uuid4()),
            role_id=str(uuid4()),
            scope_type=ScopeType.PROJECT,
            scope_id="PRJ1",
        )

        assert grant.principal_type == PrincipalType.USER
        assert grant.scope_type == ScopeType.PROJECT
        assert grant.scope_id == "PRJ1"
        assert grant.expires_at is None  # Default is no expiration

    def test_grant_with_expiration(self):
        """Test creating a time-bound grant."""
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        grant = Grant(
            principal_type=PrincipalType.USER,
            principal_id=str(uuid4()),
            role_id=str(uuid4()),
            scope_type=ScopeType.WORKSPACE,
            scope_id="WB1",
            expires_at=expires,
        )

        assert grant.expires_at == expires

    def test_grant_principal_types(self):
        """Test all principal type enums."""
        user_grant = Grant(
            principal_type=PrincipalType.USER,
            principal_id=str(uuid4()),
            role_id=str(uuid4()),
            scope_type=ScopeType.PROJECT,
            scope_id="P1",
        )

        group_grant = Grant(
            principal_type=PrincipalType.GROUP,
            principal_id=str(uuid4()),
            role_id=str(uuid4()),
            scope_type=ScopeType.PROJECT,
            scope_id="P1",
        )

        service_grant = Grant(
            principal_type=PrincipalType.SERVICE_ACCOUNT,
            principal_id=str(uuid4()),
            role_id=str(uuid4()),
            scope_type=ScopeType.PROJECT,
            scope_id="P1",
        )

        assert user_grant.principal_type == PrincipalType.USER
        assert group_grant.principal_type == PrincipalType.GROUP
        assert service_grant.principal_type == PrincipalType.SERVICE_ACCOUNT

    def test_grant_scope_types(self):
        """Test all scope type enums."""
        scopes = [
            ScopeType.WORKSPACE,
            ScopeType.PROJECT,
            ScopeType.ENVIRONMENT,
            ScopeType.FLOW,
            ScopeType.COMPONENT,
        ]

        for scope_type in scopes:
            grant = Grant(
                principal_type=PrincipalType.USER,
                principal_id=str(uuid4()),
                role_id=str(uuid4()),
                scope_type=scope_type,
                scope_id="test_id",
            )
            assert grant.scope_type == scope_type


class TestInviteModel:
    """Test Invite model for user invitations."""

    def test_invite_creation(self):
        """Test creating an invite."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
        )

        assert invite.invitee_email == "test@example.com"
        assert invite.status == InviteStatus.PENDING
        assert invite.workspace_id == "WB1"

    def test_invite_is_expired_false(self):
        """Test invite is not expired when within time window."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        assert invite.is_expired() is False

    def test_invite_is_expired_true(self):
        """Test invite is expired when past expiration date."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        assert invite.is_expired() is True

    def test_invite_can_accept_success(self):
        """Test can_accept returns True for valid acceptance."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            status=InviteStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        assert invite.can_accept("test@example.com") is True

    def test_invite_can_accept_wrong_email(self):
        """Test can_accept returns False for wrong email."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            status=InviteStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        assert invite.can_accept("wrong@example.com") is False

    def test_invite_can_accept_email_case_insensitive(self):
        """Test email matching is case-insensitive."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="Test@Example.COM",
            workspace_id="WB1",
            role_id=str(uuid4()),
            status=InviteStatus.PENDING,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        assert invite.can_accept("test@example.com") is True

    def test_invite_can_accept_expired(self):
        """Test can_accept returns False for expired invite."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            status=InviteStatus.PENDING,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )

        assert invite.can_accept("test@example.com") is False

    def test_invite_can_accept_already_accepted(self):
        """Test can_accept returns False for already accepted invite."""
        invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            status=InviteStatus.ACCEPTED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )

        assert invite.can_accept("test@example.com") is False

    def test_invite_status_enum(self):
        """Test all invite status enum values."""
        pending_invite = Invite(
            inviter_id=str(uuid4()),
            invitee_email="test@example.com",
            workspace_id="WB1",
            role_id=str(uuid4()),
            status=InviteStatus.PENDING,
        )

        assert pending_invite.status == InviteStatus.PENDING
        assert pending_invite.status == "pending"

        # Test status transitions
        pending_invite.status = InviteStatus.ACCEPTED
        assert pending_invite.status == InviteStatus.ACCEPTED

        pending_invite.status = InviteStatus.EXPIRED
        assert pending_invite.status == InviteStatus.EXPIRED

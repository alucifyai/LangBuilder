"""Unit tests for EmailService.

Tests cover:
- Email sending (with mocked SMTP)
- Template rendering
- Delivery logging
- Error handling
- Configuration validation
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi_mail import MessageSchema
from jinja2 import TemplateNotFound
from langflow.services.database.models.email.model import (
    EmailDeliveryStatus,
)
from langflow.services.email.config import EmailSettings
from langflow.services.email.service import EmailService
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Fixtures


@pytest.fixture
def email_settings():
    """Email settings fixture for testing."""
    return EmailSettings(
        SMTP_HOST="smtp.test.com",
        SMTP_PORT=587,
        SMTP_USER="test@example.com",
        SMTP_PASSWORD="test_password",  # noqa: S106
        FROM_EMAIL="noreply@test.com",
        FROM_NAME="Test Service",
        ENABLED=True,
        USE_TLS=True,
        USE_SSL=False,
    )


@pytest.fixture
def disabled_email_settings():
    """Disabled email settings fixture."""
    return EmailSettings(
        SMTP_HOST="smtp.test.com",
        SMTP_PORT=587,
        FROM_EMAIL="noreply@test.com",
        ENABLED=False,
    )


@pytest.fixture
def email_service(email_settings):
    """EmailService fixture with mocked FastMail."""
    with patch("langflow.services.email.service.FastMail"):
        service = EmailService(email_settings)
        service.fm = AsyncMock()  # Mock the FastMail instance
        yield service


@pytest.fixture
def disabled_email_service(disabled_email_settings):
    """Disabled EmailService fixture."""
    return EmailService(disabled_email_settings)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Database session fixture for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


# Configuration Tests


def test_email_settings_is_configured(email_settings):
    """Test EmailSettings.is_configured() method."""
    assert email_settings.is_configured() is True


def test_email_settings_not_configured():
    """Test EmailSettings when credentials are missing."""
    settings = EmailSettings(
        SMTP_HOST="smtp.test.com",
        SMTP_PORT=587,
        FROM_EMAIL="noreply@test.com",
        ENABLED=True,
    )
    assert settings.is_configured() is False


def test_email_settings_get_connection_info(email_settings):
    """Test EmailSettings.get_connection_info() returns correct info."""
    info = email_settings.get_connection_info()
    assert info["smtp_host"] == "smtp.test.com"
    assert info["smtp_port"] == 587
    assert info["smtp_user"] == "test@example.com"
    assert info["from_email"] == "noreply@test.com"
    assert info["configured"] is True
    # Password should not be in the info dict
    assert "password" not in str(info).lower() or "test_password" not in str(info)


def test_email_service_initialization(email_service):
    """Test EmailService initialization."""
    assert email_service.settings is not None
    assert email_service.fm is not None
    assert email_service.jinja_env is not None


def test_email_service_disabled_initialization(disabled_email_service):
    """Test EmailService initialization when disabled."""
    assert disabled_email_service.fm is None
    assert disabled_email_service.is_enabled() is False


# Email Sending Tests


@pytest.mark.asyncio
async def test_send_invitation_email_success(email_service, session):
    """Test successful invitation email sending."""
    to_email = "user@example.com"
    inviter_name = "Admin User"
    workspace_name = "Test Workspace"
    role_name = "Developer"
    invitation_link = "https://app.com/invite/token123"

    # Mock the send_message method
    email_service.fm.send_message = AsyncMock()

    # Send email
    log_entry = await email_service.send_invitation_email(
        to_email=to_email,
        inviter_name=inviter_name,
        workspace_name=workspace_name,
        role_name=role_name,
        invitation_link=invitation_link,
        session=session,
    )

    # Verify email was sent
    email_service.fm.send_message.assert_called_once()
    call_args = email_service.fm.send_message.call_args[0][0]
    assert isinstance(call_args, MessageSchema)
    assert call_args.recipients == [to_email]
    assert workspace_name in call_args.subject
    assert call_args.subtype.value == "html"

    # Verify delivery log
    assert log_entry.recipient == to_email
    assert log_entry.delivery_status == EmailDeliveryStatus.SENT.value
    assert log_entry.template_name == "invitation.html"
    assert log_entry.error_message is None


@pytest.mark.asyncio
async def test_send_role_assignment_notification_success(email_service, session):
    """Test successful role assignment notification sending."""
    to_email = "user@example.com"
    user_name = "John Doe"
    role_name = "Admin"
    resource_name = "Test Project"
    granted_by = "Super Admin"

    # Mock the send_message method
    email_service.fm.send_message = AsyncMock()

    # Send email
    log_entry = await email_service.send_role_assignment_notification(
        to_email=to_email,
        user_name=user_name,
        role_name=role_name,
        resource_name=resource_name,
        granted_by=granted_by,
        session=session,
    )

    # Verify email was sent
    email_service.fm.send_message.assert_called_once()
    call_args = email_service.fm.send_message.call_args[0][0]
    assert isinstance(call_args, MessageSchema)
    assert call_args.recipients == [to_email]
    assert role_name in call_args.subject

    # Verify delivery log
    assert log_entry.recipient == to_email
    assert log_entry.delivery_status == EmailDeliveryStatus.SENT.value
    assert log_entry.template_name == "role_assigned.html"
    assert log_entry.error_message is None


@pytest.mark.asyncio
async def test_send_email_when_disabled(disabled_email_service, session):
    """Test email sending when service is disabled."""
    to_email = "user@example.com"
    inviter_name = "Admin"
    workspace_name = "Test Workspace"
    role_name = "Developer"
    invitation_link = "https://app.com/invite/token123"

    # Send email (should not actually send)
    log_entry = await disabled_email_service.send_invitation_email(
        to_email=to_email,
        inviter_name=inviter_name,
        workspace_name=workspace_name,
        role_name=role_name,
        invitation_link=invitation_link,
        session=session,
    )

    # Verify delivery log shows failure
    assert log_entry.recipient == to_email
    assert log_entry.delivery_status == EmailDeliveryStatus.FAILED.value
    assert "not enabled" in log_entry.error_message.lower()


@pytest.mark.asyncio
async def test_send_email_smtp_failure(email_service, session):
    """Test email sending with SMTP failure."""
    to_email = "user@example.com"
    inviter_name = "Admin"
    workspace_name = "Test Workspace"
    role_name = "Developer"
    invitation_link = "https://app.com/invite/token123"

    # Mock SMTP failure
    email_service.fm.send_message = AsyncMock(side_effect=Exception("SMTP connection failed"))

    # Send email (should raise exception)
    with pytest.raises(Exception, match="SMTP connection failed"):
        await email_service.send_invitation_email(
            to_email=to_email,
            inviter_name=inviter_name,
            workspace_name=workspace_name,
            role_name=role_name,
            invitation_link=invitation_link,
            session=session,
        )


# Template Rendering Tests


def test_render_invitation_template(email_service):
    """Test invitation template rendering."""
    html = email_service._render_template(
        "invitation.html",
        inviter_name="Admin User",
        workspace_name="Test Workspace",
        role_name="Developer",
        invitation_link="https://app.com/invite/token123",
    )

    assert "Admin User" in html
    assert "Test Workspace" in html
    assert "Developer" in html
    assert "https://app.com/invite/token123" in html
    assert "<!DOCTYPE html>" in html


def test_render_role_assigned_template(email_service):
    """Test role assigned template rendering."""
    html = email_service._render_template(
        "role_assigned.html",
        user_name="John Doe",
        role_name="Admin",
        resource_name="Test Project",
        granted_by="Super Admin",
    )

    assert "John Doe" in html
    assert "Admin" in html
    assert "Test Project" in html
    assert "Super Admin" in html
    assert "<!DOCTYPE html>" in html


def test_render_template_not_found(email_service):
    """Test template rendering with missing template."""
    with pytest.raises(TemplateNotFound):
        email_service._render_template("nonexistent.html", foo="bar")


# Delivery Logging Tests


@pytest.mark.asyncio
async def test_log_delivery_success(email_service, session):
    """Test delivery logging to database."""
    log_entry = await email_service._log_delivery(
        recipient="user@example.com",
        subject="Test Subject",
        template_name="test_template.html",
        delivery_status=EmailDeliveryStatus.SENT,
        error_message=None,
        context_data={"key": "value"},
        session=session,
    )

    assert log_entry.recipient == "user@example.com"
    assert log_entry.subject == "Test Subject"
    assert log_entry.template_name == "test_template.html"
    assert log_entry.delivery_status == EmailDeliveryStatus.SENT.value
    assert log_entry.error_message is None
    assert '{"key": "value"}' in log_entry.context_data
    assert isinstance(log_entry.sent_at, datetime)
    assert log_entry.retry_count == 0


@pytest.mark.asyncio
async def test_log_delivery_with_error(email_service, session):
    """Test delivery logging with error message."""
    error_msg = "SMTP connection timeout"
    log_entry = await email_service._log_delivery(
        recipient="user@example.com",
        subject="Test Subject",
        template_name="test_template.html",
        delivery_status=EmailDeliveryStatus.FAILED,
        error_message=error_msg,
        context_data=None,
        session=session,
    )

    assert log_entry.delivery_status == EmailDeliveryStatus.FAILED.value
    assert log_entry.error_message == error_msg
    assert log_entry.context_data is None


@pytest.mark.asyncio
async def test_log_delivery_without_session(email_service):
    """Test delivery logging without database session."""
    log_entry = await email_service._log_delivery(
        recipient="user@example.com",
        subject="Test Subject",
        template_name="test_template.html",
        delivery_status=EmailDeliveryStatus.SENT,
        session=None,
    )

    # Should still create log entry object
    assert log_entry.recipient == "user@example.com"
    assert log_entry.delivery_status == EmailDeliveryStatus.SENT.value


# Integration Tests


@pytest.mark.asyncio
async def test_end_to_end_invitation_flow(email_service, session):
    """Test complete invitation email flow."""
    to_email = "newuser@example.com"
    inviter_name = "Manager"
    workspace_name = "Engineering Team"
    role_name = "Viewer"
    invitation_link = "https://app.com/invite/abc123"

    # Mock FastMail
    email_service.fm.send_message = AsyncMock()

    # Send invitation
    log_entry = await email_service.send_invitation_email(
        to_email=to_email,
        inviter_name=inviter_name,
        workspace_name=workspace_name,
        role_name=role_name,
        invitation_link=invitation_link,
        session=session,
    )

    # Verify entire flow
    assert email_service.fm.send_message.called
    assert log_entry.id is not None
    assert log_entry.recipient == to_email
    assert log_entry.delivery_status == EmailDeliveryStatus.SENT.value

    # Verify context_data is stored as JSON
    import json

    context = json.loads(log_entry.context_data)
    assert context["inviter_name"] == inviter_name
    assert context["workspace_name"] == workspace_name
    assert context["role_name"] == role_name


@pytest.mark.asyncio
async def test_end_to_end_role_assignment_flow(email_service, session):
    """Test complete role assignment notification flow."""
    to_email = "user@example.com"
    user_name = "Alice Smith"
    role_name = "Editor"
    resource_name = "Marketing Workspace"
    granted_by = "Admin"

    # Mock FastMail
    email_service.fm.send_message = AsyncMock()

    # Send notification
    log_entry = await email_service.send_role_assignment_notification(
        to_email=to_email,
        user_name=user_name,
        role_name=role_name,
        resource_name=resource_name,
        granted_by=granted_by,
        session=session,
    )

    # Verify entire flow
    assert email_service.fm.send_message.called
    assert log_entry.id is not None
    assert log_entry.recipient == to_email
    assert log_entry.delivery_status == EmailDeliveryStatus.SENT.value

    # Verify context_data
    import json

    context = json.loads(log_entry.context_data)
    assert context["user_name"] == user_name
    assert context["role_name"] == role_name
    assert context["resource_name"] == resource_name
    assert context["granted_by"] == granted_by


def test_email_service_is_enabled(email_service):
    """Test is_enabled() method."""
    assert email_service.is_enabled() is True


def test_email_service_is_disabled(disabled_email_service):
    """Test is_enabled() when disabled."""
    assert disabled_email_service.is_enabled() is False


def test_email_service_not_configured():
    """Test EmailService when SMTP not configured."""
    settings = EmailSettings(
        SMTP_HOST="smtp.test.com",
        SMTP_PORT=587,
        FROM_EMAIL="noreply@test.com",
        ENABLED=True,
    )
    service = EmailService(settings)
    assert service.fm is None
    assert service.is_enabled() is False

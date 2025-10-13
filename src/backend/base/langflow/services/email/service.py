"""Email service implementation using FastAPI-Mail.

This service provides email notification capabilities for invitations,
role assignments, and audit alerts.

Logic Nodes (Task 3.10):
- email_service → Core email sending service
- template_renderer → Jinja2 HTML template rendering
- delivery_tracker → Email delivery status monitoring

PRD References:
- Story 2.1 @AC4: Email notifications for invitation workflow
- Story 3.4 @AC6: Email notifications for role assignments

Usage:
    email_service = EmailService(settings)
    await email_service.send_invitation_email(
        to_email="user@example.com",
        inviter_name="Admin",
        workspace_name="My Workspace",
        role_name="Developer",
        invitation_link="https://app.com/invite/token123"
    )
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from langflow.services.base import Service
from langflow.services.database.models.email.model import (
    EmailDeliveryLog,
    EmailDeliveryStatus,
)
from langflow.services.email.config import EmailSettings


class EmailService(Service):
    """Email service for sending notifications.

    Handles email template rendering, delivery, and tracking for the RBAC system.

    Attributes:
        settings: Email configuration settings
        fm: FastMail instance for sending emails
        jinja_env: Jinja2 environment for template rendering
    """

    name = "email_service"

    def __init__(self, settings: EmailSettings):
        """Initialize email service.

        Args:
            settings: Email configuration settings
        """
        self.settings = settings

        # Initialize FastMail only if configured
        if settings.is_configured():
            self.conf = ConnectionConfig(
                MAIL_USERNAME=settings.SMTP_USER or "",
                MAIL_PASSWORD=settings.SMTP_PASSWORD or "",
                MAIL_FROM=settings.FROM_EMAIL,
                MAIL_PORT=settings.SMTP_PORT,
                MAIL_SERVER=settings.SMTP_HOST,
                MAIL_STARTTLS=settings.USE_TLS,
                MAIL_SSL_TLS=settings.USE_SSL,
                USE_CREDENTIALS=bool(settings.SMTP_USER and settings.SMTP_PASSWORD),
                VALIDATE_CERTS=settings.VALIDATE_CERTS,
                MAIL_FROM_NAME=settings.FROM_NAME,
                TIMEOUT=settings.TIMEOUT,
            )
            self.fm = FastMail(self.conf)
            logger.info(
                f"Email service initialized: {settings.get_connection_info()}"
            )
        else:
            self.fm = None
            logger.warning(
                "Email service not configured (missing SMTP credentials). "
                "Emails will not be sent."
            )

        # Setup Jinja2 for template rendering
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True, parents=True)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,  # Security: auto-escape HTML
        )

    def is_enabled(self) -> bool:
        """Check if email service is enabled and configured.

        Returns:
            True if email service can send emails, False otherwise
        """
        return self.settings.ENABLED and self.settings.is_configured()

    async def send_invitation_email(
        self,
        to_email: str,
        inviter_name: str,
        workspace_name: str,
        role_name: str,
        invitation_link: str,
        session: AsyncSession | None = None,
    ) -> EmailDeliveryLog:
        """Send workspace invitation email.

        Args:
            to_email: Recipient email address
            inviter_name: Name of user who sent invitation
            workspace_name: Name of workspace
            role_name: Role being granted
            invitation_link: URL to accept invitation
            session: Database session for logging (optional)

        Returns:
            EmailDeliveryLog record

        Raises:
            Exception: If email send fails
        """
        template_name = "invitation.html"
        subject = f"Invitation to join {workspace_name} on LangBuilder"

        try:
            # Render HTML template
            html = self._render_template(
                template_name,
                inviter_name=inviter_name,
                workspace_name=workspace_name,
                role_name=role_name,
                invitation_link=invitation_link,
            )

            # Send email
            if self.is_enabled():
                await self._send_email(
                    to_email=to_email,
                    subject=subject,
                    html_body=html,
                )
                delivery_status = EmailDeliveryStatus.SENT
                error_message = None
                logger.info(
                    f"Invitation email sent to {to_email} for workspace '{workspace_name}'"
                )
            else:
                delivery_status = EmailDeliveryStatus.FAILED
                error_message = "Email service not enabled or configured"
                logger.warning(
                    f"Email service disabled. Would send invitation to {to_email}"
                )

        except Exception as e:
            delivery_status = EmailDeliveryStatus.FAILED
            error_message = str(e)
            logger.error(
                f"Failed to send invitation email to {to_email}: {e}"
            )
            # Re-raise to let caller handle
            raise

        finally:
            # Log delivery (always, even if failed)
            log_entry = await self._log_delivery(
                recipient=to_email,
                subject=subject,
                template_name=template_name,
                delivery_status=delivery_status,
                error_message=error_message,
                context_data={
                    "inviter_name": inviter_name,
                    "workspace_name": workspace_name,
                    "role_name": role_name,
                },
                session=session,
            )

        return log_entry

    async def send_role_assignment_notification(
        self,
        to_email: str,
        user_name: str,
        role_name: str,
        resource_name: str,
        granted_by: str,
        session: AsyncSession | None = None,
    ) -> EmailDeliveryLog:
        """Send role assignment notification email.

        Args:
            to_email: Recipient email address
            user_name: Name of user receiving role
            role_name: Role being assigned
            resource_name: Name of resource (workspace, project, etc.)
            granted_by: Name of user who granted the role
            session: Database session for logging (optional)

        Returns:
            EmailDeliveryLog record

        Raises:
            Exception: If email send fails
        """
        template_name = "role_assigned.html"
        subject = f"New role assigned: {role_name}"

        try:
            # Render HTML template
            html = self._render_template(
                template_name,
                user_name=user_name,
                role_name=role_name,
                resource_name=resource_name,
                granted_by=granted_by,
            )

            # Send email
            if self.is_enabled():
                await self._send_email(
                    to_email=to_email,
                    subject=subject,
                    html_body=html,
                )
                delivery_status = EmailDeliveryStatus.SENT
                error_message = None
                logger.info(
                    f"Role assignment email sent to {to_email} for role '{role_name}'"
                )
            else:
                delivery_status = EmailDeliveryStatus.FAILED
                error_message = "Email service not enabled or configured"
                logger.warning(
                    f"Email service disabled. Would send role notification to {to_email}"
                )

        except Exception as e:
            delivery_status = EmailDeliveryStatus.FAILED
            error_message = str(e)
            logger.error(
                f"Failed to send role assignment email to {to_email}: {e}"
            )
            # Re-raise to let caller handle
            raise

        finally:
            # Log delivery (always, even if failed)
            log_entry = await self._log_delivery(
                recipient=to_email,
                subject=subject,
                template_name=template_name,
                delivery_status=delivery_status,
                error_message=error_message,
                context_data={
                    "user_name": user_name,
                    "role_name": role_name,
                    "resource_name": resource_name,
                    "granted_by": granted_by,
                },
                session=session,
            )

        return log_entry

    def _render_template(self, template_name: str, **context: Any) -> str:
        """Render email template with context.

        Args:
            template_name: Name of template file
            **context: Template context variables

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except TemplateNotFound:
            logger.error(f"Email template not found: {template_name}")
            raise

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> None:
        """Send email using FastMail.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body

        Raises:
            RuntimeError: If email service not configured
        """
        if not self.fm:
            msg = "Email service not configured"
            raise RuntimeError(msg)

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_body,
            subtype="html",
        )

        await self.fm.send_message(message)

    async def _log_delivery(
        self,
        recipient: str,
        subject: str,
        template_name: str,
        delivery_status: EmailDeliveryStatus,
        error_message: str | None = None,
        context_data: dict[str, Any] | None = None,
        session: AsyncSession | None = None,
    ) -> EmailDeliveryLog:
        """Log email delivery to database.

        Args:
            recipient: Recipient email address
            subject: Email subject
            template_name: Template name used
            delivery_status: Delivery status
            error_message: Error message if failed
            context_data: Additional context
            session: Database session (optional)

        Returns:
            EmailDeliveryLog record
        """
        log_entry = EmailDeliveryLog(
            recipient=recipient,
            subject=subject,
            template_name=template_name,
            delivery_status=delivery_status.value,
            error_message=error_message,
            context_data=json.dumps(context_data) if context_data else None,
            sent_at=datetime.now(timezone.utc),
        )

        if session:
            try:
                session.add(log_entry)
                await session.commit()
                await session.refresh(log_entry)
            except Exception as e:
                logger.error(f"Failed to log email delivery: {e}")
                await session.rollback()

        return log_entry

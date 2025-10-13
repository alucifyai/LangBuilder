"""Email delivery log model for tracking sent emails.

This model provides an audit trail for all emails sent by the system,
including delivery status, timestamps, and error information.

Schema Entity: EmailDeliveryLog (Task 3.10)

AppGraph Impact:
- delivery_tracker → Logs email delivery status
- email_service → Creates delivery log entries
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

import sqlmodel
from sqlmodel import Column, Field, SQLModel


class EmailDeliveryStatus(str, Enum):
    """Email delivery status enumeration.

    Attributes:
        PENDING: Email queued but not yet sent
        SENT: Email successfully sent to SMTP server
        DELIVERED: Email confirmed delivered to recipient
        FAILED: Email send failed (transient or permanent)
        BOUNCED: Email bounced back from recipient server
        REJECTED: Email rejected by recipient server (spam, invalid address)
    """

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"


class EmailDeliveryLog(SQLModel, table=True):
    """Email delivery log for audit trail.

    Tracks all emails sent by the system including delivery status,
    errors, and metadata for troubleshooting and compliance.

    Attributes:
        id: Unique identifier (UUID)
        recipient: Recipient email address
        subject: Email subject line
        template_name: Name of the email template used
        sent_at: Timestamp when email was sent
        delivery_status: Current delivery status (enum)
        error_message: Error message if delivery failed
        retry_count: Number of retry attempts
        context_data: Additional context (JSON)
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """

    __tablename__ = "email_delivery_logs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    recipient: str = Field(index=True, max_length=255, description="Recipient email address")
    subject: str = Field(max_length=500, description="Email subject line")
    template_name: str = Field(max_length=100, description="Template used for email")
    sent_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when email was sent",
    )
    delivery_status: str = Field(
        default=EmailDeliveryStatus.PENDING.value,
        max_length=20,
        index=True,
        description="Current delivery status",
    )
    error_message: str | None = Field(
        default=None, max_length=1000, description="Error message if delivery failed"
    )
    retry_count: int = Field(default=0, description="Number of retry attempts")
    context_data: str | None = Field(
        default=None,
        sa_column=Column("context_data", sqlmodel.TEXT, nullable=True),  # type: ignore[arg-type]
        description="Additional context as JSON string",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Record last update timestamp",
    )

    def __repr__(self) -> str:
        """String representation of email delivery log."""
        return (
            f"<EmailDeliveryLog(id={self.id}, recipient={self.recipient}, "
            f"status={self.delivery_status}, sent_at={self.sent_at})>"
        )

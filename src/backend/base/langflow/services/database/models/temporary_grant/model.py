"""
Temporary Grant Model

Extension to the Grant model for time-limited role assignments.
Tracks expiration, auto-revocation, and notification requirements.
"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, SQLModel, Text


class TemporaryGrant(SQLModel, table=True):
    """
    Temporary Grant Model

    Tracks time-limited role assignments that automatically expire.
    Can be used for temporary access, trial periods, or time-boxed permissions.
    """

    __tablename__ = "temporary_grant"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Core grant reference
    grant_id: str = Field(
        foreign_key="grant.id",
        index=True,
        description="Reference to the base grant",
    )

    # Temporal bounds
    starts_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="When the grant becomes active",
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="When the grant expires",
    )

    # Expiration handling
    auto_revoke: bool = Field(
        default=True,
        description="Automatically revoke grant on expiration",
    )
    notify_before_expiry: bool = Field(
        default=True,
        description="Send notification before expiration",
    )
    notification_hours: int = Field(
        default=24,
        description="Hours before expiry to send notification",
    )

    # Status tracking
    is_expired: bool = Field(
        default=False,
        index=True,
        description="Whether grant has expired",
    )
    expired_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When the grant was actually expired/revoked",
    )
    notified_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True)),
        description="When expiration notification was sent",
    )

    # Extension tracking
    extension_count: int = Field(
        default=0,
        description="Number of times grant has been extended",
    )
    max_extensions: int | None = Field(
        None,
        description="Maximum allowed extensions (null = unlimited)",
    )
    extended_by: str | None = Field(
        None,
        description="User ID who last extended the grant",
    )

    # Metadata
    reason: str | None = Field(
        None,
        sa_column=Column(Text),
        description="Reason for temporary grant",
    )
    created_by: str = Field(
        index=True,
        description="User who created the temporary grant",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

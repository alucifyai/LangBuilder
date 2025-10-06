"""
User Invite Model
"""

import enum
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from sqlmodel import Column, DateTime, Field, SQLModel
from sqlalchemy import JSON


class InviteStatus(str, enum.Enum):
    """Invite status enum"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class UserInvite(SQLModel, table=True):
    """
    User Invite Model

    Represents an invitation for a new user to join the platform.
    """

    __tablename__ = "user_invite"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )

    # Invitee information
    email: str = Field(index=True, unique=True, description="Invitee email address")

    # Inviter information
    invited_by: str = Field(index=True, description="User ID who sent the invite")
    organization_id: str = Field(index=True, description="Organization ID")

    # Invite token
    invite_token: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        unique=True,
        index=True,
        description="Unique invite token",
    )

    # Pre-assigned roles
    role_ids: list[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False),
        description="List of role IDs to assign upon acceptance",
    )

    # Status
    status: InviteStatus = Field(
        default=InviteStatus.PENDING,
        index=True,
        description="Invite status",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
        description="Invite expiration time",
    )

    # Acceptance/Revocation
    accepted_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When invite was accepted",
    )
    accepted_by_user_id: str | None = Field(
        None,
        description="User ID created upon acceptance",
    )
    revoked_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When invite was revoked",
    )
    revoked_by: str | None = Field(None, description="User ID who revoked the invite")
    revocation_reason: str | None = Field(None, description="Reason for revocation")

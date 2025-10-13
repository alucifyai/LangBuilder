"""Invitation model for user invitation workflow."""

import re
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.user.model import User
    from langflow.services.database.models.workspace.model import Workspace


class InvitationStatus(str, Enum):
    """Invitation status values."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Invitation(SQLModel, table=True):  # type: ignore[call-arg]
    """Invitation model for user invitation workflow.

    Allows workspace owners/admins to invite users via email with a secure token.
    Invitations expire after a configurable period (default 7 days).
    """

    __tablename__ = "invitation"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    workspace_id: UUID = Field(foreign_key="workspace.id", nullable=False, index=True)
    invited_by_user_id: UUID = Field(foreign_key="user.id", nullable=False)

    # Invitee details
    email: str = Field(max_length=255, nullable=False, index=True)
    invited_user_id: UUID | None = Field(foreign_key="user.id", nullable=True)  # Set when user accepts

    # Role and scope for invitation
    role_id: UUID | None = Field(foreign_key="role.id", nullable=True)
    scope_type: str = Field(default="workspace", max_length=50)  # workspace, project, etc.
    scope_id: UUID | None = Field(nullable=True)

    # Status and expiration
    status: str = Field(default=InvitationStatus.PENDING.value, index=True, max_length=50)
    expires_at: datetime = Field(nullable=False)  # Default: created_at + 7 days

    # Metadata
    message: str | None = Field(default=None, max_length=1000)
    token: str = Field(max_length=255, unique=True, nullable=False, index=True)  # Secure random token

    # Audit fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    accepted_at: datetime | None = Field(default=None, nullable=True)

    # Relationships
    workspace: "Workspace" = Relationship()
    invited_by: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[Invitation.invited_by_user_id]",
            "primaryjoin": "Invitation.invited_by_user_id == User.id",
        }
    )
    role: "Role" = Relationship()

    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure random token for the invitation."""
        return secrets.token_urlsafe(32)


class InvitationRead(SQLModel):
    """Schema for reading invitation data."""

    id: UUID
    workspace_id: UUID
    invited_by_user_id: UUID
    email: str
    invited_user_id: UUID | None
    role_id: UUID | None
    scope_type: str
    scope_id: UUID | None
    status: str
    expires_at: datetime
    message: str | None
    created_at: datetime
    updated_at: datetime
    accepted_at: datetime | None


class InvitationCreate(SQLModel):
    """Schema for creating a new invitation."""

    email: str = Field(max_length=255, min_length=3)
    role_id: UUID | None = None
    scope_type: str = Field(default="workspace")
    scope_id: UUID | None = None
    message: str | None = Field(default=None, max_length=1000)
    expires_in_days: int = Field(default=7, ge=1, le=30)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        pattern = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(pattern, v):
            msg = f"Invalid email format: {v}"
            raise ValueError(msg)
        return v

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        """Validate scope type is one of the allowed values."""
        allowed = {"workspace", "project", "environment", "flow"}
        if v not in allowed:
            msg = f"scope_type must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v

    def get_expires_at(self) -> datetime:
        """Calculate expiration datetime based on expires_in_days."""
        return datetime.now(timezone.utc) + timedelta(days=self.expires_in_days)


class InvitationAccept(SQLModel):
    """Schema for accepting an invitation."""

    token: str = Field(max_length=255, min_length=1)

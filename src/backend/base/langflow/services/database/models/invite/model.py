from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class InviteStatus(str, Enum):
    """Status of an invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"


class Invite(SQLModel, table=True):  # type: ignore[call-arg]
    """
    User invitation to workspace/project with role assignment.

    Represents: "User X invites email Y to Workspace Z with Role R"
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Inviter (who sent the invite)
    inviter_id: UUIDstr = Field(index=True)

    # Invitee (who is being invited)
    invitee_email: str = Field(index=True)

    # Where they're being invited to
    workspace_id: str = Field(index=True)

    # What role they'll get
    role_id: UUIDstr = Field(index=True)

    # Status and timing
    status: InviteStatus = Field(default=InviteStatus.PENDING, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)
    )  # 7 days to accept

    def is_expired(self) -> bool:
        """Check if invite has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    def can_accept(self, user_email: str) -> bool:
        """Check if invite can be accepted by given email."""
        return (
            self.status == InviteStatus.PENDING
            and not self.is_expired()
            and self.invitee_email.lower() == user_email.lower()
        )

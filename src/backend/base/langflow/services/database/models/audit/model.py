from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class AuditAction(str, Enum):
    """Audit action types."""

    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    GRANT_CREATED = "grant_created"
    GRANT_REVOKED = "grant_revoked"
    PERMISSION_CREATED = "permission_created"
    INVITE_CREATED = "invite_created"
    INVITE_ACCEPTED = "invite_accepted"


class AuditLog(SQLModel, table=True):  # type: ignore[call-arg]
    """
    Immutable audit log for tracking RBAC changes.

    Audit logs are append-only and never updated or deleted.
    They provide a complete history of role and grant changes.
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
        description="When the action occurred",
    )
    actor_id: UUIDstr = Field(
        index=True,
        description="User who performed the action",
    )
    action: AuditAction = Field(
        index=True,
        description="Type of action performed",
    )
    resource_type: str = Field(
        index=True,
        description="Type of resource affected (role, grant, permission, etc.)",
    )
    resource_id: str = Field(
        description="ID of the affected resource",
    )
    before_state: dict[str, Any] | None = Field(
        sa_column=Column(JSON, nullable=True),
        default=None,
        description="State before the change (for updates/deletes)",
    )
    after_state: dict[str, Any] | None = Field(
        sa_column=Column(JSON, nullable=True),
        default=None,
        description="State after the change (for creates/updates)",
    )
    metadata: dict[str, Any] | None = Field(
        sa_column=Column(JSON, nullable=True),
        default=None,
        description="Additional context about the action",
    )

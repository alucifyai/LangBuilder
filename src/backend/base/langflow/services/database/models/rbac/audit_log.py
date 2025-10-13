"""AuditLog model for RBAC system."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class AuditLog(SQLModel, table=True):  # type: ignore[call-arg]
    """Audit log model for immutable logging of RBAC events.

    Records all RBAC-related actions including role assignments, permission changes,
    access attempts, and configuration changes for compliance and security auditing.
    """

    __tablename__ = "audit_log"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Event identification
    event_type: str = Field(max_length=100, nullable=False, index=True)  # e.g., "role.assign", "permission.check"
    action: str = Field(max_length=100, nullable=False, index=True)  # e.g., "create", "read", "update", "delete"
    resource_type: str = Field(max_length=100, nullable=False, index=True)  # e.g., "role", "user", "flow"
    resource_id: UUID | None = Field(default=None, nullable=True, index=True)

    # Actor information
    actor_type: str = Field(max_length=50, nullable=False)  # "user", "service_account", "system"
    actor_id: UUID | None = Field(default=None, nullable=True, index=True)

    # Audit metadata
    status: str = Field(max_length=50, nullable=False, index=True)  # "success", "failure", "denied"
    details: dict[str, Any] | None = Field(sa_column=Column(JSON, default=dict, nullable=True))  # Additional context

    # IP and client information
    ip_address: str | None = Field(default=None, max_length=45)  # IPv4 or IPv6
    user_agent: str | None = Field(default=None, max_length=500)

    # Timestamp (immutable - no updated_at)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False, index=True)


class AuditLogRead(SQLModel):
    """Schema for reading audit log data."""

    id: UUID
    event_type: str
    action: str
    resource_type: str
    resource_id: UUID | None
    actor_type: str
    actor_id: UUID | None
    status: str
    details: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

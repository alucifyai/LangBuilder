"""AuditLog model for RBAC system.

Implements Story 5.1 - Log All RBAC Changes and
Story 5.2 - Export Compliance Report from PRD.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class AuditAction(str, Enum):
    """Types of auditable actions in the RBAC system."""

    # Permission checks
    PERMISSION_CHECK_ALLOWED = "permission_check_allowed"
    PERMISSION_CHECK_DENIED = "permission_check_denied"

    # Role management
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"

    # Grant management
    GRANT_CREATED = "grant_created"
    GRANT_UPDATED = "grant_updated"
    GRANT_REVOKED = "grant_revoked"

    # Group management
    GROUP_CREATED = "group_created"
    GROUP_UPDATED = "group_updated"
    GROUP_DELETED = "group_deleted"
    USER_ADDED_TO_GROUP = "user_added_to_group"
    USER_REMOVED_FROM_GROUP = "user_removed_from_group"

    # Service account management
    SERVICE_ACCOUNT_CREATED = "service_account_created"
    SERVICE_ACCOUNT_UPDATED = "service_account_updated"
    SERVICE_ACCOUNT_DELETED = "service_account_deleted"

    # SSO/SCIM events
    SSO_LOGIN_SUCCESS = "sso_login_success"
    SSO_LOGIN_FAILURE = "sso_login_failure"
    SCIM_USER_PROVISIONED = "scim_user_provisioned"
    SCIM_USER_DEPROVISIONED = "scim_user_deprovisioned"
    SCIM_GROUP_SYNCED = "scim_group_synced"

    # Break-glass access
    BREAK_GLASS_ACCESS = "break_glass_access"


class AuditLogBase(SQLModel):
    """Base audit log model."""

    action: AuditAction = Field(index=True, description="Type of action performed")
    actor_type: str = Field(description="Type of actor: 'user', 'service_account', 'system'")
    actor_id: str | None = Field(default=None, index=True, nullable=True, description="ID of the actor (user/SA)")
    actor_name: str | None = Field(default=None, description="Name of the actor for human readability")

    # Target of the action
    resource_type: str | None = Field(default=None, index=True, nullable=True, description="Type of resource affected")
    resource_id: str | None = Field(
        default=None, index=True, nullable=True, description="ID of the resource affected"
    )

    # Details
    details: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional details (before/after state, reason, etc.)",
    )
    result: str | None = Field(
        default=None, description="Result of the action: 'success', 'failure', 'denied'"
    )
    reason: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Reason for denial or failure",
    )

    # Context
    ip_address: str | None = Field(default=None, description="IP address of the actor")
    user_agent: str | None = Field(default=None, sa_column=Column(Text), description="User agent string")


class AuditLog(AuditLogBase, table=True):  # type: ignore[call-arg]
    """Immutable audit log table for RBAC events.

    PRD Story 5.1 @AC1: Log role assignment with actor, subject, role, scope, and timestamp
    PRD NFR 5.5: Immutable audit logs (WORM storage)

    Note: This table should be append-only. No updates or deletes allowed.
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    timestamp: datetime = Field(
        default_factory=utc_now, index=True, nullable=False, description="When the action occurred"
    )

    # Indexes for efficient querying
    # - timestamp: for time-range queries
    # - action: for filtering by action type
    # - actor_id: for finding all actions by a user/SA
    # - resource_type + resource_id: for finding all actions on a resource


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new audit log entry."""

    pass


class AuditLogRead(AuditLogBase):
    """Schema for reading audit log data in API responses.

    PRD Story 5.2 @AC1: Export user access report
    """

    id: UUIDstr
    timestamp: datetime

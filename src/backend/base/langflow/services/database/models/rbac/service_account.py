"""ServiceAccount model for RBAC system.

Implements Story 2.4 - Manage Service Accounts from PRD.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, Column, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.grant import Grant


def utc_now():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class ServiceAccountBase(SQLModel):
    """Base service account model."""

    name: str = Field(index=True, description="Service account name (e.g., 'ci-bot', 'monitoring-agent')")
    description: str | None = Field(default=None, description="Description of the service account's purpose")
    is_active: bool = Field(default=True, description="Whether the service account is active")
    metadata_: dict | None = Field(
        default=None, sa_column=Column("metadata", JSON), description="Additional metadata"
    )


class ServiceAccount(ServiceAccountBase, table=True):  # type: ignore[call-arg]
    """Service Account table for non-human identities.

    Service accounts are used for automated systems to interact with LangBuilder.

    PRD Story 2.4 @AC1: Create service account with scope and permissions
    - Service accounts receive grants like users
    - Can authenticate using API tokens
    - Permissions are scoped to specific resources
    """

    __tablename__ = "service_account"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)
    created_by: UUIDstr | None = Field(
        default=None, foreign_key="user.id", nullable=True, description="User who created this service account"
    )
    last_used_at: datetime | None = Field(default=None, nullable=True, description="Last authentication time")

    # API key for authentication (similar to user API keys)
    # NOTE: Unlike user API keys, service account API keys are hashed for security
    # See RBAC_PHASE1_AUDIT_REPORT CONCERN #1
    api_key_hash: str | None = Field(
        default=None, index=True, unique=False, nullable=True, description="Hashed API key for service account authentication"
    )

    # HIGH PRIORITY FIX #2: Key prefix for fast lookups
    # Phase 2 Audit Recommendation #2
    # Stores the first 8 characters of the API key for indexed lookup
    # Example: "sa-AbCdEf" from key "sa-AbCdEf123456..."
    key_prefix: str | None = Field(
        default=None, index=True, nullable=True, max_length=16, description="API key prefix for fast lookup"
    )

    # Relationships
    grants: list["Grant"] = Relationship(
        back_populates="service_account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    __table_args__ = (UniqueConstraint("name", name="unique_service_account_name"),)


class ServiceAccountCreate(ServiceAccountBase):
    """Schema for creating a new service account."""

    created_by: UUIDstr | None = None


class ServiceAccountRead(ServiceAccountBase):
    """Schema for reading service account data in API responses."""

    id: UUIDstr
    created_at: datetime
    updated_at: datetime
    created_by: UUIDstr | None
    last_used_at: datetime | None
    api_key: str | None = Field(
        default=None, description="Masked API key (only shown on creation)"
    )  # Will be masked like user API keys


class ServiceAccountUpdate(SQLModel):
    """Schema for updating an existing service account."""

    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
    metadata_: dict | None = Field(default=None, alias="metadata")

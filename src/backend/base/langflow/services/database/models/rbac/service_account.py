from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.workspace import Workspace
    from langflow.services.database.models.rbac.role_assignment import RoleAssignment
    from langflow.services.database.models.api_key.model import ApiKey
    from langflow.services.database.models.user.model import User


class ServiceAccountBase(SQLModel):
    """Base model for service accounts."""
    
    name: str = Field(index=True)
    description: str | None = Field(default=None, sa_column=Column(Text))
    
    # Service account metadata
    service_type: str | None = Field(default="api", index=True)  # api, webhook, integration, bot
    integration_name: str | None = Field(default=None)  # e.g., "github", "slack", "jenkins"
    
    # Token configuration
    token_prefix: str | None = Field(default="sa_")  # Prefix for generated tokens
    max_tokens: int = Field(default=5)  # Maximum number of active tokens
    token_expiry_days: int | None = Field(default=365)  # Token expiry in days
    
    # Security settings
    allowed_ips: list[str] | None = Field(default=[], sa_column=Column(JSON))
    allowed_origins: list[str] | None = Field(default=[], sa_column=Column(JSON))
    rate_limit_per_minute: int | None = Field(default=None)
    
    # Scoping
    default_scope_type: str | None = Field(default="workspace")
    default_scope_id: UUIDstr | None = Field(default=None)
    allowed_permissions: list[str] | None = Field(default=[], sa_column=Column(JSON))
    
    # Status
    is_active: bool = Field(default=True, index=True)
    is_locked: bool = Field(default=False)
    locked_reason: str | None = Field(default=None, sa_column=Column(Text))
    locked_at: datetime | None = Field(default=None)
    
    # Usage tracking
    last_used_at: datetime | None = Field(default=None)
    usage_count: int = Field(default=0)
    
    # Metadata
    metadata: dict | None = Field(default={}, sa_column=Column(JSON))
    tags: list[str] | None = Field(default=[], sa_column=Column(JSON))
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = Field(default=None)
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Service account name cannot be empty")
        if len(v) > 255:
            raise ValueError("Service account name cannot exceed 255 characters")
        # Validate service account name format
        import re
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Service account name must contain only letters, numbers, hyphens, and underscores")
        return v.strip()


class ServiceAccount(ServiceAccountBase, table=True):  # type: ignore[call-arg]
    """Service account table for automated access."""
    
    __tablename__ = "service_account"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    
    # Workspace relationship
    workspace_id: UUIDstr = Field(foreign_key="workspace.id", index=True)
    workspace: "Workspace" = Relationship(back_populates="service_accounts")
    
    # Creator/owner relationship
    created_by_id: UUIDstr = Field(foreign_key="user.id")
    created_by: "User" = Relationship(back_populates="created_service_accounts")
    
    # Relationships
    api_keys: list["ApiKey"] = Relationship(
        back_populates="service_account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    role_assignments: list["RoleAssignment"] = Relationship(
        back_populates="service_account",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="unique_service_account_name_per_workspace"),
    )


class ServiceAccountToken(SQLModel, table=True):  # type: ignore[call-arg]
    """Service account token table for authentication."""
    
    __tablename__ = "service_account_token"
    
    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    service_account_id: UUIDstr = Field(foreign_key="service_account.id", index=True)
    
    # Token details
    name: str = Field(index=True)
    token_hash: str = Field(unique=True, index=True)  # Hashed token value
    token_prefix: str = Field()  # First 8 chars for identification
    
    # Scoping
    scoped_permissions: list[str] | None = Field(default=[], sa_column=Column(JSON))
    scope_type: str | None = Field(default=None)
    scope_id: UUIDstr | None = Field(default=None)
    
    # Security
    allowed_ips: list[str] | None = Field(default=[], sa_column=Column(JSON))
    
    # Status and usage
    is_active: bool = Field(default=True, index=True)
    last_used_at: datetime | None = Field(default=None)
    usage_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
    revoked_by_id: UUIDstr | None = Field(foreign_key="user.id", default=None)
    revoke_reason: str | None = Field(default=None, sa_column=Column(Text))
    
    # Created by
    created_by_id: UUIDstr = Field(foreign_key="user.id")
    
    # Relationships
    service_account: "ServiceAccount" = Relationship()
    created_by: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ServiceAccountToken.created_by_id]",
            "primaryjoin": "ServiceAccountToken.created_by_id == User.id"
        }
    )
    revoked_by: "User" | None = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "[ServiceAccountToken.revoked_by_id]",
            "primaryjoin": "ServiceAccountToken.revoked_by_id == User.id"
        }
    )
    
    # Unique constraints
    __table_args__ = (
        UniqueConstraint("service_account_id", "name", name="unique_token_name_per_service_account"),
    )


class ServiceAccountCreate(SQLModel):
    """Schema for creating a service account."""
    
    name: str
    description: str | None = None
    workspace_id: UUID
    service_type: str | None = "api"
    integration_name: str | None = None
    token_prefix: str | None = "sa_"
    max_tokens: int = 5
    token_expiry_days: int | None = 365
    allowed_ips: list[str] | None = None
    allowed_origins: list[str] | None = None
    rate_limit_per_minute: int | None = None
    default_scope_type: str | None = "workspace"
    default_scope_id: UUID | None = None
    allowed_permissions: list[str] | None = None
    metadata: dict | None = None
    tags: list[str] | None = None
    expires_at: datetime | None = None


class ServiceAccountRead(ServiceAccountBase):
    """Schema for reading service account data."""
    
    id: UUID
    workspace_id: UUID
    created_by_id: UUID
    active_token_count: int | None = None
    total_token_count: int | None = None
    role_count: int | None = None


class ServiceAccountUpdate(SQLModel):
    """Schema for updating service account data."""
    
    name: str | None = None
    description: str | None = None
    service_type: str | None = None
    integration_name: str | None = None
    max_tokens: int | None = None
    token_expiry_days: int | None = None
    allowed_ips: list[str] | None = None
    allowed_origins: list[str] | None = None
    rate_limit_per_minute: int | None = None
    default_scope_type: str | None = None
    default_scope_id: UUID | None = None
    allowed_permissions: list[str] | None = None
    metadata: dict | None = None
    tags: list[str] | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None


class ServiceAccountTokenCreate(SQLModel):
    """Schema for creating a service account token."""
    
    service_account_id: UUID
    name: str
    scoped_permissions: list[str] | None = None
    scope_type: str | None = None
    scope_id: UUID | None = None
    allowed_ips: list[str] | None = None
    expires_at: datetime | None = None


class ServiceAccountTokenRead(SQLModel):
    """Schema for reading service account token data."""
    
    id: UUID
    service_account_id: UUID
    name: str
    token_prefix: str
    scoped_permissions: list[str] | None
    scope_type: str | None
    scope_id: UUID | None
    allowed_ips: list[str] | None
    is_active: bool
    last_used_at: datetime | None
    usage_count: int
    created_at: datetime
    expires_at: datetime | None
    created_by_id: UUID


class ServiceAccountTokenResponse(SQLModel):
    """Response when creating a new token."""
    
    id: UUID
    name: str
    token: str  # Full token (only shown once)
    token_prefix: str
    expires_at: datetime | None
    created_at: datetime
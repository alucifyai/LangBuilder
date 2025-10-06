"""
Service Account and API Token Models
"""

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Column, DateTime, Field, SQLModel, String, Text
from sqlalchemy import JSON


class ServiceAccount(SQLModel, table=True):
    """
    Service Account Model

    Represents a non-human principal (machine account) for API access.
    """

    __tablename__ = "service_account"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )
    name: str = Field(index=True, description="Service account name")
    description: str | None = Field(None, description="Service account description")
    organization_id: str = Field(index=True, description="Organization ID")

    # Ownership
    created_by: str = Field(index=True, description="User ID who created the service account")

    # Status
    is_active: bool = Field(default=True, index=True, description="Is account active")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    last_used_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Last time any token was used",
    )


class TokenScope(str, enum.Enum):
    """API Token Scopes"""

    READ = "read"  # Read-only access
    WRITE = "write"  # Write access
    ADMIN = "admin"  # Admin access
    FLOWS_READ = "flows:read"  # Read flows only
    FLOWS_WRITE = "flows:write"  # Write flows only
    PROJECTS_READ = "projects:read"  # Read projects only
    PROJECTS_WRITE = "projects:write"  # Write projects only


class APIToken(SQLModel, table=True):
    """
    API Token Model

    Represents an API token for service account authentication.
    """

    __tablename__ = "api_token"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        index=True,
    )
    service_account_id: str = Field(index=True, foreign_key="service_account.id")

    # Token details
    name: str = Field(description="Token name/description")
    token_hash: str = Field(unique=True, index=True, description="Hashed token value")
    token_prefix: str = Field(index=True, description="First 8 chars of token for identification")

    # Scopes
    scopes: list[str] = Field(
        default=[],
        sa_column=Column(JSON, nullable=False),
        description="List of token scopes (permission-level)",
    )

    # Resource-level scope restriction (Story 4.2)
    scope_type: str | None = Field(
        None,
        description="Resource scope type (Workspace, Project, Environment, Flow, Component)",
    )
    scope_id: str | None = Field(
        None,
        index=True,
        description="Resource scope ID - token only works within this resource",
    )

    # Expiration
    expires_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Token expiration time (None = never expires)",
    )

    # Usage tracking
    last_used_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="Last time this token was used",
    )
    last_used_ip: str | None = Field(None, description="Last IP address that used this token")
    use_count: int = Field(default=0, description="Number of times token has been used")

    # Status
    is_active: bool = Field(default=True, index=True, description="Is token active")
    revoked_at: datetime | None = Field(
        None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
        description="When token was revoked",
    )
    revoked_by: str | None = Field(None, description="User ID who revoked the token")
    revocation_reason: str | None = Field(None, description="Reason for revocation")

    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_by: str = Field(description="User ID who created the token")

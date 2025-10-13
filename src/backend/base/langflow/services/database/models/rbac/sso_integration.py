"""SSOIntegration model for RBAC system."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class SSOIntegration(SQLModel, table=True):  # type: ignore[call-arg]
    """SSO integration model for configuring identity providers.

    Stores configuration for SSO providers (SAML 2.0, OIDC) and SCIM provisioning.
    """

    __tablename__ = "sso_integration"

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Integration identification
    name: str = Field(max_length=255, nullable=False, unique=True, index=True)
    display_name: str = Field(max_length=255, nullable=False)
    provider_type: str = Field(max_length=50, nullable=False, index=True)  # "saml", "oidc", "scim"

    # Integration status
    is_active: bool = Field(default=True, nullable=False)

    # Provider configuration (encrypted sensitive data)
    config: dict[str, Any] = Field(sa_column=Column(JSON, default=dict, nullable=False))

    # Attribute mapping for user provisioning
    attribute_mapping: dict[str, Any] | None = Field(sa_column=Column(JSON, default=dict, nullable=True))

    # Audit fields
    created_by_user_id: UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)


class SSOIntegrationRead(SQLModel):
    """Schema for reading SSO integration data."""

    id: UUID
    name: str
    display_name: str
    provider_type: str
    is_active: bool
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class SSOIntegrationCreate(SQLModel):
    """Schema for creating a new SSO integration."""

    name: str = Field(max_length=255, min_length=3)
    display_name: str = Field(max_length=255, min_length=1)
    provider_type: str
    config: dict[str, Any]
    attribute_mapping: dict[str, Any] | None = None

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, v: str) -> str:
        """Validate provider type is one of the allowed values."""
        allowed = {"saml", "oidc", "scim"}
        if v not in allowed:
            msg = f"provider_type must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return v


class SSOIntegrationUpdate(SQLModel):
    """Schema for updating an SSO integration."""

    display_name: str | None = Field(default=None, max_length=255, min_length=1)
    is_active: bool | None = None
    config: dict[str, Any] | None = None
    attribute_mapping: dict[str, Any] | None = None

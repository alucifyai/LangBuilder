"""SSO Configuration Models.

PRD Story 2.2 - Enterprise SSO Integration
PRD Story 2.3 - Support SAML and OIDC
"""

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlmodel import Column, Field as SQLField, Relationship, SQLModel

from langflow.services.database.models.base import TimestampedBase

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User


class SSOProtocol(str, Enum):
    """Supported SSO protocols."""

    OIDC = "oidc"
    SAML = "saml"


class SSOConfigStatus(str, Enum):
    """SSO configuration status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"


class SSOConfig(TimestampedBase, table=True):
    """SSO configuration for workspace.

    Stores configuration for OIDC or SAML authentication.
    PRD Story 2.2 @AC1 - Store SSO configuration
    """

    __tablename__ = "sso_config"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True, index=True)
    workspace_id: str = SQLField(index=True, description="Workspace this SSO config belongs to")
    name: str = SQLField(description="Human-readable name for this SSO configuration")
    protocol: SSOProtocol = SQLField(description="SSO protocol (oidc or saml)")
    status: SSOConfigStatus = SQLField(
        default=SSOConfigStatus.TESTING, description="Configuration status"
    )

    # OIDC Configuration
    oidc_issuer: str | None = SQLField(default=None, description="OIDC issuer URL")
    oidc_client_id: str | None = SQLField(default=None, description="OIDC client ID")
    oidc_client_secret: str | None = SQLField(default=None, description="OIDC client secret (encrypted)")
    oidc_redirect_uri: str | None = SQLField(default=None, description="OIDC redirect URI")
    oidc_scopes: str | None = SQLField(
        default="openid profile email", description="OIDC scopes (space-separated)"
    )

    # SAML Configuration
    saml_entity_id: str | None = SQLField(default=None, description="SAML entity ID")
    saml_sso_url: str | None = SQLField(default=None, description="SAML SSO URL")
    saml_x509_cert: str | None = SQLField(default=None, description="SAML X.509 certificate")
    saml_acs_url: str | None = SQLField(default=None, description="SAML Assertion Consumer Service URL")

    # Attribute Mapping (JSON stored as string)
    attribute_mapping: str = SQLField(
        default='{"email": "email", "name": "name", "groups": "groups"}',
        description="Attribute mapping configuration (JSON)",
    )

    # Auto-provisioning settings
    auto_provision_users: bool = SQLField(
        default=True, description="Automatically create users on first SSO login"
    )
    default_role_id: UUID | None = SQLField(
        default=None, foreign_key="role.id", description="Default role for auto-provisioned users"
    )

    # JIT (Just-In-Time) provisioning
    jit_enabled: bool = SQLField(
        default=True, description="Enable just-in-time user provisioning"
    )

    # Relationships
    sso_sessions: list["SSOSession"] = Relationship(back_populates="sso_config")


class SSOSession(TimestampedBase, table=True):
    """SSO session tracking.

    Tracks SSO login sessions for security and audit purposes.
    PRD Story 2.2 @AC3 - Track SSO sessions
    """

    __tablename__ = "sso_session"

    id: UUID = SQLField(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = SQLField(foreign_key="user.id", index=True)
    sso_config_id: UUID = SQLField(foreign_key="sso_config.id", index=True)

    # Session details
    external_id: str = SQLField(description="External user ID from SSO provider")
    session_token: str = SQLField(unique=True, index=True, description="Unique session token")
    expires_at: datetime = SQLField(description="Session expiration time")

    # Authentication details
    ip_address: str | None = SQLField(default=None, description="IP address of login")
    user_agent: str | None = SQLField(default=None, description="User agent string")

    # SSO provider claims (JSON stored as string)
    sso_claims: str | None = SQLField(default=None, description="SSO provider claims (JSON)")

    # Relationships
    user: "User" = Relationship(back_populates="sso_sessions")
    sso_config: "SSOConfig" = Relationship(back_populates="sso_sessions")


# Pydantic models for API


class SSOConfigCreate(BaseModel):
    """Create SSO configuration."""

    workspace_id: str
    name: str
    protocol: SSOProtocol

    # OIDC fields
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_redirect_uri: str | None = None
    oidc_scopes: str = "openid profile email"

    # SAML fields
    saml_entity_id: str | None = None
    saml_sso_url: str | None = None
    saml_x509_cert: str | None = None
    saml_acs_url: str | None = None

    # Settings
    attribute_mapping: dict[str, str] = Field(
        default_factory=lambda: {"email": "email", "name": "name", "groups": "groups"}
    )
    auto_provision_users: bool = True
    default_role_id: UUID | None = None
    jit_enabled: bool = True


class SSOConfigUpdate(BaseModel):
    """Update SSO configuration."""

    name: str | None = None
    status: SSOConfigStatus | None = None

    # OIDC fields
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_redirect_uri: str | None = None
    oidc_scopes: str | None = None

    # SAML fields
    saml_entity_id: str | None = None
    saml_sso_url: str | None = None
    saml_x509_cert: str | None = None
    saml_acs_url: str | None = None

    # Settings
    attribute_mapping: dict[str, str] | None = None
    auto_provision_users: bool | None = None
    default_role_id: UUID | None = None
    jit_enabled: bool | None = None


class SSOConfigRead(BaseModel):
    """Read SSO configuration."""

    id: UUID
    workspace_id: str
    name: str
    protocol: SSOProtocol
    status: SSOConfigStatus

    # OIDC fields (excluding secret)
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_redirect_uri: str | None = None
    oidc_scopes: str | None = None

    # SAML fields
    saml_entity_id: str | None = None
    saml_sso_url: str | None = None
    saml_acs_url: str | None = None

    # Settings
    attribute_mapping: dict[str, str]
    auto_provision_users: bool
    default_role_id: UUID | None = None
    jit_enabled: bool

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SSOSessionRead(BaseModel):
    """Read SSO session."""

    id: UUID
    user_id: UUID
    sso_config_id: UUID
    external_id: str
    expires_at: datetime
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

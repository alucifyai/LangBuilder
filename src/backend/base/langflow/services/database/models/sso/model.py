"""
SSO Configuration Models

Models for storing SSO/SAML/OIDC configuration.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlmodel import Field, SQLModel

from langflow.schema.serialize import UUIDstr


class SSOProvider(str, Enum):
    """Supported SSO providers."""

    OIDC = "oidc"
    SAML = "saml"


class SSOEnforcement(str, Enum):
    """SSO enforcement levels."""

    OPTIONAL = "optional"  # Users can choose SSO or local login
    ENFORCED = "enforced"  # SSO is required, local login disabled
    DISABLED = "disabled"  # SSO is disabled


class SSOConfiguration(SQLModel, table=True):  # type: ignore[call-arg]
    """
    SSO Configuration for an organization.

    Stores OIDC/SAML provider settings.
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True, unique=True)

    # Organization/tenant identifier
    organization_id: str = Field(index=True)  # Could be workspace_id or org domain
    domain: str = Field(index=True)  # Company domain for SP-initiated flow

    # Provider configuration
    provider_type: SSOProvider
    enforcement: SSOEnforcement = Field(default=SSOEnforcement.OPTIONAL)

    # OIDC Configuration
    oidc_client_id: str | None = Field(default=None)
    oidc_client_secret: str | None = Field(default=None)  # Should be encrypted
    oidc_issuer: str | None = Field(default=None)
    oidc_authorization_endpoint: str | None = Field(default=None)
    oidc_token_endpoint: str | None = Field(default=None)
    oidc_userinfo_endpoint: str | None = Field(default=None)
    oidc_jwks_uri: str | None = Field(default=None)

    # SAML Configuration
    saml_entity_id: str | None = Field(default=None)
    saml_sso_url: str | None = Field(default=None)
    saml_x509_cert: str | None = Field(default=None)  # IdP certificate
    saml_slo_url: str | None = Field(default=None)  # Single Logout URL

    # Attribute mapping
    email_attribute: str = Field(default="email")
    name_attribute: str = Field(default="name")
    groups_attribute: str | None = Field(default="groups")

    # Group mapping (JSON: {"IdP_group": "LangBuilder_group_id"})
    group_mapping: dict = Field(default={}, sa_column_kwargs={"type_": "JSON"})

    # Security settings
    allow_clock_skew_seconds: int = Field(default=300)  # 5 minutes
    session_timeout_minutes: int = Field(default=480)  # 8 hours

    # Break-glass configuration
    break_glass_enabled: bool = Field(default=False)
    break_glass_account_id: str | None = Field(default=None)

    # Metadata
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SSOSession(SQLModel, table=True):  # type: ignore[call-arg]
    """
    SSO Session tracking for replay protection and SLO.
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)

    # User and SSO config
    user_id: UUIDstr = Field(index=True)
    sso_config_id: UUIDstr = Field(index=True)

    # Assertion tracking (for replay protection)
    assertion_id: str = Field(index=True, unique=True)  # SAML InResponseTo or OIDC jti
    assertion_issued_at: datetime
    assertion_expires_at: datetime

    # Session tracking
    session_token: str = Field(index=True)  # LangBuilder session token
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    # Audit trail
    ip_address: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    mfa_verified: bool = Field(default=False)


class SSOAssertion(SQLModel, table=True):  # type: ignore[call-arg]
    """
    Processed SSO assertions for replay detection.

    Stores assertion IDs to prevent replay attacks.
    """

    id: UUIDstr = Field(default_factory=uuid4, primary_key=True)
    assertion_id: str = Field(index=True, unique=True)
    used_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(index=True)
    user_id: UUIDstr

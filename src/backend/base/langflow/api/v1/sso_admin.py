"""
SSO Admin API

FastAPI endpoints for managing SSO configurations (admin only).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.utils import get_current_active_user
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.sso.crud import (
    create_sso_config,
    delete_sso_config,
    get_sso_config_by_id,
    get_sso_config_by_org,
    update_sso_config,
)
from langflow.services.database.models.sso.model import SSOConfiguration, SSOEnforcement, SSOProvider
from langflow.services.database.models.user.model import User
from langflow.services.deps import get_session

router = APIRouter(prefix="/sso/admin", tags=["SSO Administration"])


# Request/Response Models
class SSOConfigBase(BaseModel):
    """Base SSO configuration fields."""

    domain: str = Field(..., description="Company domain (e.g., acme.com)")
    provider_type: SSOProvider = Field(..., description="SSO provider (oidc or saml)")
    enforcement: SSOEnforcement = Field(
        default=SSOEnforcement.OPTIONAL,
        description="Enforcement level (disabled, optional, enforced)",
    )
    enabled: bool = Field(default=True, description="Enable SSO for this domain")

    # OIDC fields
    oidc_issuer: str | None = Field(None, description="OIDC issuer URL")
    oidc_client_id: str | None = Field(None, description="OIDC client ID")
    oidc_client_secret: str | None = Field(None, description="OIDC client secret")
    oidc_authorization_endpoint: str | None = None
    oidc_token_endpoint: str | None = None
    oidc_userinfo_endpoint: str | None = None
    oidc_jwks_uri: str | None = None

    # SAML fields
    saml_entity_id: str | None = Field(None, description="SAML IdP entity ID")
    saml_sso_url: str | None = Field(None, description="SAML SSO URL")
    saml_x509_cert: str | None = Field(None, description="SAML IdP X.509 certificate")
    saml_slo_url: str | None = None

    # Attribute mapping
    email_attribute: str | None = Field(None, description="Email claim/attribute name")
    name_attribute: str | None = Field(None, description="Name claim/attribute name")
    groups_attribute: str | None = Field(None, description="Groups claim/attribute name")

    # Session settings
    session_timeout_minutes: int = Field(default=480, description="Session timeout (minutes)")
    allow_clock_skew_seconds: int = Field(default=300, description="Clock skew tolerance (seconds)")


class SSOConfigCreate(SSOConfigBase):
    """Request to create SSO configuration."""

    organization_id: str = Field(..., description="Organization ID")


class SSOConfigUpdate(BaseModel):
    """Request to update SSO configuration."""

    domain: str | None = None
    enforcement: SSOEnforcement | None = None
    enabled: bool | None = None

    # OIDC fields
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_client_secret: str | None = None
    oidc_authorization_endpoint: str | None = None
    oidc_token_endpoint: str | None = None
    oidc_userinfo_endpoint: str | None = None
    oidc_jwks_uri: str | None = None

    # SAML fields
    saml_entity_id: str | None = None
    saml_sso_url: str | None = None
    saml_x509_cert: str | None = None
    saml_slo_url: str | None = None

    # Attribute mapping
    email_attribute: str | None = None
    name_attribute: str | None = None
    groups_attribute: str | None = None

    # Session settings
    session_timeout_minutes: int | None = None
    allow_clock_skew_seconds: int | None = None


class SSOConfigResponse(BaseModel):
    """SSO configuration response."""

    id: str
    organization_id: str
    domain: str
    provider_type: SSOProvider
    enforcement: SSOEnforcement
    enabled: bool

    # OIDC (client secret redacted)
    oidc_issuer: str | None = None
    oidc_client_id: str | None = None
    oidc_authorization_endpoint: str | None = None
    oidc_token_endpoint: str | None = None
    oidc_userinfo_endpoint: str | None = None
    oidc_jwks_uri: str | None = None

    # SAML
    saml_entity_id: str | None = None
    saml_sso_url: str | None = None
    saml_slo_url: str | None = None

    # Attribute mapping
    email_attribute: str | None = None
    name_attribute: str | None = None
    groups_attribute: str | None = None

    # Session settings
    session_timeout_minutes: int
    allow_clock_skew_seconds: int

    created_at: str
    updated_at: str

    @classmethod
    def from_config(cls, config: SSOConfiguration) -> "SSOConfigResponse":
        """Convert SSOConfiguration to response model."""
        return cls(
            id=str(config.id),
            organization_id=config.organization_id,
            domain=config.domain,
            provider_type=config.provider_type,
            enforcement=config.enforcement,
            enabled=config.enabled,
            oidc_issuer=config.oidc_issuer,
            oidc_client_id=config.oidc_client_id,
            oidc_authorization_endpoint=config.oidc_authorization_endpoint,
            oidc_token_endpoint=config.oidc_token_endpoint,
            oidc_userinfo_endpoint=config.oidc_userinfo_endpoint,
            oidc_jwks_uri=config.oidc_jwks_uri,
            saml_entity_id=config.saml_entity_id,
            saml_sso_url=config.saml_sso_url,
            saml_slo_url=config.saml_slo_url,
            email_attribute=config.email_attribute,
            name_attribute=config.name_attribute,
            groups_attribute=config.groups_attribute,
            session_timeout_minutes=config.session_timeout_minutes,
            allow_clock_skew_seconds=config.allow_clock_skew_seconds,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )


# Endpoints
@router.post("/configs", response_model=SSOConfigResponse, status_code=201)
async def create_sso_configuration(
    request: SSOConfigCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SSOConfigResponse:
    """
    Create SSO configuration (admin only).

    Args:
        request: SSO configuration data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created SSO configuration

    Raises:
        HTTPException 403: User is not authorized
        HTTPException 400: Invalid configuration
    """
    # Check admin permission
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # Validate provider-specific fields
    if request.provider_type == SSOProvider.OIDC:
        if not request.oidc_issuer or not request.oidc_client_id or not request.oidc_client_secret:
            raise HTTPException(
                status_code=400,
                detail="OIDC configuration requires issuer, client_id, and client_secret",
            )
    elif request.provider_type == SSOProvider.SAML:
        if not request.saml_entity_id or not request.saml_sso_url or not request.saml_x509_cert:
            raise HTTPException(
                status_code=400,
                detail="SAML configuration requires entity_id, sso_url, and x509_cert",
            )

    # Create configuration
    config = await create_sso_config(
        db=db,
        organization_id=request.organization_id,
        domain=request.domain,
        provider_type=request.provider_type,
        enforcement=request.enforcement,
        enabled=request.enabled,
        oidc_issuer=request.oidc_issuer,
        oidc_client_id=request.oidc_client_id,
        oidc_client_secret=request.oidc_client_secret,
        oidc_authorization_endpoint=request.oidc_authorization_endpoint,
        oidc_token_endpoint=request.oidc_token_endpoint,
        oidc_userinfo_endpoint=request.oidc_userinfo_endpoint,
        oidc_jwks_uri=request.oidc_jwks_uri,
        saml_entity_id=request.saml_entity_id,
        saml_sso_url=request.saml_sso_url,
        saml_x509_cert=request.saml_x509_cert,
        saml_slo_url=request.saml_slo_url,
        email_attribute=request.email_attribute,
        name_attribute=request.name_attribute,
        groups_attribute=request.groups_attribute,
        session_timeout_minutes=request.session_timeout_minutes,
        allow_clock_skew_seconds=request.allow_clock_skew_seconds,
    )

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_CREATED,  # TODO: Add SSO_CONFIG_CREATED
        resource_type="sso_configuration",
        resource_id=str(config.id),
        metadata={
            "domain": config.domain,
            "provider": config.provider_type.value,
            "enforcement": config.enforcement.value,
        },
    )

    return SSOConfigResponse.from_config(config)


@router.get("/configs/{config_id}", response_model=SSOConfigResponse)
async def get_sso_configuration(
    config_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SSOConfigResponse:
    """
    Get SSO configuration by ID (admin only).

    Args:
        config_id: SSO configuration ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        SSO configuration

    Raises:
        HTTPException 403: User is not authorized
        HTTPException 404: Configuration not found
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    config = await get_sso_config_by_id(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    return SSOConfigResponse.from_config(config)


@router.get("/orgs/{organization_id}/config", response_model=SSOConfigResponse)
async def get_sso_configuration_by_org(
    organization_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SSOConfigResponse:
    """
    Get SSO configuration for an organization (admin only).

    Args:
        organization_id: Organization ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        SSO configuration

    Raises:
        HTTPException 403: User is not authorized
        HTTPException 404: Configuration not found
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    config = await get_sso_config_by_org(db, organization_id)
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    return SSOConfigResponse.from_config(config)


@router.patch("/configs/{config_id}", response_model=SSOConfigResponse)
async def update_sso_configuration(
    config_id: UUID,
    request: SSOConfigUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SSOConfigResponse:
    """
    Update SSO configuration (admin only).

    Args:
        config_id: SSO configuration ID
        request: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated SSO configuration

    Raises:
        HTTPException 403: User is not authorized
        HTTPException 404: Configuration not found
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # Get existing config
    existing_config = await get_sso_config_by_id(db, config_id)
    if not existing_config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    # Prepare updates (only include non-None fields)
    updates = {k: v for k, v in request.model_dump().items() if v is not None}

    if not updates:
        return SSOConfigResponse.from_config(existing_config)

    # Update configuration
    config = await update_sso_config(db, config_id, **updates)

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_UPDATED,  # TODO: Add SSO_CONFIG_UPDATED
        resource_type="sso_configuration",
        resource_id=str(config.id),
        metadata={"updates": list(updates.keys())},
    )

    return SSOConfigResponse.from_config(config)


@router.delete("/configs/{config_id}", status_code=204)
async def delete_sso_configuration(
    config_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    Delete SSO configuration (admin only).

    Args:
        config_id: SSO configuration ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException 403: User is not authorized
        HTTPException 404: Configuration not found
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin permission required")

    success = await delete_sso_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="SSO configuration not found")

    # Audit log
    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_DELETED,  # TODO: Add SSO_CONFIG_DELETED
        resource_type="sso_configuration",
        resource_id=str(config_id),
    )

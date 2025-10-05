"""SSO authentication API endpoints.

PRD Story 2.2 - Enterprise SSO Integration
PRD Story 2.3 - Support SAML and OIDC
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from loguru import logger
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    RequirePermission,
)
from langflow.services.auth.encryption import decrypt_secret, encrypt_secret
from langflow.services.auth.oidc import OIDCService
from langflow.services.auth.saml import SAMLService
from langflow.services.database.models.sso_config import (
    SSOConfig,
    SSOConfigCreate,
    SSOConfigRead,
    SSOConfigUpdate,
    SSOProtocol,
    SSOSessionRead,
)

router = APIRouter(prefix="/sso", tags=["SSO"])


# SSO Configuration Management


@router.post("/config", response_model=SSOConfigRead, status_code=status.HTTP_201_CREATED)
async def create_sso_config(
    config: SSOConfigCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
    _perm: RequirePermission = Depends(RequirePermission("sso:create")),
):
    """Create SSO configuration.

    Args:
        config: SSO configuration data

    Returns:
        Created SSO configuration

    PRD Story 2.2 @AC1 - Configure SSO
    Phase 4 Audit - High Fix #1: Added permission check
    """

    # Validate protocol-specific fields
    if config.protocol == SSOProtocol.OIDC:
        if not all([config.oidc_issuer, config.oidc_client_id, config.oidc_client_secret]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OIDC configuration requires issuer, client_id, and client_secret",
            )
    elif config.protocol == SSOProtocol.SAML:
        if not all([config.saml_entity_id, config.saml_sso_url, config.saml_x509_cert]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SAML configuration requires entity_id, sso_url, and x509_cert",
            )

    # Create SSO config
    import json

    # CRITICAL FIX #1: Encrypt client secret before storage
    encrypted_secret = None
    if config.oidc_client_secret:
        encrypted_secret = encrypt_secret(config.oidc_client_secret)

    sso_config = SSOConfig(
        workspace_id=config.workspace_id,
        name=config.name,
        protocol=config.protocol,
        oidc_issuer=config.oidc_issuer,
        oidc_client_id=config.oidc_client_id,
        oidc_client_secret=encrypted_secret,  # Encrypted
        oidc_redirect_uri=config.oidc_redirect_uri,
        oidc_scopes=config.oidc_scopes,
        saml_entity_id=config.saml_entity_id,
        saml_sso_url=config.saml_sso_url,
        saml_x509_cert=config.saml_x509_cert,
        saml_acs_url=config.saml_acs_url,
        attribute_mapping=json.dumps(config.attribute_mapping),
        auto_provision_users=config.auto_provision_users,
        default_role_id=config.default_role_id,
        jit_enabled=config.jit_enabled,
    )

    db.add(sso_config)
    await db.commit()
    await db.refresh(sso_config)

    logger.info(f"Created SSO config {sso_config.id} for workspace {config.workspace_id}")

    return SSOConfigRead.model_validate(sso_config, from_attributes=True)


@router.get("/config", response_model=list[SSOConfigRead])
async def list_sso_configs(
    db: DbSession,
    current_user: CurrentActiveUser,
    workspace_id: str | None = Query(None, description="Filter by workspace"),
):
    """List SSO configurations.

    Args:
        workspace_id: Optional workspace filter

    Returns:
        List of SSO configurations

    PRD Story 2.2 @AC1 - List SSO configurations
    """
    # TODO: Add permission check for 'sso:read'

    stmt = select(SSOConfig)
    if workspace_id:
        stmt = stmt.where(SSOConfig.workspace_id == workspace_id)

    result = await db.exec(stmt)
    configs = result.all()

    return [SSOConfigRead.model_validate(c, from_attributes=True) for c in configs]


@router.get("/config/{config_id}", response_model=SSOConfigRead)
async def get_sso_config(
    config_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get SSO configuration by ID.

    Args:
        config_id: SSO configuration UUID

    Returns:
        SSO configuration

    PRD Story 2.2 @AC1 - Get SSO configuration
    """
    # TODO: Add permission check for 'sso:read'

    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SSO configuration '{config_id}' not found",
        )

    return SSOConfigRead.model_validate(config, from_attributes=True)


@router.patch("/config/{config_id}", response_model=SSOConfigRead)
async def update_sso_config(
    config_id: UUID,
    update: SSOConfigUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update SSO configuration.

    Args:
        config_id: SSO configuration UUID
        update: Update data

    Returns:
        Updated SSO configuration

    PRD Story 2.2 @AC1 - Update SSO configuration
    """
    # TODO: Add permission check for 'sso:update'

    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SSO configuration '{config_id}' not found",
        )

    # Update fields
    import json

    if update.name is not None:
        config.name = update.name
    if update.status is not None:
        config.status = update.status
    if update.oidc_issuer is not None:
        config.oidc_issuer = update.oidc_issuer
    if update.oidc_client_id is not None:
        config.oidc_client_id = update.oidc_client_id
    if update.oidc_client_secret is not None:
        config.oidc_client_secret = update.oidc_client_secret
    if update.oidc_redirect_uri is not None:
        config.oidc_redirect_uri = update.oidc_redirect_uri
    if update.oidc_scopes is not None:
        config.oidc_scopes = update.oidc_scopes
    if update.saml_entity_id is not None:
        config.saml_entity_id = update.saml_entity_id
    if update.saml_sso_url is not None:
        config.saml_sso_url = update.saml_sso_url
    if update.saml_x509_cert is not None:
        config.saml_x509_cert = update.saml_x509_cert
    if update.saml_acs_url is not None:
        config.saml_acs_url = update.saml_acs_url
    if update.attribute_mapping is not None:
        config.attribute_mapping = json.dumps(update.attribute_mapping)
    if update.auto_provision_users is not None:
        config.auto_provision_users = update.auto_provision_users
    if update.default_role_id is not None:
        config.default_role_id = update.default_role_id
    if update.jit_enabled is not None:
        config.jit_enabled = update.jit_enabled

    await db.commit()
    await db.refresh(config)

    logger.info(f"Updated SSO config {config_id}")

    return SSOConfigRead.model_validate(config, from_attributes=True)


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sso_config(
    config_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete SSO configuration.

    Args:
        config_id: SSO configuration UUID

    PRD Story 2.2 @AC1 - Delete SSO configuration
    """
    # TODO: Add permission check for 'sso:delete'

    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SSO configuration '{config_id}' not found",
        )

    await db.delete(config)
    await db.commit()

    logger.info(f"Deleted SSO config {config_id}")


# OIDC Authentication Flow


@router.get("/oidc/login/{config_id}")
async def oidc_login(
    config_id: UUID,
    db: DbSession,
):
    """Initiate OIDC login flow.

    Args:
        config_id: SSO configuration UUID

    Returns:
        Redirect to OIDC provider

    PRD Story 2.2 @AC2 - Initiate OIDC login
    """
    # Get SSO config
    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config or config.protocol != SSOProtocol.OIDC:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OIDC configuration '{config_id}' not found",
        )

    # Initialize OIDC service
    oidc_service = OIDCService(config)
    await oidc_service.discover_endpoints()

    # Generate state for CSRF protection
    import secrets

    state = secrets.token_urlsafe(32)

    # TODO: Store state in session/cache for verification

    # Get authorization URL
    auth_url = oidc_service.get_authorization_url(state)

    logger.info(f"Redirecting to OIDC provider for config {config_id}")
    return RedirectResponse(url=auth_url)


@router.get("/oidc/callback/{config_id}")
async def oidc_callback(
    config_id: UUID,
    request: Request,
    db: DbSession,
    code: str = Query(..., description="Authorization code"),
    state: str = Query(..., description="State parameter"),
):
    """Handle OIDC callback.

    Args:
        config_id: SSO configuration UUID
        code: Authorization code
        state: State parameter for CSRF protection

    Returns:
        User session information

    PRD Story 2.2 @AC2 - Handle OIDC callback
    """
    # TODO: Verify state parameter

    # Get SSO config
    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config or config.protocol != SSOProtocol.OIDC:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OIDC configuration '{config_id}' not found",
        )

    # Initialize OIDC service
    oidc_service = OIDCService(config)

    # Get client info
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Authenticate user
    user, sso_session = await oidc_service.authenticate(
        db=db,
        authorization_code=code,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    logger.info(f"OIDC authentication successful for user {user.username}")

    # TODO: Create JWT token for user session
    # TODO: Set session cookie
    # TODO: Redirect to application

    return {
        "user_id": str(user.id),
        "username": user.username,
        "session_id": str(sso_session.id),
        "session_token": sso_session.session_token,
    }


# SAML Authentication Flow


@router.get("/saml/login/{config_id}")
async def saml_login(
    config_id: UUID,
    request: Request,
    db: DbSession,
):
    """Initiate SAML login flow.

    Args:
        config_id: SSO configuration UUID

    Returns:
        Redirect to SAML IdP

    PRD Story 2.2 @AC2 - Initiate SAML login
    """
    # Get SSO config
    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config or config.protocol != SSOProtocol.SAML:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SAML configuration '{config_id}' not found",
        )

    # Initialize SAML service
    saml_service = SAMLService(config)

    # Prepare request data
    request_data = {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.hostname,
        "script_name": request.url.path,
        "server_port": str(request.url.port or 443),
        "get_data": dict(request.query_params),
        "post_data": {},
    }

    # Get login URL
    login_url = saml_service.get_login_url(request_data)

    logger.info(f"Redirecting to SAML IdP for config {config_id}")
    return RedirectResponse(url=login_url)


@router.post("/saml/acs/{config_id}")
async def saml_acs(
    config_id: UUID,
    request: Request,
    db: DbSession,
):
    """SAML Assertion Consumer Service (ACS) endpoint.

    Handles SAML response from IdP.

    Args:
        config_id: SSO configuration UUID

    Returns:
        User session information

    PRD Story 2.2 @AC2 - Handle SAML response
    """
    # Get SSO config
    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config or config.protocol != SSOProtocol.SAML:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SAML configuration '{config_id}' not found",
        )

    # Initialize SAML service
    saml_service = SAMLService(config)

    # Parse POST data
    form_data = await request.form()
    post_data = dict(form_data)

    # Prepare request data
    request_data = {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.url.hostname,
        "script_name": request.url.path,
        "server_port": str(request.url.port or 443),
        "get_data": dict(request.query_params),
        "post_data": post_data,
    }

    # Get client info
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    # Authenticate user
    user, sso_session = await saml_service.authenticate(
        db=db,
        request_data=request_data,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    logger.info(f"SAML authentication successful for user {user.username}")

    # TODO: Create JWT token for user session
    # TODO: Set session cookie
    # TODO: Redirect to application

    return {
        "user_id": str(user.id),
        "username": user.username,
        "session_id": str(sso_session.id),
        "session_token": sso_session.session_token,
    }


@router.get("/saml/metadata/{config_id}")
async def saml_metadata(
    config_id: UUID,
    db: DbSession,
):
    """Get SAML SP metadata.

    Args:
        config_id: SSO configuration UUID

    Returns:
        SAML metadata XML

    PRD Story 2.3 @AC2 - SAML metadata endpoint
    """
    # Get SSO config
    stmt = select(SSOConfig).where(SSOConfig.id == config_id)
    result = await db.exec(stmt)
    config = result.first()

    if not config or config.protocol != SSOProtocol.SAML:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SAML configuration '{config_id}' not found",
        )

    # Initialize SAML service
    saml_service = SAMLService(config)

    # Generate metadata
    metadata_xml = saml_service.generate_metadata()

    from fastapi.responses import Response

    return Response(content=metadata_xml, media_type="application/xml")

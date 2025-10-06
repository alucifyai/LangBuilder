"""
SSO Authentication API

FastAPI endpoints for SSO login flows (OIDC and SAML).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.sso_service import SSOAuthenticationError, SSOService
from langflow.services.database.models.sso.model import SSOEnforcement
from langflow.services.deps import get_session

router = APIRouter(prefix="/sso", tags=["SSO Authentication"])


# Request/Response Models
class SSOLoginRequest(BaseModel):
    """Request to initiate SSO login."""

    domain: str = Field(..., description="Company domain for SSO lookup")
    redirect_uri: str = Field(..., description="Callback URL after authentication")
    state: str | None = Field(None, description="CSRF protection state")


class SSOLoginResponse(BaseModel):
    """Response with SSO redirect URL."""

    provider: str = Field(..., description="SSO provider type (oidc or saml)")
    redirect_url: str = Field(..., description="URL to redirect user to IdP")
    state: str | None = Field(None, description="State parameter for CSRF protection")
    request_id: str | None = Field(None, description="SAML request ID (SAML only)")


class OIDCCallbackRequest(BaseModel):
    """OIDC callback parameters."""

    code: str = Field(..., description="Authorization code from IdP")
    state: str | None = Field(None, description="State parameter for CSRF validation")


class SAMLCallbackRequest(BaseModel):
    """SAML callback parameters."""

    SAMLResponse: str = Field(..., description="Base64-encoded SAML response")
    RelayState: str | None = Field(None, description="Relay state for CSRF validation")


class SSOAuthResponse(BaseModel):
    """SSO authentication success response."""

    user_id: str
    email: str
    session_token: str
    expires_at: str
    mfa_verified: bool = False


class SSOEnforcementResponse(BaseModel):
    """SSO enforcement status."""

    enforcement: SSOEnforcement
    enabled: bool
    message: str


# Endpoints
@router.post("/login", response_model=SSOLoginResponse)
async def initiate_sso_login(
    request: SSOLoginRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SSOLoginResponse:
    """
    Initiate SSO login flow (SP-initiated).

    This endpoint generates the SSO authorization URL and redirects the user
    to their configured Identity Provider (IdP).

    Flow:
    1. Look up SSO configuration by domain
    2. Generate authorization URL (OIDC) or SAML AuthnRequest
    3. Return redirect URL to client

    Args:
        request: SSO login request with domain and callback URL
        db: Database session

    Returns:
        SSOLoginResponse with redirect URL and provider info

    Raises:
        HTTPException 404: SSO not configured for domain
        HTTPException 400: Invalid SSO configuration
    """
    try:
        result = await SSOService.initiate_sso_login(
            db=db,
            domain=request.domain,
            redirect_uri=request.redirect_uri,
            state=request.state,
        )

        return SSOLoginResponse(**result)

    except SSOAuthenticationError as e:
        if "not configured" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/callback/oidc", response_model=SSOAuthResponse)
async def oidc_callback(
    code: str = Query(..., description="Authorization code"),
    state: str | None = Query(None, description="State parameter"),
    domain: str = Query(..., description="Company domain"),
    request: Request = None,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> SSOAuthResponse:
    """
    Handle OIDC callback after user authenticates with IdP.

    This endpoint is called by the IdP after successful authentication.

    Flow:
    1. Exchange authorization code for tokens
    2. Verify ID token signature and claims
    3. Check for replay attacks
    4. Map to existing user by email
    5. Create SSO session
    6. Return session token

    Args:
        code: Authorization code from IdP
        state: State parameter for CSRF validation
        domain: Company domain for SSO config lookup
        request: FastAPI request object
        db: Database session

    Returns:
        SSOAuthResponse with user info and session token

    Raises:
        HTTPException 401: Authentication failed
        HTTPException 400: Invalid request
    """
    try:
        # Extract client info
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None

        # Build redirect URI (must match the one used in authorization)
        redirect_uri = str(request.url.replace_query_params()).split("?")[0] if request else ""

        result = await SSOService.process_oidc_callback(
            db=db,
            code=code,
            redirect_uri=redirect_uri,
            domain=domain,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return SSOAuthResponse(**result)

    except SSOAuthenticationError as e:
        if "not provisioned" in str(e):
            raise HTTPException(
                status_code=401,
                detail="Your account is not provisioned in LangBuilder. Please contact your administrator.",
            )
        if "Replay detected" in str(e):
            raise HTTPException(status_code=401, detail="Invalid or expired authentication response")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OIDC callback error: {e}")


@router.post("/callback/saml", response_model=SSOAuthResponse)
async def saml_callback(
    SAMLResponse: str = Query(..., description="Base64-encoded SAML response"),
    RelayState: str | None = Query(None, description="Relay state"),
    domain: str = Query(..., description="Company domain"),
    request: Request = None,
    db: Annotated[AsyncSession, Depends(get_session)] = None,
) -> SSOAuthResponse:
    """
    Handle SAML response after user authenticates with IdP (ACS endpoint).

    This endpoint is the Assertion Consumer Service (ACS) that receives
    SAML responses from the Identity Provider.

    Flow:
    1. Parse and validate SAML response
    2. Verify signature
    3. Check assertion timing and conditions
    4. Check for replay attacks
    5. Map to existing user by email
    6. Create SSO session
    7. Return session token

    Args:
        SAMLResponse: Base64-encoded SAML response from IdP
        RelayState: Relay state for CSRF validation
        domain: Company domain for SSO config lookup
        request: FastAPI request object
        db: Database session

    Returns:
        SSOAuthResponse with user info and session token

    Raises:
        HTTPException 401: Authentication failed
        HTTPException 400: Invalid SAML response
    """
    try:
        # Extract client info
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None

        result = await SSOService.process_saml_response(
            db=db,
            saml_response=SAMLResponse,
            domain=domain,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return SSOAuthResponse(**result)

    except SSOAuthenticationError as e:
        if "not provisioned" in str(e):
            raise HTTPException(
                status_code=401,
                detail="Your account is not provisioned in LangBuilder. Please contact your administrator.",
            )
        if "Replay detected" in str(e):
            raise HTTPException(status_code=401, detail="Invalid or expired authentication response")
        if "Invalid signature" in str(e):
            raise HTTPException(status_code=401, detail="SAML signature verification failed")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid SAML response: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SAML callback error: {e}")


@router.get("/enforcement/{domain}", response_model=SSOEnforcementResponse)
async def check_sso_enforcement(
    domain: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SSOEnforcementResponse:
    """
    Check SSO enforcement level for a domain.

    This endpoint is used by the login page to determine whether to:
    - Show SSO login button (OPTIONAL)
    - Enforce SSO and hide password login (ENFORCED)
    - Not show SSO (DISABLED)

    Args:
        domain: Company domain to check
        db: Database session

    Returns:
        SSOEnforcementResponse with enforcement level and message
    """
    enforcement = await SSOService.check_sso_enforcement(db, domain)

    messages = {
        SSOEnforcement.DISABLED: "SSO is not enabled for this domain",
        SSOEnforcement.OPTIONAL: "SSO is available as an optional login method",
        SSOEnforcement.ENFORCED: "SSO is required for this domain",
    }

    return SSOEnforcementResponse(
        enforcement=enforcement,
        enabled=enforcement != SSOEnforcement.DISABLED,
        message=messages[enforcement],
    )


@router.get("/metadata/{organization_id}")
async def get_saml_metadata(
    organization_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """
    Get SAML SP metadata for IdP configuration.

    This endpoint returns SAML metadata XML that can be uploaded to the
    Identity Provider to configure the Service Provider (LangBuilder).

    Args:
        organization_id: Organization ID
        db: Database session

    Returns:
        SAML metadata XML

    Raises:
        HTTPException 404: SSO not configured or not SAML
    """
    config = await SSOService.get_sso_config_for_org(db, organization_id)

    if not config or not config.enabled:
        raise HTTPException(status_code=404, detail="SSO not configured for this organization")

    if config.provider_type.value != "saml":
        raise HTTPException(status_code=400, detail="Not a SAML configuration")

    # Generate SAML metadata XML
    sp_entity_id = f"langbuilder-{organization_id}"
    acs_url = f"https://app.langbuilder.com/api/v1/sso/callback/saml?domain={config.domain}"

    metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{sp_entity_id}">
    <md:SPSSODescriptor
        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</md:NameIDFormat>
        <md:AssertionConsumerService
            Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Location="{acs_url}"
            index="0"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""

    return Response(content=metadata, media_type="application/xml")

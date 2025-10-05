"""SAML 2.0 authentication implementation.

PRD Story 2.2 - Enterprise SSO Integration
PRD Story 2.3 @AC2 - Support SAML
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4
from xml.etree import ElementTree as ET

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.database.models.sso_config import SSOConfig, SSOProtocol, SSOSession
from langflow.services.database.models.user.model import User

# Optional SAML support - requires python3-saml package
try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings

    SAML_AVAILABLE = True
except ImportError:
    logger.warning(
        "python3-saml not installed. SAML authentication will not be available. "
        "Install with: pip install python3-saml"
    )
    SAML_AVAILABLE = False
    OneLogin_Saml2_Auth = None  # type: ignore
    OneLogin_Saml2_Settings = None  # type: ignore


class SAMLAuthenticationError(Exception):
    """SAML authentication error."""

    pass


class SAMLService:
    """SAML 2.0 authentication service.

    Implements SAML authentication flow:
    1. Generate SAML authentication request
    2. Redirect to SAML IdP
    3. Handle SAML response from IdP
    4. Validate SAML assertion
    5. Extract user attributes
    6. Auto-provision user if needed
    """

    def __init__(self, sso_config: SSOConfig):
        """Initialize SAML service.

        Args:
            sso_config: SSO configuration with SAML settings
        """
        if sso_config.protocol != SSOProtocol.SAML:
            raise ValueError(f"Invalid protocol: {sso_config.protocol}. Expected SAML.")

        self.config = sso_config
        self.entity_id = sso_config.saml_entity_id
        self.sso_url = sso_config.saml_sso_url
        self.x509_cert = sso_config.saml_x509_cert
        self.acs_url = sso_config.saml_acs_url

        # Build SAML settings
        self.saml_settings = self._build_saml_settings()

    def _build_saml_settings(self) -> dict[str, Any]:
        """Build SAML settings dictionary.

        Returns:
            SAML settings configuration

        PRD Story 2.3 @AC2 - SAML configuration
        """
        return {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": self.entity_id,
                "assertionConsumerService": {
                    "url": self.acs_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
                },
                "singleLogoutService": {
                    "url": f"{self.acs_url}/slo",
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            },
            "idp": {
                "entityId": self.entity_id,
                "singleSignOnService": {
                    "url": self.sso_url,
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
                },
                "x509cert": self.x509_cert,
            },
            "security": {
                "nameIdEncrypted": False,
                "authnRequestsSigned": True,
                "logoutRequestSigned": True,
                "logoutResponseSigned": True,
                "signMetadata": True,
                "wantMessagesSigned": True,
                "wantAssertionsSigned": True,
                "wantAssertionsEncrypted": False,
                "wantNameId": True,
                "wantNameIdEncrypted": False,
                "requestedAuthnContext": True,
            },
        }

    def prepare_saml_request(self, request_data: dict[str, Any]) -> OneLogin_Saml2_Auth:
        """Prepare SAML request with HTTP context.

        Args:
            request_data: HTTP request data with headers, GET/POST params

        Returns:
            SAML auth object

        PRD Story 2.2 @AC2 - Prepare SAML request
        """
        # Convert FastAPI request to python-saml format
        saml_request_data = {
            "https": "on" if request_data.get("https") else "off",
            "http_host": request_data.get("http_host", "localhost"),
            "script_name": request_data.get("script_name", ""),
            "server_port": request_data.get("server_port", "443"),
            "get_data": request_data.get("get_data", {}),
            "post_data": request_data.get("post_data", {}),
        }

        return OneLogin_Saml2_Auth(saml_request_data, self.saml_settings)

    def get_login_url(self, request_data: dict[str, Any], relay_state: str | None = None) -> str:
        """Generate SAML login URL.

        Args:
            request_data: HTTP request context
            relay_state: Optional relay state for post-login redirect

        Returns:
            SAML SSO URL with authentication request

        PRD Story 2.2 @AC2 - Initiate SAML login
        """
        auth = self.prepare_saml_request(request_data)
        return auth.login(return_to=relay_state)

    async def process_saml_response(
        self, request_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Process SAML response from IdP.

        Args:
            request_data: HTTP request with SAML response

        Returns:
            User attributes from SAML assertion

        Raises:
            SAMLAuthenticationError: If SAML response is invalid

        PRD Story 2.2 @AC2 - Process SAML response
        """
        auth = self.prepare_saml_request(request_data)

        # Process the SAML response
        auth.process_response()

        # Check for errors
        errors = auth.get_errors()
        if errors:
            error_reason = auth.get_last_error_reason()
            logger.error(f"SAML authentication errors: {errors}, reason: {error_reason}")
            raise SAMLAuthenticationError(f"SAML authentication failed: {error_reason}")

        # Verify authentication
        if not auth.is_authenticated():
            raise SAMLAuthenticationError("SAML authentication failed: not authenticated")

        # Extract attributes
        attributes = auth.get_attributes()
        nameid = auth.get_nameid()

        logger.info(f"SAML authentication successful for NameID: {nameid}")

        return {
            "nameid": nameid,
            "attributes": attributes,
            "session_index": auth.get_session_index(),
        }

    def extract_user_claims(self, saml_data: dict[str, Any]) -> dict[str, Any]:
        """Extract and map user claims from SAML attributes.

        Args:
            saml_data: SAML response data with attributes

        Returns:
            Mapped user attributes

        PRD Story 2.2 @AC4 - Map SAML attributes to user
        """
        # Parse attribute mapping
        try:
            attribute_mapping = json.loads(self.config.attribute_mapping)
        except json.JSONDecodeError:
            attribute_mapping = {
                "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
                "groups": "http://schemas.xmlsoap.org/claims/Group",
            }

        saml_attributes = saml_data.get("attributes", {})
        nameid = saml_data.get("nameid")

        # Map attributes
        mapped_attrs = {}
        for local_attr, saml_attr in attribute_mapping.items():
            if saml_attr in saml_attributes:
                # SAML attributes are arrays, take first value
                value = saml_attributes[saml_attr]
                mapped_attrs[local_attr] = value[0] if isinstance(value, list) else value

        # Ensure required fields
        if "email" not in mapped_attrs:
            mapped_attrs["email"] = nameid

        if "name" not in mapped_attrs:
            mapped_attrs["name"] = mapped_attrs["email"]

        mapped_attrs["external_id"] = nameid
        mapped_attrs["session_index"] = saml_data.get("session_index")

        return mapped_attrs

    async def auto_provision_user(
        self, db: AsyncSession, user_claims: dict[str, Any]
    ) -> User:
        """Auto-provision user from SAML claims.

        Args:
            db: Database session
            user_claims: Mapped user claims

        Returns:
            User object (existing or newly created)

        PRD Story 2.2 @AC4 - Auto-provision users
        """
        email = user_claims.get("email")
        if not email:
            raise SAMLAuthenticationError("Email not found in SAML claims")

        # Check if user exists
        stmt = select(User).where(User.username == email)
        result = await db.exec(stmt)
        user = result.first()

        if user:
            logger.info(f"Existing user found for SAML login: {email}")
            return user

        # Auto-provision new user
        if not self.config.auto_provision_users:
            raise SAMLAuthenticationError(
                f"Auto-provisioning disabled and user {email} not found"
            )

        user = User(
            username=email,
            is_active=True,
            is_superuser=False,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Auto-provisioned new user from SAML: {email}")

        # TODO: Assign default role if configured
        if self.config.default_role_id:
            # Create grant with default role
            pass

        return user

    async def create_sso_session(
        self,
        db: AsyncSession,
        user: User,
        external_id: str,
        claims: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> SSOSession:
        """Create SSO session for user.

        Args:
            db: Database session
            user: User object
            external_id: External user ID from SAML IdP
            claims: SAML claims
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            SSOSession object

        PRD Story 2.2 @AC3 - Track SSO sessions
        """
        session = SSOSession(
            user_id=user.id,
            sso_config_id=self.config.id,
            external_id=external_id,
            session_token=str(uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
            ip_address=ip_address,
            user_agent=user_agent,
            sso_claims=json.dumps(claims),
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        logger.info(f"Created SSO session {session.id} for user {user.username}")
        return session

    async def authenticate(
        self,
        db: AsyncSession,
        request_data: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, SSOSession]:
        """Complete SAML authentication flow.

        Args:
            db: Database session
            request_data: HTTP request with SAML response
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (User, SSOSession)

        PRD Story 2.2 - Complete SAML authentication
        """
        # Process SAML response
        saml_data = await self.process_saml_response(request_data)

        # Extract user claims
        user_claims = self.extract_user_claims(saml_data)

        # Auto-provision user
        user = await self.auto_provision_user(db, user_claims)

        # Create SSO session
        sso_session = await self.create_sso_session(
            db=db,
            user=user,
            external_id=user_claims["external_id"],
            claims=saml_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user, sso_session

    def generate_metadata(self) -> str:
        """Generate SAML SP metadata XML.

        Returns:
            SAML metadata XML string

        PRD Story 2.3 @AC2 - SAML metadata endpoint
        """
        settings = OneLogin_Saml2_Settings(self.saml_settings)
        metadata = settings.get_sp_metadata()
        errors = settings.validate_metadata(metadata)

        if errors:
            raise SAMLAuthenticationError(f"Invalid SAML metadata: {errors}")

        return metadata

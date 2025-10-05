"""OIDC (OpenID Connect) authentication implementation.

PRD Story 2.2 - Enterprise SSO Integration
PRD Story 2.3 @AC1 - Support OIDC
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import httpx
from fastapi import HTTPException, status
from jose import jwt
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.auth.encryption import decrypt_secret
from langflow.services.database.models.sso_config import SSOConfig, SSOProtocol, SSOSession
from langflow.services.database.models.user.model import User


class OIDCAuthenticationError(Exception):
    """OIDC authentication error."""

    pass


class OIDCService:
    """OIDC authentication service.

    Implements OpenID Connect authentication flow:
    1. Redirect to OIDC provider for authentication
    2. Handle callback with authorization code
    3. Exchange code for tokens
    4. Verify ID token
    5. Extract user claims
    6. Auto-provision user if needed
    """

    def __init__(self, sso_config: SSOConfig):
        """Initialize OIDC service.

        Args:
            sso_config: SSO configuration with OIDC settings
        """
        if sso_config.protocol != SSOProtocol.OIDC:
            raise ValueError(f"Invalid protocol: {sso_config.protocol}. Expected OIDC.")

        self.config = sso_config
        self.issuer = sso_config.oidc_issuer
        self.client_id = sso_config.oidc_client_id
        # CRITICAL FIX #1: Decrypt client secret
        self.client_secret = decrypt_secret(sso_config.oidc_client_secret) if sso_config.oidc_client_secret else None
        self.redirect_uri = sso_config.oidc_redirect_uri
        self.scopes = sso_config.oidc_scopes or "openid profile email"

        # OIDC endpoints (discovered from issuer)
        self.authorization_endpoint: str | None = None
        self.token_endpoint: str | None = None
        self.userinfo_endpoint: str | None = None
        self.jwks_uri: str | None = None
        self.issuer_metadata: dict[str, Any] = {}

    async def discover_endpoints(self) -> None:
        """Discover OIDC endpoints from provider.

        Uses OpenID Connect Discovery to fetch provider metadata.
        PRD Story 2.3 @AC1 - OIDC discovery
        """
        if not self.issuer:
            raise OIDCAuthenticationError("OIDC issuer not configured")

        discovery_url = f"{self.issuer.rstrip('/')}/.well-known/openid-configuration"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(discovery_url, timeout=10.0)
                response.raise_for_status()
                metadata = response.json()

                self.issuer_metadata = metadata
                self.authorization_endpoint = metadata.get("authorization_endpoint")
                self.token_endpoint = metadata.get("token_endpoint")
                self.userinfo_endpoint = metadata.get("userinfo_endpoint")
                self.jwks_uri = metadata.get("jwks_uri")

                logger.info(f"Discovered OIDC endpoints for issuer: {self.issuer}")

        except httpx.HTTPError as e:
            logger.error(f"Failed to discover OIDC endpoints: {e}")
            raise OIDCAuthenticationError(f"OIDC discovery failed: {e}")

    def get_authorization_url(self, state: str) -> str:
        """Generate authorization URL for OIDC login.

        Args:
            state: CSRF protection state parameter

        Returns:
            Authorization URL to redirect user to

        PRD Story 2.2 @AC2 - Initiate SSO login
        """
        if not self.authorization_endpoint:
            raise OIDCAuthenticationError("Authorization endpoint not discovered")

        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": self.scopes,
            "redirect_uri": self.redirect_uri,
            "state": state,
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorization_endpoint}?{query_string}"

    async def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from OIDC provider

        Returns:
            Token response with id_token, access_token, refresh_token

        PRD Story 2.2 @AC2 - Exchange code for tokens
        """
        if not self.token_endpoint:
            raise OIDCAuthenticationError("Token endpoint not discovered")

        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=token_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Token exchange failed: {e}")
            raise OIDCAuthenticationError(f"Token exchange failed: {e}")

    async def verify_id_token(self, id_token: str) -> dict[str, Any]:
        """Verify and decode ID token.

        Args:
            id_token: JWT ID token from OIDC provider

        Returns:
            Decoded claims from ID token

        PRD Story 2.2 @AC2 - Verify ID token
        """
        try:
            # In production, should fetch JWKS and verify signature
            # For now, decode without verification (INSECURE - for development only)
            unverified_claims = jwt.get_unverified_claims(id_token)

            # Verify issuer
            if unverified_claims.get("iss") != self.issuer:
                raise OIDCAuthenticationError("Invalid issuer in ID token")

            # Verify audience
            if unverified_claims.get("aud") != self.client_id:
                raise OIDCAuthenticationError("Invalid audience in ID token")

            # Verify expiration
            exp = unverified_claims.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise OIDCAuthenticationError("ID token expired")

            logger.info(f"Verified ID token for subject: {unverified_claims.get('sub')}")
            return unverified_claims

        except Exception as e:
            logger.error(f"ID token verification failed: {e}")
            raise OIDCAuthenticationError(f"ID token verification failed: {e}")

    async def get_userinfo(self, access_token: str) -> dict[str, Any]:
        """Fetch user information from userinfo endpoint.

        Args:
            access_token: Access token from OIDC provider

        Returns:
            User claims from userinfo endpoint

        PRD Story 2.2 @AC2 - Fetch user info
        """
        if not self.userinfo_endpoint:
            raise OIDCAuthenticationError("Userinfo endpoint not discovered")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Userinfo request failed: {e}")
            raise OIDCAuthenticationError(f"Userinfo request failed: {e}")

    def extract_user_claims(self, id_token_claims: dict[str, Any], userinfo: dict[str, Any]) -> dict[str, Any]:
        """Extract and map user claims from OIDC provider.

        Args:
            id_token_claims: Claims from ID token
            userinfo: Claims from userinfo endpoint

        Returns:
            Mapped user attributes

        PRD Story 2.2 @AC4 - Map OIDC attributes to user
        """
        # Parse attribute mapping
        try:
            attribute_mapping = json.loads(self.config.attribute_mapping)
        except json.JSONDecodeError:
            attribute_mapping = {"email": "email", "name": "name", "groups": "groups"}

        # Combine claims (userinfo takes precedence)
        all_claims = {**id_token_claims, **userinfo}

        # Map attributes
        mapped_attrs = {}
        for local_attr, remote_attr in attribute_mapping.items():
            if remote_attr in all_claims:
                mapped_attrs[local_attr] = all_claims[remote_attr]

        # Ensure required fields
        if "email" not in mapped_attrs:
            mapped_attrs["email"] = all_claims.get("email") or all_claims.get("sub")

        if "name" not in mapped_attrs:
            mapped_attrs["name"] = all_claims.get("name") or mapped_attrs["email"]

        mapped_attrs["external_id"] = id_token_claims.get("sub")

        return mapped_attrs

    async def auto_provision_user(
        self, db: AsyncSession, user_claims: dict[str, Any]
    ) -> User:
        """Auto-provision user from OIDC claims.

        Args:
            db: Database session
            user_claims: Mapped user claims

        Returns:
            User object (existing or newly created)

        PRD Story 2.2 @AC4 - Auto-provision users
        """
        email = user_claims.get("email")
        if not email:
            raise OIDCAuthenticationError("Email not found in user claims")

        # Check if user exists
        stmt = select(User).where(User.username == email)
        result = await db.exec(stmt)
        user = result.first()

        if user:
            logger.info(f"Existing user found for OIDC login: {email}")
            return user

        # Auto-provision new user
        if not self.config.auto_provision_users:
            raise OIDCAuthenticationError(
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

        logger.info(f"Auto-provisioned new user from OIDC: {email}")

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
            external_id: External user ID from SSO provider
            claims: SSO provider claims
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
        authorization_code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[User, SSOSession]:
        """Complete OIDC authentication flow.

        Args:
            db: Database session
            authorization_code: Authorization code from OIDC provider
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (User, SSOSession)

        PRD Story 2.2 - Complete SSO authentication
        """
        # Ensure endpoints are discovered
        if not self.token_endpoint:
            await self.discover_endpoints()

        # Exchange code for tokens
        tokens = await self.exchange_code_for_tokens(authorization_code)

        # Verify ID token
        id_token_claims = await self.verify_id_token(tokens["id_token"])

        # Get userinfo
        userinfo = await self.get_userinfo(tokens["access_token"])

        # Extract user claims
        user_claims = self.extract_user_claims(id_token_claims, userinfo)

        # Auto-provision user
        user = await self.auto_provision_user(db, user_claims)

        # Create SSO session
        sso_session = await self.create_sso_session(
            db=db,
            user=user,
            external_id=user_claims["external_id"],
            claims={**id_token_claims, **userinfo},
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return user, sso_session

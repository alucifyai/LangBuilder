"""
OIDC (OpenID Connect) Authentication Provider

Handles OAuth 2.0 / OIDC authentication flow.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from langflow.services.database.models.sso.model import SSOConfiguration


class OIDCProvider:
    """OIDC authentication provider."""

    def __init__(self, config: SSOConfiguration):
        """Initialize OIDC provider with configuration."""
        if not config.oidc_issuer:
            raise ValueError("OIDC issuer is required")
        if not config.oidc_client_id:
            raise ValueError("OIDC client ID is required")
        if not config.oidc_client_secret:
            raise ValueError("OIDC client secret is required")

        self.config = config
        self.issuer = config.oidc_issuer
        self.client_id = config.oidc_client_id
        self.client_secret = config.oidc_client_secret
        self.authorization_endpoint = config.oidc_authorization_endpoint
        self.token_endpoint = config.oidc_token_endpoint
        self.userinfo_endpoint = config.oidc_userinfo_endpoint
        self.jwks_uri = config.oidc_jwks_uri

    async def discover_endpoints(self) -> dict[str, str]:
        """
        Discover OIDC endpoints from .well-known/openid-configuration.

        Returns:
            Dictionary with endpoint URLs
        """
        discovery_url = f"{self.issuer}/.well-known/openid-configuration"

        async with httpx.AsyncClient() as client:
            response = await client.get(discovery_url)
            response.raise_for_status()
            config = response.json()

        # Update configuration if endpoints not set
        if not self.authorization_endpoint:
            self.authorization_endpoint = config.get("authorization_endpoint")
        if not self.token_endpoint:
            self.token_endpoint = config.get("token_endpoint")
        if not self.userinfo_endpoint:
            self.userinfo_endpoint = config.get("userinfo_endpoint")
        if not self.jwks_uri:
            self.jwks_uri = config.get("jwks_uri")

        return config

    def generate_authorization_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        scope: str = "openid email profile",
    ) -> str:
        """
        Generate OIDC authorization URL for login redirect.

        Args:
            redirect_uri: Callback URL after authentication
            state: CSRF protection state parameter
            scope: OAuth scopes to request

        Returns:
            Authorization URL
        """
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state,
        }

        return f"{self.authorization_endpoint}?{urlencode(params)}"

    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """
        Exchange authorization code for access token and ID token.

        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            Token response with access_token, id_token, etc.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def verify_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Verify and decode ID token JWT.

        Args:
            id_token: JWT ID token from OIDC provider

        Returns:
            Decoded token claims

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        # Get signing keys from JWKS endpoint
        jwks_client = PyJWKClient(self.jwks_uri)
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)

        # Verify and decode token
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=self.client_id,
            issuer=self.issuer,
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
            # Allow clock skew
            leeway=self.config.allow_clock_skew_seconds,
        )

        return claims

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """
        Fetch user info from userinfo endpoint.

        Args:
            access_token: Access token from token exchange

        Returns:
            User information dictionary
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(self.userinfo_endpoint, headers=headers)
            response.raise_for_status()
            return response.json()

    def extract_user_attributes(self, claims: dict[str, Any]) -> dict[str, Any]:
        """
        Extract user attributes from ID token claims.

        Args:
            claims: ID token claims

        Returns:
            Dictionary with email, name, groups, etc.
        """
        email_attr = self.config.email_attribute or "email"
        name_attr = self.config.name_attribute or "name"
        groups_attr = self.config.groups_attribute or "groups"

        attributes = {
            "email": claims.get(email_attr),
            "name": claims.get(name_attr),
            "groups": claims.get(groups_attr, []),
            "sub": claims.get("sub"),  # Subject identifier
            "mfa_verified": claims.get("amr") is not None,  # Authentication Methods Reference
        }

        return attributes

    def validate_assertion_timing(self, claims: dict[str, Any]) -> bool:
        """
        Validate assertion timing with clock skew tolerance.

        Args:
            claims: ID token claims with iat, exp

        Returns:
            True if timing is valid
        """
        now = datetime.now(timezone.utc)
        skew = timedelta(seconds=self.config.allow_clock_skew_seconds)

        # Check issued at time
        if "iat" in claims:
            iat = datetime.fromtimestamp(claims["iat"], tz=timezone.utc)
            if iat > now + skew:
                return False

        # Check expiration (already checked by jwt.decode, but explicit check)
        if "exp" in claims:
            exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
            if exp < now - skew:
                return False

        # Check not before if present
        if "nbf" in claims:
            nbf = datetime.fromtimestamp(claims["nbf"], tz=timezone.utc)
            if nbf > now + skew:
                return False

        return True

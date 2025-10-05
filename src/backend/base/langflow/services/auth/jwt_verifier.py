"""JWT signature verification for SSO tokens.

CRITICAL FIX from Phase 5 Audit - Recommendation #1:
Implements JWT signature verification with JWKS support for OIDC tokens.

PRD Story 2.2 - SSO Authentication
Phase 4 Critical Fix #3 - JWT Token Trust
"""

import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from loguru import logger

from langflow.services.database.models.sso_config import SSOConfig


class JWTVerificationError(Exception):
    """JWT verification failed."""

    pass


class JWTVerifier:
    """JWT signature verification service.

    Verifies JWT tokens from OIDC providers using JWKS.
    Phase 5 Audit - Critical Recommendation #1
    """

    def __init__(self, sso_config: SSOConfig):
        """Initialize JWT verifier.

        Args:
            sso_config: SSO configuration with OIDC settings
        """
        self.sso_config = sso_config
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cache_time: datetime | None = None

    async def verify_token(
        self,
        token: str,
        nonce: str | None = None,
        max_age: int | None = None,
    ) -> dict[str, Any]:
        """Verify JWT token signature and claims.

        Args:
            token: JWT token to verify
            nonce: Expected nonce (optional)
            max_age: Maximum age in seconds (optional)

        Returns:
            Verified token claims

        Raises:
            JWTVerificationError: If verification fails

        PRD Story 2.2 @AC3 - Verify SSO tokens
        """
        try:
            # Step 1: Get signing key from JWKS
            signing_key = await self._get_signing_key(token)

            # Step 2: Verify signature and decode
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256", "RS384", "RS512"],
                audience=self.sso_config.oidc_client_id,
                issuer=self.sso_config.oidc_issuer,
            )

            # Step 3: Verify standard claims
            self._verify_standard_claims(claims, nonce, max_age)

            logger.info(f"JWT verified successfully for subject: {claims.get('sub')}")
            return claims

        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            raise JWTVerificationError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            raise JWTVerificationError(f"Verification error: {e}")

    async def _get_signing_key(self, token: str) -> dict[str, Any]:
        """Get signing key from JWKS.

        Args:
            token: JWT token (to extract kid)

        Returns:
            Signing key for verification

        Raises:
            JWTVerificationError: If key not found
        """
        # Get unverified header to extract kid
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                raise JWTVerificationError("Token missing kid in header")
        except Exception as e:
            raise JWTVerificationError(f"Invalid token header: {e}")

        # Fetch JWKS (with caching)
        jwks = await self._fetch_jwks()

        # Find matching key
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwk.construct(key)

        raise JWTVerificationError(f"Signing key not found: {kid}")

    async def _fetch_jwks(self) -> dict[str, Any]:
        """Fetch JWKS from provider.

        Returns:
            JWKS document

        Raises:
            JWTVerificationError: If fetch fails
        """
        # Check cache (5 minute TTL)
        if self._jwks_cache and self._jwks_cache_time:
            age = (datetime.now(timezone.utc) - self._jwks_cache_time).total_seconds()
            if age < 300:  # 5 minutes
                logger.debug("Using cached JWKS")
                return self._jwks_cache

        # Fetch from JWKS URI
        jwks_uri = self._get_jwks_uri()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(jwks_uri, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()

            # Cache
            self._jwks_cache = jwks
            self._jwks_cache_time = datetime.now(timezone.utc)

            logger.info(f"Fetched JWKS from {jwks_uri}")
            return jwks

        except Exception as e:
            logger.error(f"Failed to fetch JWKS from {jwks_uri}: {e}")
            raise JWTVerificationError(f"JWKS fetch failed: {e}")

    def _get_jwks_uri(self) -> str:
        """Get JWKS URI from discovery or config.

        Returns:
            JWKS URI
        """
        # If JWKS URI is configured, use it
        if hasattr(self.sso_config, "oidc_jwks_uri") and self.sso_config.oidc_jwks_uri:
            return self.sso_config.oidc_jwks_uri

        # Otherwise, construct from issuer
        issuer = self.sso_config.oidc_issuer
        if not issuer:
            raise JWTVerificationError("OIDC issuer not configured")

        # Standard JWKS path
        return urljoin(issuer, "/.well-known/jwks.json")

    def _verify_standard_claims(
        self,
        claims: dict[str, Any],
        nonce: str | None = None,
        max_age: int | None = None,
    ) -> None:
        """Verify standard JWT claims.

        Args:
            claims: Decoded claims
            nonce: Expected nonce
            max_age: Maximum age in seconds

        Raises:
            JWTVerificationError: If verification fails
        """
        now = datetime.now(timezone.utc).timestamp()

        # Verify expiration (exp)
        exp = claims.get("exp")
        if not exp:
            raise JWTVerificationError("Token missing exp claim")
        if now >= exp:
            raise JWTVerificationError("Token expired")

        # Verify issued at (iat)
        iat = claims.get("iat")
        if not iat:
            raise JWTVerificationError("Token missing iat claim")
        if iat > now + 60:  # Allow 60 second clock skew
            raise JWTVerificationError("Token issued in the future")

        # Verify not before (nbf) if present
        nbf = claims.get("nbf")
        if nbf and now < nbf - 60:  # Allow 60 second clock skew
            raise JWTVerificationError("Token not yet valid")

        # Verify nonce if provided
        if nonce:
            token_nonce = claims.get("nonce")
            if not token_nonce:
                raise JWTVerificationError("Token missing nonce claim")
            if token_nonce != nonce:
                raise JWTVerificationError("Nonce mismatch")

        # Verify max_age if provided
        if max_age is not None:
            auth_time = claims.get("auth_time")
            if not auth_time:
                raise JWTVerificationError("Token missing auth_time claim")
            age = now - auth_time
            if age > max_age:
                raise JWTVerificationError(f"Token too old: {age}s > {max_age}s")

        # Verify issuer (already done by jose.jwt.decode)
        # Verify audience (already done by jose.jwt.decode)

        logger.debug("All standard claims verified")

    def extract_user_info(self, claims: dict[str, Any]) -> dict[str, Any]:
        """Extract user information from verified claims.

        Args:
            claims: Verified JWT claims

        Returns:
            User information dict with:
            - sub: Subject (unique user ID)
            - email: User email
            - name: Full name
            - given_name: First name
            - family_name: Last name
            - groups: Group memberships (if available)
        """
        return {
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "email_verified": claims.get("email_verified", False),
            "name": claims.get("name"),
            "given_name": claims.get("given_name"),
            "family_name": claims.get("family_name"),
            "preferred_username": claims.get("preferred_username"),
            "groups": claims.get("groups", []),
            "roles": claims.get("roles", []),
        }


# Global verifier cache (per SSO config)
_verifier_cache: dict[str, JWTVerifier] = {}


def get_jwt_verifier(sso_config: SSOConfig) -> JWTVerifier:
    """Get JWT verifier for SSO config.

    Args:
        sso_config: SSO configuration

    Returns:
        JWTVerifier instance
    """
    config_id = str(sso_config.id)
    if config_id not in _verifier_cache:
        _verifier_cache[config_id] = JWTVerifier(sso_config)
    return _verifier_cache[config_id]

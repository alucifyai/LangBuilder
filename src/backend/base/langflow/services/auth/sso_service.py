"""
SSO Authentication Service

Unified service for SSO authentication (OIDC and SAML).
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.sso_oidc import OIDCProvider
from langflow.services.auth.sso_saml import SAMLProvider
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.sso.crud import (
    check_assertion_used,
    create_sso_session,
    get_sso_config_by_domain,
    get_sso_config_by_org,
    mark_assertion_used,
)
from langflow.services.database.models.sso.model import SSOConfiguration, SSOEnforcement, SSOProvider
from langflow.services.database.models.user.crud import get_user_by_email


class SSOAuthenticationError(Exception):
    """Exception raised during SSO authentication."""

    pass


class SSOService:
    """SSO authentication service."""

    @staticmethod
    async def get_sso_config_for_domain(db: AsyncSession, domain: str) -> SSOConfiguration | None:
        """Get SSO configuration for a domain."""
        return await get_sso_config_by_domain(db, domain)

    @staticmethod
    async def get_sso_config_for_org(db: AsyncSession, org_id: str) -> SSOConfiguration | None:
        """Get SSO configuration for an organization."""
        return await get_sso_config_by_org(db, org_id)

    @staticmethod
    async def initiate_sso_login(
        db: AsyncSession,
        domain: str,
        redirect_uri: str,
        state: str | None = None,
    ) -> dict[str, str]:
        """
        Initiate SSO login flow (SP-initiated).

        Args:
            db: Database session
            domain: Company domain
            redirect_uri: Callback URL
            state: CSRF protection state

        Returns:
            Dictionary with redirect_url and provider info
        """
        # Get SSO configuration
        config = await get_sso_config_by_domain(db, domain)
        if not config or not config.enabled:
            raise SSOAuthenticationError("SSO not configured for this domain")

        # Generate authorization URL based on provider
        if config.provider_type == SSOProvider.OIDC:
            provider = OIDCProvider(config)
            redirect_url = provider.generate_authorization_url(redirect_uri, state)

            return {
                "provider": "oidc",
                "redirect_url": redirect_url,
                "state": state or "",
            }

        elif config.provider_type == SSOProvider.SAML:
            provider = SAMLProvider(config)
            request_id, saml_request = provider.generate_authn_request(
                sp_entity_id=f"langbuilder-{config.organization_id}",
                acs_url=redirect_uri,
                relay_state=state,
            )

            # SAML redirect (HTTP-Redirect binding)
            redirect_url = f"{provider.sso_url}?SAMLRequest={saml_request}"
            if state:
                redirect_url += f"&RelayState={state}"

            return {
                "provider": "saml",
                "redirect_url": redirect_url,
                "request_id": request_id,
            }

        raise SSOAuthenticationError(f"Unsupported provider: {config.provider_type}")

    @staticmethod
    async def process_oidc_callback(
        db: AsyncSession,
        code: str,
        redirect_uri: str,
        domain: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """
        Process OIDC callback and authenticate user.

        Args:
            db: Database session
            code: Authorization code
            redirect_uri: Callback URL
            domain: Company domain
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Dictionary with user info and session token
        """
        # Get SSO configuration
        config = await get_sso_config_by_domain(db, domain)
        if not config or config.provider_type != SSOProvider.OIDC:
            raise SSOAuthenticationError("Invalid SSO configuration")

        provider = OIDCProvider(config)

        # Exchange code for tokens
        token_response = await provider.exchange_code_for_token(code, redirect_uri)
        id_token = token_response.get("id_token")
        access_token = token_response.get("access_token")

        if not id_token:
            raise SSOAuthenticationError("No ID token in response")

        # Verify ID token
        claims = await provider.verify_id_token(id_token)

        # Check assertion ID for replay protection
        assertion_id = claims.get("jti") or claims.get("nonce")
        if not assertion_id:
            assertion_id = f"{claims.get('sub')}:{claims.get('iat')}"

        if await check_assertion_used(db, assertion_id):
            raise SSOAuthenticationError("Replay detected")

        # Validate timing
        if not provider.validate_assertion_timing(claims):
            raise SSOAuthenticationError("Invalid assertion timing")

        # Extract user attributes
        user_attrs = provider.extract_user_attributes(claims)

        # Map to existing user by email
        user = await get_user_by_email(db, user_attrs["email"])
        if not user:
            raise SSOAuthenticationError("Your account is not provisioned in LangBuilder")

        # Mark assertion as used
        exp = datetime.fromtimestamp(claims.get("exp"), tz=timezone.utc)
        await mark_assertion_used(db, assertion_id, user.id, exp)

        # Create SSO session
        session_token = f"sso_{UUID(int=int.from_bytes(assertion_id.encode()[:16], 'big'))}"
        session_expires = datetime.now(timezone.utc) + timedelta(
            minutes=config.session_timeout_minutes
        )

        await create_sso_session(
            db=db,
            user_id=user.id,
            sso_config_id=UUID(config.id),
            assertion_id=assertion_id,
            assertion_issued_at=datetime.fromtimestamp(claims.get("iat"), tz=timezone.utc),
            assertion_expires_at=exp,
            session_token=session_token,
            expires_at=session_expires,
            ip_address=ip_address,
            user_agent=user_agent,
            mfa_verified=user_attrs.get("mfa_verified", False),
        )

        # Create audit log
        await create_audit_log(
            db=db,
            actor_id=user.id,
            action=AuditAction.GRANT_CREATED,  # TODO: Add SSO_LOGIN action
            resource_type="sso_session",
            resource_id=session_token,
            metadata={
                "provider": "oidc",
                "mfa_verified": user_attrs.get("mfa_verified"),
                "ip_address": ip_address,
            },
        )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "session_token": session_token,
            "expires_at": session_expires.isoformat(),
            "mfa_verified": user_attrs.get("mfa_verified", False),
        }

    @staticmethod
    async def process_saml_response(
        db: AsyncSession,
        saml_response: str,
        domain: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """
        Process SAML response and authenticate user.

        Args:
            db: Database session
            saml_response: Base64-encoded SAML response
            domain: Company domain
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Dictionary with user info and session token
        """
        # Get SSO configuration
        config = await get_sso_config_by_domain(db, domain)
        if not config or config.provider_type != SSOProvider.SAML:
            raise SSOAuthenticationError("Invalid SSO configuration")

        provider = SAMLProvider(config)

        # Parse SAML response
        assertion_data = provider.parse_saml_response(saml_response)

        # Check assertion ID for replay protection
        assertion_id = assertion_data["assertion_id"]
        if await check_assertion_used(db, assertion_id):
            raise SSOAuthenticationError("Replay detected")

        # Validate timing
        if not provider.validate_assertion_timing(
            assertion_data["conditions"],
            config.allow_clock_skew_seconds,
        ):
            raise SSOAuthenticationError("Invalid assertion timing")

        # Verify signature (placeholder - implement with xmlsec in production)
        if not provider.verify_signature(saml_response):
            raise SSOAuthenticationError("Invalid signature")

        # Extract user attributes
        user_attrs = provider.extract_user_attributes(assertion_data)

        # Map to existing user by email
        user = await get_user_by_email(db, user_attrs["email"])
        if not user:
            raise SSOAuthenticationError("Your account is not provisioned in LangBuilder")

        # Mark assertion as used
        # Parse NotOnOrAfter for expiration
        not_on_or_after_str = assertion_data["conditions"].get("not_on_or_after")
        if not_on_or_after_str:
            exp = datetime.fromisoformat(not_on_or_after_str.replace("Z", "+00:00"))
        else:
            exp = datetime.now(timezone.utc) + timedelta(hours=1)

        await mark_assertion_used(db, assertion_id, user.id, exp)

        # Create SSO session
        session_token = f"sso_saml_{assertion_id[:16]}"
        session_expires = datetime.now(timezone.utc) + timedelta(
            minutes=config.session_timeout_minutes
        )

        issue_instant = datetime.fromisoformat(
            assertion_data["issue_instant"].replace("Z", "+00:00")
        )

        await create_sso_session(
            db=db,
            user_id=user.id,
            sso_config_id=UUID(config.id),
            assertion_id=assertion_id,
            assertion_issued_at=issue_instant,
            assertion_expires_at=exp,
            session_token=session_token,
            expires_at=session_expires,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Create audit log
        await create_audit_log(
            db=db,
            actor_id=user.id,
            action=AuditAction.GRANT_CREATED,  # TODO: Add SSO_LOGIN action
            resource_type="sso_session",
            resource_id=session_token,
            metadata={
                "provider": "saml",
                "ip_address": ip_address,
            },
        )

        return {
            "user_id": str(user.id),
            "email": user.email,
            "session_token": session_token,
            "expires_at": session_expires.isoformat(),
        }

    @staticmethod
    async def check_sso_enforcement(db: AsyncSession, domain: str) -> SSOEnforcement:
        """
        Check if SSO is enforced for a domain.

        Args:
            db: Database session
            domain: Company domain

        Returns:
            SSO enforcement level
        """
        config = await get_sso_config_by_domain(db, domain)
        if not config or not config.enabled:
            return SSOEnforcement.DISABLED

        return config.enforcement

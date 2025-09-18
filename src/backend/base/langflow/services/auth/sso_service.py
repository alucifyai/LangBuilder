"""SSO integration framework for RBAC system.

This module provides Single Sign-On integration following LangBuilder patterns,
supporting OIDC, SAML2, OAuth2, and LDAP protocols.
"""

# NO future annotations per Phase 1 requirements
from typing import TYPE_CHECKING

import base64
import json
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse
from uuid import UUID

import httpx
from loguru import logger
from pydantic import BaseModel, EmailStr
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.base import Service
from langflow.schema.serialize import UUIDstr

if TYPE_CHECKING:
    from langflow.services.database.models.rbac.sso_configuration import SSOConfiguration
    from langflow.services.database.models.user.model import User


class SSOProtocol(str, Enum):
    """Supported SSO protocols."""

    OIDC = "oidc"
    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    LDAP = "ldap"


class SSOFlowState(str, Enum):
    """SSO authentication flow states."""

    INITIATED = "initiated"
    AUTHENTICATED = "authenticated"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SSOUserClaims:
    """User claims extracted from SSO provider."""

    sub: str  # Subject identifier
    email: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    groups: Optional[List[str]] = None
    roles: Optional[List[str]] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None


@dataclass
class SSOFlowContext:
    """Context for SSO authentication flow."""

    state: str
    nonce: str
    provider_id: UUIDstr
    redirect_uri: str
    initiated_at: datetime
    expires_at: datetime
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class SSOAuthenticationResult(BaseModel):
    """Result of SSO authentication process."""

    success: bool
    user_claims: Optional[SSOUserClaims] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None
    flow_state: SSOFlowState = SSOFlowState.FAILED


class SSOProvider(ABC):
    """Abstract base class for SSO providers following LangBuilder patterns."""

    def __init__(self, configuration: "SSOConfiguration"):
        """Initialize SSO provider with configuration."""
        self.configuration = configuration
        self.protocol = SSOProtocol(configuration.protocol)
        self.client_id = configuration.client_id
        self.client_secret = configuration.client_secret
        self.base_url = configuration.provider_url
        self.scopes = configuration.scopes or []
        self.attribute_mapping = configuration.attribute_mapping or {}

    @abstractmethod
    async def initiate_flow(
        self,
        redirect_uri: str,
        state: str,
        nonce: str,
    ) -> str:
        """Initiate SSO authentication flow.

        Args:
            redirect_uri: Callback URI after authentication
            state: State parameter for CSRF protection
            nonce: Nonce for replay protection

        Returns:
            Authorization URL to redirect user to
        """
        pass

    @abstractmethod
    async def handle_callback(
        self,
        authorization_code: str,
        state: str,
        nonce: str,
    ) -> SSOAuthenticationResult:
        """Handle SSO callback and extract user claims.

        Args:
            authorization_code: Authorization code from provider
            state: State parameter for validation
            nonce: Nonce for validation

        Returns:
            Authentication result with user claims
        """
        pass

    @abstractmethod
    async def validate_token(
        self,
        token: str,
    ) -> SSOAuthenticationResult:
        """Validate SSO token and extract claims.

        Args:
            token: Token to validate

        Returns:
            Authentication result with user claims
        """
        pass

    def map_attributes(self, provider_claims: Dict[str, Any]) -> SSOUserClaims:
        """Map provider-specific claims to standard user claims.

        Args:
            provider_claims: Raw claims from SSO provider

        Returns:
            Mapped user claims
        """
        # Default mapping
        default_mapping = {
            "sub": "sub",
            "email": "email",
            "name": "name",
            "given_name": "given_name",
            "family_name": "family_name",
            "groups": "groups",
        }

        # Apply custom attribute mapping
        mapping = {**default_mapping, **self.attribute_mapping}

        mapped_claims = {}
        for standard_field, provider_field in mapping.items():
            if provider_field in provider_claims:
                mapped_claims[standard_field] = provider_claims[provider_field]

        # Extract groups and roles
        groups = mapped_claims.get("groups", [])
        if isinstance(groups, str):
            groups = [groups]

        roles = provider_claims.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]

        return SSOUserClaims(
            sub=mapped_claims.get("sub", ""),
            email=mapped_claims.get("email", ""),
            name=mapped_claims.get("name"),
            given_name=mapped_claims.get("given_name"),
            family_name=mapped_claims.get("family_name"),
            groups=groups,
            roles=roles,
            department=provider_claims.get("department"),
            organization=provider_claims.get("organization"),
            custom_attributes={
                k: v for k, v in provider_claims.items()
                if k not in ["sub", "email", "name", "given_name", "family_name", "groups", "roles"]
            },
        )


class OIDCProvider(SSOProvider):
    """OpenID Connect provider implementation."""

    def __init__(self, configuration: "SSOConfiguration"):
        """Initialize OIDC provider."""
        super().__init__(configuration)
        self.discovery_url = f"{self.base_url}/.well-known/openid_configuration"
        self._discovery_cache: Optional[Dict[str, Any]] = None
        self._cache_expires_at: Optional[datetime] = None

    async def initiate_flow(
        self,
        redirect_uri: str,
        state: str,
        nonce: str,
    ) -> str:
        """Initiate OIDC authentication flow."""
        discovery = await self._get_discovery_document()
        auth_endpoint = discovery.get("authorization_endpoint")

        if not auth_endpoint:
            raise ValueError("OIDC provider missing authorization endpoint")

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes or ["openid", "email", "profile"]),
            "state": state,
            "nonce": nonce,
        }

        return f"{auth_endpoint}?{urlencode(params)}"

    async def handle_callback(
        self,
        authorization_code: str,
        state: str,
        nonce: str,
    ) -> SSOAuthenticationResult:
        """Handle OIDC callback and exchange code for tokens."""
        try:
            discovery = await self._get_discovery_document()
            token_endpoint = discovery.get("token_endpoint")

            if not token_endpoint:
                return SSOAuthenticationResult(
                    success=False,
                    error_code="missing_token_endpoint",
                    error_message="OIDC provider missing token endpoint",
                )

            # Exchange authorization code for tokens
            token_response = await self._exchange_code_for_tokens(
                token_endpoint=token_endpoint,
                authorization_code=authorization_code,
            )

            if "error" in token_response:
                return SSOAuthenticationResult(
                    success=False,
                    error_code=token_response.get("error"),
                    error_message=token_response.get("error_description"),
                    provider_response=token_response,
                )

            # Validate and decode ID token
            id_token = token_response.get("id_token")
            if not id_token:
                return SSOAuthenticationResult(
                    success=False,
                    error_code="missing_id_token",
                    error_message="ID token not returned by provider",
                )

            # Decode ID token (simplified - in production use proper JWT validation)
            claims = await self._decode_id_token(id_token, nonce)

            # Map claims to standard format
            user_claims = self.map_attributes(claims)

            return SSOAuthenticationResult(
                success=True,
                user_claims=user_claims,
                flow_state=SSOFlowState.COMPLETED,
                provider_response=token_response,
            )

        except Exception as e:
            logger.error(f"OIDC callback handling failed: {e}")
            return SSOAuthenticationResult(
                success=False,
                error_code="callback_error",
                error_message=str(e),
            )

    async def validate_token(self, token: str) -> SSOAuthenticationResult:
        """Validate OIDC token at userinfo endpoint."""
        try:
            discovery = await self._get_discovery_document()
            userinfo_endpoint = discovery.get("userinfo_endpoint")

            if not userinfo_endpoint:
                return SSOAuthenticationResult(
                    success=False,
                    error_code="missing_userinfo_endpoint",
                    error_message="OIDC provider missing userinfo endpoint",
                )

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_endpoint,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    return SSOAuthenticationResult(
                        success=False,
                        error_code="userinfo_error",
                        error_message=f"Userinfo request failed: {response.status_code}",
                    )

                claims = response.json()
                user_claims = self.map_attributes(claims)

                return SSOAuthenticationResult(
                    success=True,
                    user_claims=user_claims,
                    flow_state=SSOFlowState.COMPLETED,
                    provider_response=claims,
                )

        except Exception as e:
            logger.error(f"OIDC token validation failed: {e}")
            return SSOAuthenticationResult(
                success=False,
                error_code="validation_error",
                error_message=str(e),
            )

    async def _get_discovery_document(self) -> Dict[str, Any]:
        """Get OIDC discovery document with caching."""
        now = datetime.now(timezone.utc)

        # Check cache
        if (self._discovery_cache and
            self._cache_expires_at and
            now < self._cache_expires_at):
            return self._discovery_cache

        # Fetch discovery document
        async with httpx.AsyncClient() as client:
            response = await client.get(self.discovery_url, timeout=30.0)
            response.raise_for_status()

            discovery = response.json()

            # Cache for 1 hour
            self._discovery_cache = discovery
            self._cache_expires_at = now + timedelta(hours=1)

            return discovery

    async def _exchange_code_for_tokens(
        self,
        token_endpoint: str,
        authorization_code: str,
    ) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )

            return response.json()

    async def _decode_id_token(self, id_token: str, expected_nonce: str) -> Dict[str, Any]:
        """Decode and validate ID token (simplified implementation)."""
        # Split JWT token
        parts = id_token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        # Decode payload (without signature validation for simplicity)
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        claims = json.loads(payload_bytes)

        # Validate nonce
        if claims.get("nonce") != expected_nonce:
            raise ValueError("Nonce mismatch")

        # Validate expiration
        exp = claims.get("exp")
        if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            raise ValueError("Token expired")

        return claims


class SAML2Provider(SSOProvider):
    """SAML 2.0 provider implementation (placeholder)."""

    async def initiate_flow(self, redirect_uri: str, state: str, nonce: str) -> str:
        """Initiate SAML2 authentication flow."""
        # TODO: Implement SAML2 authentication initiation
        raise NotImplementedError("SAML2 authentication not yet implemented")

    async def handle_callback(
        self,
        saml_response: str,
        state: str,
        nonce: str,
    ) -> SSOAuthenticationResult:
        """Handle SAML2 callback and extract user claims."""
        # TODO: Implement SAML2 response processing
        raise NotImplementedError("SAML2 callback handling not yet implemented")

    async def validate_token(self, token: str) -> SSOAuthenticationResult:
        """Validate SAML2 token."""
        # TODO: Implement SAML2 token validation
        raise NotImplementedError("SAML2 token validation not yet implemented")


class OAuth2Provider(SSOProvider):
    """OAuth 2.0 provider implementation."""

    async def initiate_flow(self, redirect_uri: str, state: str, nonce: str) -> str:
        """Initiate OAuth2 authentication flow."""
        auth_endpoint = f"{self.base_url}/oauth/authorize"

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(self.scopes or ["read:user", "user:email"]),
            "state": state,
        }

        return f"{auth_endpoint}?{urlencode(params)}"

    async def handle_callback(
        self,
        authorization_code: str,
        state: str,
        nonce: str,
    ) -> SSOAuthenticationResult:
        """Handle OAuth2 callback and exchange code for tokens."""
        try:
            token_endpoint = f"{self.base_url}/oauth/token"

            # Exchange code for access token
            data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    token_endpoint,
                    data=data,
                    headers={"Accept": "application/json"},
                    timeout=30.0,
                )

                if token_response.status_code != 200:
                    return SSOAuthenticationResult(
                        success=False,
                        error_code="token_exchange_failed",
                        error_message=f"Token exchange failed: {token_response.status_code}",
                    )

                tokens = token_response.json()
                access_token = tokens.get("access_token")

                if not access_token:
                    return SSOAuthenticationResult(
                        success=False,
                        error_code="missing_access_token",
                        error_message="Access token not returned",
                    )

                # Get user info
                user_response = await client.get(
                    f"{self.base_url}/user",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=30.0,
                )

                if user_response.status_code != 200:
                    return SSOAuthenticationResult(
                        success=False,
                        error_code="user_info_failed",
                        error_message=f"User info request failed: {user_response.status_code}",
                    )

                user_data = user_response.json()
                user_claims = self.map_attributes(user_data)

                return SSOAuthenticationResult(
                    success=True,
                    user_claims=user_claims,
                    flow_state=SSOFlowState.COMPLETED,
                    provider_response=user_data,
                )

        except Exception as e:
            logger.error(f"OAuth2 callback handling failed: {e}")
            return SSOAuthenticationResult(
                success=False,
                error_code="callback_error",
                error_message=str(e),
            )

    async def validate_token(self, token: str) -> SSOAuthenticationResult:
        """Validate OAuth2 token at user endpoint."""
        return await self.handle_callback(token, "", "")


class SSOService(Service):
    """SSO integration service following LangBuilder service patterns."""

    name = "sso_service"

    def __init__(self):
        """Initialize SSO service."""
        self._active_flows: Dict[str, SSOFlowContext] = {}
        self._provider_cache: Dict[UUIDstr, SSOProvider] = {}

    async def get_provider(
        self,
        session: AsyncSession,
        provider_id: UUIDstr,
    ) -> SSOProvider:
        """Get SSO provider instance with caching.

        Args:
            session: Database session
            provider_id: SSO provider configuration ID

        Returns:
            Configured SSO provider instance
        """
        # Check cache
        if provider_id in self._provider_cache:
            return self._provider_cache[provider_id]

        # Load from database
        from langflow.services.database.models.rbac.sso_configuration import SSOConfiguration

        config = await session.get(SSOConfiguration, provider_id)
        if not config or not config.is_active:
            raise ValueError(f"SSO provider {provider_id} not found or inactive")

        # Create provider instance
        if config.protocol == SSOProtocol.OIDC:
            provider = OIDCProvider(config)
        elif config.protocol == SSOProtocol.SAML2:
            provider = SAML2Provider(config)
        elif config.protocol == SSOProtocol.OAUTH2:
            provider = OAuth2Provider(config)
        else:
            raise ValueError(f"Unsupported SSO protocol: {config.protocol}")

        # Cache provider
        self._provider_cache[provider_id] = provider

        return provider

    async def initiate_sso_flow(
        self,
        session: AsyncSession,
        provider_id: UUIDstr,
        redirect_uri: str,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[str, str]:
        """Initiate SSO authentication flow.

        Args:
            session: Database session
            provider_id: SSO provider to use
            redirect_uri: Callback URI after authentication
            client_ip: Client IP address
            user_agent: Client user agent

        Returns:
            Tuple of (authorization_url, state) for the flow
        """
        provider = await self.get_provider(session, provider_id)

        # Generate secure state and nonce
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        # Create flow context
        now = datetime.now(timezone.utc)
        context = SSOFlowContext(
            state=state,
            nonce=nonce,
            provider_id=provider_id,
            redirect_uri=redirect_uri,
            initiated_at=now,
            expires_at=now + timedelta(minutes=10),  # 10 minute expiry
            client_ip=client_ip,
            user_agent=user_agent,
        )

        # Store flow context
        self._active_flows[state] = context

        # Initiate provider flow
        auth_url = await provider.initiate_flow(redirect_uri, state, nonce)

        logger.info(f"SSO flow initiated for provider {provider_id}")

        return auth_url, state

    async def handle_sso_callback(
        self,
        session: AsyncSession,
        state: str,
        authorization_code: Optional[str] = None,
        saml_response: Optional[str] = None,
    ) -> SSOAuthenticationResult:
        """Handle SSO callback and complete authentication.

        Args:
            session: Database session
            state: State parameter from SSO flow
            authorization_code: Authorization code (for OIDC/OAuth2)
            saml_response: SAML response (for SAML2)

        Returns:
            Authentication result with user claims
        """
        # Validate flow context
        if state not in self._active_flows:
            return SSOAuthenticationResult(
                success=False,
                error_code="invalid_state",
                error_message="Invalid or expired SSO flow state",
            )

        context = self._active_flows[state]

        # Check expiry
        if datetime.now(timezone.utc) > context.expires_at:
            del self._active_flows[state]
            return SSOAuthenticationResult(
                success=False,
                error_code="flow_expired",
                error_message="SSO flow has expired",
            )

        try:
            provider = await self.get_provider(session, context.provider_id)

            # Handle callback based on protocol
            if authorization_code:
                result = await provider.handle_callback(
                    authorization_code=authorization_code,
                    state=state,
                    nonce=context.nonce,
                )
            elif saml_response:
                result = await provider.handle_callback(
                    saml_response=saml_response,
                    state=state,
                    nonce=context.nonce,
                )
            else:
                return SSOAuthenticationResult(
                    success=False,
                    error_code="missing_callback_data",
                    error_message="No authorization code or SAML response provided",
                )

            # Clean up flow context
            del self._active_flows[state]

            if result.success:
                logger.info(f"SSO authentication successful for {result.user_claims.email if result.user_claims else 'unknown'}")
            else:
                logger.warning(f"SSO authentication failed: {result.error_message}")

            return result

        except Exception as e:
            logger.error(f"SSO callback handling failed: {e}")

            # Clean up flow context
            if state in self._active_flows:
                del self._active_flows[state]

            return SSOAuthenticationResult(
                success=False,
                error_code="callback_error",
                error_message=str(e),
            )

    async def provision_user_from_sso(
        self,
        session: AsyncSession,
        user_claims: SSOUserClaims,
        provider_id: UUIDstr,
    ) -> "User":
        """Provision or update user from SSO claims.

        Args:
            session: Database session
            user_claims: User claims from SSO provider
            provider_id: SSO provider ID

        Returns:
            Provisioned or updated user
        """
        from langflow.services.database.models.user.model import User

        if not user_claims.email:
            raise ValueError("Email is required for user provisioning")

        # Check if user exists
        user_query = select(User).where(User.username == user_claims.email)
        result = await session.exec(user_query)
        user = result.first()

        if user:
            # Update existing user
            if user_claims.name and user_claims.name != user.username:
                user.username = user_claims.name

            # Update last login
            user.last_login_at = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(user)

            logger.info(f"Updated existing user from SSO: {user_claims.email}")
        else:
            # Create new user
            user = User(
                username=user_claims.email,
                email=user_claims.email,
                is_active=True,
                is_superuser=False,
                last_login_at=datetime.now(timezone.utc),
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.info(f"Created new user from SSO: {user_claims.email}")

        # Handle group provisioning if enabled
        if user_claims.groups:
            await self._provision_user_groups(session, user, user_claims.groups, provider_id)

        return user

    async def _provision_user_groups(
        self,
        session: AsyncSession,
        user: "User",
        groups: List[str],
        provider_id: UUIDstr,
    ) -> None:
        """Provision user group memberships from SSO claims."""
        from langflow.services.database.models.rbac.user_group import UserGroup, UserGroupMembership

        # Get or create groups
        for group_name in groups:
            # Check if group exists
            group_query = select(UserGroup).where(
                UserGroup.name == group_name,
                UserGroup.sso_provider_id == provider_id,
            )
            result = await session.exec(group_query)
            group = result.first()

            if not group:
                # Create group
                group = UserGroup(
                    name=group_name,
                    description=f"SSO group: {group_name}",
                    sso_provider_id=UUID(provider_id),
                    is_active=True,
                )
                session.add(group)
                await session.commit()
                await session.refresh(group)

            # Check if user is already in group
            membership_query = select(UserGroupMembership).where(
                UserGroupMembership.user_id == user.id,
                UserGroupMembership.group_id == group.id,
                UserGroupMembership.is_active == True,
            )
            result = await session.exec(membership_query)
            membership = result.first()

            if not membership:
                # Add user to group
                membership = UserGroupMembership(
                    user_id=user.id,
                    group_id=group.id,
                    is_active=True,
                )
                session.add(membership)

        await session.commit()

    def cleanup_expired_flows(self) -> None:
        """Clean up expired SSO flows."""
        now = datetime.now(timezone.utc)
        expired_states = [
            state for state, context in self._active_flows.items()
            if now > context.expires_at
        ]

        for state in expired_states:
            del self._active_flows[state]

        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired SSO flows")

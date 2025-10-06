"""
Unit tests for SSO API endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from langflow.services.database.models.sso.model import SSOConfiguration, SSOEnforcement, SSOProvider


@pytest.fixture
def oidc_config():
    """OIDC configuration fixture."""
    return SSOConfiguration(
        id=str(uuid4()),
        organization_id="org-123",
        domain="acme.com",
        provider_type=SSOProvider.OIDC,
        enforcement=SSOEnforcement.OPTIONAL,
        enabled=True,
        oidc_issuer="https://idp.example.com",
        oidc_client_id="client-123",
        oidc_client_secret="secret-456",
        oidc_authorization_endpoint="https://idp.example.com/authorize",
        oidc_token_endpoint="https://idp.example.com/token",
        oidc_userinfo_endpoint="https://idp.example.com/userinfo",
        oidc_jwks_uri="https://idp.example.com/.well-known/jwks.json",
        session_timeout_minutes=480,
        allow_clock_skew_seconds=300,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestSSOAuthAPI:
    """Test SSO authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_initiate_sso_login_success(self, client: AsyncClient, oidc_config):
        """Test initiating SSO login successfully."""
        with patch(
            "langflow.api.v1.sso.SSOService.initiate_sso_login",
            return_value={
                "provider": "oidc",
                "redirect_url": "https://idp.example.com/authorize?client_id=client-123",
                "state": "csrf-token-123",
            },
        ):
            response = await client.post(
                "/api/v1/sso/login",
                json={
                    "domain": "acme.com",
                    "redirect_uri": "https://app.langbuilder.com/callback",
                    "state": "csrf-token-123",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["provider"] == "oidc"
            assert "redirect_url" in data

    @pytest.mark.asyncio
    async def test_initiate_sso_login_not_configured(self, client: AsyncClient):
        """Test initiating SSO login when not configured."""
        from langflow.services.auth.sso_service import SSOAuthenticationError

        with patch(
            "langflow.api.v1.sso.SSOService.initiate_sso_login",
            side_effect=SSOAuthenticationError("SSO not configured for this domain"),
        ):
            response = await client.post(
                "/api/v1/sso/login",
                json={
                    "domain": "unknown.com",
                    "redirect_uri": "https://app.langbuilder.com/callback",
                },
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_oidc_callback_success(self, client: AsyncClient):
        """Test OIDC callback processing successfully."""
        with patch(
            "langflow.api.v1.sso.SSOService.process_oidc_callback",
            return_value={
                "user_id": str(uuid4()),
                "email": "test@acme.com",
                "session_token": "sso_token_123",
                "expires_at": "2024-12-31T23:59:59Z",
                "mfa_verified": True,
            },
        ):
            response = await client.post(
                "/api/v1/sso/callback/oidc?code=auth-code-123&domain=acme.com&state=csrf-token"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "test@acme.com"
            assert "session_token" in data

    @pytest.mark.asyncio
    async def test_oidc_callback_user_not_provisioned(self, client: AsyncClient):
        """Test OIDC callback when user is not provisioned."""
        from langflow.services.auth.sso_service import SSOAuthenticationError

        with patch(
            "langflow.api.v1.sso.SSOService.process_oidc_callback",
            side_effect=SSOAuthenticationError("Your account is not provisioned in LangBuilder"),
        ):
            response = await client.post(
                "/api/v1/sso/callback/oidc?code=auth-code-123&domain=acme.com"
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "not provisioned" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_oidc_callback_replay_detected(self, client: AsyncClient):
        """Test OIDC callback with replay attack."""
        from langflow.services.auth.sso_service import SSOAuthenticationError

        with patch(
            "langflow.api.v1.sso.SSOService.process_oidc_callback",
            side_effect=SSOAuthenticationError("Replay detected"),
        ):
            response = await client.post(
                "/api/v1/sso/callback/oidc?code=auth-code-123&domain=acme.com"
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_saml_callback_success(self, client: AsyncClient):
        """Test SAML callback processing successfully."""
        with patch(
            "langflow.api.v1.sso.SSOService.process_saml_response",
            return_value={
                "user_id": str(uuid4()),
                "email": "test@acme.com",
                "session_token": "sso_saml_token_123",
                "expires_at": "2024-12-31T23:59:59Z",
            },
        ):
            response = await client.post(
                "/api/v1/sso/callback/saml?SAMLResponse=base64encoded&domain=acme.com"
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["email"] == "test@acme.com"
            assert "session_token" in data

    @pytest.mark.asyncio
    async def test_check_sso_enforcement_optional(self, client: AsyncClient):
        """Test checking SSO enforcement - optional."""
        with patch(
            "langflow.api.v1.sso.SSOService.check_sso_enforcement",
            return_value=SSOEnforcement.OPTIONAL,
        ):
            response = await client.get("/api/v1/sso/enforcement/acme.com")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["enforcement"] == "optional"
            assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_check_sso_enforcement_enforced(self, client: AsyncClient):
        """Test checking SSO enforcement - enforced."""
        with patch(
            "langflow.api.v1.sso.SSOService.check_sso_enforcement",
            return_value=SSOEnforcement.ENFORCED,
        ):
            response = await client.get("/api/v1/sso/enforcement/acme.com")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["enforcement"] == "enforced"
            assert data["enabled"] is True

    @pytest.mark.asyncio
    async def test_check_sso_enforcement_disabled(self, client: AsyncClient):
        """Test checking SSO enforcement - disabled."""
        with patch(
            "langflow.api.v1.sso.SSOService.check_sso_enforcement",
            return_value=SSOEnforcement.DISABLED,
        ):
            response = await client.get("/api/v1/sso/enforcement/acme.com")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["enforcement"] == "disabled"
            assert data["enabled"] is False

    @pytest.mark.asyncio
    async def test_get_saml_metadata(self, client: AsyncClient, oidc_config):
        """Test getting SAML metadata."""
        saml_config = oidc_config
        saml_config.provider_type = SSOProvider.SAML

        with patch(
            "langflow.api.v1.sso.SSOService.get_sso_config_for_org",
            return_value=saml_config,
        ):
            response = await client.get("/api/v1/sso/metadata/org-123")

            assert response.status_code == status.HTTP_200_OK
            assert response.headers["content-type"] == "application/xml; charset=utf-8"
            assert b"EntityDescriptor" in response.content

    @pytest.mark.asyncio
    async def test_get_saml_metadata_not_configured(self, client: AsyncClient):
        """Test getting SAML metadata when not configured."""
        with patch(
            "langflow.api.v1.sso.SSOService.get_sso_config_for_org",
            return_value=None,
        ):
            response = await client.get("/api/v1/sso/metadata/org-123")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_saml_metadata_oidc_provider(self, client: AsyncClient, oidc_config):
        """Test getting SAML metadata for OIDC provider (should fail)."""
        with patch(
            "langflow.api.v1.sso.SSOService.get_sso_config_for_org",
            return_value=oidc_config,  # OIDC provider
        ):
            response = await client.get("/api/v1/sso/metadata/org-123")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Not a SAML configuration" in response.json()["detail"]

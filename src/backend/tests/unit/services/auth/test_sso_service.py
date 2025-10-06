"""
Unit tests for SSO authentication service.
"""

import base64
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.sso_service import SSOAuthenticationError, SSOService
from langflow.services.database.models.sso.model import SSOConfiguration, SSOEnforcement, SSOProvider
from langflow.services.database.models.user.model import User


@pytest.fixture
def oidc_config():
    """OIDC SSO configuration fixture."""
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
        email_attribute="email",
        name_attribute="name",
        groups_attribute="groups",
        session_timeout_minutes=480,
        allow_clock_skew_seconds=300,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def saml_config():
    """SAML SSO configuration fixture."""
    return SSOConfiguration(
        id=str(uuid4()),
        organization_id="org-123",
        domain="acme.com",
        provider_type=SSOProvider.SAML,
        enforcement=SSOEnforcement.OPTIONAL,
        enabled=True,
        saml_entity_id="https://idp.example.com/saml",
        saml_sso_url="https://idp.example.com/sso/saml",
        saml_x509_cert="MII...",
        saml_slo_url="https://idp.example.com/slo/saml",
        email_attribute="email",
        name_attribute="name",
        groups_attribute="groups",
        session_timeout_minutes=480,
        allow_clock_skew_seconds=300,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user():
    """Mock user fixture."""
    return User(
        id=uuid4(),
        username="testuser",
        email="test@acme.com",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


class TestSSOService:
    """Test SSO service methods."""

    @pytest.mark.asyncio
    async def test_get_sso_config_for_domain(self, oidc_config):
        """Test getting SSO config by domain."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ):
            config = await SSOService.get_sso_config_for_domain(mock_db, "acme.com")

            assert config is not None
            assert config.domain == "acme.com"
            assert config.provider_type == SSOProvider.OIDC

    @pytest.mark.asyncio
    async def test_initiate_sso_login_oidc(self, oidc_config):
        """Test initiating OIDC SSO login."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ):
            result = await SSOService.initiate_sso_login(
                db=mock_db,
                domain="acme.com",
                redirect_uri="https://app.langbuilder.com/callback",
                state="csrf-token-123",
            )

            assert result["provider"] == "oidc"
            assert "redirect_url" in result
            assert "client_id=client-123" in result["redirect_url"]
            assert "state=csrf-token-123" in result["redirect_url"]

    @pytest.mark.asyncio
    async def test_initiate_sso_login_saml(self, saml_config):
        """Test initiating SAML SSO login."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=saml_config,
        ):
            result = await SSOService.initiate_sso_login(
                db=mock_db,
                domain="acme.com",
                redirect_uri="https://app.langbuilder.com/callback",
                state="csrf-token-123",
            )

            assert result["provider"] == "saml"
            assert "redirect_url" in result
            assert "request_id" in result
            assert "SAMLRequest=" in result["redirect_url"]
            assert "RelayState=csrf-token-123" in result["redirect_url"]

    @pytest.mark.asyncio
    async def test_initiate_sso_login_not_configured(self):
        """Test initiating SSO login with no configuration."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=None,
        ):
            with pytest.raises(SSOAuthenticationError, match="not configured"):
                await SSOService.initiate_sso_login(
                    db=mock_db,
                    domain="unknown.com",
                    redirect_uri="https://app.langbuilder.com/callback",
                )

    @pytest.mark.asyncio
    async def test_process_oidc_callback_success(self, oidc_config, mock_user):
        """Test successful OIDC callback processing."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock token response
        token_response = {
            "access_token": "access-token-123",
            "id_token": "id-token-456",
            "token_type": "Bearer",
        }

        # Mock ID token claims
        claims = {
            "sub": "user-123",
            "email": "test@acme.com",
            "name": "Test User",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "jti": "assertion-123",
        }

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ), patch(
            "langflow.services.auth.sso_oidc.OIDCProvider.exchange_code_for_token",
            return_value=token_response,
        ), patch(
            "langflow.services.auth.sso_oidc.OIDCProvider.verify_id_token",
            return_value=claims,
        ), patch(
            "langflow.services.auth.sso_service.check_assertion_used",
            return_value=False,
        ), patch(
            "langflow.services.auth.sso_service.get_user_by_email",
            return_value=mock_user,
        ), patch(
            "langflow.services.auth.sso_service.mark_assertion_used",
            new_callable=AsyncMock,
        ), patch(
            "langflow.services.auth.sso_service.create_sso_session",
            new_callable=AsyncMock,
        ), patch(
            "langflow.services.auth.sso_service.create_audit_log",
            new_callable=AsyncMock,
        ):
            result = await SSOService.process_oidc_callback(
                db=mock_db,
                code="auth-code-123",
                redirect_uri="https://app.langbuilder.com/callback",
                domain="acme.com",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

            assert result["user_id"] == str(mock_user.id)
            assert result["email"] == mock_user.email
            assert "session_token" in result
            assert "expires_at" in result

    @pytest.mark.asyncio
    async def test_process_oidc_callback_replay_detected(self, oidc_config):
        """Test OIDC callback with replay attack detection."""
        mock_db = AsyncMock(spec=AsyncSession)

        token_response = {
            "id_token": "id-token-456",
            "access_token": "access-token-123",
        }

        claims = {
            "sub": "user-123",
            "email": "test@acme.com",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "jti": "assertion-123",
        }

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ), patch(
            "langflow.services.auth.sso_oidc.OIDCProvider.exchange_code_for_token",
            return_value=token_response,
        ), patch(
            "langflow.services.auth.sso_oidc.OIDCProvider.verify_id_token",
            return_value=claims,
        ), patch(
            "langflow.services.auth.sso_service.check_assertion_used",
            return_value=True,  # Replay detected
        ):
            with pytest.raises(SSOAuthenticationError, match="Replay detected"):
                await SSOService.process_oidc_callback(
                    db=mock_db,
                    code="auth-code-123",
                    redirect_uri="https://app.langbuilder.com/callback",
                    domain="acme.com",
                )

    @pytest.mark.asyncio
    async def test_process_oidc_callback_user_not_provisioned(self, oidc_config):
        """Test OIDC callback when user account doesn't exist."""
        mock_db = AsyncMock(spec=AsyncSession)

        token_response = {
            "id_token": "id-token-456",
            "access_token": "access-token-123",
        }

        claims = {
            "sub": "user-123",
            "email": "nonexistent@acme.com",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
            "jti": "assertion-123",
        }

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ), patch(
            "langflow.services.auth.sso_oidc.OIDCProvider.exchange_code_for_token",
            return_value=token_response,
        ), patch(
            "langflow.services.auth.sso_oidc.OIDCProvider.verify_id_token",
            return_value=claims,
        ), patch(
            "langflow.services.auth.sso_service.check_assertion_used",
            return_value=False,
        ), patch(
            "langflow.services.auth.sso_service.get_user_by_email",
            return_value=None,  # User not found
        ):
            with pytest.raises(SSOAuthenticationError, match="not provisioned"):
                await SSOService.process_oidc_callback(
                    db=mock_db,
                    code="auth-code-123",
                    redirect_uri="https://app.langbuilder.com/callback",
                    domain="acme.com",
                )

    @pytest.mark.asyncio
    async def test_process_saml_response_success(self, saml_config, mock_user):
        """Test successful SAML response processing."""
        mock_db = AsyncMock(spec=AsyncSession)

        # Mock SAML assertion data
        assertion_data = {
            "response_id": "response-123",
            "assertion_id": "assertion-456",
            "in_response_to": "request-789",
            "subject": "test@acme.com",
            "issue_instant": datetime.now(timezone.utc).isoformat(),
            "conditions": {
                "not_before": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                "not_on_or_after": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            },
            "attributes": {
                "email": "test@acme.com",
                "name": "Test User",
            },
        }

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=saml_config,
        ), patch(
            "langflow.services.auth.sso_saml.SAMLProvider.parse_saml_response",
            return_value=assertion_data,
        ), patch(
            "langflow.services.auth.sso_saml.SAMLProvider.validate_assertion_timing",
            return_value=True,
        ), patch(
            "langflow.services.auth.sso_saml.SAMLProvider.verify_signature",
            return_value=True,
        ), patch(
            "langflow.services.auth.sso_service.check_assertion_used",
            return_value=False,
        ), patch(
            "langflow.services.auth.sso_service.get_user_by_email",
            return_value=mock_user,
        ), patch(
            "langflow.services.auth.sso_service.mark_assertion_used",
            new_callable=AsyncMock,
        ), patch(
            "langflow.services.auth.sso_service.create_sso_session",
            new_callable=AsyncMock,
        ), patch(
            "langflow.services.auth.sso_service.create_audit_log",
            new_callable=AsyncMock,
        ):
            result = await SSOService.process_saml_response(
                db=mock_db,
                saml_response=base64.b64encode(b"<saml>...</saml>").decode(),
                domain="acme.com",
                ip_address="192.168.1.1",
                user_agent="Mozilla/5.0",
            )

            assert result["user_id"] == str(mock_user.id)
            assert result["email"] == mock_user.email
            assert "session_token" in result
            assert "expires_at" in result

    @pytest.mark.asyncio
    async def test_check_sso_enforcement_optional(self, oidc_config):
        """Test checking SSO enforcement level - optional."""
        mock_db = AsyncMock(spec=AsyncSession)
        oidc_config.enforcement = SSOEnforcement.OPTIONAL

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ):
            enforcement = await SSOService.check_sso_enforcement(mock_db, "acme.com")

            assert enforcement == SSOEnforcement.OPTIONAL

    @pytest.mark.asyncio
    async def test_check_sso_enforcement_enforced(self, oidc_config):
        """Test checking SSO enforcement level - enforced."""
        mock_db = AsyncMock(spec=AsyncSession)
        oidc_config.enforcement = SSOEnforcement.ENFORCED

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=oidc_config,
        ):
            enforcement = await SSOService.check_sso_enforcement(mock_db, "acme.com")

            assert enforcement == SSOEnforcement.ENFORCED

    @pytest.mark.asyncio
    async def test_check_sso_enforcement_disabled(self):
        """Test checking SSO enforcement level - disabled."""
        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "langflow.services.auth.sso_service.get_sso_config_by_domain",
            return_value=None,
        ):
            enforcement = await SSOService.check_sso_enforcement(mock_db, "acme.com")

            assert enforcement == SSOEnforcement.DISABLED

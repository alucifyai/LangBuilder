"""
CRUD operations for SSO Configuration.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.sso.model import (
    SSOAssertion,
    SSOConfiguration,
    SSOEnforcement,
    SSOProvider,
    SSOSession,
)


async def get_sso_config_by_id(db: AsyncSession, config_id: UUID) -> SSOConfiguration | None:
    """Get SSO configuration by ID."""
    if isinstance(config_id, str):
        config_id = UUID(config_id)
    stmt = select(SSOConfiguration).where(SSOConfiguration.id == config_id)
    return (await db.exec(stmt)).first()


async def get_sso_config_by_domain(db: AsyncSession, domain: str) -> SSOConfiguration | None:
    """Get SSO configuration by company domain."""
    stmt = (
        select(SSOConfiguration)
        .where(SSOConfiguration.domain == domain)
        .where(SSOConfiguration.enabled == True)  # noqa: E712
    )
    return (await db.exec(stmt)).first()


async def get_sso_config_by_org(db: AsyncSession, organization_id: str) -> SSOConfiguration | None:
    """Get SSO configuration by organization ID."""
    stmt = (
        select(SSOConfiguration)
        .where(SSOConfiguration.organization_id == organization_id)
        .where(SSOConfiguration.enabled == True)  # noqa: E712
    )
    return (await db.exec(stmt)).first()


async def create_sso_config(
    db: AsyncSession,
    organization_id: str,
    domain: str,
    provider_type: SSOProvider,
    **kwargs,
) -> SSOConfiguration:
    """Create a new SSO configuration."""
    config = SSOConfiguration(
        organization_id=organization_id,
        domain=domain,
        provider_type=provider_type,
        **kwargs,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def update_sso_config(
    db: AsyncSession,
    config_id: UUID,
    **updates,
) -> SSOConfiguration | None:
    """Update SSO configuration."""
    config = await get_sso_config_by_id(db, config_id)
    if not config:
        return None

    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)

    config.updated_at = datetime.now(timezone.utc)
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


async def delete_sso_config(db: AsyncSession, config_id: UUID) -> bool:
    """Delete SSO configuration."""
    config = await get_sso_config_by_id(db, config_id)
    if not config:
        return False

    await db.delete(config)
    await db.commit()
    return True


# SSO Session management
async def create_sso_session(
    db: AsyncSession,
    user_id: UUID,
    sso_config_id: UUID,
    assertion_id: str,
    assertion_issued_at: datetime,
    assertion_expires_at: datetime,
    session_token: str,
    expires_at: datetime,
    **kwargs,
) -> SSOSession:
    """Create SSO session for tracking."""
    session = SSOSession(
        user_id=str(user_id),
        sso_config_id=str(sso_config_id),
        assertion_id=assertion_id,
        assertion_issued_at=assertion_issued_at,
        assertion_expires_at=assertion_expires_at,
        session_token=session_token,
        expires_at=expires_at,
        **kwargs,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_sso_session_by_token(db: AsyncSession, session_token: str) -> SSOSession | None:
    """Get SSO session by session token."""
    stmt = select(SSOSession).where(SSOSession.session_token == session_token)
    return (await db.exec(stmt)).first()


async def delete_sso_session(db: AsyncSession, session_id: UUID) -> bool:
    """Delete SSO session (logout)."""
    stmt = select(SSOSession).where(SSOSession.id == session_id)
    session = (await db.exec(stmt)).first()
    if not session:
        return False

    await db.delete(session)
    await db.commit()
    return True


# Replay protection
async def check_assertion_used(db: AsyncSession, assertion_id: str) -> bool:
    """Check if assertion has already been used (replay detection)."""
    stmt = select(SSOAssertion).where(SSOAssertion.assertion_id == assertion_id)
    assertion = (await db.exec(stmt)).first()
    return assertion is not None


async def mark_assertion_used(
    db: AsyncSession,
    assertion_id: str,
    user_id: UUID,
    expires_at: datetime,
) -> SSOAssertion:
    """Mark assertion as used for replay protection."""
    assertion = SSOAssertion(
        assertion_id=assertion_id,
        user_id=str(user_id),
        expires_at=expires_at,
    )
    db.add(assertion)
    await db.commit()
    await db.refresh(assertion)
    return assertion


async def cleanup_expired_assertions(db: AsyncSession) -> int:
    """Clean up expired assertions (for maintenance)."""
    now = datetime.now(timezone.utc)
    stmt = select(SSOAssertion).where(SSOAssertion.expires_at < now)
    expired = (await db.exec(stmt)).all()

    count = 0
    for assertion in expired:
        await db.delete(assertion)
        count += 1

    await db.commit()
    return count

"""
CRUD operations for Service Accounts and API Tokens
"""

import hashlib
import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.service_account.model import APIToken, ServiceAccount


# ============================================================================
# Service Account CRUD
# ============================================================================


async def create_service_account(
    db: AsyncSession,
    name: str,
    organization_id: str,
    created_by: UUID,
    description: str | None = None,
) -> ServiceAccount:
    """Create a new service account."""
    account = ServiceAccount(
        name=name,
        description=description,
        organization_id=organization_id,
        created_by=str(created_by),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def get_service_account_by_id(db: AsyncSession, account_id: UUID | str) -> ServiceAccount | None:
    """Get service account by ID."""
    stmt = select(ServiceAccount).where(ServiceAccount.id == str(account_id))
    return (await db.exec(stmt)).first()


async def list_service_accounts(
    db: AsyncSession,
    organization_id: str,
    skip: int = 0,
    limit: int = 100,
) -> list[ServiceAccount]:
    """List service accounts for an organization."""
    stmt = (
        select(ServiceAccount)
        .where(ServiceAccount.organization_id == organization_id)
        .offset(skip)
        .limit(limit)
        .order_by(ServiceAccount.created_at.desc())
    )
    return list((await db.exec(stmt)).all())


async def update_service_account(
    db: AsyncSession,
    account_id: UUID | str,
    **updates,
) -> ServiceAccount | None:
    """Update service account."""
    account = await get_service_account_by_id(db, account_id)
    if not account:
        return None

    for key, value in updates.items():
        if hasattr(account, key):
            setattr(account, key, value)

    account.updated_at = datetime.now(timezone.utc)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def delete_service_account(db: AsyncSession, account_id: UUID | str) -> bool:
    """Delete service account and all associated tokens."""
    account = await get_service_account_by_id(db, account_id)
    if not account:
        return False

    # Delete all associated tokens first
    stmt = select(APIToken).where(APIToken.service_account_id == str(account_id))
    tokens = (await db.exec(stmt)).all()
    for token in tokens:
        await db.delete(token)

    await db.delete(account)
    await db.commit()
    return True


# ============================================================================
# API Token CRUD
# ============================================================================


def generate_api_token() -> tuple[str, str, str]:
    """
    Generate API token.

    Returns:
        Tuple of (token, token_hash, token_prefix)
    """
    # Generate random token (64 chars hex = 256 bits)
    token = f"lbt_{secrets.token_hex(32)}"  # lbt = LangBuilder Token

    # Hash for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Prefix for identification (first 12 chars: lbt_ + 8 chars)
    token_prefix = token[:12]

    return token, token_hash, token_prefix


async def create_api_token(
    db: AsyncSession,
    service_account_id: UUID | str,
    name: str,
    created_by: UUID,
    scopes: list[str],
    expires_at: datetime | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
) -> tuple[APIToken, str]:
    """
    Create a new API token.

    Args:
        scope_type: Resource scope type (Workspace, Project, etc.) - Story 4.2
        scope_id: Resource scope ID - restricts token to this resource only

    Returns:
        Tuple of (token_record, plaintext_token)

    Note: The plaintext token is only returned once and should be shown to the user.
    """
    token, token_hash, token_prefix = generate_api_token()

    api_token = APIToken(
        service_account_id=str(service_account_id),
        name=name,
        token_hash=token_hash,
        token_prefix=token_prefix,
        scopes=scopes,
        expires_at=expires_at,
        created_by=str(created_by),
        scope_type=scope_type,
        scope_id=scope_id,
    )

    db.add(api_token)
    await db.commit()
    await db.refresh(api_token)

    return api_token, token


async def get_api_token_by_hash(db: AsyncSession, token_hash: str) -> APIToken | None:
    """Get API token by hash (for authentication)."""
    stmt = select(APIToken).where(
        APIToken.token_hash == token_hash,
        APIToken.is_active == True,  # noqa: E712
    )
    return (await db.exec(stmt)).first()


async def get_api_token_by_id(db: AsyncSession, token_id: UUID | str) -> APIToken | None:
    """Get API token by ID."""
    stmt = select(APIToken).where(APIToken.id == str(token_id))
    return (await db.exec(stmt)).first()


async def list_api_tokens(
    db: AsyncSession,
    service_account_id: UUID | str,
    include_revoked: bool = False,
) -> list[APIToken]:
    """List API tokens for a service account."""
    stmt = select(APIToken).where(APIToken.service_account_id == str(service_account_id))

    if not include_revoked:
        stmt = stmt.where(APIToken.is_active == True)  # noqa: E712

    stmt = stmt.order_by(APIToken.created_at.desc())
    return list((await db.exec(stmt)).all())


async def revoke_api_token(
    db: AsyncSession,
    token_id: UUID | str,
    revoked_by: UUID,
    reason: str | None = None,
) -> APIToken | None:
    """Revoke an API token."""
    token = await get_api_token_by_id(db, token_id)
    if not token:
        return None

    token.is_active = False
    token.revoked_at = datetime.now(timezone.utc)
    token.revoked_by = str(revoked_by)
    token.revocation_reason = reason

    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token


async def record_token_usage(
    db: AsyncSession,
    token_id: UUID | str,
    ip_address: str | None = None,
) -> None:
    """Record token usage for tracking."""
    token = await get_api_token_by_id(db, token_id)
    if not token:
        return

    now = datetime.now(timezone.utc)
    token.last_used_at = now
    token.last_used_ip = ip_address
    token.use_count += 1

    # Also update service account last_used_at
    account = await get_service_account_by_id(db, token.service_account_id)
    if account:
        account.last_used_at = now
        db.add(account)

    db.add(token)
    await db.commit()


async def delete_api_token(db: AsyncSession, token_id: UUID | str) -> bool:
    """Delete an API token permanently."""
    token = await get_api_token_by_id(db, token_id)
    if not token:
        return False

    await db.delete(token)
    await db.commit()
    return True


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    """Clean up expired tokens (maintenance task)."""
    now = datetime.now(timezone.utc)
    stmt = select(APIToken).where(
        APIToken.expires_at.isnot(None),
        APIToken.expires_at < now,
        APIToken.is_active == True,  # noqa: E712
    )

    expired_tokens = (await db.exec(stmt)).all()
    count = 0

    for token in expired_tokens:
        token.is_active = False
        token.revoked_at = now
        token.revocation_reason = "Expired"
        db.add(token)
        count += 1

    await db.commit()
    return count

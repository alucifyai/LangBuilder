from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.grant.model import Grant, PrincipalType, ScopeType


async def get_grant_by_id(db: AsyncSession, grant_id: UUID) -> Grant | None:
    """Get a grant by its ID."""
    if isinstance(grant_id, str):
        grant_id = UUID(grant_id)
    stmt = select(Grant).where(Grant.id == grant_id)
    return (await db.exec(stmt)).first()


async def get_grants_for_principal(
    db: AsyncSession,
    principal_type: PrincipalType,
    principal_id: UUID,
) -> list[Grant]:
    """Get all grants for a specific principal."""
    if isinstance(principal_id, str):
        principal_id = UUID(principal_id)

    stmt = (
        select(Grant)
        .where(Grant.principal_type == principal_type)
        .where(Grant.principal_id == principal_id)
    )

    # Filter out expired grants
    now = datetime.now(timezone.utc)
    stmt = stmt.where((Grant.expires_at.is_(None)) | (Grant.expires_at > now))

    result = await db.exec(stmt)
    return list(result.all())


async def get_grants_for_scope(
    db: AsyncSession,
    scope_type: ScopeType,
    scope_id: str,
) -> list[Grant]:
    """Get all grants for a specific scope."""
    stmt = select(Grant).where(Grant.scope_type == scope_type).where(Grant.scope_id == scope_id)

    # Filter out expired grants
    now = datetime.now(timezone.utc)
    stmt = stmt.where((Grant.expires_at.is_(None)) | (Grant.expires_at > now))

    result = await db.exec(stmt)
    return list(result.all())


async def create_grant(
    db: AsyncSession,
    principal_type: PrincipalType,
    principal_id: UUID,
    role_id: UUID,
    scope_type: ScopeType,
    scope_id: str,
    expires_at: datetime | None = None,
) -> Grant:
    """Create a new grant (role assignment)."""
    grant = Grant(
        principal_type=principal_type,
        principal_id=str(principal_id),
        role_id=str(role_id),
        scope_type=scope_type,
        scope_id=scope_id,
        expires_at=expires_at,
    )

    db.add(grant)
    await db.commit()
    await db.refresh(grant)
    return grant


async def delete_grant(db: AsyncSession, grant_id: UUID) -> bool:
    """Delete (revoke) a grant."""
    grant = await get_grant_by_id(db, grant_id)
    if not grant:
        return False

    await db.delete(grant)
    await db.commit()
    return True


async def count_grants_by_role(db: AsyncSession, role_id: UUID) -> int:
    """
    Count active grants for a specific role.

    Args:
        db: Database session
        role_id: Role ID to count grants for

    Returns:
        Number of active (non-expired) grants using this role
    """
    if isinstance(role_id, str):
        role_id = UUID(role_id)

    # Filter out expired grants
    now = datetime.now(timezone.utc)
    stmt = (
        select(func.count(Grant.id))
        .where(Grant.role_id == str(role_id))
        .where((Grant.expires_at.is_(None)) | (Grant.expires_at > now))
    )

    result = await db.exec(stmt)
    return result.one()

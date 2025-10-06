from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.permission.model import Permission


async def get_all_permissions(db: AsyncSession) -> list[Permission]:
    """Get all permissions from the catalog."""
    stmt = select(Permission)
    result = await db.exec(stmt)
    return list(result.all())


async def get_permission_by_id(db: AsyncSession, permission_id: str) -> Permission | None:
    """Get a specific permission by its ID."""
    stmt = select(Permission).where(Permission.id == permission_id)
    return (await db.exec(stmt)).first()


async def permission_exists(db: AsyncSession, permission_id: str) -> bool:
    """Check if a permission exists in the catalog."""
    permission = await get_permission_by_id(db, permission_id)
    return permission is not None

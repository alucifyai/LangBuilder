from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.permission.crud import get_all_permissions
from langflow.services.database.models.role.model import Role


async def get_role_by_id(db: AsyncSession, role_id: UUID) -> Role | None:
    """Get a role by its ID."""
    if isinstance(role_id, str):
        role_id = UUID(role_id)
    stmt = select(Role).where(Role.id == role_id)
    return (await db.exec(stmt)).first()


async def get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    """Get a role by its name."""
    stmt = select(Role).where(Role.name == name)
    return (await db.exec(stmt)).first()


async def get_all_roles(db: AsyncSession) -> list[Role]:
    """Get all roles."""
    stmt = select(Role)
    result = await db.exec(stmt)
    return list(result.all())


async def create_role(db: AsyncSession, name: str, permissions: list[str]) -> Role:
    """
    Create a new role with permission validation.

    Args:
        db: Database session
        name: Role name (must be unique)
        permissions: List of permission IDs

    Returns:
        Created Role

    Raises:
        HTTPException: If role name already exists or permissions are invalid
    """
    # Check if role name already exists
    existing = await get_role_by_name(db, name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role name must be unique",
        )

    # Validate permissions exist in catalog
    all_permissions = await get_all_permissions(db)
    valid_permission_ids = {p.id for p in all_permissions}

    role = Role(name=name, permissions=permissions)
    is_valid, unknown = role.validate_permissions(valid_permission_ids)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown permission id: {unknown[0]}",
        )

    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


async def update_role(
    db: AsyncSession,
    role_id: UUID,
    name: str | None = None,
    permissions: list[str] | None = None,
) -> Role:
    """
    Update a role and increment version.

    Args:
        db: Database session
        role_id: Role ID to update
        name: New name (optional)
        permissions: New permissions list (optional)

    Returns:
        Updated Role

    Raises:
        HTTPException: If role not found or validation fails
    """
    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    if name and name != role.name:
        # Check for duplicate name
        existing = await get_role_by_name(db, name)
        if existing and existing.id != role_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Role name must be unique",
            )
        role.name = name

    if permissions is not None:
        # Validate new permissions
        all_permissions = await get_all_permissions(db)
        valid_permission_ids = {p.id for p in all_permissions}

        temp_role = Role(name="temp", permissions=permissions)
        is_valid, unknown = temp_role.validate_permissions(valid_permission_ids)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown permission id: {unknown[0]}",
            )

        role.permissions = permissions

    # Increment version and update timestamp
    role.version += 1
    role.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(role)
    return role


async def delete_role(db: AsyncSession, role_id: UUID) -> bool:
    """Delete a role."""
    role = await get_role_by_id(db, role_id)
    if not role:
        return False

    await db.delete(role)
    await db.commit()
    return True

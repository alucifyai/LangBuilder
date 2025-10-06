"""
CRUD operations for Group and GroupMembership
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .model import Group, GroupMembership


# Group CRUD
async def create_group(
    session: AsyncSession,
    name: str,
    description: str | None = None,
    organization_id: str | None = None,
) -> Group:
    """Create a new group"""
    group = Group(
        name=name,
        description=description,
        organization_id=organization_id,
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def get_group(session: AsyncSession, group_id: UUID) -> Group | None:
    """Get group by ID"""
    result = await session.exec(select(Group).where(Group.id == group_id))
    return result.first()


async def get_group_by_name(session: AsyncSession, name: str) -> Group | None:
    """Get group by name"""
    result = await session.exec(select(Group).where(Group.name == name))
    return result.first()


async def list_groups(
    session: AsyncSession,
    organization_id: str | None = None,
    limit: int = 100,
) -> list[Group]:
    """List all groups with optional filters"""
    query = select(Group)

    if organization_id:
        query = query.where(Group.organization_id == organization_id)

    query = query.limit(limit)
    result = await session.exec(query)
    return list(result.all())


async def update_group(
    session: AsyncSession,
    group: Group,
    name: str | None = None,
    description: str | None = None,
) -> Group:
    """Update group"""
    if name is not None:
        group.name = name
    if description is not None:
        group.description = description

    group.updated_at = datetime.now(timezone.utc)
    session.add(group)
    await session.commit()
    await session.refresh(group)
    return group


async def delete_group(session: AsyncSession, group: Group) -> None:
    """Delete group and all memberships"""
    # First delete all memberships
    result = await session.exec(
        select(GroupMembership).where(GroupMembership.group_id == group.id)
    )
    memberships = result.all()
    for membership in memberships:
        await session.delete(membership)

    # Then delete the group
    await session.delete(group)
    await session.commit()


# GroupMembership CRUD
async def add_user_to_group(
    session: AsyncSession,
    group_id: UUID,
    user_id: UUID,
) -> GroupMembership:
    """Add a user to a group"""
    membership = GroupMembership(
        group_id=group_id,
        user_id=user_id,
    )
    session.add(membership)
    await session.commit()
    await session.refresh(membership)
    return membership


async def remove_user_from_group(
    session: AsyncSession,
    group_id: UUID,
    user_id: UUID,
) -> None:
    """Remove a user from a group"""
    result = await session.exec(
        select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
        )
    )
    membership = result.first()
    if membership:
        await session.delete(membership)
        await session.commit()


async def get_group_members(
    session: AsyncSession,
    group_id: UUID,
) -> list[UUID]:
    """Get all user IDs in a group"""
    result = await session.exec(
        select(GroupMembership.user_id).where(GroupMembership.group_id == group_id)
    )
    return list(result.all())


async def get_user_groups(
    session: AsyncSession,
    user_id: UUID,
) -> list[UUID]:
    """Get all group IDs a user belongs to"""
    result = await session.exec(
        select(GroupMembership.group_id).where(GroupMembership.user_id == user_id)
    )
    return list(result.all())

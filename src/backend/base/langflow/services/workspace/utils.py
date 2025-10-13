"""Workspace utility functions for multi-tenant operations."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.services.database.models.workspace.model import Workspace, WorkspaceMember


async def get_user_default_workspace(user_id: UUID, session: AsyncSession) -> Workspace | None:
    """Get user's default/primary workspace.

    Returns the first active workspace where the user is a member, prioritizing:
    1. Workspace named "Default Workspace"
    2. Workspace where user is owner
    3. Any workspace where user is a member

    Args:
        user_id: User UUID
        session: Database session

    Returns:
        Workspace object if found, None otherwise

    Example:
        >>> workspace = await get_user_default_workspace(current_user.id, session)
        >>> if workspace:
        >>>     print(f"User's default workspace: {workspace.name}")
    """
    # Try to find "Default Workspace" first (created by migration)
    stmt = (
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True,  # noqa: E712
            Workspace.is_active == True,  # noqa: E712
            Workspace.name == "Default Workspace",
        )
    )
    result = await session.exec(stmt)
    default_workspace = result.first()

    if default_workspace:
        return default_workspace

    # Fallback: Find workspace where user is owner
    stmt = (
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True,  # noqa: E712
            WorkspaceMember.role == "owner",
            Workspace.is_active == True,  # noqa: E712
        )
        .order_by(Workspace.created_at)  # Oldest first
    )
    result = await session.exec(stmt)
    owner_workspace = result.first()

    if owner_workspace:
        return owner_workspace

    # Last resort: Any workspace where user is a member
    stmt = (
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == user_id,
            WorkspaceMember.is_active == True,  # noqa: E712
            Workspace.is_active == True,  # noqa: E712
        )
        .order_by(Workspace.created_at)
    )
    result = await session.exec(stmt)
    return result.first()

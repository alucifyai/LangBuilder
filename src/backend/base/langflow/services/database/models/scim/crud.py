"""
SCIM 2.0 CRUD operations
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.user.model import User

from .model import SCIMGroup, SCIMGroupMembership, SCIMProvisioningLog, SCIMUser


async def create_scim_user(
    session: AsyncSession,
    external_id: str,
    username: str,
    email: str,
    given_name: str | None = None,
    family_name: str | None = None,
    display_name: str | None = None,
    active: bool = True,
    organization_id: str | None = None,
    scim_meta: dict[str, Any] | None = None,
) -> SCIMUser:
    """Create a new SCIM user"""
    scim_user = SCIMUser(
        external_id=external_id,
        username=username,
        email=email,
        given_name=given_name,
        family_name=family_name,
        display_name=display_name,
        active=active,
        organization_id=organization_id,
        scim_meta=scim_meta,
    )

    session.add(scim_user)
    await session.commit()
    await session.refresh(scim_user)

    # Also create the actual LangBuilder user
    try:
        user = User(
            username=username,
            is_active=active,
            is_superuser=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Link SCIM user to LangBuilder user
        scim_user.user_id = user.id
        session.add(scim_user)
        await session.commit()
        await session.refresh(scim_user)
    except IntegrityError:
        # User already exists, try to link it
        result = await session.exec(select(User).where(User.username == username))
        user = result.first()
        if user:
            scim_user.user_id = user.id
            session.add(scim_user)
            await session.commit()
            await session.refresh(scim_user)

    return scim_user


async def update_scim_user(
    session: AsyncSession,
    scim_user: SCIMUser,
    username: str | None = None,
    email: str | None = None,
    given_name: str | None = None,
    family_name: str | None = None,
    display_name: str | None = None,
    active: bool | None = None,
    scim_meta: dict[str, Any] | None = None,
) -> SCIMUser:
    """Update an existing SCIM user"""
    if username is not None:
        scim_user.username = username
    if email is not None:
        scim_user.email = email
    if given_name is not None:
        scim_user.given_name = given_name
    if family_name is not None:
        scim_user.family_name = family_name
    if display_name is not None:
        scim_user.display_name = display_name
    if active is not None:
        scim_user.active = active

        # Also update LangBuilder user
        if scim_user.user_id:
            result = await session.exec(select(User).where(User.id == scim_user.user_id))
            user = result.first()
            if user:
                user.is_active = active
                session.add(user)

    if scim_meta is not None:
        scim_user.scim_meta = scim_meta

    scim_user.updated_at = datetime.now(timezone.utc)
    session.add(scim_user)
    await session.commit()
    await session.refresh(scim_user)
    return scim_user


async def delete_scim_user(session: AsyncSession, scim_user: SCIMUser) -> None:
    """
    Delete a SCIM user (soft delete - marks as inactive)
    """
    scim_user.active = False
    scim_user.updated_at = datetime.now(timezone.utc)

    # Also deactivate LangBuilder user
    if scim_user.user_id:
        result = await session.exec(select(User).where(User.id == scim_user.user_id))
        user = result.first()
        if user:
            user.is_active = False
            session.add(user)

    session.add(scim_user)
    await session.commit()


async def get_scim_user_by_external_id(session: AsyncSession, external_id: str) -> SCIMUser | None:
    """Get SCIM user by external ID"""
    result = await session.exec(select(SCIMUser).where(SCIMUser.external_id == external_id))
    return result.first()


async def list_scim_users(
    session: AsyncSession,
    organization_id: str | None = None,
    active_only: bool = False,
    limit: int = 100,
) -> list[SCIMUser]:
    """List SCIM users with optional filters"""
    query = select(SCIMUser)

    if organization_id:
        query = query.where(SCIMUser.organization_id == organization_id)
    if active_only:
        query = query.where(SCIMUser.active == True)  # noqa: E712

    query = query.limit(limit)
    result = await session.exec(query)
    return list(result.all())


# SCIM Group operations
async def create_scim_group(
    session: AsyncSession,
    external_id: str,
    display_name: str,
    organization_id: str | None = None,
    mapped_role_id: UUID | None = None,
    mapped_scope_type: str | None = None,
    mapped_scope_id: str | None = None,
    scim_meta: dict[str, Any] | None = None,
) -> SCIMGroup:
    """Create a new SCIM group"""
    scim_group = SCIMGroup(
        external_id=external_id,
        display_name=display_name,
        organization_id=organization_id,
        mapped_role_id=mapped_role_id,
        mapped_scope_type=mapped_scope_type,
        mapped_scope_id=mapped_scope_id,
        scim_meta=scim_meta,
    )

    session.add(scim_group)
    await session.commit()
    await session.refresh(scim_group)
    return scim_group


async def update_scim_group(
    session: AsyncSession,
    scim_group: SCIMGroup,
    display_name: str | None = None,
    mapped_role_id: UUID | None = None,
    mapped_scope_type: str | None = None,
    mapped_scope_id: str | None = None,
    scim_meta: dict[str, Any] | None = None,
) -> SCIMGroup:
    """Update an existing SCIM group"""
    if display_name is not None:
        scim_group.display_name = display_name
    if mapped_role_id is not None:
        scim_group.mapped_role_id = mapped_role_id
    if mapped_scope_type is not None:
        scim_group.mapped_scope_type = mapped_scope_type
    if mapped_scope_id is not None:
        scim_group.mapped_scope_id = mapped_scope_id
    if scim_meta is not None:
        scim_group.scim_meta = scim_meta

    scim_group.updated_at = datetime.now(timezone.utc)
    session.add(scim_group)
    await session.commit()
    await session.refresh(scim_group)
    return scim_group


async def delete_scim_group(session: AsyncSession, scim_group: SCIMGroup) -> None:
    """Delete a SCIM group"""
    # First delete all memberships
    result = await session.exec(
        select(SCIMGroupMembership).where(SCIMGroupMembership.scim_group_id == scim_group.id)
    )
    memberships = result.all()
    for membership in memberships:
        await session.delete(membership)

    # Then delete the group
    await session.delete(scim_group)
    await session.commit()


async def get_scim_group_by_external_id(session: AsyncSession, external_id: str) -> SCIMGroup | None:
    """Get SCIM group by external ID"""
    result = await session.exec(select(SCIMGroup).where(SCIMGroup.external_id == external_id))
    return result.first()


async def list_scim_groups(
    session: AsyncSession,
    organization_id: str | None = None,
    limit: int = 100,
) -> list[SCIMGroup]:
    """List SCIM groups with optional filters"""
    query = select(SCIMGroup)

    if organization_id:
        query = query.where(SCIMGroup.organization_id == organization_id)

    query = query.limit(limit)
    result = await session.exec(query)
    return list(result.all())


# SCIM Group Membership operations
async def create_scim_group_membership(
    session: AsyncSession,
    scim_group_id: UUID,
    scim_user_id: UUID,
    member_ref: str | None = None,
    member_type: str = "User",
) -> SCIMGroupMembership:
    """Add a user to a SCIM group"""
    membership = SCIMGroupMembership(
        scim_group_id=scim_group_id,
        scim_user_id=scim_user_id,
        member_ref=member_ref,
        member_type=member_type,
    )

    session.add(membership)
    await session.commit()
    await session.refresh(membership)

    # If group has a role mapping, grant the role to the user
    result = await session.exec(select(SCIMGroup).where(SCIMGroup.id == scim_group_id))
    group = result.first()

    if group and group.mapped_role_id:
        # Import here to avoid circular import
        from langflow.services.database.models.rbac import create_grant

        # Get the user's LangBuilder user_id
        result = await session.exec(select(SCIMUser).where(SCIMUser.id == scim_user_id))
        scim_user = result.first()

        if scim_user and scim_user.user_id:
            # Create grant for the user
            try:
                await create_grant(
                    session=session,
                    principal_type="user",
                    principal_id=str(scim_user.user_id),
                    role_id=group.mapped_role_id,
                    scope_type=group.mapped_scope_type,
                    scope_id=group.mapped_scope_id,
                )
            except IntegrityError:
                # Grant already exists, that's fine
                await session.rollback()

    return membership


# Provisioning log operations
async def log_scim_event(
    session: AsyncSession,
    event_type: str,
    resource_type: str,
    status: str,
    external_id: str | None = None,
    error_message: str | None = None,
    request_payload: dict[str, Any] | None = None,
    response_payload: dict[str, Any] | None = None,
    organization_id: str | None = None,
    idp_source: str | None = None,
) -> SCIMProvisioningLog:
    """Log a SCIM provisioning event"""
    log_entry = SCIMProvisioningLog(
        event_type=event_type,
        resource_type=resource_type,
        status=status,
        external_id=external_id,
        error_message=error_message,
        request_payload=request_payload,
        response_payload=response_payload,
        organization_id=organization_id,
        idp_source=idp_source,
    )

    session.add(log_entry)
    await session.commit()
    await session.refresh(log_entry)
    return log_entry

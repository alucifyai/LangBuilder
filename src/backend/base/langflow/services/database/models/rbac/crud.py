"""CRUD operations for RBAC models.

Implements GAP #6 from RBAC_PHASE1_AUDIT_REPORT.
Provides async database operations for all RBAC entities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

    from langflow.services.database.models.rbac.audit_log import AuditLog, AuditLogCreate
    from langflow.services.database.models.rbac.grant import Grant, GrantCreate, GrantUpdate
    from langflow.services.database.models.rbac.group import Group, GroupCreate, GroupUpdate
    from langflow.services.database.models.rbac.permission import Permission
    from langflow.services.database.models.rbac.role import Role, RoleCreate, RoleUpdate
    from langflow.services.database.models.rbac.service_account import (
        ServiceAccount,
        ServiceAccountCreate,
        ServiceAccountUpdate,
    )


# ============================================================================
# Permission CRUD (Read-only - catalog is seeded, not user-editable)
# ============================================================================


async def get_permission_by_id(db: AsyncSession, permission_id: str) -> Permission | None:
    """Get permission by ID (format: 'resource_type:action')."""
    from langflow.services.database.models.rbac.permission import Permission

    stmt = select(Permission).where(Permission.id == permission_id)
    return (await db.exec(stmt)).first()


async def list_permissions(
    db: AsyncSession, resource_type: str | None = None, action: str | None = None
) -> list[Permission]:
    """List permissions with optional filters."""
    from langflow.services.database.models.rbac.permission import Permission

    stmt = select(Permission)

    if resource_type:
        stmt = stmt.where(Permission.resource_type == resource_type)
    if action:
        stmt = stmt.where(Permission.action == action)

    return list((await db.exec(stmt)).all())


# ============================================================================
# Role CRUD
# ============================================================================


async def get_role_by_id(db: AsyncSession, role_id: UUID | str) -> Role | None:
    """Get role by ID."""
    from langflow.services.database.models.rbac.role import Role

    if isinstance(role_id, str):
        role_id = UUID(role_id)

    stmt = select(Role).where(Role.id == role_id)
    return (await db.exec(stmt)).first()


async def get_role_by_name(db: AsyncSession, name: str) -> Role | None:
    """Get role by name."""
    from langflow.services.database.models.rbac.role import Role

    stmt = select(Role).where(Role.name == name)
    return (await db.exec(stmt)).first()


async def list_roles(db: AsyncSession, include_system: bool = True) -> list[Role]:
    """List all roles."""
    from langflow.services.database.models.rbac.role import Role

    stmt = select(Role)
    if not include_system:
        stmt = stmt.where(Role.is_system_role == False)  # noqa: E712

    return list((await db.exec(stmt)).all())


async def create_role(db: AsyncSession, role_data: RoleCreate) -> Role:
    """Create a new role (PRD Story 1.2 @AC1)."""
    from langflow.services.database.models.rbac.role import Role

    # Check for duplicate name
    existing = await get_role_by_name(db, role_data.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Role '{role_data.name}' already exists")

    # Validate permissions exist
    from langflow.services.database.models.rbac.permission import Permission

    for perm_id in role_data.permissions:
        perm = await get_permission_by_id(db, perm_id)
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown permission: {perm_id}"
            )

    role = Role.model_validate(role_data, from_attributes=True)
    db.add(role)

    try:
        await db.commit()
        await db.refresh(role)
        return role
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def update_role(db: AsyncSession, role_id: UUID | str, role_data: RoleUpdate) -> Role:
    """Update a role (PRD Story 1.2 @AC3 - version tracking)."""
    from langflow.services.database.models.rbac.role import Role

    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Prevent modification of system roles
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify system roles"
        )

    update_data = role_data.model_dump(exclude_unset=True)
    changed = False

    for attr, value in update_data.items():
        if hasattr(role, attr) and value is not None:
            setattr(role, attr, value)
            changed = True

    if not changed:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Nothing to update")

    # Increment version and update timestamp (PRD Story 1.2 @AC3)
    role.version += 1
    role.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(role)
        return role
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def delete_role(db: AsyncSession, role_id: UUID | str) -> None:
    """Delete a role."""
    from langflow.services.database.models.rbac.role import Role

    role = await get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Prevent deletion of system roles
    if role.is_system_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete system roles"
        )

    # Check for active grants using this role
    from langflow.services.database.models.rbac.grant import Grant

    stmt = select(Grant).where(Grant.role_id == role.id)
    grants = (await db.exec(stmt)).all()
    if grants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete role: {len(grants)} active grant(s) exist",
        )

    await db.delete(role)
    await db.commit()


# ============================================================================
# Group CRUD
# ============================================================================


async def get_group_by_id(db: AsyncSession, group_id: UUID | str) -> Group | None:
    """Get group by ID."""
    from langflow.services.database.models.rbac.group import Group

    if isinstance(group_id, str):
        group_id = UUID(group_id)

    stmt = select(Group).where(Group.id == group_id)
    return (await db.exec(stmt)).first()


async def get_group_by_name(db: AsyncSession, name: str) -> Group | None:
    """Get group by name."""
    from langflow.services.database.models.rbac.group import Group

    stmt = select(Group).where(Group.name == name)
    return (await db.exec(stmt)).first()


async def get_group_by_external_id(db: AsyncSession, external_id: str) -> Group | None:
    """Get group by external IdP ID (for SCIM sync - PRD Story 2.3)."""
    from langflow.services.database.models.rbac.group import Group

    stmt = select(Group).where(Group.external_id == external_id)
    return (await db.exec(stmt)).first()


async def list_groups(db: AsyncSession) -> list[Group]:
    """List all groups."""
    from langflow.services.database.models.rbac.group import Group

    stmt = select(Group)
    return list((await db.exec(stmt)).all())


async def create_group(db: AsyncSession, group_data: GroupCreate) -> Group:
    """Create a new group."""
    from langflow.services.database.models.rbac.group import Group

    # Check for duplicate name
    existing = await get_group_by_name(db, group_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Group '{group_data.name}' already exists"
        )

    group = Group.model_validate(group_data, from_attributes=True)
    db.add(group)

    try:
        await db.commit()
        await db.refresh(group)
        return group
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def update_group(db: AsyncSession, group_id: UUID | str, group_data: GroupUpdate) -> Group:
    """Update a group."""
    from langflow.services.database.models.rbac.group import Group

    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    update_data = group_data.model_dump(exclude_unset=True)
    changed = False

    for attr, value in update_data.items():
        if hasattr(group, attr) and value is not None:
            setattr(group, attr, value)
            changed = True

    if not changed:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Nothing to update")

    group.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(group)
        return group
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def delete_group(db: AsyncSession, group_id: UUID | str) -> None:
    """Delete a group."""
    from langflow.services.database.models.rbac.group import Group

    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Check for active grants
    from langflow.services.database.models.rbac.grant import Grant

    stmt = select(Grant).where(Grant.group_id == group.id)
    grants = (await db.exec(stmt)).all()
    if grants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete group: {len(grants)} active grant(s) exist",
        )

    await db.delete(group)
    await db.commit()


async def add_user_to_group(db: AsyncSession, group_id: UUID | str, user_id: UUID | str) -> None:
    """Add a user to a group."""
    from sqlmodel import text

    if isinstance(group_id, str):
        group_id = UUID(group_id)
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    # Verify group exists
    group = await get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Verify user exists
    from langflow.services.database.models.user.crud import get_user_by_id

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        stmt = text("INSERT INTO user_group (user_id, group_id) VALUES (:user_id, :group_id)")
        await db.exec(stmt, {"user_id": str(user_id), "group_id": str(group_id)})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # User already in group, this is idempotent
        pass


async def remove_user_from_group(db: AsyncSession, group_id: UUID | str, user_id: UUID | str) -> None:
    """Remove a user from a group."""
    from sqlmodel import text

    if isinstance(group_id, str):
        group_id = UUID(group_id)
    if isinstance(user_id, str):
        user_id = UUID(user_id)

    stmt = text("DELETE FROM user_group WHERE user_id = :user_id AND group_id = :group_id")
    result = await db.exec(stmt, {"user_id": str(user_id), "group_id": str(group_id)})
    await db.commit()

    if result.rowcount == 0:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not in group")


# ============================================================================
# Grant CRUD
# ============================================================================


async def get_grant_by_id(db: AsyncSession, grant_id: UUID | str) -> Grant | None:
    """Get grant by ID."""
    from langflow.services.database.models.rbac.grant import Grant

    if isinstance(grant_id, str):
        grant_id = UUID(grant_id)

    stmt = select(Grant).where(Grant.id == grant_id)
    return (await db.exec(stmt)).first()


async def list_grants(
    db: AsyncSession,
    principal_type: str | None = None,
    principal_id: str | None = None,
    scope_type: str | None = None,
    scope_id: str | None = None,
    role_id: str | None = None,
) -> list[Grant]:
    """List grants with optional filters (PRD Story 3.1 @AC1 - list all grants)."""
    from langflow.services.database.models.rbac.grant import Grant

    stmt = select(Grant)

    if principal_type:
        stmt = stmt.where(Grant.principal_type == principal_type)
    if principal_id:
        stmt = stmt.where(Grant.principal_id == principal_id)
    if scope_type:
        stmt = stmt.where(Grant.scope_type == scope_type)
    if scope_id:
        stmt = stmt.where(Grant.scope_id == scope_id)
    if role_id:
        stmt = stmt.where(Grant.role_id == role_id)

    return list((await db.exec(stmt)).all())


async def create_grant(db: AsyncSession, grant_data: GrantCreate, created_by: UUID | str | None = None) -> Grant:
    """Create a new grant (PRD Story 2.1 @AC1, Story 3.4 @AC1)."""
    from langflow.services.database.models.rbac.grant import Grant

    # Verify role exists
    role = await get_role_by_id(db, grant_data.role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Verify principal exists based on type
    from langflow.services.database.models.rbac.grant import PrincipalType

    if grant_data.principal_type == PrincipalType.USER:
        from langflow.services.database.models.user.crud import get_user_by_id

        principal = await get_user_by_id(db, grant_data.principal_id)
        if not principal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    elif grant_data.principal_type == PrincipalType.GROUP:
        principal = await get_group_by_id(db, grant_data.principal_id)
        if not principal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    elif grant_data.principal_type == PrincipalType.SERVICE_ACCOUNT:
        principal = await get_service_account_by_id(db, grant_data.principal_id)
        if not principal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service account not found")

    grant = Grant.model_validate(grant_data, from_attributes=True)
    if created_by:
        grant.created_by = str(created_by)

    db.add(grant)

    try:
        await db.commit()
        await db.refresh(grant)
        return grant
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def update_grant(db: AsyncSession, grant_id: UUID | str, grant_data: GrantUpdate) -> Grant:
    """Update a grant (e.g., extend expiration)."""
    from langflow.services.database.models.rbac.grant import Grant

    grant = await get_grant_by_id(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    update_data = grant_data.model_dump(exclude_unset=True)
    changed = False

    for attr, value in update_data.items():
        if hasattr(grant, attr) and value is not None:
            setattr(grant, attr, value)
            changed = True

    if not changed:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Nothing to update")

    try:
        await db.commit()
        await db.refresh(grant)
        return grant
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def delete_grant(db: AsyncSession, grant_id: UUID | str) -> None:
    """Delete a grant (revoke access - PRD Story 3.4 @AC4)."""
    from langflow.services.database.models.rbac.grant import Grant

    grant = await get_grant_by_id(db, grant_id)
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    await db.delete(grant)
    await db.commit()


# ============================================================================
# ServiceAccount CRUD
# ============================================================================


async def get_service_account_by_id(db: AsyncSession, sa_id: UUID | str) -> ServiceAccount | None:
    """Get service account by ID."""
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    if isinstance(sa_id, str):
        sa_id = UUID(sa_id)

    stmt = select(ServiceAccount).where(ServiceAccount.id == sa_id)
    return (await db.exec(stmt)).first()


async def get_service_account_by_name(db: AsyncSession, name: str) -> ServiceAccount | None:
    """Get service account by name."""
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    stmt = select(ServiceAccount).where(ServiceAccount.name == name)
    return (await db.exec(stmt)).first()


async def get_service_account_by_api_key(db: AsyncSession, api_key: str) -> ServiceAccount | None:
    """Get service account by API key (used for authentication).

    HIGH PRIORITY FIX #2: Optimized authentication using key_prefix index
    Phase 2 Audit Recommendation #2

    Uses indexed key_prefix (first 8 chars) to reduce candidates before hash verification.
    Performance: O(N) -> O(log N) for lookup + O(K) for verification, where K << N

    Args:
        db: Database session
        api_key: Plaintext API key to authenticate

    Returns:
        ServiceAccount if authenticated, None otherwise
    """
    from langflow.services.auth.utils import verify_password
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    # Extract key prefix for indexed lookup (first 8-16 chars)
    # Standard format: "sa-{random}" where random is 32+ chars
    # We use enough prefix to make collisions rare but not so much that
    # we reveal too much of the key in the database
    prefix_length = min(16, len(api_key))
    key_prefix = api_key[:prefix_length]

    # Query only service accounts with matching prefix (indexed)
    # This dramatically reduces hash verification candidates
    stmt = select(ServiceAccount).where(
        ServiceAccount.is_active == True,  # noqa: E712
        ServiceAccount.key_prefix == key_prefix
    )
    service_accounts = (await db.exec(stmt)).all()

    # Verify hash for matching candidates (typically 1 or 0)
    for sa in service_accounts:
        if sa.api_key_hash and verify_password(api_key, sa.api_key_hash):
            return sa

    return None


async def list_service_accounts(db: AsyncSession, active_only: bool = False) -> list[ServiceAccount]:
    """List all service accounts."""
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    stmt = select(ServiceAccount)
    if active_only:
        stmt = stmt.where(ServiceAccount.is_active == True)  # noqa: E712

    return list((await db.exec(stmt)).all())


async def create_service_account(
    db: AsyncSession, sa_data: ServiceAccountCreate, created_by: UUID | str | None = None
) -> tuple[ServiceAccount, str]:
    """Create a new service account (PRD Story 2.4 @AC1).

    Returns:
        Tuple of (ServiceAccount, plaintext_api_key)
        The plaintext API key is only returned once and should be stored by the caller.
    """
    import secrets

    from langflow.services.auth.utils import get_password_hash
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    # Check for duplicate name
    existing = await get_service_account_by_name(db, sa_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Service account '{sa_data.name}' already exists"
        )

    sa = ServiceAccount.model_validate(sa_data, from_attributes=True)
    if created_by:
        sa.created_by = str(created_by)

    # Generate API key and hash it (RBAC_PHASE1_AUDIT_REPORT CONCERN #1)
    plaintext_api_key = f"sa-{secrets.token_urlsafe(32)}"
    sa.api_key_hash = get_password_hash(plaintext_api_key)

    # HIGH PRIORITY FIX #2: Store key prefix for fast lookups
    # Phase 2 Audit Recommendation #2
    sa.key_prefix = plaintext_api_key[:16]

    db.add(sa)

    try:
        await db.commit()
        await db.refresh(sa)
        return sa, plaintext_api_key  # Return plaintext key only once
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def update_service_account(
    db: AsyncSession, sa_id: UUID | str, sa_data: ServiceAccountUpdate
) -> ServiceAccount:
    """Update a service account."""
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    sa = await get_service_account_by_id(db, sa_id)
    if not sa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service account not found")

    update_data = sa_data.model_dump(exclude_unset=True)
    changed = False

    for attr, value in update_data.items():
        if hasattr(sa, attr) and value is not None:
            setattr(sa, attr, value)
            changed = True

    if not changed:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED, detail="Nothing to update")

    sa.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(sa)
        return sa
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def delete_service_account(db: AsyncSession, sa_id: UUID | str) -> None:
    """Delete a service account."""
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    sa = await get_service_account_by_id(db, sa_id)
    if not sa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service account not found")

    # Check for active grants
    from langflow.services.database.models.rbac.grant import Grant

    stmt = select(Grant).where(Grant.service_account_id == sa.id)
    grants = (await db.exec(stmt)).all()
    if grants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete service account: {len(grants)} active grant(s) exist",
        )

    await db.delete(sa)
    await db.commit()


async def rotate_service_account_api_key(db: AsyncSession, sa_id: UUID | str) -> tuple[ServiceAccount, str]:
    """Rotate (regenerate) service account API key.

    Returns:
        Tuple of (ServiceAccount, plaintext_api_key)
        The plaintext API key is only returned once and should be stored by the caller.
    """
    import secrets

    from langflow.services.auth.utils import get_password_hash
    from langflow.services.database.models.rbac.service_account import ServiceAccount

    sa = await get_service_account_by_id(db, sa_id)
    if not sa:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service account not found")

    # Generate new API key and hash it (RBAC_PHASE1_AUDIT_REPORT CONCERN #1)
    plaintext_api_key = f"sa-{secrets.token_urlsafe(32)}"
    sa.api_key_hash = get_password_hash(plaintext_api_key)

    # HIGH PRIORITY FIX #2: Store key prefix for fast lookups
    # Phase 2 Audit Recommendation #2
    sa.key_prefix = plaintext_api_key[:16]

    sa.updated_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(sa)
        return sa, plaintext_api_key  # Return plaintext key only once
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


# ============================================================================
# AuditLog CRUD (Append-only)
# ============================================================================


async def create_audit_log(db: AsyncSession, audit_data: AuditLogCreate) -> AuditLog:
    """Create an audit log entry (PRD Story 5.1 @AC1).

    AuditLog is append-only - no update or delete operations.
    """
    from langflow.services.database.models.rbac.audit_log import AuditLog

    audit = AuditLog.model_validate(audit_data, from_attributes=True)
    db.add(audit)

    try:
        await db.commit()
        await db.refresh(audit)
        return audit
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


async def list_audit_logs(
    db: AsyncSession,
    action: str | None = None,
    actor_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """List audit logs with filters.

    HIGH PRIORITY FIX from Phase 3 Audit: Added date range filtering
    PRD Story 5.1 @AC2, Story 5.2 @AC3

    Args:
        db: Database session
        action: Filter by action type
        actor_id: Filter by actor ID
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        start_date: Filter logs after this date (inclusive)
        end_date: Filter logs before this date (inclusive)
        limit: Maximum results
        offset: Pagination offset

    Returns:
        List of AuditLog objects ordered by timestamp descending
    """
    from langflow.services.database.models.rbac.audit_log import AuditLog

    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if resource_type:
        stmt = stmt.where(AuditLog.resource_type == resource_type)
    if resource_id:
        stmt = stmt.where(AuditLog.resource_id == resource_id)

    # HIGH PRIORITY FIX: Date range filtering
    if start_date:
        stmt = stmt.where(AuditLog.timestamp >= start_date)
    if end_date:
        stmt = stmt.where(AuditLog.timestamp <= end_date)

    stmt = stmt.limit(limit).offset(offset)

    return list((await db.exec(stmt)).all())


async def get_audit_log_by_id(db: AsyncSession, audit_id: UUID | str) -> AuditLog | None:
    """Get audit log by ID."""
    from langflow.services.database.models.rbac.audit_log import AuditLog

    if isinstance(audit_id, str):
        audit_id = UUID(audit_id)

    stmt = select(AuditLog).where(AuditLog.id == audit_id)
    return (await db.exec(stmt)).first()

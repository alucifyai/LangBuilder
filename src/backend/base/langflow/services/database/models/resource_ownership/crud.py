"""
CRUD operations for Resource Ownership
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.resource_ownership.model import (
    OwnershipTransferRequest,
    ResourceOwnership,
)


# ============================================================================
# Resource Ownership CRUD
# ============================================================================


async def create_ownership(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
    owner_type: str,
    owner_id: UUID | str,
) -> ResourceOwnership:
    """Create resource ownership record."""
    ownership = ResourceOwnership(
        resource_type=resource_type,
        resource_id=resource_id,
        owner_type=owner_type,
        owner_id=str(owner_id),
    )

    db.add(ownership)
    await db.commit()
    await db.refresh(ownership)
    return ownership


async def get_ownership(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
) -> ResourceOwnership | None:
    """Get ownership for a resource."""
    stmt = select(ResourceOwnership).where(
        ResourceOwnership.resource_type == resource_type,
        ResourceOwnership.resource_id == resource_id,
    )
    return (await db.exec(stmt)).first()


async def get_owned_resources(
    db: AsyncSession,
    owner_id: UUID | str,
    resource_type: str | None = None,
) -> list[ResourceOwnership]:
    """Get all resources owned by a principal."""
    stmt = select(ResourceOwnership).where(ResourceOwnership.owner_id == str(owner_id))

    if resource_type:
        stmt = stmt.where(ResourceOwnership.resource_type == resource_type)

    return list((await db.exec(stmt)).all())


async def transfer_ownership(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
    new_owner_id: UUID | str,
    transferred_by: UUID | str,
) -> ResourceOwnership | None:
    """Transfer ownership of a resource."""
    ownership = await get_ownership(db, resource_type, resource_id)
    if not ownership:
        return None

    # Record transfer
    ownership.transferred_from = ownership.owner_id
    ownership.owner_id = str(new_owner_id)
    ownership.transferred_at = datetime.now(timezone.utc)
    ownership.transferred_by = str(transferred_by)

    db.add(ownership)
    await db.commit()
    await db.refresh(ownership)
    return ownership


async def delete_ownership(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
) -> bool:
    """Delete ownership record (when resource is deleted)."""
    ownership = await get_ownership(db, resource_type, resource_id)
    if not ownership:
        return False

    await db.delete(ownership)
    await db.commit()
    return True


# ============================================================================
# Ownership Transfer Request CRUD
# ============================================================================


async def create_transfer_request(
    db: AsyncSession,
    resource_type: str,
    resource_id: str,
    current_owner_id: UUID | str,
    new_owner_id: UUID | str,
    requested_by: UUID | str,
    expires_in_days: int = 7,
) -> OwnershipTransferRequest:
    """Create an ownership transfer request."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    request = OwnershipTransferRequest(
        resource_type=resource_type,
        resource_id=resource_id,
        current_owner_id=str(current_owner_id),
        new_owner_id=str(new_owner_id),
        requested_by=str(requested_by),
        expires_at=expires_at,
    )

    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def get_transfer_request(
    db: AsyncSession,
    request_id: UUID | str,
) -> OwnershipTransferRequest | None:
    """Get transfer request by ID."""
    stmt = select(OwnershipTransferRequest).where(
        OwnershipTransferRequest.id == str(request_id)
    )
    return (await db.exec(stmt)).first()


async def list_pending_transfer_requests(
    db: AsyncSession,
    owner_id: UUID | str | None = None,
) -> list[OwnershipTransferRequest]:
    """List pending transfer requests, optionally filtered by owner."""
    stmt = select(OwnershipTransferRequest).where(
        OwnershipTransferRequest.status == "pending"
    )

    if owner_id:
        stmt = stmt.where(
            (OwnershipTransferRequest.current_owner_id == str(owner_id))
            | (OwnershipTransferRequest.new_owner_id == str(owner_id))
        )

    stmt = stmt.order_by(OwnershipTransferRequest.created_at.desc())
    return list((await db.exec(stmt)).all())


async def approve_transfer_request(
    db: AsyncSession,
    request_id: UUID | str,
    approved_by: UUID | str,
) -> OwnershipTransferRequest | None:
    """Approve a transfer request and execute the transfer."""
    request = await get_transfer_request(db, request_id)
    if not request or request.status != "pending":
        return None

    # Update request status
    request.status = "approved"
    request.approved_by = str(approved_by)
    request.resolved_at = datetime.now(timezone.utc)

    # Execute the transfer
    await transfer_ownership(
        db=db,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        new_owner_id=request.new_owner_id,
        transferred_by=approved_by,
    )

    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def reject_transfer_request(
    db: AsyncSession,
    request_id: UUID | str,
    rejected_by: UUID | str,
    reason: str | None = None,
) -> OwnershipTransferRequest | None:
    """Reject a transfer request."""
    request = await get_transfer_request(db, request_id)
    if not request or request.status != "pending":
        return None

    request.status = "rejected"
    request.approved_by = str(rejected_by)
    request.resolved_at = datetime.now(timezone.utc)
    request.rejection_reason = reason

    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def cancel_transfer_request(
    db: AsyncSession,
    request_id: UUID | str,
) -> OwnershipTransferRequest | None:
    """Cancel a transfer request."""
    request = await get_transfer_request(db, request_id)
    if not request or request.status != "pending":
        return None

    request.status = "cancelled"
    request.resolved_at = datetime.now(timezone.utc)

    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def cleanup_expired_transfer_requests(db: AsyncSession) -> int:
    """Mark expired transfer requests (maintenance task)."""
    now = datetime.now(timezone.utc)
    stmt = select(OwnershipTransferRequest).where(
        OwnershipTransferRequest.expires_at < now,
        OwnershipTransferRequest.status == "pending",
    )

    expired_requests = (await db.exec(stmt)).all()
    count = 0

    for request in expired_requests:
        request.status = "expired"
        request.resolved_at = now
        db.add(request)
        count += 1

    await db.commit()
    return count

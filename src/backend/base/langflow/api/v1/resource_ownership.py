"""
Resource Ownership API
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.auth.utils import get_current_active_user
from langflow.services.database.models.audit.crud import create_audit_log
from langflow.services.database.models.audit.model import AuditAction
from langflow.services.database.models.resource_ownership.crud import (
    approve_transfer_request,
    cancel_transfer_request,
    create_ownership,
    create_transfer_request,
    get_owned_resources,
    get_ownership,
    list_pending_transfer_requests,
    reject_transfer_request,
    transfer_ownership,
)
from langflow.services.database.models.user.model import User
from langflow.services.deps import get_session

router = APIRouter(prefix="/ownership", tags=["Resource Ownership"])


# Request/Response Models
class OwnershipCreate(BaseModel):
    """Request to create ownership record."""

    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource ID")
    owner_type: str = Field(default="user", description="Owner type")
    owner_id: str = Field(..., description="Owner ID")


class OwnershipResponse(BaseModel):
    """Ownership record response."""

    id: str
    resource_type: str
    resource_id: str
    owner_type: str
    owner_id: str
    transferred_from: str | None
    transferred_at: str | None
    created_at: str


class TransferRequest(BaseModel):
    """Request to transfer ownership."""

    new_owner_id: str = Field(..., description="New owner ID")
    require_approval: bool = Field(
        default=False,
        description="Require approval from new owner",
    )


class TransferRequestResponse(BaseModel):
    """Transfer request response."""

    id: str
    resource_type: str
    resource_id: str
    current_owner_id: str
    new_owner_id: str
    requested_by: str
    status: str
    created_at: str
    expires_at: str
    approved_by: str | None = None
    resolved_at: str | None = None
    rejection_reason: str | None = None


class ApproveRejectRequest(BaseModel):
    """Request to approve/reject transfer."""

    reason: str | None = Field(None, description="Rejection reason (if rejecting)")


# Endpoints
@router.post("", response_model=OwnershipResponse, status_code=201)
async def create_ownership_record(
    request: OwnershipCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> OwnershipResponse:
    """Create ownership record for a resource."""
    ownership = await create_ownership(
        db=db,
        resource_type=request.resource_type,
        resource_id=request.resource_id,
        owner_type=request.owner_type,
        owner_id=request.owner_id,
    )

    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_CREATED,
        resource_type="ownership",
        resource_id=ownership.id,
        metadata={
            "resource_type": ownership.resource_type,
            "resource_id": ownership.resource_id,
        },
    )

    return OwnershipResponse(
        id=ownership.id,
        resource_type=ownership.resource_type,
        resource_id=ownership.resource_id,
        owner_type=ownership.owner_type,
        owner_id=ownership.owner_id,
        transferred_from=ownership.transferred_from,
        transferred_at=ownership.transferred_at.isoformat() if ownership.transferred_at else None,
        created_at=ownership.created_at.isoformat(),
    )


@router.get("/{resource_type}/{resource_id}", response_model=OwnershipResponse)
async def get_ownership_record(
    resource_type: str,
    resource_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> OwnershipResponse:
    """Get ownership record for a resource."""
    ownership = await get_ownership(db, resource_type, resource_id)

    if not ownership:
        raise HTTPException(status_code=404, detail="Ownership record not found")

    return OwnershipResponse(
        id=ownership.id,
        resource_type=ownership.resource_type,
        resource_id=ownership.resource_id,
        owner_type=ownership.owner_type,
        owner_id=ownership.owner_id,
        transferred_from=ownership.transferred_from,
        transferred_at=ownership.transferred_at.isoformat() if ownership.transferred_at else None,
        created_at=ownership.created_at.isoformat(),
    )


@router.get("/owner/{owner_id}", response_model=list[OwnershipResponse])
async def list_owned_resources(
    owner_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    resource_type: str | None = None,
) -> list[OwnershipResponse]:
    """List resources owned by a principal."""
    ownerships = await get_owned_resources(db, owner_id, resource_type)

    return [
        OwnershipResponse(
            id=o.id,
            resource_type=o.resource_type,
            resource_id=o.resource_id,
            owner_type=o.owner_type,
            owner_id=o.owner_id,
            transferred_from=o.transferred_from,
            transferred_at=o.transferred_at.isoformat() if o.transferred_at else None,
            created_at=o.created_at.isoformat(),
        )
        for o in ownerships
    ]


@router.post("/{resource_type}/{resource_id}/transfer")
async def transfer_resource_ownership(
    resource_type: str,
    resource_id: str,
    request: TransferRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Transfer ownership of a resource."""
    ownership = await get_ownership(db, resource_type, resource_id)

    if not ownership:
        raise HTTPException(status_code=404, detail="Ownership record not found")

    # Check if current user is owner or admin
    if ownership.owner_id != str(current_user.id) and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only owner can transfer ownership")

    if request.require_approval:
        # Create transfer request
        transfer_req = await create_transfer_request(
            db=db,
            resource_type=resource_type,
            resource_id=resource_id,
            current_owner_id=ownership.owner_id,
            new_owner_id=request.new_owner_id,
            requested_by=current_user.id,
        )

        return TransferRequestResponse(
            id=transfer_req.id,
            resource_type=transfer_req.resource_type,
            resource_id=transfer_req.resource_id,
            current_owner_id=transfer_req.current_owner_id,
            new_owner_id=transfer_req.new_owner_id,
            requested_by=transfer_req.requested_by,
            status=transfer_req.status,
            created_at=transfer_req.created_at.isoformat(),
            expires_at=transfer_req.expires_at.isoformat(),
        )
    else:
        # Direct transfer
        updated = await transfer_ownership(
            db=db,
            resource_type=resource_type,
            resource_id=resource_id,
            new_owner_id=request.new_owner_id,
            transferred_by=current_user.id,
        )

        await create_audit_log(
            db=db,
            actor_id=current_user.id,
            action=AuditAction.GRANT_UPDATED,
            resource_type="ownership",
            resource_id=updated.id,
            metadata={"new_owner": request.new_owner_id},
        )

        return OwnershipResponse(
            id=updated.id,
            resource_type=updated.resource_type,
            resource_id=updated.resource_id,
            owner_type=updated.owner_type,
            owner_id=updated.owner_id,
            transferred_from=updated.transferred_from,
            transferred_at=updated.transferred_at.isoformat() if updated.transferred_at else None,
            created_at=updated.created_at.isoformat(),
        )


@router.get("/transfers/pending", response_model=list[TransferRequestResponse])
async def list_pending_transfers(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[TransferRequestResponse]:
    """List pending transfer requests for current user."""
    requests = await list_pending_transfer_requests(db, current_user.id)

    return [
        TransferRequestResponse(
            id=r.id,
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            current_owner_id=r.current_owner_id,
            new_owner_id=r.new_owner_id,
            requested_by=r.requested_by,
            status=r.status,
            created_at=r.created_at.isoformat(),
            expires_at=r.expires_at.isoformat(),
            approved_by=r.approved_by,
            resolved_at=r.resolved_at.isoformat() if r.resolved_at else None,
            rejection_reason=r.rejection_reason,
        )
        for r in requests
    ]


@router.post("/transfers/{request_id}/approve", response_model=TransferRequestResponse)
async def approve_transfer(
    request_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TransferRequestResponse:
    """Approve an ownership transfer request."""
    result = await approve_transfer_request(db, request_id, current_user.id)

    if not result:
        raise HTTPException(status_code=404, detail="Transfer request not found")

    await create_audit_log(
        db=db,
        actor_id=current_user.id,
        action=AuditAction.GRANT_UPDATED,
        resource_type="ownership_transfer",
        resource_id=result.id,
    )

    return TransferRequestResponse(
        id=result.id,
        resource_type=result.resource_type,
        resource_id=result.resource_id,
        current_owner_id=result.current_owner_id,
        new_owner_id=result.new_owner_id,
        requested_by=result.requested_by,
        status=result.status,
        created_at=result.created_at.isoformat(),
        expires_at=result.expires_at.isoformat(),
        approved_by=result.approved_by,
        resolved_at=result.resolved_at.isoformat() if result.resolved_at else None,
    )


@router.post("/transfers/{request_id}/reject", response_model=TransferRequestResponse)
async def reject_transfer(
    request_id: UUID,
    request: ApproveRejectRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TransferRequestResponse:
    """Reject an ownership transfer request."""
    result = await reject_transfer_request(db, request_id, current_user.id, request.reason)

    if not result:
        raise HTTPException(status_code=404, detail="Transfer request not found")

    return TransferRequestResponse(
        id=result.id,
        resource_type=result.resource_type,
        resource_id=result.resource_id,
        current_owner_id=result.current_owner_id,
        new_owner_id=result.new_owner_id,
        requested_by=result.requested_by,
        status=result.status,
        created_at=result.created_at.isoformat(),
        expires_at=result.expires_at.isoformat(),
        approved_by=result.approved_by,
        resolved_at=result.resolved_at.isoformat() if result.resolved_at else None,
        rejection_reason=result.rejection_reason,
    )


@router.delete("/transfers/{request_id}", status_code=204)
async def cancel_transfer(
    request_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Cancel a transfer request."""
    result = await cancel_transfer_request(db, request_id)

    if not result:
        raise HTTPException(status_code=404, detail="Transfer request not found")

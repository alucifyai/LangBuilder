"""
API endpoints for Temporary Grants
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.temporary_grant import crud
from langflow.services.database.models.temporary_grant.model import TemporaryGrant
from langflow.services.deps import get_session

router = APIRouter(prefix="/temporary-grants", tags=["Temporary Grants"])


# Request/Response Models
class CreateTemporaryGrantRequest(BaseModel):
    """Request to create a temporary grant."""

    grant_id: str = Field(..., description="Base grant ID to make temporary")
    expires_at: datetime = Field(..., description="When the grant expires")
    starts_at: datetime | None = Field(None, description="When grant becomes active")
    auto_revoke: bool = Field(True, description="Auto-revoke on expiration")
    notify_before_expiry: bool = Field(True, description="Send notification before expiry")
    notification_hours: int = Field(24, description="Hours before expiry to notify")
    max_extensions: int | None = Field(None, description="Max allowed extensions")
    reason: str | None = Field(None, description="Reason for temporary grant")


class ExtendTemporaryGrantRequest(BaseModel):
    """Request to extend a temporary grant."""

    new_expires_at: datetime = Field(..., description="New expiration time")


class TemporaryGrantResponse(BaseModel):
    """Response with temporary grant details."""

    id: str
    grant_id: str
    starts_at: datetime
    expires_at: datetime
    auto_revoke: bool
    notify_before_expiry: bool
    notification_hours: int
    is_expired: bool
    expired_at: datetime | None
    notified_at: datetime | None
    extension_count: int
    max_extensions: int | None
    extended_by: str | None
    reason: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExpirationProcessResult(BaseModel):
    """Result of processing expired grants."""

    processed_count: int
    message: str


# Endpoints
@router.post("", response_model=TemporaryGrantResponse, status_code=status.HTTP_201_CREATED)
async def create_temporary_grant(
    request: CreateTemporaryGrantRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> TemporaryGrant:
    """
    Create a temporary grant.
    Requires admin permissions.
    """
    # Validate expiration is in the future
    if request.expires_at <= datetime.now(request.expires_at.tzinfo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiration time must be in the future",
        )

    # Validate starts_at is before expires_at
    if request.starts_at and request.starts_at >= request.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start time must be before expiration time",
        )

    # TODO: Verify grant_id exists
    # TODO: Get current user ID
    created_by = "system"  # Placeholder

    temp_grant = await crud.create_temporary_grant(
        db=db,
        grant_id=request.grant_id,
        expires_at=request.expires_at,
        created_by=created_by,
        starts_at=request.starts_at,
        auto_revoke=request.auto_revoke,
        notify_before_expiry=request.notify_before_expiry,
        notification_hours=request.notification_hours,
        max_extensions=request.max_extensions,
        reason=request.reason,
    )

    return temp_grant


@router.get("", response_model=list[TemporaryGrantResponse])
async def list_temporary_grants(
    db: Annotated[AsyncSession, Depends(get_session)],
    include_expired: bool = False,
    # TODO: Add current_user dependency and permission check
) -> list[TemporaryGrant]:
    """
    List temporary grants.
    Requires admin permissions.
    """
    return await crud.list_temporary_grants(db, include_expired=include_expired)


@router.get("/expiring-soon", response_model=list[TemporaryGrantResponse])
async def list_expiring_soon(
    db: Annotated[AsyncSession, Depends(get_session)],
    hours: int = 24,
    # TODO: Add current_user dependency and permission check
) -> list[TemporaryGrant]:
    """
    List grants expiring within specified hours.
    Requires admin permissions.
    """
    return await crud.list_expiring_soon(db, hours=hours)


@router.get("/grant/{grant_id}", response_model=TemporaryGrantResponse)
async def get_temporary_grant_by_grant(
    grant_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> TemporaryGrant:
    """
    Get temporary grant by base grant ID.
    Requires admin permissions.
    """
    temp_grant = await crud.get_temporary_grant_by_grant_id(db, grant_id)
    if not temp_grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No temporary grant found for grant {grant_id}",
        )
    return temp_grant


@router.get("/{temp_grant_id}", response_model=TemporaryGrantResponse)
async def get_temporary_grant(
    temp_grant_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> TemporaryGrant:
    """
    Get temporary grant by ID.
    Requires admin permissions.
    """
    temp_grant = await crud.get_temporary_grant_by_id(db, temp_grant_id)
    if not temp_grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Temporary grant {temp_grant_id} not found",
        )
    return temp_grant


@router.post("/{temp_grant_id}/extend", response_model=TemporaryGrantResponse)
async def extend_temporary_grant(
    temp_grant_id: str,
    request: ExtendTemporaryGrantRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> TemporaryGrant:
    """
    Extend a temporary grant's expiration.
    Requires admin permissions.
    """
    # Validate new expiration is in the future
    if request.new_expires_at <= datetime.now(request.new_expires_at.tzinfo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New expiration time must be in the future",
        )

    # TODO: Get current user ID
    extended_by = "system"  # Placeholder

    temp_grant = await crud.extend_temporary_grant(
        db=db,
        temp_grant_id=temp_grant_id,
        new_expires_at=request.new_expires_at,
        extended_by=extended_by,
    )

    if not temp_grant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot extend grant (may be expired or at max extensions)",
        )

    return temp_grant


@router.post("/{temp_grant_id}/expire", response_model=TemporaryGrantResponse)
async def expire_grant_manually(
    temp_grant_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> TemporaryGrant:
    """
    Manually expire a temporary grant.
    Requires admin permissions.
    """
    temp_grant = await crud.expire_grant(db, temp_grant_id, revoke_base_grant=True)
    if not temp_grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Temporary grant {temp_grant_id} not found",
        )
    return temp_grant


@router.post("/process-expired", response_model=ExpirationProcessResult)
async def process_expired_grants(
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> ExpirationProcessResult:
    """
    Process all expired grants (revoke and mark as expired).
    This should be called by a scheduled job.
    Requires admin permissions.
    """
    count = await crud.process_expired_grants(db)
    return ExpirationProcessResult(
        processed_count=count,
        message=f"Processed {count} expired grant(s)",
    )


@router.delete("/{temp_grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_temporary_grant(
    temp_grant_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency and permission check
) -> None:
    """
    Delete temporary grant tracking.
    Does not affect the base grant.
    Requires admin permissions.
    """
    success = await crud.delete_temporary_grant(db, temp_grant_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Temporary grant {temp_grant_id} not found",
        )

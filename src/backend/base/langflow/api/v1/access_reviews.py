"""
API endpoints for Access Reviews
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.access_review import crud
from langflow.services.database.models.access_review.model import (
    AccessAnomaly,
    AccessReviewCampaign,
    AccessReviewItem,
)
from langflow.services.deps import get_session

router = APIRouter(prefix="/access-reviews", tags=["Access Reviews"])


# Request/Response Models
class CreateCampaignRequest(BaseModel):
    """Request to create a review campaign."""

    name: str
    start_date: datetime
    due_date: datetime
    scope_type: str = "organization"
    scope_id: str | None = None
    description: str | None = None
    campaign_type: str = "periodic"
    reviewers: list[str] | None = None
    compliance_framework: str | None = None
    auto_revoke_on_no_response: bool = False
    is_recurring: bool = False
    recurrence_interval_days: int | None = None


class CampaignResponse(BaseModel):
    """Response with campaign details."""

    id: str
    name: str
    description: str | None
    campaign_type: str
    scope_type: str
    scope_id: str | None
    start_date: datetime
    due_date: datetime
    status: str
    total_items: int
    reviewed_items: int
    approved_items: int
    revoked_items: int
    created_by: str
    reviewers: list[str]
    compliance_framework: str | None
    auto_revoke_on_no_response: bool
    is_recurring: bool
    recurrence_interval_days: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class ReviewItemResponse(BaseModel):
    """Response with review item details."""

    id: str
    campaign_id: str
    grant_id: str
    principal_id: str
    principal_email: str | None
    role_id: str
    role_name: str | None
    resource_type: str | None
    resource_id: str | None
    status: str
    reviewer_id: str | None
    reviewed_at: datetime | None
    decision: str | None
    justification: str | None
    last_used_at: datetime | None
    usage_count: int
    anomaly_score: float | None
    anomaly_reasons: list[str] | None
    risk_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewDecisionRequest(BaseModel):
    """Request to make a review decision."""

    decision: str = Field(..., description="Decision: approve or revoke")
    justification: str | None = Field(None, description="Justification for decision")


class BulkReviewRequest(BaseModel):
    """Request to review multiple items."""

    item_ids: list[str]
    decision: str
    justification: str | None = None


class AnomalyResponse(BaseModel):
    """Response with anomaly details."""

    id: str
    anomaly_type: str
    severity: str
    confidence: float
    principal_id: str
    principal_email: str | None
    grant_id: str | None
    title: str
    description: str
    evidence: dict | None
    recommendations: list[str] | None
    status: str
    assigned_to: str | None
    resolved_at: datetime | None
    resolution_notes: str | None
    detected_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResolveAnomalyRequest(BaseModel):
    """Request to resolve an anomaly."""

    status: str = Field(..., description="Status: resolved or false_positive")
    resolution_notes: str | None = None


# Campaign endpoints


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CreateCampaignRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AccessReviewCampaign:
    """
    Create an access review campaign.
    Requires admin permissions.
    """
    # TODO: Get current user ID
    created_by = "system"

    campaign = await crud.create_review_campaign(
        db=db,
        name=request.name,
        start_date=request.start_date,
        due_date=request.due_date,
        created_by=created_by,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        description=request.description,
        campaign_type=request.campaign_type,
        reviewers=request.reviewers,
        compliance_framework=request.compliance_framework,
        auto_revoke_on_no_response=request.auto_revoke_on_no_response,
        is_recurring=request.is_recurring,
        recurrence_interval_days=request.recurrence_interval_days,
    )

    return campaign


@router.get("/campaigns", response_model=list[CampaignResponse])
async def list_campaigns(
    db: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = Query(None, alias="status"),
    created_by: str | None = None,
    active_only: bool = False,
    # TODO: Add current_user dependency
) -> list[AccessReviewCampaign]:
    """
    List access review campaigns.
    Requires admin or reviewer permissions.
    """
    return await crud.list_review_campaigns(
        db=db, status=status_filter, created_by=created_by, active_only=active_only
    )


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AccessReviewCampaign:
    """
    Get a specific campaign.
    Requires admin or reviewer permissions.
    """
    campaign = await crud.get_review_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    return campaign


@router.patch("/campaigns/{campaign_id}/status")
async def update_campaign_status_route(
    campaign_id: str,
    new_status: str = Query(..., alias="status"),
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> CampaignResponse:
    """
    Update campaign status.
    Requires admin permissions.
    """
    campaign = await crud.update_campaign_status(db, campaign_id, new_status)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    return CampaignResponse.model_validate(campaign)


# Review item endpoints


@router.get("/campaigns/{campaign_id}/items", response_model=list[ReviewItemResponse])
async def list_campaign_items(
    campaign_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = Query(None, alias="status"),
    reviewer_id: str | None = None,
    # TODO: Add current_user dependency
) -> list[AccessReviewItem]:
    """
    List review items for a campaign.
    Requires admin or reviewer permissions.
    """
    return await crud.list_review_items(
        db=db, campaign_id=campaign_id, status=status_filter, reviewer_id=reviewer_id
    )


@router.get("/items/{item_id}", response_model=ReviewItemResponse)
async def get_review_item(
    item_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AccessReviewItem:
    """
    Get a specific review item.
    Requires admin or reviewer permissions.
    """
    item = await crud.get_review_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {item_id} not found",
        )
    return item


@router.post("/items/{item_id}/review", response_model=ReviewItemResponse)
async def review_item(
    item_id: str,
    request: ReviewDecisionRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AccessReviewItem:
    """
    Make a review decision on an item.
    Requires reviewer permissions.
    """
    # Validate decision
    if request.decision not in ["approve", "revoke"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approve' or 'revoke'",
        )

    # TODO: Get current user ID
    reviewer_id = "system"

    item = await crud.review_access_item(
        db=db,
        item_id=item_id,
        reviewer_id=reviewer_id,
        decision=request.decision,
        justification=request.justification,
        auto_execute=True,
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review item {item_id} not found",
        )

    return item


@router.post("/items/bulk-review")
async def bulk_review(
    request: BulkReviewRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> dict:
    """
    Review multiple items at once.
    Requires reviewer permissions.
    """
    # Validate decision
    if request.decision not in ["approve", "revoke"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approve' or 'revoke'",
        )

    # TODO: Get current user ID
    reviewer_id = "system"

    count = await crud.bulk_review_items(
        db=db,
        item_ids=request.item_ids,
        reviewer_id=reviewer_id,
        decision=request.decision,
        justification=request.justification,
    )

    return {"reviewed_count": count, "message": f"Reviewed {count} item(s)"}


@router.post("/process-overdue")
async def process_overdue(
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> dict:
    """
    Process overdue reviews (auto-revoke if configured).
    Should be run by scheduled job.
    Requires admin permissions.
    """
    revoked_count = await crud.process_overdue_reviews(db)
    return {
        "revoked_count": revoked_count,
        "message": f"Auto-revoked {revoked_count} overdue access grant(s)",
    }


# Anomaly endpoints


@router.get("/anomalies", response_model=list[AnomalyResponse])
async def list_anomalies(
    db: Annotated[AsyncSession, Depends(get_session)],
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = None,
    anomaly_type: str | None = None,
    principal_id: str | None = None,
    limit: int = Query(100, le=500),
    # TODO: Add current_user dependency
) -> list[AccessAnomaly]:
    """
    List access anomalies.
    Requires admin or security permissions.
    """
    return await crud.list_anomalies(
        db=db,
        status=status_filter,
        severity=severity,
        anomaly_type=anomaly_type,
        principal_id=principal_id,
        limit=limit,
    )


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyResponse)
async def get_anomaly(
    anomaly_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AccessAnomaly:
    """
    Get a specific anomaly.
    Requires admin or security permissions.
    """
    anomaly = await crud.get_anomaly(db, anomaly_id)
    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly {anomaly_id} not found",
        )
    return anomaly


@router.post("/anomalies/{anomaly_id}/resolve", response_model=AnomalyResponse)
async def resolve_anomaly_route(
    anomaly_id: str,
    request: ResolveAnomalyRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> AccessAnomaly:
    """
    Resolve an anomaly.
    Requires security or admin permissions.
    """
    anomaly = await crud.resolve_anomaly(
        db=db,
        anomaly_id=anomaly_id,
        status=request.status,
        resolution_notes=request.resolution_notes,
    )

    if not anomaly:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anomaly {anomaly_id} not found",
        )

    return anomaly

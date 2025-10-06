"""
CRUD operations for Access Reviews
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.access_review.model import (
    AccessAnomaly,
    AccessReviewCampaign,
    AccessReviewItem,
)
from langflow.services.database.models.grant.crud import revoke_grant


# Campaign operations


async def create_review_campaign(
    db: AsyncSession,
    name: str,
    start_date: datetime,
    due_date: datetime,
    created_by: str,
    scope_type: str = "organization",
    scope_id: str | None = None,
    description: str | None = None,
    campaign_type: str = "periodic",
    reviewers: list[str] | None = None,
    compliance_framework: str | None = None,
    auto_revoke_on_no_response: bool = False,
    is_recurring: bool = False,
    recurrence_interval_days: int | None = None,
) -> AccessReviewCampaign:
    """Create an access review campaign."""
    campaign = AccessReviewCampaign(
        name=name,
        description=description,
        campaign_type=campaign_type,
        scope_type=scope_type,
        scope_id=scope_id,
        start_date=start_date,
        due_date=due_date,
        created_by=created_by,
        reviewers=reviewers or [],
        compliance_framework=compliance_framework,
        auto_revoke_on_no_response=auto_revoke_on_no_response,
        is_recurring=is_recurring,
        recurrence_interval_days=recurrence_interval_days,
    )

    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def get_review_campaign(
    db: AsyncSession,
    campaign_id: UUID | str,
) -> AccessReviewCampaign | None:
    """Get review campaign by ID."""
    stmt = select(AccessReviewCampaign).where(AccessReviewCampaign.id == str(campaign_id))
    return (await db.exec(stmt)).first()


async def list_review_campaigns(
    db: AsyncSession,
    status: str | None = None,
    created_by: str | None = None,
    active_only: bool = False,
) -> list[AccessReviewCampaign]:
    """List review campaigns."""
    stmt = select(AccessReviewCampaign)

    if status:
        stmt = stmt.where(AccessReviewCampaign.status == status)

    if created_by:
        stmt = stmt.where(AccessReviewCampaign.created_by == created_by)

    if active_only:
        stmt = stmt.where(AccessReviewCampaign.status == "active")

    stmt = stmt.order_by(AccessReviewCampaign.created_at.desc())
    return list((await db.exec(stmt)).all())


async def update_campaign_status(
    db: AsyncSession,
    campaign_id: UUID | str,
    status: str,
) -> AccessReviewCampaign | None:
    """Update campaign status."""
    campaign = await get_review_campaign(db, campaign_id)
    if not campaign:
        return None

    campaign.status = status
    campaign.updated_at = datetime.now(timezone.utc)

    if status == "completed":
        campaign.completed_at = datetime.now(timezone.utc)

    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def update_campaign_stats(
    db: AsyncSession,
    campaign_id: UUID | str,
) -> None:
    """Recalculate campaign statistics."""
    campaign = await get_review_campaign(db, campaign_id)
    if not campaign:
        return

    items = await list_review_items(db, campaign_id)
    campaign.total_items = len(items)
    campaign.reviewed_items = sum(1 for item in items if item.status != "pending")
    campaign.approved_items = sum(1 for item in items if item.decision == "approve")
    campaign.revoked_items = sum(1 for item in items if item.decision == "revoke")
    campaign.updated_at = datetime.now(timezone.utc)

    db.add(campaign)
    await db.commit()


# Review item operations


async def create_review_item(
    db: AsyncSession,
    campaign_id: str,
    grant_id: str,
    principal_id: str,
    role_id: str,
    principal_email: str | None = None,
    role_name: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    reviewer_id: str | None = None,
    risk_level: str = "low",
    last_used_at: datetime | None = None,
    usage_count: int = 0,
) -> AccessReviewItem:
    """Create a review item."""
    item = AccessReviewItem(
        campaign_id=campaign_id,
        grant_id=grant_id,
        principal_id=principal_id,
        principal_email=principal_email,
        role_id=role_id,
        role_name=role_name,
        resource_type=resource_type,
        resource_id=resource_id,
        reviewer_id=reviewer_id,
        risk_level=risk_level,
        last_used_at=last_used_at,
        usage_count=usage_count,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def get_review_item(
    db: AsyncSession,
    item_id: UUID | str,
) -> AccessReviewItem | None:
    """Get review item by ID."""
    stmt = select(AccessReviewItem).where(AccessReviewItem.id == str(item_id))
    return (await db.exec(stmt)).first()


async def list_review_items(
    db: AsyncSession,
    campaign_id: str,
    status: str | None = None,
    reviewer_id: str | None = None,
) -> list[AccessReviewItem]:
    """List review items for a campaign."""
    stmt = select(AccessReviewItem).where(AccessReviewItem.campaign_id == campaign_id)

    if status:
        stmt = stmt.where(AccessReviewItem.status == status)

    if reviewer_id:
        stmt = stmt.where(AccessReviewItem.reviewer_id == reviewer_id)

    stmt = stmt.order_by(AccessReviewItem.risk_level.desc(), AccessReviewItem.created_at)
    return list((await db.exec(stmt)).all())


async def review_access_item(
    db: AsyncSession,
    item_id: UUID | str,
    reviewer_id: str,
    decision: str,
    justification: str | None = None,
    auto_execute: bool = True,
) -> AccessReviewItem | None:
    """Review an access item (approve or revoke)."""
    item = await get_review_item(db, item_id)
    if not item:
        return None

    item.status = "approved" if decision == "approve" else "revoked"
    item.decision = decision
    item.reviewer_id = reviewer_id
    item.reviewed_at = datetime.now(timezone.utc)
    item.justification = justification
    item.updated_at = datetime.now(timezone.utc)

    db.add(item)

    # Auto-execute revocation if configured
    if auto_execute and decision == "revoke":
        await revoke_grant(db, item.grant_id)

    await db.commit()
    await db.refresh(item)

    # Update campaign stats
    await update_campaign_stats(db, item.campaign_id)

    return item


async def bulk_review_items(
    db: AsyncSession,
    item_ids: list[str],
    reviewer_id: str,
    decision: str,
    justification: str | None = None,
) -> int:
    """Review multiple items at once."""
    count = 0
    for item_id in item_ids:
        result = await review_access_item(
            db, item_id, reviewer_id, decision, justification, auto_execute=True
        )
        if result:
            count += 1
    return count


async def process_overdue_reviews(
    db: AsyncSession,
) -> int:
    """Process overdue review items (auto-revoke if configured)."""
    now = datetime.now(timezone.utc)

    # Find campaigns past due date with auto-revoke enabled
    stmt = (
        select(AccessReviewCampaign)
        .where(AccessReviewCampaign.due_date < now)
        .where(AccessReviewCampaign.status == "active")
        .where(AccessReviewCampaign.auto_revoke_on_no_response == True)  # noqa: E712
    )
    overdue_campaigns = list((await db.exec(stmt)).all())

    revoked_count = 0
    for campaign in overdue_campaigns:
        # Get pending items
        pending_items = await list_review_items(db, campaign.id, status="pending")

        for item in pending_items:
            # Auto-revoke
            item.status = "revoked"
            item.decision = "revoke"
            item.reviewed_at = now
            item.justification = "Auto-revoked: No response by due date"
            db.add(item)

            await revoke_grant(db, item.grant_id)
            revoked_count += 1

        # Update campaign
        campaign.status = "completed"
        campaign.completed_at = now
        db.add(campaign)

        await update_campaign_stats(db, campaign.id)

    await db.commit()
    return revoked_count


# Anomaly detection


async def create_anomaly(
    db: AsyncSession,
    anomaly_type: str,
    principal_id: str,
    title: str,
    description: str,
    severity: str = "medium",
    confidence: float = 0.5,
    principal_email: str | None = None,
    grant_id: str | None = None,
    evidence: dict | None = None,
    recommendations: list[str] | None = None,
) -> AccessAnomaly:
    """Create an access anomaly."""
    anomaly = AccessAnomaly(
        anomaly_type=anomaly_type,
        severity=severity,
        confidence=confidence,
        principal_id=principal_id,
        principal_email=principal_email,
        grant_id=grant_id,
        title=title,
        description=description,
        evidence=evidence,
        recommendations=recommendations,
    )

    db.add(anomaly)
    await db.commit()
    await db.refresh(anomaly)
    return anomaly


async def get_anomaly(
    db: AsyncSession,
    anomaly_id: UUID | str,
) -> AccessAnomaly | None:
    """Get anomaly by ID."""
    stmt = select(AccessAnomaly).where(AccessAnomaly.id == str(anomaly_id))
    return (await db.exec(stmt)).first()


async def list_anomalies(
    db: AsyncSession,
    status: str | None = None,
    severity: str | None = None,
    anomaly_type: str | None = None,
    principal_id: str | None = None,
    limit: int = 100,
) -> list[AccessAnomaly]:
    """List access anomalies."""
    stmt = select(AccessAnomaly)

    if status:
        stmt = stmt.where(AccessAnomaly.status == status)

    if severity:
        stmt = stmt.where(AccessAnomaly.severity == severity)

    if anomaly_type:
        stmt = stmt.where(AccessAnomaly.anomaly_type == anomaly_type)

    if principal_id:
        stmt = stmt.where(AccessAnomaly.principal_id == principal_id)

    stmt = stmt.order_by(AccessAnomaly.severity.desc(), AccessAnomaly.detected_at.desc())
    stmt = stmt.limit(limit)

    return list((await db.exec(stmt)).all())


async def resolve_anomaly(
    db: AsyncSession,
    anomaly_id: UUID | str,
    status: str,
    resolution_notes: str | None = None,
) -> AccessAnomaly | None:
    """Resolve an anomaly."""
    anomaly = await get_anomaly(db, anomaly_id)
    if not anomaly:
        return None

    anomaly.status = status
    anomaly.resolved_at = datetime.now(timezone.utc)
    anomaly.resolution_notes = resolution_notes
    anomaly.updated_at = datetime.now(timezone.utc)

    db.add(anomaly)
    await db.commit()
    await db.refresh(anomaly)
    return anomaly


async def detect_unused_access(
    db: AsyncSession,
    days_threshold: int = 90,
) -> list[AccessAnomaly]:
    """
    Detect unused access (grants not used in X days).
    This is a placeholder - real implementation would query grant usage data.
    """
    # TODO: Implement actual usage tracking integration
    # This would query grant usage from audit logs or usage tracking tables
    return []


async def detect_dormant_users(
    db: AsyncSession,
    days_threshold: int = 180,
) -> list[AccessAnomaly]:
    """
    Detect dormant users (not logged in for X days).
    This is a placeholder - real implementation would query auth logs.
    """
    # TODO: Implement actual dormant user detection from auth logs
    return []

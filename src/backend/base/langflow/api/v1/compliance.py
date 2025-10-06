"""
API endpoints for Compliance Reports
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.services.database.models.compliance import crud
from langflow.services.database.models.compliance.model import ComplianceControl, ComplianceReport
from langflow.services.deps import get_session

router = APIRouter(prefix="/compliance", tags=["Compliance"])


# Request/Response Models
class GenerateReportRequest(BaseModel):
    """Request to generate a compliance report."""

    name: str
    report_type: str = Field(..., description="Type: soc2, gdpr, iso27001, custom")
    period_start: datetime
    period_end: datetime
    framework_version: str | None = None
    description: str | None = None
    organization_id: str | None = None


class ComplianceReportResponse(BaseModel):
    """Response with compliance report details."""

    id: str
    name: str
    report_type: str
    framework_version: str | None
    description: str | None
    period_start: datetime
    period_end: datetime
    status: str
    completion_percentage: int
    summary: dict | None
    findings: list[dict] | None
    recommendations: list[dict] | None
    controls: list[dict] | None
    metrics: dict | None
    generated_by: str
    organization_id: str | None
    attestation_required: bool
    attested_by: str | None
    attested_at: datetime | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class ComplianceControlResponse(BaseModel):
    """Response with compliance control details."""

    id: str
    control_id: str
    framework: str
    category: str
    name: str
    description: str
    requirements: list[str]
    implementation_status: str
    implementation_notes: str | None
    responsible_party: str | None
    evidence_required: bool
    evidence_items: list[str] | None
    last_tested_at: datetime | None
    test_frequency_days: int | None
    test_results: dict | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdateControlRequest(BaseModel):
    """Request to update control implementation."""

    implementation_status: str
    implementation_notes: str | None = None


class RecordTestRequest(BaseModel):
    """Request to record control test results."""

    test_results: dict


# Report endpoints


@router.post("/reports", response_model=ComplianceReportResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(
    request: GenerateReportRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> ComplianceReport:
    """
    Generate a compliance report.
    Requires admin permissions.
    """
    # TODO: Get current user ID
    generated_by = "system"

    # Route to specific report generator based on type
    if request.report_type == "soc2":
        report = await crud.generate_soc2_report(
            db=db,
            period_start=request.period_start,
            period_end=request.period_end,
            generated_by=generated_by,
            organization_id=request.organization_id,
        )
    elif request.report_type == "gdpr":
        report = await crud.generate_gdpr_report(
            db=db,
            period_start=request.period_start,
            period_end=request.period_end,
            generated_by=generated_by,
            organization_id=request.organization_id,
        )
    elif request.report_type == "custom" or request.report_type == "access":
        report = await crud.generate_access_report(
            db=db,
            period_start=request.period_start,
            period_end=request.period_end,
            generated_by=generated_by,
            organization_id=request.organization_id,
        )
    else:
        # Generic report
        report = await crud.create_compliance_report(
            db=db,
            name=request.name,
            report_type=request.report_type,
            period_start=request.period_start,
            period_end=request.period_end,
            generated_by=generated_by,
            framework_version=request.framework_version,
            description=request.description,
            organization_id=request.organization_id,
        )

    return report


@router.get("/reports", response_model=list[ComplianceReportResponse])
async def list_reports(
    db: Annotated[AsyncSession, Depends(get_session)],
    report_type: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    organization_id: str | None = None,
    limit: int = Query(50, le=200),
    # TODO: Add current_user dependency
) -> list[ComplianceReport]:
    """
    List compliance reports.
    Requires admin permissions.
    """
    return await crud.list_compliance_reports(
        db=db,
        report_type=report_type,
        status=status_filter,
        organization_id=organization_id,
        limit=limit,
    )


@router.get("/reports/{report_id}", response_model=ComplianceReportResponse)
async def get_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> ComplianceReport:
    """
    Get a specific compliance report.
    Requires admin permissions.
    """
    report = await crud.get_compliance_report(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    return report


@router.post("/reports/{report_id}/attest", response_model=ComplianceReportResponse)
async def attest_report(
    report_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> ComplianceReport:
    """
    Attest to a compliance report.
    Requires authorized attestor role.
    """
    # TODO: Get current user ID
    attested_by = "system"

    report = await crud.attest_report(db, report_id, attested_by)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found or does not require attestation",
        )
    return report


# Control endpoints


@router.get("/controls", response_model=list[ComplianceControlResponse])
async def list_controls(
    db: Annotated[AsyncSession, Depends(get_session)],
    framework: str | None = None,
    implementation_status: str | None = None,
    active_only: bool = True,
    # TODO: Add current_user dependency
) -> list[ComplianceControl]:
    """
    List compliance controls.
    Requires admin permissions.
    """
    return await crud.list_compliance_controls(
        db=db,
        framework=framework,
        implementation_status=implementation_status,
        active_only=active_only,
    )


@router.get("/controls/{control_id}", response_model=ComplianceControlResponse)
async def get_control(
    control_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> ComplianceControl:
    """
    Get a specific compliance control.
    Requires admin permissions.
    """
    control = await crud.get_compliance_control(db, control_id)
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found",
        )
    return control


@router.patch("/controls/{control_id}/implementation", response_model=ComplianceControlResponse)
async def update_control_implementation(
    control_id: str,
    request: UpdateControlRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> ComplianceControl:
    """
    Update control implementation status.
    Requires admin permissions.
    """
    control = await crud.update_control_implementation(
        db=db,
        control_id=control_id,
        implementation_status=request.implementation_status,
        implementation_notes=request.implementation_notes,
    )

    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found",
        )

    return control


@router.post("/controls/{control_id}/test", response_model=ComplianceControlResponse)
async def record_control_test(
    control_id: str,
    request: RecordTestRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> ComplianceControl:
    """
    Record control test results.
    Requires auditor or admin permissions.
    """
    control = await crud.record_control_test(
        db=db, control_id=control_id, test_results=request.test_results
    )

    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found",
        )

    return control


@router.post("/seed/soc2-controls")
async def seed_soc2_controls(
    db: Annotated[AsyncSession, Depends(get_session)],
    # TODO: Add current_user dependency
) -> dict:
    """
    Seed SOC2 compliance controls.
    Requires admin permissions.
    """
    await crud.seed_soc2_controls(db)
    return {"message": "SOC2 controls seeded successfully"}

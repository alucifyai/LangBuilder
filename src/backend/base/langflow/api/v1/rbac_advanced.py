"""Advanced RBAC API endpoints for Phase 5 features.

This module provides API endpoints for advanced RBAC features including:
- Multi-environment permission management
- Service account management with token scoping
- Break-glass emergency access
- Advanced audit logging and compliance reporting
- Conditional permissions management

Implementation follows existing LangBuilder API patterns and includes
comprehensive permission checking and audit logging.
"""

# NO future annotations per Phase 1 requirements
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import build_content_type_to_response
from langflow.services.auth.utils import get_current_active_user
from langflow.services.deps import get_session

# Import advanced features service
from langflow.services.rbac.advanced_features_service import AdvancedRBACFeaturesService, ConditionalPermissionContext
from langflow.services.rbac.dependencies import RBACAdmin, WorkspaceAdmin

router = APIRouter(prefix="/rbac-advanced", tags=["RBAC Advanced Features"])

# Request/Response Models

class EnvironmentPermissionRequest(BaseModel):
    """Request model for environment permission check."""
    environment_id: str = Field(description="Environment ID to check")
    action: str = Field(description="Action to perform (deploy, read, write, delete)")
    context: dict | None = Field(default=None, description="Additional context for conditional permissions")


class EnvironmentPermissionResponse(BaseModel):
    """Response model for environment permission check."""
    granted: bool = Field(description="Whether permission is granted")
    environment_id: str = Field(description="Environment ID")
    action: str = Field(description="Action checked")
    user_id: str = Field(description="User ID")
    evaluation_time_ms: float = Field(description="Time taken for evaluation")


class ServiceAccountCreateRequest(BaseModel):
    """Request model for creating service account with token."""
    workspace_id: str = Field(description="Workspace ID for service account")
    account_name: str = Field(description="Name of the service account")
    token_name: str = Field(description="Name of the token")
    scoped_permissions: list[str] = Field(description="List of permissions for the token")
    scope_type: str = Field(default="workspace", description="Type of scope (workspace, project, environment)")
    scope_id: str | None = Field(default=None, description="ID of the scope entity")
    allowed_ips: list[str] | None = Field(default=None, description="List of allowed IP addresses")
    expires_days: int = Field(default=365, description="Token expiration in days")


class ServiceAccountTokenValidationRequest(BaseModel):
    """Request model for service account token validation."""
    token_hash: str = Field(description="Hashed token value")
    requested_action: str = Field(description="Action being requested")
    resource_type: str = Field(description="Type of resource being accessed")
    resource_id: str | None = Field(default=None, description="ID of specific resource")


class BreakGlassAccessRequest(BaseModel):
    """Request model for break-glass emergency access."""
    justification: str = Field(min_length=20, description="Justification for emergency access")
    emergency_level: str = Field(default="medium", description="Level of emergency (low, medium, high, critical)")
    requested_permissions: list[str] | None = Field(default=None, description="Specific permissions being requested")
    resource_context: dict | None = Field(default=None, description="Context about resources being accessed")


class BreakGlassAccessResponse(BaseModel):
    """Response model for break-glass access evaluation."""
    granted: bool = Field(description="Whether access is granted")
    justification: str = Field(description="Provided justification")
    emergency_level: str = Field(description="Emergency level")
    approval_required: bool = Field(description="Whether additional approval is required")
    approval_timeout_minutes: int = Field(description="Timeout for approval process")
    evaluation_time_ms: float = Field(description="Time taken for evaluation")


class ComplianceReportRequest(BaseModel):
    """Request model for compliance report generation."""
    report_type: str = Field(default="soc2", description="Type of compliance report (soc2, iso27001, gdpr, ccpa)")
    start_date: datetime | None = Field(default=None, description="Start date for report period")
    end_date: datetime | None = Field(default=None, description="End date for report period")
    workspace_id: str | None = Field(default=None, description="Workspace ID to filter report")


# API Endpoints

@router.post(
    "/environment/check-permission",
    response_model=EnvironmentPermissionResponse,
    status_code=status.HTTP_200_OK,
    responses=build_content_type_to_response(status.HTTP_200_OK),
)
async def check_environment_permission(
    request: Request,
    permission_request: EnvironmentPermissionRequest,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> EnvironmentPermissionResponse:
    """Check if user has permission for specific environment action.
    
    This endpoint evaluates environment-scoped permissions including
    conditional checks based on IP, time, risk score, and MFA status.
    """
    try:
        # Initialize advanced features service
        advanced_service = AdvancedRBACFeaturesService()
        await advanced_service.initialize_service()

        # Create conditional permission context from request
        context = ConditionalPermissionContext(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_time=datetime.now(timezone.utc),
            custom_attributes=permission_request.context or {}
        )

        start_time = datetime.now(timezone.utc)

        # Check environment permission
        granted = await advanced_service.check_environment_permission(
            session=session,
            user=current_user,
            environment_id=permission_request.environment_id,
            action=permission_request.action,
            context=context
        )

        evaluation_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.info("Environment permission check completed", extra={
            "user_id": str(current_user.id),
            "environment_id": permission_request.environment_id,
            "action": permission_request.action,
            "granted": granted,
            "evaluation_time_ms": evaluation_time
        })

        return EnvironmentPermissionResponse(
            granted=granted,
            environment_id=permission_request.environment_id,
            action=permission_request.action,
            user_id=str(current_user.id),
            evaluation_time_ms=evaluation_time
        )

    except Exception as exc:
        logger.error("Error checking environment permission", extra={
            "user_id": str(current_user.id),
            "environment_id": permission_request.environment_id,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during environment permission check"
        ) from exc


@router.post(
    "/service-account/create-with-token",
    status_code=status.HTTP_201_CREATED,
    responses=build_content_type_to_response(status.HTTP_201_CREATED),
)
async def create_service_account_with_token(
    create_request: ServiceAccountCreateRequest,
    current_user=Depends(WorkspaceAdmin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Create service account with scoped token.
    
    This endpoint creates a new service account and generates a scoped
    API token with specific permissions and scope restrictions.
    """
    try:
        # Initialize advanced features service
        advanced_service = AdvancedRBACFeaturesService()
        await advanced_service.initialize_service()

        # Create service account with scoped token
        result = await advanced_service.create_service_account_with_scoped_token(
            session=session,
            creator=current_user,
            workspace_id=create_request.workspace_id,
            account_name=create_request.account_name,
            token_name=create_request.token_name,
            scoped_permissions=create_request.scoped_permissions,
            scope_type=create_request.scope_type,
            scope_id=create_request.scope_id,
            allowed_ips=create_request.allowed_ips,
            expires_days=create_request.expires_days
        )

        logger.info("Service account created with scoped token", extra={
            "creator_id": str(current_user.id),
            "workspace_id": create_request.workspace_id,
            "service_account_id": result["service_account"]["id"],
            "token_id": result["token"]["id"]
        })

        return result

    except Exception as exc:
        logger.error("Error creating service account with token", extra={
            "creator_id": str(current_user.id),
            "workspace_id": create_request.workspace_id,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during service account creation"
        ) from exc


@router.post(
    "/service-account/validate-token-scope",
    status_code=status.HTTP_200_OK,
    responses=build_content_type_to_response(status.HTTP_200_OK),
)
async def validate_service_account_token_scope(
    request: Request,
    validation_request: ServiceAccountTokenValidationRequest,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Validate service account token scope for requested action.
    
    This endpoint validates whether a service account token has the
    necessary scope and permissions for the requested action.
    """
    try:
        # Initialize advanced features service
        advanced_service = AdvancedRBACFeaturesService()
        await advanced_service.initialize_service()

        # Create context for validation
        context = ConditionalPermissionContext(
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_time=datetime.now(timezone.utc)
        )

        start_time = datetime.now(timezone.utc)

        # Validate token scope
        valid = await advanced_service.validate_service_account_token_scope(
            session=session,
            token_hash=validation_request.token_hash,
            requested_action=validation_request.requested_action,
            resource_type=validation_request.resource_type,
            resource_id=validation_request.resource_id,
            context=context
        )

        evaluation_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.info("Service account token validation completed", extra={
            "token_prefix": validation_request.token_hash[:8] + "...",
            "requested_action": validation_request.requested_action,
            "resource_type": validation_request.resource_type,
            "valid": valid,
            "evaluation_time_ms": evaluation_time
        })

        return {
            "valid": valid,
            "requested_action": validation_request.requested_action,
            "resource_type": validation_request.resource_type,
            "resource_id": validation_request.resource_id,
            "evaluation_time_ms": evaluation_time
        }

    except Exception as exc:
        logger.error("Error validating service account token scope", extra={
            "token_prefix": validation_request.token_hash[:8] + "...",
            "requested_action": validation_request.requested_action,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during token validation"
        ) from exc


@router.post(
    "/break-glass/request-access",
    response_model=BreakGlassAccessResponse,
    status_code=status.HTTP_200_OK,
    responses=build_content_type_to_response(status.HTTP_200_OK),
)
async def request_break_glass_access(
    break_glass_request: BreakGlassAccessRequest,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> BreakGlassAccessResponse:
    """Request break-glass emergency access.
    
    This endpoint evaluates break-glass access requests for emergency
    situations requiring elevated permissions with proper justification.
    """
    try:
        # Initialize advanced features service
        advanced_service = AdvancedRBACFeaturesService()
        await advanced_service.initialize_service()

        start_time = datetime.now(timezone.utc)

        # Evaluate break-glass access
        result = await advanced_service.evaluate_break_glass_access(
            session=session,
            user=current_user,
            justification=break_glass_request.justification,
            emergency_level=break_glass_request.emergency_level,
            requested_permissions=break_glass_request.requested_permissions,
            resource_context=break_glass_request.resource_context
        )

        evaluation_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.warning("Break-glass access request evaluated", extra={
            "user_id": str(current_user.id),
            "emergency_level": break_glass_request.emergency_level,
            "granted": result.granted,
            "approval_required": result.approval_required,
            "evaluation_time_ms": evaluation_time
        })

        return BreakGlassAccessResponse(
            granted=result.granted,
            justification=result.justification or break_glass_request.justification,
            emergency_level=result.emergency_level,
            approval_required=result.approval_required,
            approval_timeout_minutes=result.approval_timeout_minutes,
            evaluation_time_ms=evaluation_time
        )

    except Exception as exc:
        logger.error("Error evaluating break-glass access", extra={
            "user_id": str(current_user.id),
            "emergency_level": break_glass_request.emergency_level,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during break-glass access evaluation"
        ) from exc


@router.post(
    "/compliance/generate-report",
    status_code=status.HTTP_200_OK,
    responses=build_content_type_to_response(status.HTTP_200_OK),
)
async def generate_compliance_report(
    report_request: ComplianceReportRequest,
    current_user=Depends(RBACAdmin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Generate compliance report for audit purposes.
    
    This endpoint generates comprehensive compliance reports for various
    standards including SOC 2, ISO 27001, GDPR, and CCPA.
    """
    try:
        # Initialize advanced features service
        advanced_service = AdvancedRBACFeaturesService()
        await advanced_service.initialize_service()

        start_time = datetime.now(timezone.utc)

        # Generate compliance report
        report = await advanced_service.generate_compliance_report(
            session=session,
            report_type=report_request.report_type,
            start_date=report_request.start_date,
            end_date=report_request.end_date,
            workspace_id=report_request.workspace_id
        )

        generation_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Add generation metadata
        report["generation_metadata"] = {
            "requested_by": str(current_user.id),
            "generation_time_ms": generation_time,
            "langbuilder_version": "2.0.0",  # TODO: Get from version info
            "report_format": "json"
        }

        logger.info("Compliance report generated", extra={
            "user_id": str(current_user.id),
            "report_type": report_request.report_type,
            "workspace_id": report_request.workspace_id,
            "total_events": report.get("total_events", 0),
            "generation_time_ms": generation_time
        })

        return report

    except Exception as exc:
        logger.error("Error generating compliance report", extra={
            "user_id": str(current_user.id),
            "report_type": report_request.report_type,
            "workspace_id": report_request.workspace_id,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during compliance report generation"
        ) from exc


@router.get(
    "/environment/{environment_id}/permissions",
    status_code=status.HTTP_200_OK,
    responses=build_content_type_to_response(status.HTTP_200_OK),
)
async def get_environment_permissions(
    environment_id: str,
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get user's permissions for a specific environment.
    
    This endpoint returns all permissions the current user has for
    the specified environment, including conditional restrictions.
    """
    try:
        # Import necessary models
        from sqlalchemy import and_, select

        from langflow.services.database.models.rbac.environment import Environment
        from langflow.services.database.models.rbac.permission import Permission
        from langflow.services.database.models.rbac.role_assignment import RoleAssignment
        from langflow.services.database.models.rbac.role_permission import RolePermission

        # Get environment details
        environment_result = await session.exec(
            select(Environment).where(Environment.id == environment_id)
        )
        environment = environment_result.first()

        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Environment not found"
            )

        # Get user's role assignments for this environment
        role_assignments_result = await session.exec(
            select(RoleAssignment).where(
                and_(
                    RoleAssignment.user_id == current_user.id,
                    RoleAssignment.environment_id == environment_id,
                    RoleAssignment.is_active == True
                )
            )
        )
        role_assignments = role_assignments_result.all()

        # Get permissions for assigned roles
        permissions = []
        for assignment in role_assignments:
            role_permissions_result = await session.exec(
                select(Permission)
                .join(RolePermission)
                .where(RolePermission.role_id == assignment.role_id)
            )
            role_permissions = role_permissions_result.all()
            permissions.extend([{
                "name": perm.name,
                "description": perm.description,
                "role_id": str(assignment.role_id),
                "assignment_id": str(assignment.id)
            } for perm in role_permissions])

        # Get conditional restrictions
        conditional_restrictions = {
            "ip_restrictions": environment.type == "production",
            "time_restrictions": environment.type == "production",
            "mfa_required": environment.type == "production",
            "risk_threshold": 0.7 if environment.type == "production" else 0.9
        }

        logger.info("Environment permissions retrieved", extra={
            "user_id": str(current_user.id),
            "environment_id": environment_id,
            "permission_count": len(permissions),
            "environment_type": environment.type
        })

        return {
            "environment": {
                "id": str(environment.id),
                "name": environment.name,
                "type": environment.type,
                "project_id": str(environment.project_id)
            },
            "permissions": permissions,
            "conditional_restrictions": conditional_restrictions,
            "user_id": str(current_user.id)
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Error getting environment permissions", extra={
            "user_id": str(current_user.id),
            "environment_id": environment_id,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error retrieving environment permissions"
        ) from exc


@router.get(
    "/service-accounts/{workspace_id}",
    status_code=status.HTTP_200_OK,
    responses=build_content_type_to_response(status.HTTP_200_OK),
)
async def list_workspace_service_accounts(
    workspace_id: str,
    include_tokens: bool = Query(default=False, description="Include token information"),
    current_user=Depends(WorkspaceAdmin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """List service accounts for a workspace.
    
    This endpoint returns all service accounts in the specified workspace
    with optional token information for administrative purposes.
    """
    try:
        from sqlalchemy import select

        from langflow.services.database.models.rbac.service_account import ServiceAccount, ServiceAccountToken

        # Get service accounts for workspace
        service_accounts_result = await session.exec(
            select(ServiceAccount).where(ServiceAccount.workspace_id == workspace_id)
        )
        service_accounts = service_accounts_result.all()

        accounts_data = []
        for account in service_accounts:
            account_data = {
                "id": str(account.id),
                "name": account.name,
                "description": account.description,
                "service_type": account.service_type,
                "is_active": account.is_active,
                "created_at": account.created_at.isoformat(),
                "last_used_at": account.last_used_at.isoformat() if account.last_used_at else None,
                "created_by_id": str(account.created_by_id)
            }

            if include_tokens:
                # Get token information (without sensitive data)
                tokens_result = await session.exec(
                    select(ServiceAccountToken).where(
                        ServiceAccountToken.service_account_id == account.id
                    )
                )
                tokens = tokens_result.all()

                account_data["tokens"] = [{
                    "id": str(token.id),
                    "name": token.name,
                    "token_prefix": token.token_prefix,
                    "is_active": token.is_active,
                    "scoped_permissions": token.scoped_permissions,
                    "scope_type": token.scope_type,
                    "scope_id": str(token.scope_id) if token.scope_id else None,
                    "last_used_at": token.last_used_at.isoformat() if token.last_used_at else None,
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                    "usage_count": token.usage_count
                } for token in tokens]

                account_data["active_token_count"] = len([t for t in tokens if t.is_active])
                account_data["total_token_count"] = len(tokens)

            accounts_data.append(account_data)

        logger.info("Service accounts listed", extra={
            "user_id": str(current_user.id),
            "workspace_id": workspace_id,
            "account_count": len(accounts_data),
            "include_tokens": include_tokens
        })

        return {
            "workspace_id": workspace_id,
            "service_accounts": accounts_data,
            "total_count": len(accounts_data)
        }

    except Exception as exc:
        logger.error("Error listing service accounts", extra={
            "user_id": str(current_user.id),
            "workspace_id": workspace_id,
            "error": str(exc)
        }, exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error listing service accounts"
        ) from exc

"""Enhanced API Endpoint Example with Complete RBAC Integration.

This example demonstrates how to integrate the enhanced RBAC system
with token scoping, data access controls, and comprehensive security
enforcement in FastAPI endpoints.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.auth.enhanced_auth import EnhancedAuthenticationService
from langflow.services.database.models.flow.model import Flow, FlowCreate, FlowRead, FlowUpdate
from langflow.services.rbac.runtime_enforcement import RBACRuntimeEnforcementService, RuntimeEnforcementContext
from loguru import logger

# Example router with enhanced RBAC
router = APIRouter(prefix="/enhanced-flows", tags=["Enhanced Flows"])

# Security scheme for extracting API keys
security = HTTPBearer(auto_error=False)


async def get_enhanced_enforcement_context(
    request: Request,
    session: Annotated[DbSession, Depends()],
    current_user: Annotated[CurrentActiveUser, Depends()],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> RuntimeEnforcementContext:
    """Create enhanced enforcement context from request."""
    # Initialize services
    auth_service = EnhancedAuthenticationService()
    # Note: In real implementation, rbac_service would be injected
    from langflow.services.deps import get_rbac_service

    rbac_service = get_rbac_service()
    enforcement_service = RBACRuntimeEnforcementService(rbac_service, auth_service)

    # Extract API key
    api_key = None
    if credentials:
        api_key = credentials.credentials
    else:
        # Check other sources
        api_key = request.headers.get("x-api-key") or request.query_params.get("x-api-key")

    # Extract workspace/project/environment from request
    workspace_id = request.path_params.get("workspace_id")
    project_id = request.path_params.get("project_id")
    environment_id = request.path_params.get("environment_id")

    # Create enforcement context
    return await enforcement_service.create_enforcement_context(
        session=session,
        api_key=api_key,
        user=current_user,
        workspace_id=UUID(workspace_id) if workspace_id else None,
        project_id=UUID(project_id) if project_id else None,
        environment_id=UUID(environment_id) if environment_id else None,
        request_path=request.url.path,
        request_method=request.method,
    )


@router.get("/flows/{flow_id}", response_model=FlowRead)
async def get_flow_with_enhanced_rbac(
    flow_id: UUID,
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
):
    """Get a flow with comprehensive RBAC and token scoping enforcement."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Perform secure data operation
        flow = await enforcement_service.secure_data_operation(
            session=session,
            context=context,
            operation="get",
            model_class=Flow,
            model_id=flow_id,
            permission_override="flow:read",
        )

        if not flow:
            # Audit the failed access attempt
            await enforcement_service.audit_enforcement_decision(
                context=context,
                operation="get",
                resource_type="flow",
                resource_id=flow_id,
                permission="flow:read",
                decision=False,
                reason="Access denied or resource not found",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found or access denied")

        # Audit successful access
        await enforcement_service.audit_enforcement_decision(
            context=context,
            operation="get",
            resource_type="flow",
            resource_id=flow_id,
            permission="flow:read",
            decision=True,
            reason="Access granted",
        )

        return FlowRead.model_validate(flow, from_attributes=True)

    except Exception as e:
        logger.error(f"Error retrieving flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.get("/flows", response_model=list[FlowRead])
async def list_flows_with_enhanced_rbac(
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
    limit: int = 50,
    offset: int = 0,
):
    """List flows with comprehensive RBAC filtering and token scoping."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Build filters based on context
        filters = {}
        if context.effective_workspace_id:
            filters["workspace_id"] = context.effective_workspace_id

        # Perform secure list operation
        flows = await enforcement_service.secure_data_operation(
            session=session,
            context=context,
            operation="list",
            model_class=Flow,
            data={**filters, "limit": limit, "offset": offset},
            permission_override="flow:read",
        )

        if flows is None:
            flows = []

        # Audit the list operation
        await enforcement_service.audit_enforcement_decision(
            context=context,
            operation="list",
            resource_type="flow",
            permission="flow:read",
            decision=True,
            reason=f"Listed {len(flows)} flows",
        )

        return [FlowRead.model_validate(flow, from_attributes=True) for flow in flows]

    except Exception as e:
        logger.error(f"Error listing flows: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.post("/flows", response_model=FlowRead, status_code=status.HTTP_201_CREATED)
async def create_flow_with_enhanced_rbac(
    flow_data: FlowCreate,
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
):
    """Create a flow with comprehensive RBAC and token scoping enforcement."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Check workspace-level create permission
        workspace_access = await enforcement_service.check_resource_access(
            session=session,
            context=context,
            permission="flow:write",
            resource_type="workspace",
            resource_id=context.effective_workspace_id,
        )

        if not workspace_access:
            await enforcement_service.audit_enforcement_decision(
                context=context,
                operation="create",
                resource_type="flow",
                permission="flow:write",
                decision=False,
                reason="Insufficient workspace permissions",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create flows in this workspace",
            )

        # Prepare flow data
        flow_dict = flow_data.model_dump()
        flow_dict["user_id"] = context.user.id
        if context.effective_workspace_id:
            flow_dict["workspace_id"] = context.effective_workspace_id

        # Perform secure create operation
        flow = await enforcement_service.secure_data_operation(
            session=session,
            context=context,
            operation="create",
            model_class=Flow,
            data=flow_dict,
            permission_override="flow:write",
        )

        if not flow:
            await enforcement_service.audit_enforcement_decision(
                context=context,
                operation="create",
                resource_type="flow",
                permission="flow:write",
                decision=False,
                reason="Flow creation failed",
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create flow")

        # Commit the transaction
        await session.commit()

        # Audit successful creation
        await enforcement_service.audit_enforcement_decision(
            context=context,
            operation="create",
            resource_type="flow",
            resource_id=flow.id,
            permission="flow:write",
            decision=True,
            reason="Flow created successfully",
        )

        return FlowRead.model_validate(flow, from_attributes=True)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating flow: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.put("/flows/{flow_id}", response_model=FlowRead)
async def update_flow_with_enhanced_rbac(
    flow_id: UUID,
    flow_data: FlowUpdate,
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
):
    """Update a flow with comprehensive RBAC and token scoping enforcement."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Prepare update data
        update_data = flow_data.model_dump(exclude_unset=True)

        # Perform secure update operation
        flow = await enforcement_service.secure_data_operation(
            session=session,
            context=context,
            operation="update",
            model_class=Flow,
            model_id=flow_id,
            data=update_data,
            permission_override="flow:write",
        )

        if not flow:
            await enforcement_service.audit_enforcement_decision(
                context=context,
                operation="update",
                resource_type="flow",
                resource_id=flow_id,
                permission="flow:write",
                decision=False,
                reason="Flow not found or access denied",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found or access denied")

        # Commit the transaction
        await session.commit()

        # Audit successful update
        await enforcement_service.audit_enforcement_decision(
            context=context,
            operation="update",
            resource_type="flow",
            resource_id=flow_id,
            permission="flow:write",
            decision=True,
            reason="Flow updated successfully",
        )

        return FlowRead.model_validate(flow, from_attributes=True)

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.delete("/flows/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow_with_enhanced_rbac(
    flow_id: UUID,
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
):
    """Delete a flow with comprehensive RBAC and token scoping enforcement."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Perform secure delete operation
        success = await enforcement_service.secure_data_operation(
            session=session,
            context=context,
            operation="delete",
            model_class=Flow,
            model_id=flow_id,
            permission_override="flow:delete",
        )

        if not success:
            await enforcement_service.audit_enforcement_decision(
                context=context,
                operation="delete",
                resource_type="flow",
                resource_id=flow_id,
                permission="flow:delete",
                decision=False,
                reason="Flow not found or access denied",
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found or access denied")

        # Commit the transaction
        await session.commit()

        # Audit successful deletion
        await enforcement_service.audit_enforcement_decision(
            context=context,
            operation="delete",
            resource_type="flow",
            resource_id=flow_id,
            permission="flow:delete",
            decision=True,
            reason="Flow deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting flow {flow_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.post("/flows/bulk-operation")
async def bulk_flow_operation(
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
    operation: str = "read",
    flow_ids: list[UUID] | None = None,
):
    """Perform bulk operations on flows with individual permission checking."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Validate bulk operation and get allowed flow IDs
        flow_id_list = flow_ids or []
        allowed_flow_ids = await enforcement_service.validate_bulk_operation(
            session=session,
            context=context,
            operation=operation,
            resource_type="flow",
            resource_ids=flow_id_list,
            permission_override=f"flow:{operation}",
        )

        # Audit the bulk operation
        await enforcement_service.audit_enforcement_decision(
            context=context,
            operation=f"bulk_{operation}",
            resource_type="flow",
            permission=f"flow:{operation}",
            decision=True,
            reason=f"Bulk operation allowed on {len(allowed_flow_ids)}/{len(flow_ids)} flows",
        )

        return {
            "requested_ids": [str(flow_id) for flow_id in flow_id_list],
            "allowed_ids": [str(flow_id) for flow_id in allowed_flow_ids],
            "denied_count": len(flow_id_list) - len(allowed_flow_ids),
        }

    except Exception as e:
        logger.error(f"Error in bulk flow operation: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


@router.get("/flows/{flow_id}/permissions")
async def get_flow_permissions(
    flow_id: UUID,
    session: Annotated[DbSession, Depends()],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
):
    """Get effective permissions for a specific flow."""
    try:
        # Initialize enforcement service
        from langflow.services.deps import get_rbac_service

        rbac_service = get_rbac_service()
        enforcement_service = RBACRuntimeEnforcementService(rbac_service)

        # Check if user can read the flow first
        flow_access = await enforcement_service.check_resource_access(
            session=session, context=context, permission="flow:read", resource_type="flow", resource_id=flow_id
        )

        if not flow_access:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found or access denied")

        # Get effective permissions
        effective_permissions = await enforcement_service.get_effective_permissions(
            session=session, context=context, resource_type="flow"
        )

        # Filter flow-specific permissions
        flow_permissions = [p for p in effective_permissions if p.startswith("flow:")]

        return {
            "flow_id": str(flow_id),
            "effective_permissions": flow_permissions,
            "token_scoped": bool(context.token_validation and context.token_validation.scoped_permissions),
            "scope_type": context.token_validation.scope_type if context.token_validation else None,
            "scope_id": str(context.token_validation.scope_id)
            if context.token_validation and context.token_validation.scope_id
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting flow permissions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from e


# Example of token scope validation decorator
def require_flow_scope(flow_id: UUID):
    """Decorator to require specific flow scope for endpoints."""

    async def scope_validator(
        context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
    ):
        if (
            context.token_validation
            and context.token_validation.scope_type == "flow"
            and context.token_validation.scope_id != flow_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token is scoped to a different flow: {context.token_validation.scope_id}",
            )
        return True

    return Depends(scope_validator)


@router.get("/flows/{flow_id}/scoped-data")
async def get_scoped_flow_data(
    flow_id: UUID,
    _scope_check: Annotated[bool, Depends(require_flow_scope)],
):
    """Example endpoint that requires specific flow scope."""
    # This endpoint demonstrates how to enforce that a token is scoped to a specific flow
    # The require_flow_scope dependency will check that the token scope matches the flow_id

    return {"flow_id": str(flow_id), "message": "Access granted to scoped flow data", "scope_validated": True}

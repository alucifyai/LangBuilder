"""Service Account management API endpoints for RBAC system."""

from typing import Annotated, TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlmodel import and_, select

from langflow.api.utils import CurrentActiveUser, DbSession, custom_params
from langflow.api.v1.rbac.dependencies import (
    get_permission_engine,
)
from langflow.api.v1.rbac.security_middleware import (
    SecurityRequirement,
    ValidationRequirement,
    get_authenticated_user,
    secure_endpoint,
)
from langflow.services.auth.authorization_patterns import get_enhanced_enforcement_context
from langflow.services.rbac.runtime_enforcement import RuntimeEnforcementContext
from langflow.schema.serialize import UUIDstr
from langflow.services.database.models.rbac.service_account import (
    ServiceAccount,
    ServiceAccountCreate,
    ServiceAccountRead,
    ServiceAccountToken,
    ServiceAccountTokenCreate,
    ServiceAccountTokenRead,
    ServiceAccountTokenResponse,
    ServiceAccountUpdate,
)
from langflow.services.database.models.rbac.workspace import Workspace
from langflow.services.rbac.permission_engine import PermissionEngine

if TYPE_CHECKING:
    pass

router = APIRouter(
    prefix="/service-accounts",
    tags=["RBAC", "Service Accounts"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/", response_model=list[ServiceAccountRead])
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="service_account",
        action="read",
        require_workspace_access=True,
        audit_action="list_service_accounts",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def list_service_accounts(
    request: Request,
    session: DbSession,
    current_user: Annotated[CurrentActiveUser, Depends(get_authenticated_user)],
    context: Annotated[RuntimeEnforcementContext, Depends(get_enhanced_enforcement_context)],
    workspace_id: UUIDstr,
    params: Annotated[Params | None, Depends(custom_params)],
    search: str | None = None,
    is_active: bool | None = None,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> list[ServiceAccountRead]:
    """List service accounts in a workspace."""
    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="read",
        resource_id=workspace_id,
        workspace_id=workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to list service accounts: {result.reason}"
        )

    statement = select(ServiceAccount).where(ServiceAccount.workspace_id == workspace_id)

    # Apply filters
    if search:
        statement = statement.where(
            (ServiceAccount.name.ilike(f"%{search}%")) |
            (ServiceAccount.description.ilike(f"%{search}%"))
        )

    if is_active is not None:
        statement = statement.where(ServiceAccount.is_active == is_active)

    # Apply pagination using fastapi_pagination
    if params:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=DeprecationWarning, module=r"fastapi_pagination\.ext\.sqlalchemy"
            )
            paginated_result = await apaginate(session, statement, params=params)
            return [ServiceAccountRead.model_validate(sa) for sa in paginated_result.items]
    else:
        result = await session.exec(statement)
        service_accounts = result.all()
        return [ServiceAccountRead.model_validate(sa) for sa in service_accounts]


@router.post("/", response_model=ServiceAccountRead, status_code=status.HTTP_201_CREATED)
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def create_service_account(
    service_account_data: ServiceAccountCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> ServiceAccountRead:
    """Create a new service account."""
    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="create",
        resource_id=service_account_data.workspace_id,
        workspace_id=service_account_data.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to create service account: {result.reason}"
        )

    # Verify workspace exists
    workspace = await session.get(Workspace, service_account_data.workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Check for duplicate name in workspace
    statement = select(ServiceAccount).where(
        and_(
            ServiceAccount.workspace_id == service_account_data.workspace_id,
            ServiceAccount.name == service_account_data.name
        )
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service account with this name already exists in workspace"
        )

    # Create service account
    service_account = ServiceAccount(
        **service_account_data.model_dump(),
        created_by=current_user.id
    )

    session.add(service_account)
    await session.commit()
    await session.refresh(service_account)

    return ServiceAccountRead.model_validate(service_account)


@router.get("/{service_account_id}", response_model=ServiceAccountRead)
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def get_service_account(
    service_account_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> ServiceAccountRead:
    """Get service account by ID."""
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="read",
        resource_id=service_account.workspace_id,
        workspace_id=service_account.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to read service account: {result.reason}"
        )

    return ServiceAccountRead.model_validate(service_account)


@router.put("/{service_account_id}", response_model=ServiceAccountRead)
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def update_service_account(
    service_account_id: UUIDstr,
    service_account_data: ServiceAccountUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> ServiceAccountRead:
    """Update service account."""
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="update",
        resource_id=service_account.workspace_id,
        workspace_id=service_account.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to update service account: {result.reason}"
        )

    # Update fields
    update_data = service_account_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service_account, field, value)

    await session.commit()
    await session.refresh(service_account)

    return ServiceAccountRead.model_validate(service_account)


@router.delete("/{service_account_id}", status_code=status.HTTP_204_NO_CONTENT)
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def delete_service_account(
    service_account_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> None:
    """Delete service account."""
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="delete",
        resource_id=service_account.workspace_id,
        workspace_id=service_account.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to delete service account: {result.reason}"
        )

    await session.delete(service_account)
    await session.commit()


@router.post("/{service_account_id}/tokens", response_model=ServiceAccountTokenResponse, status_code=status.HTTP_201_CREATED)
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def create_service_account_token(
    service_account_id: UUIDstr,
    token_data: ServiceAccountTokenCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> ServiceAccountTokenResponse:
    """Create a new token for service account."""
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="update",
        resource_id=service_account.workspace_id,
        workspace_id=service_account.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to create service account token: {result.reason}"
        )

    # Create token
    import hashlib
    import secrets
    from datetime import datetime, timedelta

    # Generate token
    token_value = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token_value.encode()).hexdigest()

    # Set expiry if provided
    expires_at = None
    if token_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=token_data.expires_in_days)

    token = ServiceAccountToken(
        service_account_id=service_account_id,
        name=token_data.name,
        description=token_data.description,
        token_hash=token_hash,
        expires_at=expires_at,
        scopes=token_data.scopes,
        ip_restrictions=token_data.ip_restrictions,
        created_by=current_user.id
    )

    session.add(token)
    await session.commit()
    await session.refresh(token)

    return ServiceAccountTokenResponse(
        id=token.id,
        name=token.name,
        description=token.description,
        token=token_value,  # Only returned on creation
        expires_at=token.expires_at,
        scopes=token.scopes,
        ip_restrictions=token.ip_restrictions,
        created_at=token.created_at,
        created_by=token.created_by
    )


@router.get("/{service_account_id}/tokens", response_model=list[ServiceAccountTokenRead])
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def list_service_account_tokens(
    service_account_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    params: Annotated[Params | None, Depends(custom_params)],
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> list[ServiceAccountTokenRead]:
    """List tokens for service account."""
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="read",
        resource_id=service_account.workspace_id,
        workspace_id=service_account.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to list service account tokens: {result.reason}"
        )

    statement = select(ServiceAccountToken).where(
        ServiceAccountToken.service_account_id == service_account_id
    )

    # Apply pagination using fastapi_pagination
    if params:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", category=DeprecationWarning, module=r"fastapi_pagination\.ext\.sqlalchemy"
            )
            paginated_result = await apaginate(session, statement, params=params)
            return [ServiceAccountTokenRead.model_validate(token) for token in paginated_result.items]
    else:
        result = await session.exec(statement)
        tokens = result.all()
        return [ServiceAccountTokenRead.model_validate(token) for token in tokens]


@router.delete("/{service_account_id}/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
@secure_endpoint(
    security_req=SecurityRequirement(
        resource_type="rbac_resource",
        action="read",
        require_workspace_access=True,
        audit_action="rbac_operation",
    ),
    validation_req=ValidationRequirement(
        validate_workspace_exists=True,
    ),
    audit_enabled=True,
)
async def delete_service_account_token(
    service_account_id: UUIDstr,
    token_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    permission_engine: PermissionEngine = Depends(get_permission_engine),
) -> None:
    """Delete service account token."""
    service_account = await session.get(ServiceAccount, service_account_id)
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )

    # Check workspace permission
    result = await permission_engine.check_permission(
        session=session,
        user=current_user,
        resource_type="workspace",
        action="update",
        resource_id=service_account.workspace_id,
        workspace_id=service_account.workspace_id,
    )

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to delete service account token: {result.reason}"
        )

    token = await session.get(ServiceAccountToken, token_id)
    if not token or token.service_account_id != service_account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )

    await session.delete(token)
    await session.commit()

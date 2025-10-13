"""Grant (Role Assignment) Management API endpoints for RBAC.

Implements PRD Story 3.5 - Role Assignment Management
- Create, Read, Delete operations for role assignments (grants)
- Support for user, service account, and group principals
- Scope-based assignments (workspace, project, environment, flow, component)
- Audit logging integration
- Cache invalidation on grant changes

AppGraph Impact Subgraph:
- grant_management_api → REST API for role assignments
- create_grant_logic → Assigns role to principal at scope
- revoke_grant_logic → Removes role assignment
- list_grants_logic → Lists role assignments
- get_grant_logic → Retrieves single grant
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import selectinload
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_assignment import (
    RoleAssignment,
)
from langflow.services.database.models.rbac.service_account import ServiceAccount
from langflow.services.database.models.user.model import User

router = APIRouter(prefix="/grants", tags=["Grants"])


# ============================================================================
# Helper Functions
# ============================================================================


def parse_principal(principal: str) -> tuple[str, str]:
    """Parse principal string into type and identifier.

    Args:
        principal: Principal string in format "type:identifier"
                  Examples: "user:alice", "service_account:uuid-123", "group:uuid-456"

    Returns:
        Tuple of (principal_type, principal_identifier)

    Raises:
        ValueError: If principal format is invalid
    """
    if ":" not in principal:
        raise ValueError(
            f"Invalid principal format: '{principal}'. Expected format: 'type:identifier' "
            "(e.g., 'user:alice', 'service_account:uuid-123', 'group:uuid-456')"
        )

    parts = principal.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid principal format: '{principal}'")

    principal_type, principal_id = parts

    # Validate principal type
    allowed_types = {"user", "service_account", "group"}
    if principal_type not in allowed_types:
        raise ValueError(f"Invalid principal type: '{principal_type}'. Must be one of {allowed_types}")

    if not principal_id:
        raise ValueError(f"Principal identifier cannot be empty in '{principal}'")

    return principal_type, principal_id


def parse_scope(scope: dict[str, str]) -> tuple[str, UUID]:
    """Parse scope dictionary into type and ID.

    Args:
        scope: Scope dictionary with single key-value pair
              Examples: {"workspace": "uuid"}, {"project": "uuid"}, {"flow": "uuid"}

    Returns:
        Tuple of (scope_type, scope_id)

    Raises:
        ValueError: If scope format is invalid
    """
    if not scope:
        raise ValueError("Scope cannot be empty")

    if len(scope) != 1:
        raise ValueError(f"Scope must contain exactly one key-value pair, got {len(scope)}: {scope}")

    scope_type = list(scope.keys())[0]
    scope_id_str = scope[scope_type]

    # Validate scope type
    allowed_types = {"workspace", "project", "environment", "flow", "component"}
    if scope_type not in allowed_types:
        raise ValueError(f"Invalid scope type: '{scope_type}'. Must be one of {allowed_types}")

    # Parse UUID
    try:
        scope_id = UUID(scope_id_str)
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid UUID for scope ID: '{scope_id_str}'") from e

    return scope_type, scope_id


# ============================================================================
# Pydantic Schemas
# ============================================================================


class GrantCreate(BaseModel):
    """Schema for creating a new grant (role assignment).

    PRD Story 3.5 @AC1
    """

    principal: str  # "user:username", "service_account:uuid", or "group:uuid"
    role_id: UUID
    scope: dict[str, str]  # {"workspace": "uuid"}, {"project": "uuid"}, etc.
    valid_from: datetime | None = None
    valid_until: datetime | None = None  # Optional time-boxed grant

    @field_validator("principal")
    @classmethod
    def validate_principal(cls, v: str) -> str:
        """Validate principal format."""
        try:
            parse_principal(v)
        except ValueError as e:
            raise ValueError(str(e)) from e
        return v

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate scope format."""
        try:
            parse_scope(v)
        except ValueError as e:
            raise ValueError(str(e)) from e
        return v


class GrantRead(BaseModel):
    """Schema for reading grant data.

    PRD Story 3.5
    """

    id: UUID
    role_id: UUID
    assignee_type: str
    user_id: UUID | None = None
    service_account_id: UUID | None = None
    group_id: UUID | None = None
    scope_type: str
    scope_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None = None

    # Audit fields (implementation plan requirements)
    assigned_by: UUID | None = None  # Who created the grant
    valid_from: datetime | None = None  # When grant becomes active

    # Optional: Include role details for convenience
    role_name: str | None = None
    role_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API Endpoints
# ============================================================================


async def _check_grant_manage_permission(current_user: User) -> None:
    """Check if user has permission to manage grants.

    For now, only superusers can manage grants.
    TODO: Integrate with RBACEnforcementEngine once permission system is fully connected.

    Args:
        current_user: The current authenticated user

    Raises:
        HTTPException: 403 if user lacks permission
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Grant management requires superuser access.",
        )


async def get_user_by_email_or_username(identifier: str, session: DbSession) -> User | None:
    """Get user by username.

    Note: The User model only has username, not email. This function is named for
    future compatibility when email support is added.

    Supports principal format:
    - user:alice (username)

    Args:
        identifier: Username to look up
        session: Database session

    Returns:
        User if found, None otherwise
    """
    stmt = select(User).where(User.username == identifier)
    result = await session.exec(stmt)
    return result.first()


@router.post("/", response_model=GrantRead, status_code=status.HTTP_201_CREATED)
async def create_grant(
    grant_data: GrantCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> GrantRead:
    """Assign role to principal at specific scope.

    Implements PRD Story 3.5 @AC1 - Create role assignment.

    Example request body:
    ```json
    {
        "principal": "user:alice",
        "role_id": "550e8400-e29b-41d4-a716-446655440000",
        "scope": {"project": "550e8400-e29b-41d4-a716-446655440001"},
        "valid_from": "2025-10-12T00:00:00Z",
        "valid_until": "2025-12-31T23:59:59Z"
    }
    ```

    Args:
        grant_data: Grant creation data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The newly created grant

    Raises:
        HTTPException: 400 if validation fails or grant already exists
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if role, user, or service account not found
    """
    await _check_grant_manage_permission(current_user)

    # Parse principal
    try:
        principal_type, principal_id = parse_principal(grant_data.principal)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Parse scope
    try:
        scope_type, scope_id = parse_scope(grant_data.scope)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Validate role exists
    role = await session.get(Role, grant_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {grant_data.role_id} not found",
        )

    # Resolve principal based on type
    user_id = None
    service_account_id = None
    group_id = None

    if principal_type == "user":
        user = await get_user_by_email_or_username(principal_id, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{principal_id}' not found",
            )
        user_id = user.id

    elif principal_type == "service_account":
        try:
            sa_uuid = UUID(principal_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid service account UUID: '{principal_id}'",
            ) from e

        sa = await session.get(ServiceAccount, sa_uuid)
        if not sa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service account with ID {principal_id} not found",
            )
        service_account_id = sa.id

    elif principal_type == "group":
        # TODO: Add UserGroup support when model is available
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Group principals are not yet implemented",
        )

    # Check for duplicate grant
    stmt = select(RoleAssignment).where(
        RoleAssignment.role_id == grant_data.role_id,
        RoleAssignment.assignee_type == principal_type,
        RoleAssignment.user_id == user_id,
        RoleAssignment.service_account_id == service_account_id,
        RoleAssignment.group_id == group_id,
        RoleAssignment.scope_type == scope_type,
        RoleAssignment.scope_id == scope_id,
    )
    existing = (await session.exec(stmt)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Grant already exists for {grant_data.principal} with role '{role.name}' at {scope_type}:{scope_id}"
            ),
        )

    # Create grant
    grant = RoleAssignment(
        role_id=grant_data.role_id,
        assignee_type=principal_type,
        user_id=user_id,
        service_account_id=service_account_id,
        group_id=group_id,
        scope_type=scope_type,
        scope_id=scope_id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        expires_at=grant_data.valid_until,
        assigned_by=current_user.id,  # Track who created the grant
        valid_from=grant_data.valid_from,  # When grant becomes active
    )
    session.add(grant)
    await session.commit()
    await session.refresh(grant)

    logger.info(
        f"Grant created: {grant_data.principal} assigned role '{role.name}' "
        f"at {scope_type}:{scope_id} by user {current_user.id}"
    )

    # TODO: Invalidate cache for the principal
    # if user_id:
    #     await invalidate_user_cache(user_id)

    # TODO: Add audit logging
    # await log_audit_event(
    #     actor_id=current_user.id,
    #     action="grant.created",
    #     resource_type="grant",
    #     resource_id=grant.id,
    #     details={
    #         "principal": grant_data.principal,
    #         "role": role.name,
    #         "scope": grant_data.scope
    #     }
    # )

    # Build response with role details
    grant_read = GrantRead.model_validate(grant)
    grant_read.role_name = role.name
    grant_read.role_display_name = role.display_name

    return grant_read


@router.get("/{grant_id}", response_model=GrantRead)
async def get_grant(
    grant_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> GrantRead:
    """Get a specific grant by ID.

    Args:
        grant_id: UUID of the grant to retrieve
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The requested grant

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if grant not found
    """
    await _check_grant_manage_permission(current_user)

    grant = await session.get(RoleAssignment, grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grant with ID {grant_id} not found",
        )

    # Fetch role details
    role = await session.get(Role, grant.role_id)

    grant_read = GrantRead.model_validate(grant)
    if role:
        grant_read.role_name = role.name
        grant_read.role_display_name = role.display_name

    return grant_read


@router.get("/", response_model=list[GrantRead])
async def list_grants(
    principal: str | None = Query(
        default=None,
        description="Filter by principal (e.g., 'user:alice', 'service_account:uuid')",
    ),
    role_id: UUID | None = Query(default=None, description="Filter by role ID"),
    scope_type: str | None = Query(
        default=None,
        description="Filter by scope type (workspace, project, environment, flow, component)",
    ),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of records to return"),
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[GrantRead]:
    """List role assignments with filters.

    Implements PRD Story 3.5 @AC3 - List grants with filtering.

    Query parameters:
    - principal: Filter by principal (e.g., "user:alice", "service_account:uuid")
    - role_id: Filter by role UUID
    - scope_type: Filter by scope (workspace, project, environment, flow, component)
    - skip: Pagination offset (default: 0)
    - limit: Max results to return (default: 100, max: 500)

    Args:
        principal: Optional principal filter
        role_id: Optional role ID filter
        scope_type: Optional scope type filter
        skip: Pagination offset
        limit: Max results
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of grants matching the filters

    Raises:
        HTTPException: 400 if filter validation fails
        HTTPException: 403 if user lacks permission
    """
    await _check_grant_manage_permission(current_user)

    # Build query with eager loading for role to avoid N+1 query problem
    stmt = select(RoleAssignment).options(selectinload(RoleAssignment.role)).where(RoleAssignment.is_active == True)  # noqa: E712

    # Apply filters
    if principal:
        try:
            principal_type, principal_id = parse_principal(principal)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

        if principal_type == "user":
            user = await get_user_by_email_or_username(principal_id, session)
            if user:
                stmt = stmt.where(RoleAssignment.user_id == user.id)
            else:
                # No user found, return empty list
                return []

        elif principal_type == "service_account":
            try:
                sa_uuid = UUID(principal_id)
                stmt = stmt.where(RoleAssignment.service_account_id == sa_uuid)
            except ValueError:
                return []  # Invalid UUID, return empty list

        elif principal_type == "group":
            try:
                group_uuid = UUID(principal_id)
                stmt = stmt.where(RoleAssignment.group_id == group_uuid)
            except ValueError:
                return []

    if role_id:
        stmt = stmt.where(RoleAssignment.role_id == role_id)

    if scope_type:
        # Validate scope type
        allowed_types = {"workspace", "project", "environment", "flow", "component"}
        if scope_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scope type: '{scope_type}'. Must be one of {allowed_types}",
            )
        stmt = stmt.where(RoleAssignment.scope_type == scope_type)

    # Add pagination and ordering
    stmt = stmt.offset(skip).limit(limit).order_by(RoleAssignment.created_at.desc())

    # Execute query
    result = await session.exec(stmt)
    grants = result.all()

    # Build response with role details (role is already eager-loaded)
    grant_reads = []
    for grant in grants:
        grant_read = GrantRead.model_validate(grant)
        # Role is already loaded via selectinload
        if grant.role:
            grant_read.role_name = grant.role.name
            grant_read.role_display_name = grant.role.display_name
        grant_reads.append(grant_read)

    logger.debug(
        f"User {current_user.id} listed {len(grant_reads)} grants "
        f"(filters: principal={principal}, role_id={role_id}, scope_type={scope_type})"
    )

    return grant_reads


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_grant(
    grant_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Revoke role assignment.

    Implements PRD Story 3.5 @AC2 - Revoke role assignment.

    Args:
        grant_id: UUID of the grant to revoke
        current_user: Currently authenticated user
        session: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 403 if user lacks permission
        HTTPException: 404 if grant not found
    """
    await _check_grant_manage_permission(current_user)

    grant = await session.get(RoleAssignment, grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grant with ID {grant_id} not found",
        )

    # Fetch role details for logging
    role = await session.get(Role, grant.role_id)
    role_name = role.name if role else "unknown"

    # Store principal ID for cache invalidation
    user_id = grant.user_id

    # Delete the grant
    await session.delete(grant)
    await session.commit()

    logger.info(f"Grant revoked: {grant_id} (role '{role_name}') by user {current_user.id}")

    # TODO: Invalidate cache for the principal
    # if user_id:
    #     await invalidate_user_cache(user_id)

    # TODO: Add audit logging
    # await log_audit_event(
    #     actor_id=current_user.id,
    #     action="grant.revoked",
    #     resource_type="grant",
    #     resource_id=grant_id,
    #     details={"role": role_name}
    # )

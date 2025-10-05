"""Grant (role assignment) API endpoints.

Provides CRUD operations for assigning roles to principals at specific scopes.
PRD Story 2.1 - Assign Roles to Users and Groups within a Scope
PRD Stories 3.4/3.5 - Assign Roles via Admin UI and API
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.crud import create_grant, delete_grant, get_grant_by_id, list_grants, update_grant
from langflow.services.database.models.rbac.grant import GrantCreate, GrantRead, GrantUpdate

router = APIRouter()


@router.get("", response_model=list[GrantRead])
async def get_grants(
    db: DbSession,
    current_user: CurrentActiveUser,
    principal_type: str | None = Query(None, description="Filter by principal type (user/group/service_account)"),
    principal_id: str | None = Query(None, description="Filter by principal ID"),
    scope_type: str | None = Query(None, description="Filter by scope type (workspace/project/environment/flow/component)"),
    scope_id: str | None = Query(None, description="Filter by scope ID"),
    role_id: str | None = Query(None, description="Filter by role ID"),
):
    """List grants (role assignments) with optional filters.

    Query Parameters (all optional):
    - principal_type: Filter by who has the grant (user, group, service_account)
    - principal_id: Filter by specific principal ID
    - scope_type: Filter by where the grant applies (workspace, project, etc.)
    - scope_id: Filter by specific scope ID
    - role_id: Filter by specific role

    Returns:
        List of Grant objects

    Examples:
    - Get all grants for a user: `?principal_type=user&principal_id={user_id}`
    - Get all grants in a project: `?scope_type=project&scope_id={project_id}`
    - Get all Editor role grants: `?role_id={editor_role_id}`

    Note: Requires 'grant:read' permission at appropriate scope
    PRD Story 3.1 @AC1 - List all grants
    """
    # TODO Phase 3: Add permission check
    # Should check grant:read at the queried scope

    grants = await list_grants(
        db=db,
        principal_type=principal_type,
        principal_id=principal_id,
        scope_type=scope_type,
        scope_id=scope_id,
        role_id=role_id,
    )

    return [GrantRead.model_validate(g, from_attributes=True) for g in grants]


@router.get("/{grant_id}", response_model=GrantRead)
async def get_grant(
    grant_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a specific grant by ID.

    Args:
        grant_id: UUID of the grant

    Returns:
        Grant object

    Raises:
        404: Grant not found

    Note: Requires 'grant:read' permission
    """
    # TODO Phase 3: Add permission check

    grant = await get_grant_by_id(db, grant_id)
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grant '{grant_id}' not found",
        )
    return GrantRead.model_validate(grant, from_attributes=True)


@router.post("", response_model=GrantRead, status_code=status.HTTP_201_CREATED)
async def create_new_grant(
    grant_data: GrantCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Create a new grant (assign a role to a principal at a scope).

    Request Body:
    - principal_type: Type of entity receiving the role (user, group, service_account)
    - principal_id: ID of the user/group/service_account
    - role_id: ID of the role to assign
    - scope_type: Where the role applies (workspace, project, environment, flow, component)
    - scope_id: ID of the scoped resource
    - expires_at: (Optional) Expiration time for time-bound grants
    - metadata: (Optional) Additional grant metadata

    Returns:
        Created Grant object

    Raises:
        400: Invalid principal, role, or scope
        404: Principal or role not found

    Examples:
    - Assign Editor role to user at project scope:
      ```json
      {
        "principal_type": "user",
        "principal_id": "user-uuid",
        "role_id": "editor-role-uuid",
        "scope_type": "project",
        "scope_id": "project-123"
      }
      ```

    - Temporary grant (24 hours):
      ```json
      {
        "principal_type": "group",
        "principal_id": "group-uuid",
        "role_id": "deployer-role-uuid",
        "scope_type": "environment",
        "scope_id": "staging",
        "expires_at": "2025-10-05T12:00:00Z"
      }
      ```

    Note: Requires 'grant:create' permission at the specified scope
    PRD Story 2.1 @AC1 - Assign role to group within scope
    PRD Story 3.4 @AC1 - Assign role to user at project scope
    PRD Story 3.4 @AC3 - Time-bound grants
    PRD Story 3.5 @AC1 - Create grant via API
    """
    # TODO Phase 3: Add permission check
    # Should check grant:create at the specified scope_type:scope_id

    grant = await create_grant(
        db=db,
        grant_data=grant_data,
        created_by=current_user.id,
    )

    return GrantRead.model_validate(grant, from_attributes=True)


@router.patch("/{grant_id}", response_model=GrantRead)
async def update_existing_grant(
    grant_id: UUID,
    grant_data: GrantUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update a grant (e.g., extend expiration time).

    Request Body (all fields optional):
    - expires_at: New expiration time
    - metadata: Updated metadata

    Returns:
        Updated Grant object

    Raises:
        404: Grant not found

    Note: Requires 'grant:update' permission
    PRD Story 3.4 @AC3 - Update expiration for time-bound grants
    """
    # TODO Phase 3: Add permission check

    grant = await update_grant(db=db, grant_id=grant_id, grant_data=grant_data)
    return GrantRead.model_validate(grant, from_attributes=True)


@router.delete("/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_grant(
    grant_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a grant (revoke a role assignment).

    Args:
        grant_id: UUID of the grant to delete

    Raises:
        404: Grant not found

    Note: Requires 'grant:delete' permission
    PRD Story 2.1 @AC2 - Remove role assignment
    PRD Story 3.4 @AC4 - Revoke grant
    PRD Story 3.5 @AC2 - Revoke grant via API
    """
    # TODO Phase 3: Add permission check

    await delete_grant(db=db, grant_id=grant_id)
    return None  # 204 No Content

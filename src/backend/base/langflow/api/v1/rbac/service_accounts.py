"""ServiceAccount management API endpoints.

Provides CRUD operations for service accounts (non-human identities).
PRD Story 2.4 - Manage Service Accounts
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.rbac.crud import (
    create_service_account,
    delete_service_account,
    get_service_account_by_id,
    list_service_accounts,
    rotate_service_account_api_key,
    update_service_account,
)
from langflow.services.database.models.rbac.service_account import ServiceAccountCreate, ServiceAccountRead, ServiceAccountUpdate

router = APIRouter()


class ServiceAccountCreatedResponse(BaseModel):
    """Response when creating a service account.

    Includes the plaintext API key (shown only once).
    """

    service_account: ServiceAccountRead
    api_key: str  # Plaintext key (shown only on creation)


class ServiceAccountKeyRotatedResponse(BaseModel):
    """Response when rotating a service account API key.

    Includes the new plaintext API key (shown only once).
    """

    service_account: ServiceAccountRead
    api_key: str  # New plaintext key


@router.get("", response_model=list[ServiceAccountRead])
async def get_service_accounts(
    db: DbSession,
    current_user: CurrentActiveUser,
    active_only: bool = Query(False, description="Only show active service accounts"),
):
    """List all service accounts.

    Query Parameters:
    - active_only: If true, only returns active (not disabled) service accounts

    Returns:
        List of ServiceAccount objects (with masked API keys)

    Note: Requires 'service_account:read' permission
    """
    # TODO Phase 3: Add permission check

    service_accounts = await list_service_accounts(db=db, active_only=active_only)
    return [ServiceAccountRead.model_validate(sa, from_attributes=True) for sa in service_accounts]


@router.get("/{service_account_id}", response_model=ServiceAccountRead)
async def get_service_account(
    service_account_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Get a specific service account by ID.

    Args:
        service_account_id: UUID of the service account

    Returns:
        ServiceAccount object (with masked API key)

    Raises:
        404: Service account not found

    Note: Requires 'service_account:read' permission
    """
    # TODO Phase 3: Add permission check

    sa = await get_service_account_by_id(db, service_account_id)
    if not sa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service account '{service_account_id}' not found",
        )
    return ServiceAccountRead.model_validate(sa, from_attributes=True)


@router.post("", response_model=ServiceAccountCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_new_service_account(
    sa_data: ServiceAccountCreate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Create a new service account.

    Request Body:
    - name: Unique service account name (e.g., "ci-bot", "monitoring-agent")
    - description: Optional description of purpose
    - metadata: Optional metadata

    Returns:
        ServiceAccount object with plaintext API key

    **IMPORTANT**: The API key is shown only once! Store it securely.

    Raises:
        409: Service account name already exists

    Example Response:
    ```json
    {
      "service_account": {
        "id": "uuid",
        "name": "ci-bot",
        "is_active": true,
        ...
      },
      "api_key": "sa-AbCdEf123456..."  # Store this securely!
    }
    ```

    Note: Requires 'service_account:create' permission
    PRD Story 2.4 @AC1 - Create service account
    """
    # TODO Phase 3: Add permission check

    sa, plaintext_key = await create_service_account(
        db=db,
        sa_data=sa_data,
        created_by=current_user.id,
    )

    return ServiceAccountCreatedResponse(
        service_account=ServiceAccountRead.model_validate(sa, from_attributes=True),
        api_key=plaintext_key,
    )


@router.patch("/{service_account_id}", response_model=ServiceAccountRead)
async def update_existing_service_account(
    service_account_id: UUID,
    sa_data: ServiceAccountUpdate,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Update a service account.

    Request Body (all fields optional):
    - name: New name
    - description: New description
    - is_active: Enable/disable the account
    - metadata: Updated metadata

    Returns:
        Updated ServiceAccount object

    Raises:
        404: Service account not found
        409: Name conflict

    Note: To rotate the API key, use POST /{service_account_id}/rotate-key
    Note: Requires 'service_account:update' permission
    """
    # TODO Phase 3: Add permission check

    sa = await update_service_account(db=db, sa_id=service_account_id, sa_data=sa_data)
    return ServiceAccountRead.model_validate(sa, from_attributes=True)


@router.delete("/{service_account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_service_account(
    service_account_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete a service account.

    Service accounts with active grants cannot be deleted.

    Args:
        service_account_id: UUID of the service account to delete

    Raises:
        404: Service account not found
        409: Service account has active grants

    Note: Requires 'service_account:delete' permission
    """
    # TODO Phase 3: Add permission check

    await delete_service_account(db=db, sa_id=service_account_id)
    return None  # 204 No Content


@router.post("/{service_account_id}/rotate-key", response_model=ServiceAccountKeyRotatedResponse)
async def rotate_service_account_key(
    service_account_id: UUID,
    db: DbSession,
    current_user: CurrentActiveUser,
):
    """Rotate (regenerate) a service account's API key.

    The old key is immediately invalidated.

    Returns:
        ServiceAccount object with new plaintext API key

    **IMPORTANT**: The new API key is shown only once! Store it securely.

    Raises:
        404: Service account not found

    Example Response:
    ```json
    {
      "service_account": {
        "id": "uuid",
        "name": "ci-bot",
        ...
      },
      "api_key": "sa-NewKey789..."  # Store this securely!
    }
    ```

    Note: Requires 'service_account:update' permission (manage_tokens)
    """
    # TODO Phase 3: Add permission check
    # Should require service_account:update or manage_tokens permission

    sa, new_plaintext_key = await rotate_service_account_api_key(
        db=db,
        sa_id=service_account_id,
    )

    return ServiceAccountKeyRotatedResponse(
        service_account=ServiceAccountRead.model_validate(sa, from_attributes=True),
        api_key=new_plaintext_key,
    )

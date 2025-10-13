"""Invitation Management API endpoints.

Implements PRD Story 1.1 @AC6 - Invitation Management
- Accept workspace invitation via token
- Reject workspace invitation
- List user's pending invitations

AppGraph Impact Subgraph (Task 3.9):
- invitation_management_api → REST API for invitations
- accept_invitation_logic → Validates and accepts invitation
- reject_invitation_logic → Rejects invitation
- list_invitations_logic → Lists pending invitations for user
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.invitation.model import (
    Invitation,
    InvitationRead,
    InvitationStatus,
)
from langflow.services.database.models.rbac.role_assignment import RoleAssignment
from langflow.services.database.models.workspace.model import WorkspaceMember
from langflow.services.rbac.audit import log_audit_event

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("/{token}/accept", status_code=status.HTTP_200_OK)
async def accept_invitation(
    token: str,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> dict:
    """Accept workspace invitation (PRD Story 1.1 @AC6).

    Only the invited user (email match) can accept.

    Args:
        token: Unique invitation token
        current_user: Currently authenticated user
        session: Database session

    Returns:
        Dictionary with status and workspace_id

    Raises:
        HTTPException: 404 if invitation not found or already processed
        HTTPException: 400 if invitation has expired
        HTTPException: 403 if current user email doesn't match invited email
        HTTPException: 409 if user is already a workspace member
    """
    # Fetch invitation
    stmt = select(Invitation).where(
        Invitation.token == token,
        Invitation.status == InvitationStatus.PENDING.value,
    )
    result = await session.exec(stmt)
    inv = result.first()

    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )

    # Check expiration
    # Make expires_at timezone-aware if it's naive (from database)
    expires_at = inv.expires_at if inv.expires_at.tzinfo else inv.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        inv.status = InvitationStatus.EXPIRED.value
        inv.updated_at = datetime.now(timezone.utc)
        await session.commit()
        logger.warning(f"Invitation {inv.id} has expired (token: {token})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    # PRD @AC6: Only invited user can accept
    if current_user.email != inv.email:
        logger.warning(
            f"User {current_user.id} ({current_user.email}) attempted to accept "
            f"invitation for {inv.email}"
        )
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="invitation.accept_denied",
            resource_type="invitation",
            resource_id=inv.id,
            status="denied",
            details={
                "reason": "email_mismatch",
                "user_email": current_user.email,
                "invited_email": inv.email,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invite_not_for_user: This invitation is for a different user",
        )

    # Check if user is already a member of the workspace
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == inv.workspace_id,
        WorkspaceMember.user_id == current_user.id,
    )
    result = await session.exec(stmt)
    existing_member = result.first()

    if existing_member:
        # User is already a member - mark invitation as accepted anyway
        inv.status = InvitationStatus.ACCEPTED.value
        inv.invited_user_id = current_user.id
        inv.accepted_at = datetime.now(timezone.utc)
        inv.updated_at = datetime.now(timezone.utc)
        await session.commit()

        logger.info(
            f"User {current_user.id} is already a member of workspace {inv.workspace_id}, "
            f"invitation {inv.id} marked as accepted"
        )

        return {
            "status": "accepted",
            "workspace_id": str(inv.workspace_id),
            "already_member": True,
        }

    # Add user to workspace
    member = WorkspaceMember(
        workspace_id=inv.workspace_id,
        user_id=current_user.id,
        role="member",  # Default role
        is_active=True,
        joined_at=datetime.now(timezone.utc),
    )
    session.add(member)

    # Assign role if specified in invitation
    if inv.role_id:
        grant = RoleAssignment(
            role_id=inv.role_id,
            assignee_type="user",
            user_id=current_user.id,
            service_account_id=None,
            group_id=None,
            scope_type=inv.scope_type,
            scope_id=inv.scope_id,
            is_active=True,
            assigned_by=inv.invited_by_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(grant)
        logger.info(
            f"Assigned role {inv.role_id} to user {current_user.id} "
            f"with scope {inv.scope_type}:{inv.scope_id}"
        )

    # Update invitation status
    inv.status = InvitationStatus.ACCEPTED.value
    inv.invited_user_id = current_user.id
    inv.accepted_at = datetime.now(timezone.utc)
    inv.updated_at = datetime.now(timezone.utc)

    await session.commit()

    logger.info(
        f"User {current_user.id} accepted invitation {inv.id} "
        f"to workspace {inv.workspace_id}"
    )

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="invitation.accepted",
        resource_type="invitation",
        resource_id=inv.id,
        details={
            "workspace_id": str(inv.workspace_id),
            "role_id": str(inv.role_id) if inv.role_id else None,
            "scope_type": inv.scope_type,
            "scope_id": str(inv.scope_id) if inv.scope_id else None,
        },
    )

    return {
        "status": "accepted",
        "workspace_id": str(inv.workspace_id),
        "role_granted": inv.role_id is not None,
    }


@router.post("/{token}/reject", status_code=status.HTTP_200_OK)
async def reject_invitation(
    token: str,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> dict:
    """Reject workspace invitation.

    Only the invited user (email match) can reject.

    Args:
        token: Unique invitation token
        current_user: Currently authenticated user
        session: Database session

    Returns:
        Dictionary with status confirmation

    Raises:
        HTTPException: 404 if invitation not found or already processed
        HTTPException: 400 if invitation has expired
        HTTPException: 403 if current user email doesn't match invited email
    """
    # Fetch invitation
    stmt = select(Invitation).where(
        Invitation.token == token,
        Invitation.status == InvitationStatus.PENDING.value,
    )
    result = await session.exec(stmt)
    inv = result.first()

    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already processed",
        )

    # Check expiration
    # Make expires_at timezone-aware if it's naive (from database)
    expires_at = inv.expires_at if inv.expires_at.tzinfo else inv.expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        inv.status = InvitationStatus.EXPIRED.value
        inv.updated_at = datetime.now(timezone.utc)
        await session.commit()
        logger.warning(f"Invitation {inv.id} has expired (token: {token})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    # Only invited user can reject
    if current_user.email != inv.email:
        logger.warning(
            f"User {current_user.id} ({current_user.email}) attempted to reject "
            f"invitation for {inv.email}"
        )
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="invitation.reject_denied",
            resource_type="invitation",
            resource_id=inv.id,
            status="denied",
            details={
                "reason": "email_mismatch",
                "user_email": current_user.email,
                "invited_email": inv.email,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invite_not_for_user: This invitation is for a different user",
        )

    # Update invitation status
    inv.status = InvitationStatus.REJECTED.value
    inv.invited_user_id = current_user.id
    inv.updated_at = datetime.now(timezone.utc)

    await session.commit()

    logger.info(
        f"User {current_user.id} rejected invitation {inv.id} "
        f"to workspace {inv.workspace_id}"
    )

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="invitation.rejected",
        resource_type="invitation",
        resource_id=inv.id,
        details={
            "workspace_id": str(inv.workspace_id),
        },
    )

    return {
        "status": "rejected",
        "workspace_id": str(inv.workspace_id),
    }


@router.get("/pending", response_model=list[InvitationRead])
async def list_pending_invitations(
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[InvitationRead]:
    """List pending invitations for the current user.

    Returns all invitations sent to the current user's email that are still pending.

    Args:
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of pending invitations
    """
    # Query pending invitations for current user's email
    stmt = (
        select(Invitation)
        .where(
            Invitation.email == current_user.email,
            Invitation.status == InvitationStatus.PENDING.value,
            Invitation.expires_at > datetime.now(timezone.utc),  # Only non-expired
        )
        .order_by(Invitation.created_at.desc())
    )

    result = await session.exec(stmt)
    invitations = result.all()

    logger.info(
        f"User {current_user.id} listed {len(invitations)} pending invitations"
    )

    return [InvitationRead.model_validate(inv) for inv in invitations]

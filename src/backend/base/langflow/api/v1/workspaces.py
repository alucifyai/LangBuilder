"""Workspace Management API endpoints.

Implements PRD Story 1.1 - Workspace Management
- Create workspace with creator as owner
- List user's workspaces
- Invite workspace members via email
- Remove workspace members
- Delete workspace with confirmation

AppGraph Impact Subgraph (Task 3.7):
- workspace_management_api → REST API for workspaces
- create_workspace_logic → Creates workspace with creator as owner
- update_workspace_logic → Updates workspace settings
- delete_workspace_logic → Deletes workspace (with safeguards)
- invite_workspace_member_logic → Invites user to workspace
- remove_workspace_member_logic → Removes workspace member
- list_workspaces_logic → Lists user's workspaces
"""

import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.invitation.model import Invitation
from langflow.services.database.models.user.model import User
from langflow.services.database.models.workspace.model import (
    Workspace,
    WorkspaceCreate,
    WorkspaceInvite,
    WorkspaceMember,
    WorkspaceRead,
    WorkspaceUpdate,
)
from langflow.services.rbac.audit import log_audit_event
from langflow.services.rbac.enforcement import RBACEnforcementEngine

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


async def check_workspace_permission(
    user_id: UUID,
    workspace_id: UUID,
    permission: str,
    required_roles: list[str],
    session: DbSession,
) -> bool:
    """Check if user has workspace permission via RBAC or role-based fallback.

    This function provides backwards compatibility during RBAC migration by falling back
    to role-based checks when RBAC grants don't exist yet.

    Args:
        user_id: User ID to check
        workspace_id: Workspace ID
        permission: Permission string (e.g., "workspace.invite_users")
        required_roles: List of workspace member roles that grant this permission
        session: Database session

    Returns:
        True if user has permission, False otherwise
    """
    # First try RBAC permission system
    rbac_engine = RBACEnforcementEngine(session=session)
    has_rbac_perm = await rbac_engine.has_permission(
        user_id=user_id,
        permission=permission,
        resource_type="workspace",
        resource_id=workspace_id,
    )

    if has_rbac_perm:
        return True

    # Fallback: Check workspace membership role
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
        WorkspaceMember.is_active == True,  # noqa: E712
    )
    member_result = await session.exec(stmt)
    member = member_result.first()

    if member and member.role in required_roles:
        logger.debug(
            f"Permission granted via role fallback: user {user_id} has role '{member.role}' "
            f"in workspace {workspace_id} (required roles: {required_roles})"
        )
        return True

    return False


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a workspace name.

    Args:
        name: The workspace name

    Returns:
        A lowercase, hyphenated slug

    Example:
        "My Workspace" -> "my-workspace"
        "Test_Project 123" -> "test-project-123"
    """
    # Convert to lowercase and replace spaces/underscores with hyphens
    slug = name.lower()
    slug = re.sub(r"[_\s]+", "-", slug)
    # Remove any non-alphanumeric characters except hyphens
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    # Remove duplicate hyphens
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug


async def send_invitation_email(
    to_email: str,
    workspace_name: str,
    inviter_name: str,
    invitation_token: str,
    message: str | None = None,
) -> None:
    """Send invitation email to user.

    TODO: Integrate with email service when available.
    For now, this is a stub that logs the invitation details.

    Args:
        to_email: Recipient email address
        workspace_name: Name of the workspace
        inviter_name: Name of the user sending the invitation
        invitation_token: Secure token for accepting invitation
        message: Optional custom message from inviter
    """
    logger.info(
        f"EMAIL INVITATION: to={to_email}, workspace={workspace_name}, "
        f"inviter={inviter_name}, token={invitation_token[:8]}..., "
        f"message={message if message else '(none)'}"
    )
    # TODO: Replace with actual email service call
    # await email_service.send_invitation(...)


async def get_user_by_email(email: str, session: DbSession) -> User | None:
    """Get user by email address.

    Note: Current User model only has username, not email field.
    This is a placeholder for future email support.
    For now, we'll just return None to indicate user doesn't exist yet.

    Args:
        email: Email address to look up
        session: Database session

    Returns:
        User if found, None otherwise
    """
    # TODO: Implement when User model has email field
    # stmt = select(User).where(User.email == email)
    # result = await session.exec(stmt)
    # return result.first()
    return None


@router.post("/", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> WorkspaceRead:
    """Create workspace with creator as owner.

    Implements PRD Story 1.1 - Create workspace

    The workspace slug is auto-generated from the name if not provided,
    and the creating user is automatically added as an owner.

    Args:
        workspace_data: Workspace creation data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The newly created workspace

    Raises:
        HTTPException: 400 if workspace slug already exists
    """
    # Generate slug from name if not provided
    slug = workspace_data.slug if workspace_data.slug else generate_slug(workspace_data.name)

    # Validate slug uniqueness (handle conflicts by appending random suffix)
    original_slug = slug
    attempts = 0
    max_attempts = 10

    while attempts < max_attempts:
        stmt = select(Workspace).where(Workspace.slug == slug)
        existing = (await session.exec(stmt)).first()

        if not existing:
            # Slug is unique, proceed
            break

        # Slug is taken, generate a new one with random suffix
        if attempts == 0 and workspace_data.slug:
            # User provided slug is taken, error out
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workspace slug '{slug}' is already taken. Please choose a different slug.",
            )

        # Auto-generated slug is taken, append random suffix
        random_suffix = secrets.token_hex(4)
        slug = f"{original_slug}-{random_suffix}"
        attempts += 1
        logger.info(f"Slug conflict detected, trying: {slug}")

    if attempts >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to generate unique workspace slug after multiple attempts. Please try a different name.",
        )

    # Create workspace
    try:
        workspace = Workspace(
            name=workspace_data.name,
            slug=slug,
            description=workspace_data.description,
            created_by=current_user.id,
            settings=workspace_data.settings if workspace_data.settings else {},
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(workspace)
        await session.flush()  # Get workspace.id before adding member

        # Add creator as owner
        member = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role="owner",
            is_active=True,
            joined_at=datetime.now(UTC),
        )
        session.add(member)

        await session.commit()
        await session.refresh(workspace)

        logger.info(
            f"Workspace created: {workspace.name} (ID: {workspace.id}) "
            f"by user {current_user.id} with owner role"
        )

        # Audit log
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="workspace.created",
            resource_type="workspace",
            resource_id=workspace.id,
            details={"name": workspace.name, "slug": workspace.slug},
        )

        return WorkspaceRead.model_validate(workspace)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database error creating workspace: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create workspace due to database constraint violation.",
        ) from e


@router.get("/", response_model=list[WorkspaceRead])
async def list_workspaces(
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[WorkspaceRead]:
    """List user's workspaces.

    Implements PRD Story 1.1 - List workspaces

    Returns only workspaces where the user is an active member.

    Args:
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of workspaces where user is a member
    """
    # Query workspaces where user is a member
    stmt = (
        select(Workspace)
        .join(WorkspaceMember)
        .where(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.is_active == True,  # noqa: E712
            Workspace.is_active == True,  # noqa: E712
        )
        .order_by(Workspace.created_at.desc())
    )

    result = await session.exec(stmt)
    workspaces = result.all()

    return [WorkspaceRead.model_validate(w) for w in workspaces]


@router.patch("/{workspace_id}", response_model=WorkspaceRead)
async def update_workspace(
    workspace_id: UUID,
    workspace_data: WorkspaceUpdate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> WorkspaceRead:
    """Update workspace settings.

    Implements PRD Story 1.1 - Update workspace

    Only workspace owners can update workspace settings. Allows updating name,
    description, active status, and settings.

    Args:
        workspace_id: UUID of the workspace to update
        workspace_data: Workspace update data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The updated workspace

    Raises:
        HTTPException: 404 if workspace not found
        HTTPException: 403 if user is not workspace owner
    """
    # Fetch workspace
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace not found: {workspace_id}",
        )

    # Check permission using centralized RBAC system with role-based fallback
    if not current_user.is_superuser:
        has_perm = await check_workspace_permission(
            user_id=current_user.id,
            workspace_id=workspace_id,
            permission="workspace.update",
            required_roles=["owner"],
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update workspace",
            )

    # Track what was updated for audit log
    updates = {}

    # Update fields if provided
    if workspace_data.name is not None:
        updates["name"] = {"old": workspace.name, "new": workspace_data.name}
        workspace.name = workspace_data.name

    if workspace_data.description is not None:
        updates["description"] = {"old": workspace.description, "new": workspace_data.description}
        workspace.description = workspace_data.description

    if workspace_data.is_active is not None:
        updates["is_active"] = {"old": workspace.is_active, "new": workspace_data.is_active}
        workspace.is_active = workspace_data.is_active

    if workspace_data.settings is not None:
        updates["settings"] = {"old": "updated", "new": "updated"}  # Don't log full settings
        workspace.settings = workspace_data.settings

    # Update timestamp
    workspace.updated_at = datetime.now(UTC)

    # Commit changes
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)

    logger.info(f"Workspace updated: {workspace.name} (ID: {workspace_id}) by user {current_user.id}")

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="workspace.updated",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"updates": updates},
    )

    return WorkspaceRead.model_validate(workspace)


@router.post("/{workspace_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_workspace_member(
    workspace_id: UUID,
    invite_data: WorkspaceInvite,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> dict[str, str]:
    """Invite user to workspace via email.

    Implements PRD Story 1.1 @AC5, @AC6 - Invite users to workspace

    Creates an invitation that the user must accept. If the user doesn't
    have an account yet, they can sign up using the invitation link.

    Requires the inviter to be a workspace owner or admin.

    Args:
        workspace_id: UUID of the workspace
        invite_data: Invitation data (email, role_id, message)
        current_user: Currently authenticated user
        session: Database session

    Returns:
        Dictionary with status and invitation_id

    Raises:
        HTTPException: 403 if user lacks permission (not owner/admin)
        HTTPException: 404 if workspace not found
        HTTPException: 400 if user is already a member
    """
    # Verify workspace exists
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace not found: {workspace_id}",
        )

    # Check permission using centralized RBAC system with role-based fallback
    if not current_user.is_superuser:
        has_perm = await check_workspace_permission(
            user_id=current_user.id,
            workspace_id=workspace_id,
            permission="workspace.invite_users",
            required_roles=["owner", "admin"],
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to invite workspace members",
            )

    # Check if user already a member (by email)
    existing_user = await get_user_by_email(invite_data.email, session)
    if existing_user:
        stmt = select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == existing_user.id,
        )
        existing_member_result = await session.exec(stmt)
        if existing_member_result.first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {invite_data.email} is already a workspace member",
            )

    # Create invitation
    invitation = Invitation(
        workspace_id=workspace_id,
        invited_by_user_id=current_user.id,
        email=invite_data.email,
        invited_user_id=existing_user.id if existing_user else None,
        role_id=invite_data.role_id,
        scope_type="workspace",
        scope_id=workspace_id,
        status="pending",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        token=secrets.token_urlsafe(32),
        message=invite_data.message,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(invitation)
    await session.commit()
    await session.refresh(invitation)

    logger.info(
        f"Workspace invitation created: user {current_user.id} invited "
        f"{invite_data.email} to workspace {workspace_id} (invitation ID: {invitation.id})"
    )

    # Send email notification
    await send_invitation_email(
        to_email=invite_data.email,
        workspace_name=workspace.name,
        inviter_name=current_user.username,
        invitation_token=invitation.token,
        message=invite_data.message,
    )

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="workspace_member.invited",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"email": invite_data.email, "invitation_id": str(invitation.id)},
    )

    return {"status": "invited", "invitation_id": str(invitation.id)}


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Remove member from workspace.

    Implements PRD Story 1.1 - Remove workspace member

    Only workspace owners can remove members. Cannot remove the last owner.

    Args:
        workspace_id: UUID of the workspace
        user_id: UUID of the user to remove
        current_user: Currently authenticated user
        session: Database session

    Raises:
        HTTPException: 403 if user is not workspace owner
        HTTPException: 404 if workspace or member not found
        HTTPException: 400 if trying to remove last owner
    """
    # Check permission using centralized RBAC system with role-based fallback
    if not current_user.is_superuser:
        has_perm = await check_workspace_permission(
            user_id=current_user.id,
            workspace_id=workspace_id,
            permission="workspace.remove_members",
            required_roles=["owner"],
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to remove workspace members",
            )

    # Find member to remove
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )
    member_result = await session.exec(stmt)
    member = member_result.first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this workspace",
        )

    # Cannot remove last owner
    if member.role == "owner":
        owner_count_stmt = select(func.count(WorkspaceMember.id)).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.role == "owner",
            WorkspaceMember.is_active == True,  # noqa: E712
        )
        owner_count_result = await session.exec(owner_count_stmt)
        owner_count = owner_count_result.one()

        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last workspace owner. Transfer ownership first or delete the workspace.",
            )

    # Remove member
    await session.delete(member)
    await session.commit()

    logger.info(f"User {user_id} removed from workspace {workspace_id} by user {current_user.id}")

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="workspace_member.removed",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"removed_user_id": str(user_id), "removed_user_role": member.role},
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    confirm: str = Query(..., description="Must be workspace name to confirm deletion"),
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Delete workspace with confirmation.

    Implements PRD Story 1.1 - Delete workspace

    Only workspace owners can delete workspaces. Requires confirmation by
    providing the exact workspace name. Cascades to all projects and flows.

    Args:
        workspace_id: UUID of the workspace to delete
        confirm: Must match workspace name exactly
        current_user: Currently authenticated user
        session: Database session

    Raises:
        HTTPException: 404 if workspace not found
        HTTPException: 403 if user is not workspace owner
        HTTPException: 400 if confirmation name doesn't match
    """
    # Fetch workspace
    workspace = await session.get(Workspace, workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace not found: {workspace_id}",
        )

    # Check permission using centralized RBAC system with role-based fallback
    if not current_user.is_superuser:
        has_perm = await check_workspace_permission(
            user_id=current_user.id,
            workspace_id=workspace_id,
            permission="workspace.delete",
            required_roles=["owner"],
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete workspace",
            )

    # Confirm deletion by name
    if confirm != workspace.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Confirmation failed. Please provide the exact workspace name '{workspace.name}' to confirm deletion.",
        )

    workspace_name = workspace.name

    # Delete workspace (cascade will handle members, projects, flows, etc.)
    await session.delete(workspace)
    await session.commit()

    logger.warning(f"Workspace deleted: {workspace_name} (ID: {workspace_id}) by user {current_user.id}")

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="workspace.deleted",
        resource_type="workspace",
        resource_id=workspace_id,
        details={"name": workspace_name, "confirmed": True},
    )

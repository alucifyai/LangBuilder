"""Token scope enforcement for RBAC (PRD Story 4.2).

This module implements token scope validation to restrict API keys to specific
resources (workspace, project, flow). When a scoped API key is used, all resource
access is validated to ensure it falls within the token's scope.

Logic Nodes (Task 4.4):
- token_scope_validation → Validate resource is within token scope
- scope_resolution_helpers → Resolve resource to workspace/project hierarchy

PRD References:
- Story 4.2: Scoped API Keys for external integrations
- Story 4.2 @AC1: Token scoped to workspace
- Story 4.2 @AC2: Token scoped to specific project
- Story 4.2 @AC3: Token scoped to specific flow

Usage:
    # In RBAC dependency:
    await validate_token_scope(request, "flow", flow_id, session, current_user)
"""

import logging
from uuid import UUID

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _log_scope_violation_audit(
    session: AsyncSession,
    current_user: "User | None",  # noqa: F821
    scope_type: str,
    scope_id: UUID,
    resource_type: str,
    resource_id: UUID,
    violation_type: str,
) -> None:
    """Log token scope violation to audit log (GAP-2 fix).

    Args:
        session: Database session
        current_user: User or service account making the request
        scope_type: Token scope type (workspace, project, flow)
        scope_id: Token scope ID
        resource_type: Requested resource type
        resource_id: Requested resource ID
        violation_type: Type of violation (workspace_mismatch, project_mismatch, flow_mismatch, non_flow_access)
    """
    if not current_user:
        logger.debug("Skipping audit log for scope violation - no current_user provided")
        return

    try:
        from langflow.services.rbac.audit import log_audit_event_safe

        await log_audit_event_safe(
            session=session,
            actor_id=current_user.id,
            action="token_scope_violation",
            resource_type=resource_type,
            resource_id=resource_id,
            status="denied",
            details={
                "token_scope_type": scope_type,
                "token_scope_id": str(scope_id),
                "requested_resource_type": resource_type,
                "requested_resource_id": str(resource_id),
                "violation_type": violation_type,
            },
        )
        logger.debug("Audit log created for token scope violation: %s", violation_type)
    except Exception as e:
        # Audit logging should not break the request - log error and continue
        logger.error("Failed to create audit log for token scope violation: %s", e)


async def validate_token_scope(
    request: Request,
    resource_type: str,
    resource_id: UUID,
    session: AsyncSession,
    current_user: "User | None" = None,  # noqa: F821
) -> None:
    """Validate that the requested resource is within the API key's scope.

    This function checks if the current request is using a scoped API key and validates
    that the requested resource falls within the token's scope. If the token is scoped
    to a workspace/project/flow, access to resources outside that scope is denied.

    Args:
        request: FastAPI request object containing API key scope info in request.state
        resource_type: Type of resource being accessed (e.g., "flow", "project", "workspace")
        resource_id: UUID of the resource being accessed
        session: Database session for resource hierarchy lookups
        current_user: Optional User object for audit logging (GAP-2 fix)

    Returns:
        None: Scope validation passed, access allowed

    Raises:
        HTTPException 403: If resource is outside token scope

    Token Scope Rules:
        1. Unscoped tokens (scope_type=None): Full access within RBAC permissions
        2. Workspace-scoped: Access to all resources in that workspace
        3. Project-scoped: Access to project and all its flows
        4. Flow-scoped: Access to that specific flow only

    Examples:
        >>> # Token scoped to project A
        >>> await validate_token_scope(request, "flow", flow_id, session)
        >>> # -> Allowed if flow belongs to project A
        >>> # -> Denied if flow belongs to different project

        >>> # Token scoped to workspace W
        >>> await validate_token_scope(request, "project", project_id, session)
        >>> # -> Allowed if project belongs to workspace W
        >>> # -> Denied if project belongs to different workspace
    """
    # Check if request has API key scope info (attached during authentication)
    api_key_scope = getattr(request.state, "api_key_scope", None)

    # If no API key scope, this is JWT auth or unscoped API key - allow access
    # (RBAC permissions will be checked separately)
    if not api_key_scope:
        logger.debug("No API key scope found - JWT or unscoped token, allowing access")
        return

    scope_type = api_key_scope.get("scope_type")
    scope_id = api_key_scope.get("scope_id")

    # Unscoped token - allow access (backward compatibility)
    if not scope_type or not scope_id:
        logger.debug("Unscoped API key - allowing access")
        return

    logger.debug(
        "Validating token scope: scope_type=%s, scope_id=%s, resource_type=%s, resource_id=%s",
        scope_type,
        scope_id,
        resource_type,
        resource_id,
    )

    # Validate scope based on scope_type
    if scope_type == "workspace":
        # Workspace-scoped token: Check if resource belongs to this workspace
        resource_workspace_id = await get_resource_workspace_id(session, resource_type, resource_id)
        if resource_workspace_id != scope_id:
            logger.warning(
                "Token scope violation: workspace-scoped token (workspace=%s) attempted to access "
                "resource in different workspace (resource_workspace=%s, resource_type=%s, resource_id=%s)",
                scope_id,
                resource_workspace_id,
                resource_type,
                resource_id,
            )

            # GAP-2: Log audit event for scope violation
            await _log_scope_violation_audit(
                session=session,
                current_user=current_user,
                scope_type=scope_type,
                scope_id=scope_id,
                resource_type=resource_type,
                resource_id=resource_id,
                violation_type="workspace_mismatch",
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token scope violation: This API key is scoped to a different workspace",
            )

    elif scope_type == "project":
        # Project-scoped token: Check if resource belongs to this project or is the project itself
        if resource_type == "project":
            # Accessing the project itself
            if resource_id != scope_id:
                logger.warning(
                    "Token scope violation: project-scoped token (project=%s) attempted to access "
                    "different project (resource_id=%s)",
                    scope_id,
                    resource_id,
                )

                # GAP-2: Log audit event for scope violation
                await _log_scope_violation_audit(
                    session=session,
                    current_user=current_user,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    violation_type="project_direct_mismatch",
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token scope violation: This API key is scoped to a different project",
                )
        else:
            # Accessing a child resource (flow, component, etc.)
            resource_project_id = await get_resource_project_id(session, resource_type, resource_id)
            if resource_project_id != scope_id:
                logger.warning(
                    "Token scope violation: project-scoped token (project=%s) attempted to access "
                    "resource in different project (resource_project=%s, resource_type=%s, resource_id=%s)",
                    scope_id,
                    resource_project_id,
                    resource_type,
                    resource_id,
                )

                # GAP-2: Log audit event for scope violation
                await _log_scope_violation_audit(
                    session=session,
                    current_user=current_user,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    violation_type="project_child_mismatch",
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token scope violation: This API key is scoped to a different project",
                )

    elif scope_type == "flow":
        # Flow-scoped token: Check if accessing this specific flow
        if resource_type == "flow":
            if resource_id != scope_id:
                logger.warning(
                    "Token scope violation: flow-scoped token (flow=%s) attempted to access "
                    "different flow (resource_id=%s)",
                    scope_id,
                    resource_id,
                )

                # GAP-2: Log audit event for scope violation
                await _log_scope_violation_audit(
                    session=session,
                    current_user=current_user,
                    scope_type=scope_type,
                    scope_id=scope_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    violation_type="flow_mismatch",
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token scope violation: This API key is scoped to a different flow",
                )
        else:
            # Flow-scoped tokens can only access the specific flow, not other resources
            logger.warning(
                "Token scope violation: flow-scoped token (flow=%s) attempted to access "
                "non-flow resource (resource_type=%s, resource_id=%s)",
                scope_id,
                resource_type,
                resource_id,
            )

            # GAP-2: Log audit event for scope violation
            await _log_scope_violation_audit(
                session=session,
                current_user=current_user,
                scope_type=scope_type,
                scope_id=scope_id,
                resource_type=resource_type,
                resource_id=resource_id,
                violation_type="flow_non_flow_access",
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token scope violation: This API key is scoped to a specific flow only",
            )

    else:
        # Unknown scope type - deny for safety
        logger.error("Unknown token scope type: %s", scope_type)

        # GAP-2: Log audit event for invalid scope type
        await _log_scope_violation_audit(
            session=session,
            current_user=current_user,
            scope_type=scope_type,
            scope_id=scope_id,
            resource_type=resource_type,
            resource_id=resource_id,
            violation_type="invalid_scope_type",
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Invalid token scope type: {scope_type}",
        )

    logger.info(
        "Token scope validation passed: scope_type=%s, scope_id=%s, resource_type=%s, resource_id=%s",
        scope_type,
        scope_id,
        resource_type,
        resource_id,
    )


async def get_resource_workspace_id(session: AsyncSession, resource_type: str, resource_id: UUID) -> UUID | None:
    """Resolve a resource to its workspace ID.

    This helper function traverses the resource hierarchy to find the workspace
    that contains the resource. Used for workspace-scoped token validation.

    Args:
        session: Database session
        resource_type: Type of resource (e.g., "flow", "project", "workspace")
        resource_id: UUID of the resource

    Returns:
        UUID of the workspace containing this resource, or None if not found

    Hierarchy:
        workspace (direct)
        project.workspace_id
        flow.folder.workspace_id (folder = project)
        component.flow.folder.workspace_id
    """
    from sqlmodel import select

    if resource_type == "workspace":
        # Direct workspace access
        return resource_id

    if resource_type == "project":
        # Project -> workspace_id
        from langflow.services.database.models.folder.model import Folder

        result = await session.exec(select(Folder.workspace_id).where(Folder.id == resource_id))
        return result.first()

    if resource_type == "flow":
        # Flow -> folder.workspace_id
        from langflow.services.database.models.flow.model import Flow

        result = await session.exec(
            select(Flow.folder_id).where(Flow.id == resource_id)
        )
        folder_id = result.first()
        if not folder_id:
            return None

        # Get workspace_id from folder
        from langflow.services.database.models.folder.model import Folder

        result = await session.exec(select(Folder.workspace_id).where(Folder.id == folder_id))
        return result.first()

    # Unknown resource type - cannot resolve
    logger.warning("Cannot resolve workspace for unknown resource type: %s", resource_type)
    return None


async def get_resource_project_id(session: AsyncSession, resource_type: str, resource_id: UUID) -> UUID | None:
    """Resolve a resource to its project ID.

    This helper function traverses the resource hierarchy to find the project
    (folder) that contains the resource. Used for project-scoped token validation.

    Args:
        session: Database session
        resource_type: Type of resource (e.g., "flow", "component")
        resource_id: UUID of the resource

    Returns:
        UUID of the project (folder) containing this resource, or None if not found

    Hierarchy:
        project (direct - project is stored as Folder)
        flow.folder_id
        component.flow.folder_id
    """
    from sqlmodel import select

    if resource_type == "project":
        # Direct project access
        return resource_id

    if resource_type == "flow":
        # Flow -> folder_id (folder = project)
        from langflow.services.database.models.flow.model import Flow

        result = await session.exec(select(Flow.folder_id).where(Flow.id == resource_id))
        return result.first()

    # Unknown resource type - cannot resolve
    logger.warning("Cannot resolve project for unknown resource type: %s", resource_type)
    return None


def attach_api_key_scope_to_request(
    request: Request,
    workspace_id: UUID | None,
    scope_type: str | None,
    scope_id: UUID | None,
    scoped_permissions: dict | None,
) -> None:
    """Attach API key scope information to request state.

    This function is called during API key authentication to store the token's
    scope information in the request state, making it available to RBAC dependencies
    for scope validation.

    Args:
        request: FastAPI request object
        workspace_id: Workspace ID associated with the API key
        scope_type: Type of scope (workspace, project, flow, or None for unscoped)
        scope_id: ID of the scoped resource (or None for unscoped)
        scoped_permissions: Explicit permission list for this token (or None)

    Side Effects:
        Sets request.state.api_key_scope with scope information
    """
    request.state.api_key_scope = {
        "workspace_id": workspace_id,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "scoped_permissions": scoped_permissions,
    }
    logger.debug(
        "Attached API key scope to request: workspace_id=%s, scope_type=%s, scope_id=%s",
        workspace_id,
        scope_type,
        scope_id,
    )

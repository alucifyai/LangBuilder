"""Environment Management API endpoints.

Implements PRD Story 1.1 @AC4, Story 2.1 @AC8 - Environment Management
- Create environment in project (dev/staging/prod)
- List environments in project
- Update environment settings
- Delete environment

AppGraph Impact Subgraph (Task 3.8):
- environment_management_api → REST API for environments
- create_environment_logic → Creates environment within project
- list_environments_logic → Lists environments for project
- update_environment_logic → Updates environment settings
- delete_environment_logic → Deletes environment (prevents deployment)
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.environment.model import (
    Environment,
    EnvironmentCreate,
    EnvironmentRead,
    EnvironmentUpdate,
)
from langflow.services.database.models.folder.model import Folder
from langflow.services.rbac.audit import log_audit_event
from langflow.services.rbac.enforcement import RBACEnforcementEngine

router = APIRouter(prefix="/environments", tags=["Environments"])


async def check_project_permission(
    user_id: UUID,
    project_id: UUID,
    permission: str,
    session: DbSession,
) -> bool:
    """Check if user has project permission via RBAC.

    This function checks RBAC permissions for project-level operations.
    For environments, we check permissions at the project level since
    environments are scoped to projects.

    Args:
        user_id: User ID to check
        project_id: Project (Folder) ID
        permission: Permission string (e.g., "environment.create")
        session: Database session

    Returns:
        True if user has permission, False otherwise
    """
    rbac_engine = RBACEnforcementEngine(session=session)
    has_perm = await rbac_engine.has_permission(
        user_id=user_id,
        permission=permission,
        resource_type="project",
        resource_id=project_id,
    )

    if has_perm:
        return True

    # Fallback: Check if user owns the project (folder)
    project = await session.get(Folder, project_id)
    if project and project.user_id == user_id:
        logger.debug(
            f"Permission granted via project ownership: user {user_id} owns project {project_id}"
        )
        return True

    return False


async def check_environment_permission(
    user_id: UUID,
    environment_id: UUID,
    permission: str,
    session: DbSession,
) -> bool:
    """Check if user has environment permission via RBAC.

    This function checks RBAC permissions for environment-specific operations.
    It also checks project ownership as a fallback.

    Args:
        user_id: User ID to check
        environment_id: Environment ID
        permission: Permission string (e.g., "environment.update")
        session: Database session

    Returns:
        True if user has permission, False otherwise
    """
    rbac_engine = RBACEnforcementEngine(session=session)

    # First try environment-scoped permission
    has_perm = await rbac_engine.has_permission(
        user_id=user_id,
        permission=permission,
        resource_type="environment",
        resource_id=environment_id,
    )

    if has_perm:
        return True

    # Fallback: Check if user owns the parent project
    environment = await session.get(Environment, environment_id)
    if environment:
        project = await session.get(Folder, environment.project_id)
        if project and project.user_id == user_id:
            logger.debug(
                f"Permission granted via project ownership: user {user_id} owns project "
                f"{environment.project_id} containing environment {environment_id}"
            )
            return True

    return False


@router.post("/{project_id}/environments/", response_model=EnvironmentRead, status_code=status.HTTP_201_CREATED)
async def create_environment(
    project_id: UUID,
    environment_data: EnvironmentCreate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> EnvironmentRead:
    """Create environment in project.

    Implements PRD Story 1.1 @AC4 - Create environment in project

    Creates a deployment environment (dev/staging/prod) within a project.
    Environments provide isolation for different deployment stages.

    Args:
        project_id: UUID of the project (folder)
        environment_data: Environment creation data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The newly created environment

    Raises:
        HTTPException: 404 if project not found
        HTTPException: 403 if user lacks permission
        HTTPException: 409 if environment name already exists in project
    """
    # Verify project exists
    project = await session.get(Folder, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    # Check permission
    if not current_user.is_superuser:
        has_perm = await check_project_permission(
            user_id=current_user.id,
            project_id=project_id,
            permission="environment.create",
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create environment in this project",
            )

    # Create environment
    try:
        environment = Environment(
            project_id=project_id,
            name=environment_data.name,
            environment_type=environment_data.environment_type,
            description=environment_data.description,
            config=environment_data.config if environment_data.config else {},
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        session.add(environment)
        await session.commit()
        await session.refresh(environment)

        logger.info(
            f"Environment created: {environment.name} ({environment.environment_type}) "
            f"in project {project_id} by user {current_user.id}"
        )

        # Audit log
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="environment.created",
            resource_type="environment",
            resource_id=environment.id,
            details={
                "name": environment.name,
                "type": environment.environment_type,
                "project_id": str(project_id),
            },
        )

        return EnvironmentRead.model_validate(environment)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database error creating environment: {e}")
        # Check if it's a unique constraint violation on environment name
        error_str = str(e).lower()
        if (
            "uq_project_environment_name" in error_str
            or ("unique" in error_str and "environment.name" in error_str)
            or ("unique" in error_str and "project_id" in error_str and "name" in error_str)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment '{environment_data.name}' already exists in this project",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create environment due to database constraint violation",
        ) from e


@router.get("/{project_id}/environments/", response_model=list[EnvironmentRead])
async def list_environments(
    project_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> list[EnvironmentRead]:
    """List environments in project.

    Implements PRD Story 1.1 @AC4 - List environments

    Returns all active environments within a project.

    Args:
        project_id: UUID of the project (folder)
        current_user: Currently authenticated user
        session: Database session

    Returns:
        List of environments in the project

    Raises:
        HTTPException: 404 if project not found
        HTTPException: 403 if user lacks permission
    """
    # Verify project exists
    project = await session.get(Folder, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found: {project_id}",
        )

    # Check permission
    if not current_user.is_superuser:
        has_perm = await check_project_permission(
            user_id=current_user.id,
            project_id=project_id,
            permission="environment.list",
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to list environments in this project",
            )

    # Query environments for this project
    stmt = (
        select(Environment)
        .where(
            Environment.project_id == project_id,
            Environment.is_active == True,  # noqa: E712
        )
        .order_by(Environment.environment_type, Environment.name)
    )

    result = await session.exec(stmt)
    environments = result.all()

    return [EnvironmentRead.model_validate(env) for env in environments]


@router.patch("/{environment_id}", response_model=EnvironmentRead)
async def update_environment(
    environment_id: UUID,
    environment_data: EnvironmentUpdate,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> EnvironmentRead:
    """Update environment settings.

    Implements PRD Story 1.1 @AC4 - Update environment

    Allows updating environment name, description, configuration, and active status.
    Environment type cannot be changed after creation.

    Args:
        environment_id: UUID of the environment
        environment_data: Environment update data
        current_user: Currently authenticated user
        session: Database session

    Returns:
        The updated environment

    Raises:
        HTTPException: 404 if environment not found
        HTTPException: 403 if user lacks permission
    """
    # Fetch environment
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment not found: {environment_id}",
        )

    # Check permission
    if not current_user.is_superuser:
        has_perm = await check_environment_permission(
            user_id=current_user.id,
            environment_id=environment_id,
            permission="environment.update",
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to update this environment",
            )

    # Track what was updated for audit log
    updates = {}

    # Update fields if provided
    if environment_data.name is not None:
        updates["name"] = {"old": environment.name, "new": environment_data.name}
        environment.name = environment_data.name

    if environment_data.description is not None:
        updates["description"] = {"old": environment.description, "new": environment_data.description}
        environment.description = environment_data.description

    if environment_data.is_active is not None:
        updates["is_active"] = {"old": environment.is_active, "new": environment_data.is_active}
        environment.is_active = environment_data.is_active

    if environment_data.config is not None:
        updates["config"] = {"old": "updated", "new": "updated"}  # Don't log full config
        environment.config = environment_data.config

    # Update timestamp
    environment.updated_at = datetime.now(UTC)

    # Commit changes
    try:
        session.add(environment)
        await session.commit()
        await session.refresh(environment)

        logger.info(
            f"Environment updated: {environment.name} (ID: {environment_id}) by user {current_user.id}"
        )

        # Audit log
        await log_audit_event(
            session=session,
            actor_id=current_user.id,
            action="environment.updated",
            resource_type="environment",
            resource_id=environment_id,
            details={"updates": updates},
        )

        return EnvironmentRead.model_validate(environment)

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database error updating environment: {e}")
        # Check if it's a unique constraint violation on environment name
        error_str = str(e).lower()
        if (
            "uq_project_environment_name" in error_str
            or ("unique" in error_str and "environment.name" in error_str)
            or ("unique" in error_str and "project_id" in error_str and "name" in error_str)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Environment name '{environment_data.name}' already exists in this project",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update environment due to database constraint violation",
        ) from e


@router.delete("/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(
    environment_id: UUID,
    current_user: CurrentActiveUser = None,
    session: DbSession = None,
) -> None:
    """Delete environment.

    Implements PRD Story 1.1 @AC4 - Delete environment

    Deletes an environment, which prevents further deployments to it.
    Flows deployed to this environment will lose their environment reference.

    Args:
        environment_id: UUID of the environment to delete
        current_user: Currently authenticated user
        session: Database session

    Raises:
        HTTPException: 404 if environment not found
        HTTPException: 403 if user lacks permission
    """
    # Fetch environment
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment not found: {environment_id}",
        )

    # Check permission
    if not current_user.is_superuser:
        has_perm = await check_environment_permission(
            user_id=current_user.id,
            environment_id=environment_id,
            permission="environment.delete",
            session=session,
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to delete this environment",
            )

    environment_name = environment.name
    environment_type = environment.environment_type
    project_id = environment.project_id

    # Delete environment
    await session.delete(environment)
    await session.commit()

    logger.warning(
        f"Environment deleted: {environment_name} ({environment_type}) "
        f"from project {project_id} by user {current_user.id}"
    )

    # Audit log
    await log_audit_event(
        session=session,
        actor_id=current_user.id,
        action="environment.deleted",
        resource_type="environment",
        resource_id=environment_id,
        details={
            "name": environment_name,
            "type": environment_type,
            "project_id": str(project_id),
        },
    )

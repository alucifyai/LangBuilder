"""Environment management API endpoints for RBAC system."""

from typing import TYPE_CHECKING
from langflow.schema.serialize import UUIDstr

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, and_
from sqlmodel.ext.asyncio.session import AsyncSession

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.api.v1.rbac.dependencies import (
    check_project_permission,
    get_permission_engine,
)
from langflow.services.rbac.permission_engine import PermissionEngine
from langflow.services.database.models.rbac.environment import (
    Environment,
    EnvironmentCreate,
    EnvironmentRead,
    EnvironmentUpdate,
    EnvironmentType,
    EnvironmentDeployment,
)
from langflow.services.database.models.rbac.project import Project

if TYPE_CHECKING:
    from langflow.services.database.models.user.model import User

router = APIRouter(
    prefix="/environments",
    tags=["RBAC", "Environments"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)


@router.get("/", response_model=list[EnvironmentRead])
async def list_environments(
    session: DbSession,
    current_user: CurrentActiveUser,
    project_id: UUIDstr,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = None,
    environment_type: EnvironmentType | None = None,
    is_active: bool | None = None,
) -> list[EnvironmentRead]:
    """List environments in a project."""
    
    # Check project permission
    await check_project_permission(session, current_user, project_id, "environment:read")

    statement = select(Environment).where(Environment.project_id == project_id)

    # Apply filters
    if search:
        statement = statement.where(
            (Environment.name.ilike(f"%{search}%")) |
            (Environment.description.ilike(f"%{search}%"))
        )

    if environment_type:
        statement = statement.where(Environment.type == environment_type)

    if is_active is not None:
        statement = statement.where(Environment.is_active == is_active)

    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    result = await session.exec(statement)
    environments = result.all()

    return [EnvironmentRead.model_validate(env) for env in environments]


@router.post("/", response_model=EnvironmentRead, status_code=status.HTTP_201_CREATED)
async def create_environment(
    environment_data: EnvironmentCreate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> EnvironmentRead:
    """Create a new environment."""
    
    # Check project permission
    await check_project_permission(
        session, current_user, environment_data.project_id, "environment:create"
    )

    # Verify project exists
    project = await session.get(Project, environment_data.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Check for duplicate name in project
    statement = select(Environment).where(
        and_(
            Environment.project_id == environment_data.project_id,
            Environment.name == environment_data.name
        )
    )
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environment with this name already exists in project"
        )

    # Create environment
    environment = Environment(
        **environment_data.model_dump(),
        created_by=current_user.id,
        workspace_id=project.workspace_id  # Inherit from project
    )
    
    session.add(environment)
    await session.commit()
    await session.refresh(environment)

    return EnvironmentRead.model_validate(environment)


@router.get("/{environment_id}", response_model=EnvironmentRead)
async def get_environment(
    environment_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> EnvironmentRead:
    """Get environment by ID."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:read"
    )

    return EnvironmentRead.model_validate(environment)


@router.put("/{environment_id}", response_model=EnvironmentRead)
async def update_environment(
    environment_id: UUIDstr,
    environment_data: EnvironmentUpdate,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> EnvironmentRead:
    """Update environment."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:update"
    )

    # Update fields
    update_data = environment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(environment, field, value)

    await session.commit()
    await session.refresh(environment)

    return EnvironmentRead.model_validate(environment)


@router.delete("/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(
    environment_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> None:
    """Delete environment."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:delete"
    )

    await session.delete(environment)
    await session.commit()


@router.get("/{environment_id}/deployments", response_model=list[dict])
async def list_environment_deployments(
    environment_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    """List deployments for environment."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:read"
    )

    statement = select(EnvironmentDeployment).where(
        EnvironmentDeployment.environment_id == environment_id
    ).offset(skip).limit(limit)
    
    result = await session.exec(statement)
    deployments = result.all()

    return [
        {
            "id": str(dep.id),
            "environment_id": str(dep.environment_id),
            "flow_id": str(dep.flow_id) if dep.flow_id else None,
            "deployment_config": dep.deployment_config,
            "status": dep.status,
            "created_at": dep.created_at.isoformat() if dep.created_at else None,
            "deployed_at": dep.deployed_at.isoformat() if dep.deployed_at else None,
            "created_by": str(dep.created_by) if dep.created_by else None,
        }
        for dep in deployments
    ]


@router.post("/{environment_id}/deployments", status_code=status.HTTP_201_CREATED)
async def create_environment_deployment(
    environment_id: UUIDstr,
    deployment_data: dict,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Create a new deployment in environment."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:deploy"
    )

    # Create deployment
    from datetime import datetime
    deployment = EnvironmentDeployment(
        environment_id=environment_id,
        flow_id=deployment_data.get("flow_id"),
        deployment_config=deployment_data.get("deployment_config", {}),
        status="pending",
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    
    session.add(deployment)
    await session.commit()
    await session.refresh(deployment)

    return {
        "id": str(deployment.id),
        "environment_id": str(deployment.environment_id),
        "flow_id": str(deployment.flow_id) if deployment.flow_id else None,
        "deployment_config": deployment.deployment_config,
        "status": deployment.status,
        "created_at": deployment.created_at.isoformat(),
        "created_by": str(deployment.created_by),
    }


@router.get("/{environment_id}/variables", response_model=list[dict])
async def list_environment_variables(
    environment_id: UUIDstr,
    session: DbSession,
    current_user: CurrentActiveUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict]:
    """List variables scoped to environment."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:read"
    )

    # This would query the Variable model with environment_id filter
    # For now, return placeholder response
    return []


@router.post("/{environment_id}/variables", status_code=status.HTTP_201_CREATED)
async def create_environment_variable(
    environment_id: UUIDstr,
    variable_data: dict,
    session: DbSession,
    current_user: CurrentActiveUser,
) -> dict:
    """Create a variable scoped to environment."""
    
    environment = await session.get(Environment, environment_id)
    if not environment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )

    # Check project permission
    await check_project_permission(
        session, current_user, environment.project_id, "environment:update"
    )

    # This would create a Variable with environment_id scope
    # For now, return placeholder response
    return {
        "id": "placeholder",
        "name": variable_data.get("name"),
        "value": variable_data.get("value"),
        "environment_id": str(environment_id),
    }
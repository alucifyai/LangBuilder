"""RBAC dependencies for FastAPI endpoints."""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Callable
from uuid import UUID

from fastapi import Depends, HTTPException, Path, status
from sqlmodel import Session

from langflow.api.utils import get_current_user, get_session

if TYPE_CHECKING:
    from langflow.services.database.models.flow.model import Flow
    from langflow.services.database.models.rbac.environment import Environment
    from langflow.services.database.models.rbac.project import Project
    from langflow.services.database.models.rbac.role import Role
    from langflow.services.database.models.rbac.workspace import Workspace
    from langflow.services.database.models.user.model import User

# Import for runtime use
from langflow.services.database.models.rbac.workspace import Workspace


def get_workspace_by_id(
    workspace_id: UUID = Path(...),
    session: Session = Depends(get_session),
) -> Workspace:
    """Get workspace by ID or raise 404."""
    workspace = session.get(Workspace, workspace_id)
    if not workspace or workspace.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return workspace


def get_project_by_id(
    project_id: UUID = Path(...),
    session: Session = Depends(get_session),
) -> Project:
    """Get project by ID or raise 404."""
    project = session.get(Project, project_id)
    if not project or not project.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


def get_environment_by_id(
    environment_id: UUID = Path(...),
    session: Session = Depends(get_session),
) -> Environment:
    """Get environment by ID or raise 404."""
    environment = session.get(Environment, environment_id)
    if not environment or not environment.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Environment not found"
        )
    return environment


def get_role_by_id(
    role_id: UUID = Path(...),
    session: Session = Depends(get_session),
) -> Role:
    """Get role by ID or raise 404."""
    role = session.get(Role, role_id)
    if not role or not role.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


def get_flow_by_id(
    flow_id: UUID = Path(...),
    session: Session = Depends(get_session),
) -> Flow:
    """Get flow by ID or raise 404."""
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow not found"
        )
    return flow


class PermissionChecker:
    """Permission checker for RBAC system."""
    
    def __init__(self, session: Session, user: User):
        self.session = session
        self.user = user
    
    def has_workspace_permission(self, workspace: Workspace, permission: str) -> bool:
        """Check if user has permission on workspace."""
        # Super admin has all permissions
        if self.user.is_superuser:
            return True
        
        # Workspace owner has all permissions
        if workspace.owner_id == self.user.id:
            return True
        
        # TODO: Implement proper role-based permission checking
        # This is a placeholder implementation
        
        return False
    
    def has_project_permission(self, project: Project, permission: str) -> bool:
        """Check if user has permission on project."""
        # Super admin has all permissions
        if self.user.is_superuser:
            return True
        
        # Project owner has all permissions
        if project.owner_id == self.user.id:
            return True
        
        # Check workspace-level permissions
        workspace = self.session.get(Workspace, project.workspace_id)
        if workspace and self.has_workspace_permission(workspace, permission):
            return True
        
        # TODO: Implement proper role-based permission checking
        
        return False
    
    def has_environment_permission(self, environment: Environment, permission: str) -> bool:
        """Check if user has permission on environment."""
        # Super admin has all permissions
        if self.user.is_superuser:
            return True
        
        # Environment owner has all permissions
        if environment.owner_id == self.user.id:
            return True
        
        # Check project-level permissions
        project = self.session.get(Project, environment.project_id)
        if project and self.has_project_permission(project, permission):
            return True
        
        # TODO: Implement proper role-based permission checking
        
        return False
    
    def has_flow_permission(self, flow: Flow, permission: str) -> bool:
        """Check if user has permission on flow."""
        # Super admin has all permissions
        if self.user.is_superuser:
            return True
        
        # Flow owner has all permissions
        if flow.user_id == self.user.id:
            return True
        
        # Check environment-level permissions if flow is in environment
        if flow.environment_id:
            environment = self.session.get(Environment, flow.environment_id)
            if environment and self.has_environment_permission(environment, permission):
                return True
        
        # Check project-level permissions if flow is in project
        if flow.project_id:
            project = self.session.get(Project, flow.project_id)
            if project and self.has_project_permission(project, permission):
                return True
        
        # TODO: Implement proper role-based permission checking
        
        return False


def check_workspace_permission(permission: str):
    """Dependency factory for workspace permission checking."""
    def dependency(
        workspace: Workspace = Depends(get_workspace_by_id),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ) -> Workspace:
        checker = PermissionChecker(session, current_user)
        if not checker.has_workspace_permission(workspace, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission}"
            )
        return workspace
    
    return dependency


def check_project_permission(permission: str):
    """Dependency factory for project permission checking."""
    def dependency(
        project: Project = Depends(get_project_by_id),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ) -> Project:
        checker = PermissionChecker(session, current_user)
        if not checker.has_project_permission(project, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission}"
            )
        return project
    
    return dependency


def check_environment_permission(permission: str):
    """Dependency factory for environment permission checking."""
    def dependency(
        environment: Environment = Depends(get_environment_by_id),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ) -> Environment:
        checker = PermissionChecker(session, current_user)
        if not checker.has_environment_permission(environment, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission}"
            )
        return environment
    
    return dependency


def check_flow_permission(permission: str):
    """Dependency factory for flow permission checking."""
    def dependency(
        flow: Flow = Depends(get_flow_by_id),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ) -> Flow:
        checker = PermissionChecker(session, current_user)
        if not checker.has_flow_permission(flow, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {permission}"
            )
        return flow
    
    return dependency


def require_permission(permission: str):
    """Decorator for checking permissions in route handlers."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a placeholder - would need proper implementation
            # based on the specific resource type and context
            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def check_api_key_permissions(
    api_key: str,
    permission: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    session: Session = Depends(get_session),
) -> bool:
    """Check if API key has required permissions for resource."""
    from langflow.services.database.models.api_key.model import ApiKey
    
    # Get API key from database
    db_api_key = session.query(ApiKey).filter(
        ApiKey.api_key == api_key,
        ApiKey.is_active == True
    ).first()
    
    if not db_api_key:
        return False
    
    # Update last used timestamp
    from datetime import datetime, timezone
    db_api_key.last_used_at = datetime.now(timezone.utc)
    db_api_key.total_uses += 1
    session.commit()
    
    # Check if API key has scoped permissions
    if db_api_key.scoped_permissions:
        permission_code = f"{resource_type}:{permission}"
        if permission_code not in db_api_key.scoped_permissions:
            return False
    
    # Check scope restrictions
    if db_api_key.scope_type and db_api_key.scope_id:
        if resource_type != db_api_key.scope_type:
            return False
        if resource_id and str(resource_id) != str(db_api_key.scope_id):
            return False
    
    return True
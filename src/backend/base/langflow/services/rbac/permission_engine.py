"""Permission engine for RBAC system.

Provides fast permission checking with caching and hierarchical scope resolution.
Target: <100ms p95 latency for permission checks.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import redis
from sqlmodel import Session

from langflow.services.database.models.user.model import User
from langflow.services.database.models.rbac.permission import Permission, PermissionAction, ResourceType
from langflow.services.database.models.rbac.role import Role
from langflow.services.database.models.rbac.role_assignment import RoleAssignment, AssignmentScope
from langflow.services.database.models.rbac.workspace import Workspace
from langflow.services.database.models.rbac.project import Project
from langflow.services.database.models.rbac.environment import Environment
from langflow.services.database.models.flow.model import Flow


class PermissionResult:
    """Result of a permission check."""
    
    def __init__(
        self,
        granted: bool,
        reason: str,
        cached: bool = False,
        scope_path: Optional[List[str]] = None,
        applicable_roles: Optional[List[str]] = None,
        check_duration_ms: Optional[float] = None
    ):
        self.granted = granted
        self.reason = reason
        self.cached = cached
        self.scope_path = scope_path or []
        self.applicable_roles = applicable_roles or []
        self.check_duration_ms = check_duration_ms
    
    def __bool__(self) -> bool:
        return self.granted


class PermissionEngine:
    """High-performance permission engine with caching and scope resolution."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.cache_ttl = 300  # 5 minutes
        self.scope_hierarchy = [
            AssignmentScope.WORKSPACE,
            AssignmentScope.PROJECT, 
            AssignmentScope.ENVIRONMENT,
            AssignmentScope.FLOW,
            AssignmentScope.COMPONENT
        ]
    
    async def check_permission(
        self,
        session: Session,
        user: User,
        resource_type: ResourceType,
        action: PermissionAction,
        resource_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PermissionResult:
        """Check if user has permission for the specified action on resource.
        
        Args:
            session: Database session
            user: User requesting permission
            resource_type: Type of resource being accessed
            action: Action being performed
            resource_id: Specific resource ID (optional for type-level permissions)
            context: Additional context for conditional permissions
            
        Returns:
            PermissionResult with granted status and metadata
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._build_cache_key(user.id, resource_type, action, resource_id)
            if self.redis:
                cached_result = await self._get_cached_permission(cache_key)
                if cached_result is not None:
                    cached_result.check_duration_ms = (time.time() - start_time) * 1000
                    return cached_result
            
            # Super admin bypass
            if user.is_superuser:
                result = PermissionResult(
                    granted=True,
                    reason="Super admin access",
                    scope_path=["system"],
                    applicable_roles=["super_admin"]
                )
                await self._cache_permission(cache_key, result)
                result.check_duration_ms = (time.time() - start_time) * 1000
                return result
            
            # Get resource scope path
            scope_path = await self._resolve_resource_scope(session, resource_type, resource_id)
            
            # Find applicable role assignments
            role_assignments = await self._get_user_role_assignments(session, user.id, scope_path)
            
            # Check permissions for each role assignment
            for assignment in role_assignments:
                role = await self._get_role_with_permissions(session, assignment.role_id)
                if not role:
                    continue
                
                # Check if role has required permission
                permission_granted = await self._check_role_permission(
                    session, role, resource_type, action, context
                )
                
                if permission_granted:
                    result = PermissionResult(
                        granted=True,
                        reason=f"Permission granted via role '{role.name}' in scope '{assignment.scope_type}'",
                        scope_path=scope_path,
                        applicable_roles=[role.name]
                    )
                    await self._cache_permission(cache_key, result)
                    result.check_duration_ms = (time.time() - start_time) * 1000
                    return result
            
            # Permission denied
            result = PermissionResult(
                granted=False,
                reason="No applicable permissions found",
                scope_path=scope_path,
                applicable_roles=[assignment.role.name for assignment in role_assignments if assignment.role]
            )
            await self._cache_permission(cache_key, result, ttl=60)  # Cache denials for 1 minute
            result.check_duration_ms = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            # Log error and deny by default
            result = PermissionResult(
                granted=False,
                reason=f"Permission check failed: {str(e)}",
                scope_path=[],
                applicable_roles=[]
            )
            result.check_duration_ms = (time.time() - start_time) * 1000
            return result
    
    async def check_bulk_permissions(
        self,
        session: Session,
        user: User,
        permission_requests: List[Tuple[ResourceType, PermissionAction, Optional[UUID]]]
    ) -> Dict[Tuple[ResourceType, PermissionAction, Optional[UUID]], PermissionResult]:
        """Check multiple permissions efficiently."""
        results = {}
        
        # Check cache for all requests
        cache_keys = []
        for resource_type, action, resource_id in permission_requests:
            cache_key = self._build_cache_key(user.id, resource_type, action, resource_id)
            cache_keys.append(cache_key)
        
        if self.redis:
            cached_results = await self._get_cached_permissions_bulk(cache_keys)
        else:
            cached_results = {}
        
        # Process uncached requests
        uncached_requests = []
        for i, request in enumerate(permission_requests):
            if cache_keys[i] in cached_results:
                results[request] = cached_results[cache_keys[i]]
            else:
                uncached_requests.append(request)
        
        # Process uncached requests in parallel
        if uncached_requests:
            tasks = []
            for resource_type, action, resource_id in uncached_requests:
                task = self.check_permission(session, user, resource_type, action, resource_id)
                tasks.append(task)
            
            uncached_results = await asyncio.gather(*tasks)
            for i, request in enumerate(uncached_requests):
                results[request] = uncached_results[i]
        
        return results
    
    async def get_user_permissions(
        self,
        session: Session,
        user_id: UUID,
        scope_type: Optional[AssignmentScope] = None,
        scope_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all permissions for a user in a given scope."""
        
        # Get user role assignments
        query = session.query(RoleAssignment).filter(
            RoleAssignment.user_id == user_id,
            RoleAssignment.is_active == True
        )
        
        if scope_type:
            query = query.filter(RoleAssignment.scope_type == scope_type)
        
        if scope_id:
            scope_field = getattr(RoleAssignment, f"{scope_type.value}_id")
            query = query.filter(scope_field == scope_id)
        
        assignments = query.all()
        
        # Collect all permissions
        permissions = []
        for assignment in assignments:
            role = session.get(Role, assignment.role_id)
            if role and role.is_active:
                role_permissions = session.query(Permission).join(
                    RolePermission,
                    Permission.id == RolePermission.permission_id
                ).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.is_granted == True
                ).all()
                
                for perm in role_permissions:
                    permissions.append({
                        "permission_id": str(perm.id),
                        "permission_code": perm.code,
                        "permission_name": perm.name,
                        "resource_type": perm.resource_type,
                        "action": perm.action,
                        "role_id": str(role.id),
                        "role_name": role.name,
                        "scope_type": assignment.scope_type,
                        "scope_id": getattr(assignment, f"{assignment.scope_type.value}_id"),
                        "granted_at": assignment.assigned_at.isoformat()
                    })
        
        return permissions
    
    async def _resolve_resource_scope(
        self,
        session: Session,
        resource_type: ResourceType,
        resource_id: Optional[UUID]
    ) -> List[str]:
        """Resolve the full scope path for a resource."""
        if not resource_id:
            return [resource_type.value]
        
        scope_path = []
        
        if resource_type == ResourceType.WORKSPACE:
            workspace = session.get(Workspace, resource_id)
            if workspace:
                scope_path = [f"workspace:{workspace.id}"]
        
        elif resource_type == ResourceType.PROJECT:
            project = session.get(Project, resource_id)
            if project:
                scope_path = [
                    f"workspace:{project.workspace_id}",
                    f"project:{project.id}"
                ]
        
        elif resource_type == ResourceType.ENVIRONMENT:
            environment = session.get(Environment, resource_id)
            if environment:
                project = session.get(Project, environment.project_id)
                if project:
                    scope_path = [
                        f"workspace:{project.workspace_id}",
                        f"project:{project.id}",
                        f"environment:{environment.id}"
                    ]
        
        elif resource_type == ResourceType.FLOW:
            flow = session.get(Flow, resource_id)
            if flow:
                if flow.environment_id:
                    environment = session.get(Environment, flow.environment_id)
                    if environment:
                        project = session.get(Project, environment.project_id)
                        if project:
                            scope_path = [
                                f"workspace:{project.workspace_id}",
                                f"project:{project.id}",
                                f"environment:{environment.id}",
                                f"flow:{flow.id}"
                            ]
                elif flow.project_id:
                    project = session.get(Project, flow.project_id)
                    if project:
                        scope_path = [
                            f"workspace:{project.workspace_id}",
                            f"project:{project.id}",
                            f"flow:{flow.id}"
                        ]
        
        return scope_path
    
    async def _get_user_role_assignments(
        self,
        session: Session,
        user_id: UUID,
        scope_path: List[str]
    ) -> List[RoleAssignment]:
        """Get all role assignments that apply to the given scope path."""
        assignments = []
        
        # Extract scope IDs from path
        scope_ids = {}
        for scope_item in scope_path:
            if ":" in scope_item:
                scope_type, scope_id = scope_item.split(":", 1)
                scope_ids[scope_type] = UUID(scope_id)
        
        # Check assignments at each scope level (inheritance)
        for scope_type in self.scope_hierarchy:
            scope_field = f"{scope_type.value}_id"
            
            if scope_type.value in scope_ids:
                # Direct assignment at this scope
                direct_assignments = session.query(RoleAssignment).filter(
                    RoleAssignment.user_id == user_id,
                    RoleAssignment.is_active == True,
                    getattr(RoleAssignment, scope_field) == scope_ids[scope_type.value]
                ).all()
                assignments.extend(direct_assignments)
                
                # Inherited assignments from parent scopes
                if scope_type == AssignmentScope.PROJECT and "workspace" in scope_ids:
                    workspace_assignments = session.query(RoleAssignment).filter(
                        RoleAssignment.user_id == user_id,
                        RoleAssignment.is_active == True,
                        RoleAssignment.workspace_id == scope_ids["workspace"],
                        RoleAssignment.project_id.is_(None)
                    ).all()
                    assignments.extend(workspace_assignments)
                
                # Similar inheritance logic for other scope levels...
        
        return assignments
    
    async def _get_role_with_permissions(self, session: Session, role_id: UUID) -> Optional[Role]:
        """Get role with its permissions loaded."""
        return session.get(Role, role_id)
    
    async def _check_role_permission(
        self,
        session: Session,
        role: Role,
        resource_type: ResourceType,
        action: PermissionAction,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if role has specific permission."""
        from langflow.services.database.models.rbac.permission import RolePermission
        
        # Look for exact permission match
        permission_code = f"{resource_type.value}:{action.value}"
        
        role_permission = session.query(RolePermission).join(Permission).filter(
            RolePermission.role_id == role.id,
            RolePermission.is_granted == True,
            Permission.code == permission_code
        ).first()
        
        if role_permission:
            # Check temporal constraints
            if role_permission.expires_at:
                if datetime.now(timezone.utc) > role_permission.expires_at:
                    return False
            
            # Check conditional constraints
            if role_permission.conditions and context:
                # TODO: Implement condition evaluation
                pass
            
            return True
        
        # Check for wildcard permissions
        wildcard_code = f"{resource_type.value}:*"
        wildcard_permission = session.query(RolePermission).join(Permission).filter(
            RolePermission.role_id == role.id,
            RolePermission.is_granted == True,
            Permission.code == wildcard_code
        ).first()
        
        return wildcard_permission is not None
    
    def _build_cache_key(
        self,
        user_id: UUID,
        resource_type: ResourceType,
        action: PermissionAction,
        resource_id: Optional[UUID]
    ) -> str:
        """Build cache key for permission check."""
        resource_part = f"{resource_id}" if resource_id else "type"
        return f"perm:{user_id}:{resource_type.value}:{action.value}:{resource_part}"
    
    async def _get_cached_permission(self, cache_key: str) -> Optional[PermissionResult]:
        """Get cached permission result."""
        if not self.redis:
            return None
        
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                import json
                data = json.loads(cached_data)
                return PermissionResult(
                    granted=data["granted"],
                    reason=data["reason"],
                    cached=True,
                    scope_path=data.get("scope_path", []),
                    applicable_roles=data.get("applicable_roles", [])
                )
        except Exception:
            pass
        
        return None
    
    async def _cache_permission(
        self,
        cache_key: str,
        result: PermissionResult,
        ttl: Optional[int] = None
    ):
        """Cache permission result."""
        if not self.redis:
            return
        
        try:
            import json
            cache_data = {
                "granted": result.granted,
                "reason": result.reason,
                "scope_path": result.scope_path,
                "applicable_roles": result.applicable_roles,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.redis.setex(
                cache_key,
                ttl or self.cache_ttl,
                json.dumps(cache_data)
            )
        except Exception:
            pass
    
    async def _get_cached_permissions_bulk(self, cache_keys: List[str]) -> Dict[str, PermissionResult]:
        """Get multiple cached permissions."""
        results = {}
        if not self.redis:
            return results
        
        try:
            cached_values = await self.redis.mget(cache_keys)
            for i, cached_data in enumerate(cached_values):
                if cached_data:
                    import json
                    data = json.loads(cached_data)
                    results[cache_keys[i]] = PermissionResult(
                        granted=data["granted"],
                        reason=data["reason"],
                        cached=True,
                        scope_path=data.get("scope_path", []),
                        applicable_roles=data.get("applicable_roles", [])
                    )
        except Exception:
            pass
        
        return results
    
    async def invalidate_user_permissions(self, user_id: UUID):
        """Invalidate all cached permissions for a user."""
        if not self.redis:
            return
        
        try:
            pattern = f"perm:{user_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
        except Exception:
            pass
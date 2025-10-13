"""RBAC Service Module.

This module provides Role-Based Access Control (RBAC) functionality including:
- Permission catalog and system roles (constants.py)
- Database initialization and seeding (initialization.py)
- Permission evaluation engine (enforcement.py)
- Scope resolution (scope_resolver.py)
- Permission caching (cache.py)
- Event-based cache invalidation (events.py)
- FastAPI dependencies for endpoint protection (dependencies.py)
"""

from langflow.services.rbac.cache import PermissionCache, get_permission_cache, reset_permission_cache
from langflow.services.rbac.constants import (
    PERMISSIONS,
    SYSTEM_ROLES,
    TOTAL_PERMISSIONS_COUNT,
    TOTAL_SYSTEM_ROLES_COUNT,
    expand_wildcards,
    get_all_permission_names,
    get_permission_by_name,
    validate_role_permissions,
)
from langflow.services.rbac.dependencies import (
    require_create,
    require_delete,
    require_deploy,
    require_execute,
    require_export,
    require_permission,
    require_read,
    require_update,
)
from langflow.services.rbac.enforcement import RBACEnforcementEngine
from langflow.services.rbac.events import (
    invalidate_group_members_cache_async,
    invalidate_resource_cache_async,
    invalidate_role_cache_async,
    invalidate_user_cache_async,
    register_rbac_cache_invalidation_listeners,
)
from langflow.services.rbac.initialization import seed_permissions_and_roles
from langflow.services.rbac.scope_resolver import ScopeResolver

__all__ = [
    # Constants and utilities
    "PERMISSIONS",
    "SYSTEM_ROLES",
    "TOTAL_PERMISSIONS_COUNT",
    "TOTAL_SYSTEM_ROLES_COUNT",
    "expand_wildcards",
    "get_all_permission_names",
    "get_permission_by_name",
    "validate_role_permissions",
    # Initialization
    "seed_permissions_and_roles",
    # Core enforcement
    "RBACEnforcementEngine",
    "ScopeResolver",
    # Caching
    "PermissionCache",
    "get_permission_cache",
    "reset_permission_cache",
    # Event-based cache invalidation
    "register_rbac_cache_invalidation_listeners",
    "invalidate_user_cache_async",
    "invalidate_role_cache_async",
    "invalidate_group_members_cache_async",
    "invalidate_resource_cache_async",
    # FastAPI dependencies
    "require_permission",
    "require_read",
    "require_create",
    "require_update",
    "require_delete",
    "require_export",
    "require_execute",
    "require_deploy",
]

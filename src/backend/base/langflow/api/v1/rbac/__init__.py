"""RBAC API module - Unified router for all RBAC endpoints."""

from fastapi import APIRouter

from .workspaces import router as workspaces_router
from .projects import router as projects_router  
from .roles import router as roles_router
from .permissions import router as permissions_router

# Import additional routers that need to be created
try:
    from .service_accounts import router as service_accounts_router
    HAS_SERVICE_ACCOUNTS = True
except ImportError:
    HAS_SERVICE_ACCOUNTS = False

try:
    from .environments import router as environments_router
    HAS_ENVIRONMENTS = True
except ImportError:
    HAS_ENVIRONMENTS = False

try:
    from .audit import router as audit_router
    HAS_AUDIT = True
except ImportError:
    HAS_AUDIT = False

try:
    from .user_groups import router as user_groups_router
    HAS_USER_GROUPS = True
except ImportError:
    HAS_USER_GROUPS = False

try:
    from .role_assignments import router as role_assignments_router
    HAS_ROLE_ASSIGNMENTS = True
except ImportError:
    HAS_ROLE_ASSIGNMENTS = False

# Main RBAC router with unified prefix
rbac_router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing authentication"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource does not exist"},
        422: {"description": "Validation Error - Invalid request data"},
    },
)

# Include all RBAC sub-routers
rbac_router.include_router(workspaces_router)
rbac_router.include_router(projects_router)
rbac_router.include_router(roles_router)
rbac_router.include_router(permissions_router)

# Include optional routers if available
if HAS_SERVICE_ACCOUNTS:
    rbac_router.include_router(service_accounts_router)
if HAS_ENVIRONMENTS:
    rbac_router.include_router(environments_router)
if HAS_AUDIT:
    rbac_router.include_router(audit_router)
if HAS_USER_GROUPS:
    rbac_router.include_router(user_groups_router)
if HAS_ROLE_ASSIGNMENTS:
    rbac_router.include_router(role_assignments_router)

# Export the main router and individual routers for backwards compatibility
__all__ = [
    "rbac_router",
    "permissions_router",
    "projects_router", 
    "roles_router",
    "workspaces_router",
]

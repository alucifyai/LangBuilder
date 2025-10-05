"""RBAC API endpoints.

Implements Phase 3 of RBAC implementation:
- Role management API
- Permission catalog API
- Grant (role assignment) API
- Group management API
- ServiceAccount management API
- Audit log query API
"""

from fastapi import APIRouter

from langflow.api.v1.rbac import audit_logs, grants, permissions, roles, service_accounts
# TODO: Re-enable when Group model is implemented
# from langflow.api.v1.rbac import groups

router = APIRouter(prefix="/rbac", tags=["RBAC"])

# Include all RBAC sub-routers
router.include_router(permissions.router, prefix="/permissions")
router.include_router(roles.router, prefix="/roles")
router.include_router(grants.router, prefix="/grants")
# TODO: Re-enable when Group model is implemented
# router.include_router(groups.router, prefix="/groups")
router.include_router(service_accounts.router, prefix="/service-accounts")
router.include_router(audit_logs.router, prefix="/audit-logs")

__all__ = ["router"]

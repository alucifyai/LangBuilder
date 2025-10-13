"""RBAC API endpoints for Role-Based Access Control."""

from fastapi import APIRouter

from langflow.api.v1.rbac.grants import router as grants_router
from langflow.api.v1.rbac.groups import router as groups_router
from langflow.api.v1.rbac.permissions import router as permissions_router
from langflow.api.v1.rbac.roles import router as roles_router
from langflow.api.v1.rbac.service_accounts import router as service_accounts_router

rbac_router = APIRouter(prefix="/rbac", tags=["RBAC"])
rbac_router.include_router(roles_router)
rbac_router.include_router(permissions_router)
rbac_router.include_router(grants_router)
rbac_router.include_router(groups_router)
rbac_router.include_router(service_accounts_router)

__all__ = ["rbac_router"]

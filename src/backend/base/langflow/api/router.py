# Router for base api
from fastapi import APIRouter

from langflow.api.v1 import (
    access_reviews_router,
    api_key_router,
    audit_router,
    audit_logs_router,
    chat_router,
    compliance_router,
    endpoints_router,
    files_router,
    flows_router,
    folders_router,
    grants_router,
    groups_router,
    iac_router,
    invites_router,
    user_invites_router,
    login_router,
    mcp_projects_router,
    mcp_router,
    monitor_router,
    permissions_router,
    projects_router,
    ownership_router,
    roles_router,
    scim_router,
    service_accounts_router,
    sso_router,
    sso_admin_router,
    starter_projects_router,
    store_router,
    temporary_grants_router,
    users_router,
    validate_router,
    variables_router,
)
from langflow.api.v1.voice_mode import router as voice_mode_router
from langflow.api.v2 import files_router as files_router_v2
from langflow.api.v2 import mcp_router as mcp_router_v2

router_v1 = APIRouter(
    prefix="/v1",
)

router_v2 = APIRouter(
    prefix="/v2",
)

router_v1.include_router(chat_router)
router_v1.include_router(endpoints_router)
router_v1.include_router(validate_router)
router_v1.include_router(store_router)
router_v1.include_router(flows_router)
router_v1.include_router(users_router)
router_v1.include_router(access_reviews_router)
router_v1.include_router(api_key_router)
router_v1.include_router(audit_logs_router)
router_v1.include_router(compliance_router)
router_v1.include_router(login_router)
router_v1.include_router(variables_router)
router_v1.include_router(files_router)
router_v1.include_router(monitor_router)
router_v1.include_router(folders_router)
router_v1.include_router(invites_router)
router_v1.include_router(user_invites_router)
router_v1.include_router(permissions_router)
router_v1.include_router(ownership_router)
router_v1.include_router(roles_router)
router_v1.include_router(grants_router)
router_v1.include_router(groups_router)
router_v1.include_router(iac_router)
router_v1.include_router(scim_router)
router_v1.include_router(audit_router)
router_v1.include_router(service_accounts_router)
router_v1.include_router(sso_router)
router_v1.include_router(sso_admin_router)
router_v1.include_router(projects_router)
router_v1.include_router(starter_projects_router)
router_v1.include_router(mcp_router)
router_v1.include_router(voice_mode_router)
router_v1.include_router(mcp_projects_router)
router_v1.include_router(temporary_grants_router)

router_v2.include_router(files_router_v2)
router_v2.include_router(mcp_router_v2)

router = APIRouter(
    prefix="/api",
)
router.include_router(router_v1)
router.include_router(router_v2)

# RBAC Enhancement - Impact Analysis

## Architectural Gaps to Address

Based on PRD and current state analysis:

1. **Scope Hierarchy Not Defined**
   - PRD defines: Workspace > Project > Environment > Flow > Component
   - **Current State**: Only User > Folder (Project) > Flow exists
   - **Missing**: Workspace, Environment concepts
   - **Decision Needed**: Map Workspace to top-level Folder? Add Workspace model?

2. **Permission Evaluation Engine Needed**
   - Must resolve effective permissions considering:
     - User's roles at multiple scopes
     - Group memberships
     - Scope inheritance (workspace grants flow down)
     - Deny-by-default, explicit deny precedence
   - **Performance Requirement**: ≤100ms p95 (PRD NFR 5.1)
   - **Recommendation**: Build in-memory cache with invalidation

3. **SSO Integration Architecture**
   - Must support SAML 2.0 and OIDC
   - Requires: IdP metadata parser, assertion validator, attribute mapper
   - **Recommendation**: Use `python-saml` or `authlib` library

4. **SCIM Provisioning Service**
   - Must implement SCIM 2.0 server endpoints
   - Async user/group sync from IdP
   - **Recommendation**: Use `scim2-server` library or FastAPI endpoints

5. **Audit Logging Infrastructure**
   - Immutable, write-only audit log table
   - High-volume writes (every RBAC decision could be logged)
   - **Recommendation**: Async logging to separate table/service, consider event sourcing pattern

## Files That Will Need Modification

**Database Models** (New):
- `src/backend/base/langflow/services/database/models/rbac/role.py`
- `src/backend/base/langflow/services/database/models/rbac/permission.py`
- `src/backend/base/langflow/services/database/models/rbac/grant.py`
- `src/backend/base/langflow/services/database/models/rbac/group.py`
- `src/backend/base/langflow/services/database/models/rbac/service_account.py`
- `src/backend/base/langflow/services/database/models/rbac/audit_log.py`
- `src/backend/base/langflow/services/database/models/rbac/sso_config.py` (or extend settings)

**Database Models** (Modify):
- `src/backend/base/langflow/services/database/models/user/model.py` - Add group, role relationships
- `src/backend/base/langflow/services/database/models/folder/model.py` - Leverage `auth_settings`, add workspace concept
- `src/backend/base/langflow/services/database/models/flow/model.py` - Remove binary `access_type`, rely on RBAC
- `src/backend/base/langflow/services/database/models/api_key/model.py` - Add scope fields

**Authentication/Authorization** (Modify):
- `src/backend/base/langflow/services/auth/utils.py` - Add RBAC enforcement functions
- `src/backend/base/langflow/services/auth/service.py` - Integrate RBAC service

**Authentication/Authorization** (New):
- `src/backend/base/langflow/services/auth/rbac_enforcer.py` - Permission evaluation engine
- `src/backend/base/langflow/services/auth/scope_resolver.py` - Scope hierarchy resolver
- `src/backend/base/langflow/services/auth/sso_handler.py` - SSO assertion validation
- `src/backend/base/langflow/services/auth/scim_service.py` - SCIM provisioning logic

**API Endpoints** (New):
- `src/backend/base/langflow/api/v1/rbac/roles.py`
- `src/backend/base/langflow/api/v1/rbac/permissions.py`
- `src/backend/base/langflow/api/v1/rbac/grants.py`
- `src/backend/base/langflow/api/v1/rbac/groups.py`
- `src/backend/base/langflow/api/v1/rbac/service_accounts.py`
- `src/backend/base/langflow/api/v1/rbac/audit.py`
- `src/backend/base/langflow/api/v1/admin/sso.py`
- `src/backend/base/langflow/api/v1/admin/scim.py` (SCIM 2.0 server endpoints)

**API Endpoints** (Modify - Add RBAC Guards):
- `src/backend/base/langflow/api/v1/flows.py` - Check `read`, `update`, `delete`, `export_flow`, `deploy_environment` permissions
- `src/backend/base/langflow/api/v1/projects.py` - Check `read`, `update`, `delete` permissions at project scope
- `src/backend/base/langflow/api/v1/endpoints.py` - Check `modify_component_settings` permission
- `src/backend/base/langflow/api/v1/users.py` - Check `invite_users` permission
- `src/backend/base/langflow/api/v1/api_key.py` - Check `manage_tokens` permission

**Middleware** (New):
- `src/backend/base/langflow/middleware/rbac_middleware.py` - FastAPI dependency for permission checking

**Frontend Pages** (New):
- `src/frontend/src/pages/AdminPage/RoleManagement.tsx`
- `src/frontend/src/pages/AdminPage/PermissionManagement.tsx`
- `src/frontend/src/pages/AdminPage/GroupManagement.tsx`
- `src/frontend/src/pages/AdminPage/ServiceAccountManagement.tsx`
- `src/frontend/src/pages/AdminPage/AuditLog.tsx`
- `src/frontend/src/pages/Settings/SSOSettings.tsx`

**Frontend Contexts** (Modify):
- `src/frontend/src/contexts/authContext.tsx` - Add permission state, checking functions

**Frontend Stores** (Modify):
- `src/frontend/src/stores/authStore.ts` - Add `roles`, `permissions`, `groups` state

**Frontend Components** (New):
- `src/frontend/src/components/PermissionGuard.tsx` - Conditional rendering based on permissions
- `src/frontend/src/components/RoleSelector.tsx` - Role selection dropdown
- `src/frontend/src/components/PermissionMatrix.tsx` - Visual permission matrix

**Database Migration**:
- `src/backend/base/langflow/alembic/versions/XXXX_add_rbac_models.py` - Initial RBAC schema
- `src/backend/base/langflow/alembic/versions/XXXX_migrate_existing_permissions.py` - Data migration

## New Files/Modules Needed

See "Files That Will Need Modification" section above - all items marked "(New)".

**Additionally**:
- **IaC Support** (Story 3.3, 3.6):
  - `src/backend/base/langflow/services/rbac/iac_parser.py` - YAML/Terraform parser
  - `src/backend/base/langflow/cli/rbac_apply.py` - CLI command to apply RBAC config from YAML
  - Documentation: `docs/rbac_iac_format.md` - YAML/Terraform format specification

- **Testing**:
  - `src/backend/tests/unit/services/auth/test_rbac_enforcer.py`
  - `src/backend/tests/integration/api/v1/rbac/test_roles.py`
  - `src/frontend/tests/pages/AdminPage/RoleManagement.test.tsx`

## Integration Considerations

**Must Integrate With**:
1. **Existing Auth Middleware** (`src/backend/base/langflow/services/auth/utils.py:api_key_security`)
   - Extend to resolve user's effective permissions after authentication
   - Add permission cache to avoid database queries on every request

2. **Database Session Management** (`src/backend/base/langflow/services/database/service.py`)
   - RBAC queries must use same async session patterns
   - Consider read replicas for permission lookups (high read volume)

3. **FastAPI Dependency Injection**
   - Create reusable dependencies: `Depends(require_permission("flow:read"))`
   - Must work with existing `CurrentActiveUser` dependency

4. **Frontend Route Guards** (`src/frontend/src/routes.tsx`)
   - Wrap routes with `PermissionGuard` component
   - Redirect unauthorized users to appropriate error page

5. **API Response Models**
   - Extend user response models to include `roles`, `permissions`, `groups`
   - Add `effective_permissions` to context-aware responses

**Performance Considerations**:
- **Permission Cache**: In-memory cache (Redis or Python `lru_cache`) for permission lookups
  - Cache key: `(user_id, resource_type, resource_id, action)`
  - TTL: 5 minutes (configurable)
  - Invalidation: On role/grant changes
- **Batch Permission Checks**: When listing resources, check permissions in batch (single query)
- **Lazy Loading**: Don't load all user permissions upfront, only check when needed

---

# Quick Reference - Key Files and Entry Points

## Critical Files for Understanding the System

**Backend (Python/FastAPI)**
- **Main Entry**: `src/backend/base/langflow/main.py` - FastAPI application initialization
- **Server**: `src/backend/base/langflow/server.py` - Server setup
- **Configuration**: `.env.example` - Environment configuration template
- **Database Models**: `src/backend/base/langflow/services/database/models/` - All SQLModel definitions
- **Authentication**: `src/backend/base/langflow/services/auth/utils.py` - Current auth implementation
- **API Routes**: `src/backend/base/langflow/api/v1/` - All REST API endpoints

**Frontend (React/TypeScript)**
- **Main Entry**: `src/frontend/src/index.tsx` - React application entry
- **App Component**: `src/frontend/src/App.tsx` - Root component
- **Auth Context**: `src/frontend/src/contexts/authContext.tsx` - Authentication state management
- **Routes**: `src/frontend/src/routes.tsx` - Application routing
- **Stores**: `src/frontend/src/stores/` - Zustand state management

## Enhancement Impact Areas (RBAC Implementation)

Based on the PRD requirements, the following areas will need modification:

### Database Layer
- `src/backend/base/langflow/services/database/models/user/model.py` - Extend User model with role relationships
- **NEW MODELS NEEDED**:
  - `models/rbac/role.py` - Role definitions
  - `models/rbac/permission.py` - Permission catalog
  - `models/rbac/grant.py` - Role assignments (grants)
  - `models/rbac/group.py` - User groups
  - `models/rbac/service_account.py` - Service accounts
  - `models/rbac/audit_log.py` - RBAC audit logs

### API Layer
- `src/backend/base/langflow/api/v1/login.py` - SSO integration points
- **NEW API ENDPOINTS NEEDED**:
  - `api/v1/rbac/roles.py` - Role CRUD
  - `api/v1/rbac/permissions.py` - Permission catalog
  - `api/v1/rbac/grants.py` - Role assignments
  - `api/v1/rbac/groups.py` - Group management
  - `api/v1/rbac/service_accounts.py` - Service account management
  - `api/v1/rbac/audit.py` - Audit log queries
  - `api/v1/admin/sso.py` - SSO/SCIM configuration

### Authorization Middleware
- `src/backend/base/langflow/services/auth/utils.py` - Add RBAC enforcement logic
- **NEW MIDDLEWARE NEEDED**:
  - `middleware/rbac_enforcer.py` - Permission checking middleware
  - `middleware/scope_resolver.py` - Resolve effective permissions with scope hierarchy

### Existing Resource Endpoints (Require RBAC Guards)
- `api/v1/flows.py` - Add permission checks for flow operations
- `api/v1/projects.py` - Add permission checks for project (folder) operations
- `api/v1/endpoints.py` - Add permission checks for component operations
- `api/v1/users.py` - Add permission checks for user management

### Frontend Components
- `src/frontend/src/contexts/authContext.tsx` - Extend with permission checking
- **NEW COMPONENTS NEEDED**:
  - `pages/AdminPage/RoleManagement.tsx` - Role management UI
  - `pages/AdminPage/PermissionManagement.tsx` - Permission assignment UI
  - `pages/AdminPage/GroupManagement.tsx` - Group management UI
  - `pages/AdminPage/AuditLog.tsx` - Audit log viewer
  - `pages/Settings/SSOSettings.tsx` - SSO configuration UI
  - `components/PermissionGuard.tsx` - Conditional rendering based on permissions

---

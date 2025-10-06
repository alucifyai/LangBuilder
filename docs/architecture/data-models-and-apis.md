# Data Models and APIs

## Data Models

All models use **SQLModel** (Pydantic + SQLAlchemy), stored in `src/backend/base/langflow/services/database/models/`.

**Existing Core Models:**

1. **User** (`user/model.py`)
   - Primary entity for authentication
   - Binary role system: `is_active`, `is_superuser`
   - Relationships: flows, folders, api_keys, variables

2. **Folder** (`folder/model.py`)
   - Represents "Projects" in PRD terminology
   - Hierarchical (parent_id for sub-projects)
   - `auth_settings` (JSON) field exists but unused - **opportunity for RBAC config**

3. **Flow** (`flow/model.py`)
   - Workflow/component definitions
   - Basic access control: `access_type` (PRIVATE/PUBLIC)
   - `locked` field prevents editing
   - Related to Folder (project), User (owner)

4. **ApiKey** (`api_key/model.py`)
   - API tokens for programmatic access
   - Associated with User
   - **No scope limiting currently**

5. **Variable** (`variable/model.py`)
   - Global variables per user
   - **No project scoping**

**Missing Models (Needed for RBAC):**

Based on PRD requirements, the following models do NOT exist and must be created:

1. **Role** - Role definitions with permission sets
2. **Permission** - Permission catalog (CRUD + extended actions)
3. **Grant** - Role assignments to users/groups at specific scopes
4. **Group** - User groups for collective role assignment
5. **ServiceAccount** - Non-human identities with scoped permissions
6. **AuditLog** - Immutable log of RBAC changes and access decisions
7. **SSOConfig** - SSO/SCIM integration settings (or extend settings service)

## API Specifications

**Current API Pattern**: RESTful with FastAPI, Pydantic schemas for validation

**Authentication**:
- JWT via `Authorization: Bearer <token>` header OR
- API key via `x-api-key` header/query param

**Current API Endpoints** (selected, relevant to RBAC):

```
POST   /api/v1/login                # Authenticate, get JWT tokens
POST   /api/v1/refresh              # Refresh access token
POST   /api/v1/logout               # Invalidate tokens
GET    /api/v1/auto_login           # Auto-login for dev (deprecated)

GET    /api/v1/users/                # List users (superuser only)
POST   /api/v1/users/                # Create user (superuser only)
GET    /api/v1/users/{user_id}      # Get user (own or superuser)
PATCH  /api/v1/users/{user_id}      # Update user (own or superuser)
DELETE /api/v1/users/{user_id}      # Delete user (superuser only)

GET    /api/v1/projects/             # List projects (own)
POST   /api/v1/projects/             # Create project
GET    /api/v1/projects/{id}         # Get project (own)
PATCH  /api/v1/projects/{id}         # Update project (own)
DELETE /api/v1/projects/{id}         # Delete project (own)

GET    /api/v1/flows/                # List flows (own or public)
POST   /api/v1/flows/                # Create flow
GET    /api/v1/flows/{id}            # Get flow (own or public)
PATCH  /api/v1/flows/{id}            # Update flow (own)
DELETE /api/v1/flows/{id}            # Delete flow (own)
POST   /api/v1/flows/{id}/run        # Execute flow (requires specific checks)

GET    /api/v1/api_key/              # List API keys (own)
POST   /api/v1/api_key/              # Create API key
DELETE /api/v1/api_key/{id}          # Delete API key (own)
```

**Missing API Endpoints (Needed for RBAC):**

According to PRD Stories 3.1, 3.2, 3.4, 3.5:

```
# Role Management (Story 3.1, 3.2)
GET    /api/admin/roles/             # List roles
POST   /api/admin/roles/             # Create role
GET    /api/admin/roles/{id}         # Get role
PATCH  /api/admin/roles/{id}         # Update role
DELETE /api/admin/roles/{id}         # Delete role

# Permission Catalog (Story 1.1)
GET    /api/admin/permissions/       # List available permissions

# Grant Management (Story 3.4, 3.5)
GET    /api/admin/grants/            # List role assignments
POST   /api/admin/grants/            # Assign role to principal
GET    /api/admin/grants/{id}        # Get grant
DELETE /api/admin/grants/{id}        # Revoke grant

# Group Management (Story 2.1)
GET    /api/admin/groups/            # List groups
POST   /api/admin/groups/            # Create group
PATCH  /api/admin/groups/{id}        # Update group (members)
DELETE /api/admin/groups/{id}        # Delete group

# Service Account Management (Story 2.4)
GET    /api/admin/service_accounts/  # List service accounts
POST   /api/admin/service_accounts/  # Create service account
DELETE /api/admin/service_accounts/{id} # Delete service account

# Audit Logs (Story 5.1, 5.2)
GET    /api/admin/audit/             # Query audit logs
GET    /api/admin/audit/export       # Export compliance report

# SSO Configuration (Story 2.2)
GET    /api/admin/sso/config         # Get SSO configuration
PUT    /api/admin/sso/config         # Update SSO configuration
POST   /api/v1/sso/login             # SSO-initiated login
POST   /api/v1/sso/callback          # IdP callback (SAML/OIDC)
```

---

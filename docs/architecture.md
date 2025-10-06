# LangBuilder (LangFlow) Brownfield Architecture Document

## Introduction

This document captures the **CURRENT STATE** of the LangBuilder (LangFlow fork) codebase, including technical patterns, existing authentication mechanisms, and areas relevant to implementing the comprehensive RBAC enhancement outlined in the PRD. It serves as a reference for AI agents working on the RBAC feature implementation.

### Document Scope

**Focused on areas relevant to**: Implementing Granular Access Control & RBAC system across workspaces, projects, flows, components, and environments as described in `docs/PRD _ Granular Access Control & RBAC – LangBuilder.md`.

### Change Log

| Date       | Version | Description                 | Author  |
| ---------- | ------- | --------------------------- | ------- |
| 2025-10-04 | 1.0     | Initial brownfield analysis | Winston |

---

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

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

### Enhancement Impact Areas (RBAC Implementation)

Based on the PRD requirements, the following areas will need modification:

#### Database Layer
- `src/backend/base/langflow/services/database/models/user/model.py` - Extend User model with role relationships
- **NEW MODELS NEEDED**:
  - `models/rbac/role.py` - Role definitions
  - `models/rbac/permission.py` - Permission catalog
  - `models/rbac/grant.py` - Role assignments (grants)
  - `models/rbac/group.py` - User groups
  - `models/rbac/service_account.py` - Service accounts
  - `models/rbac/audit_log.py` - RBAC audit logs

#### API Layer
- `src/backend/base/langflow/api/v1/login.py` - SSO integration points
- **NEW API ENDPOINTS NEEDED**:
  - `api/v1/rbac/roles.py` - Role CRUD
  - `api/v1/rbac/permissions.py` - Permission catalog
  - `api/v1/rbac/grants.py` - Role assignments
  - `api/v1/rbac/groups.py` - Group management
  - `api/v1/rbac/service_accounts.py` - Service account management
  - `api/v1/rbac/audit.py` - Audit log queries
  - `api/v1/admin/sso.py` - SSO/SCIM configuration

#### Authorization Middleware
- `src/backend/base/langflow/services/auth/utils.py` - Add RBAC enforcement logic
- **NEW MIDDLEWARE NEEDED**:
  - `middleware/rbac_enforcer.py` - Permission checking middleware
  - `middleware/scope_resolver.py` - Resolve effective permissions with scope hierarchy

#### Existing Resource Endpoints (Require RBAC Guards)
- `api/v1/flows.py` - Add permission checks for flow operations
- `api/v1/projects.py` - Add permission checks for project (folder) operations
- `api/v1/endpoints.py` - Add permission checks for component operations
- `api/v1/users.py` - Add permission checks for user management

#### Frontend Components
- `src/frontend/src/contexts/authContext.tsx` - Extend with permission checking
- **NEW COMPONENTS NEEDED**:
  - `pages/AdminPage/RoleManagement.tsx` - Role management UI
  - `pages/AdminPage/PermissionManagement.tsx` - Permission assignment UI
  - `pages/AdminPage/GroupManagement.tsx` - Group management UI
  - `pages/AdminPage/AuditLog.tsx` - Audit log viewer
  - `pages/Settings/SSOSettings.tsx` - SSO configuration UI
  - `components/PermissionGuard.tsx` - Conditional rendering based on permissions

---

## High Level Architecture

### Technical Summary

LangBuilder is a **Python web application with React frontend** for building language model workflows (LangChain-based). It's a fork/derivative of LangFlow with enterprise enhancements planned.

**Architecture Pattern**: Monolithic backend (FastAPI) + SPA frontend (React), deployed as a single service or containerized.

**Current State**:
- **Authentication**: JWT-based with OAuth2 password flow, optional auto-login for development
- **Authorization**: Basic user/superuser roles ONLY (binary permissions)
- **Database**: SQLAlchemy + SQLModel with async support
- **API**: RESTful with FastAPI, WebSocket support for real-time features
- **State Management**: React Context + Zustand stores

### Actual Tech Stack

| Category        | Technology           | Version       | Notes                                    |
| --------------- | -------------------- | ------------- | ---------------------------------------- |
| **Backend**     |                      |               |                                          |
| Runtime         | Python               | 3.10-3.13     | Type hints, async/await                  |
| Framework       | FastAPI              | (via deps)    | Async ASGI framework                     |
| ORM             | SQLModel/SQLAlchemy  | >=2.0.38      | Async session support                    |
| Database        | SQLite/PostgreSQL    | Varies        | Configurable via env (default SQLite)    |
| Authentication  | python-jose          | (JWT)         | JWT token generation/validation          |
| Password Hash   | cryptography/Fernet  | (via deps)    | Password hashing                         |
| Migration       | Alembic              | (included)    | Database migrations                      |
| Validation      | Pydantic             | v2            | Data validation via SQLModel             |
| **Frontend**    |                      |               |                                          |
| Runtime         | Node.js              | 18+           | Development only                         |
| Framework       | React                | 18.3.1        | Functional components, hooks             |
| Build Tool      | Vite                 | 5.4.19        | Fast dev server, HMR                     |
| State Mgmt      | Zustand              | 4.5.2         | Lightweight state management             |
| UI Library      | Radix UI + Tailwind  | Latest        | Headless components + utility CSS        |
| Routing         | React Router         | 6.23.1        | Client-side routing                      |
| HTTP Client     | Axios                | 1.7.4         | API requests                             |
| Type Checking   | TypeScript           | 5.4.5         | Strict mode                              |
| **DevOps**      |                      |               |                                          |
| Package Manager | uv (backend)         | Latest        | Fast Python package manager              |
| Package Manager | npm (frontend)       | Latest        | Node.js package manager                  |
| Build System    | Make                 | GNU Make      | Unified dev commands                     |
| Containerization| Docker               | Latest        | Multi-service docker-compose             |

### Repository Structure Reality Check

- **Type**: Monorepo (backend + frontend in single repo)
- **Package Manager**: `uv` for Python, `npm` for Node.js
- **Notable**: Frontend builds static files that are served by backend in production

---

## Source Tree and Module Organization

### Project Structure (Actual)

```text
LangBuilder/
├── src/
│   ├── backend/
│   │   ├── base/langflow/           # Core langflow package
│   │   │   ├── __main__.py          # CLI entry point
│   │   │   ├── main.py              # FastAPI app initialization
│   │   │   ├── server.py            # Server setup
│   │   │   ├── api/                 # REST API routes
│   │   │   │   ├── v1/              # API version 1
│   │   │   │   │   ├── login.py     # Auth endpoints (JWT login, refresh, logout)
│   │   │   │   │   ├── users.py     # User CRUD
│   │   │   │   │   ├── projects.py  # Project (Folder) CRUD
│   │   │   │   │   ├── flows.py     # Flow CRUD and execution
│   │   │   │   │   ├── endpoints.py # Component/endpoint management
│   │   │   │   │   ├── api_key.py   # API key management
│   │   │   │   │   └── ...          # Other resource endpoints
│   │   │   │   └── v2/              # API version 2 (minimal)
│   │   │   ├── services/
│   │   │   │   ├── auth/            # Authentication service
│   │   │   │   │   ├── utils.py     # JWT creation, validation, user auth
│   │   │   │   │   └── service.py   # Auth service interface
│   │   │   │   ├── database/
│   │   │   │   │   ├── models/      # SQLModel database models
│   │   │   │   │   │   ├── user/    # User, UserCreate, UserRead, UserUpdate
│   │   │   │   │   │   ├── flow/    # Flow model (workflows)
│   │   │   │   │   │   ├── folder/  # Folder model (projects)
│   │   │   │   │   │   ├── api_key/ # API key model
│   │   │   │   │   │   ├── variable/# Global variables
│   │   │   │   │   │   ├── message/ # Chat messages
│   │   │   │   │   │   └── ...      # Other models
│   │   │   │   │   └── service.py   # Database service (session management)
│   │   │   │   └── settings/        # Application settings
│   │   │   ├── graph/               # Workflow graph execution engine
│   │   │   ├── components/          # LangChain component library
│   │   │   ├── schema/              # Pydantic schemas
│   │   │   └── utils/               # Utility functions
│   │   ├── langflow/                # Wrapper package (minimal)
│   │   └── tests/                   # Backend tests
│   └── frontend/
│       ├── src/
│       │   ├── index.tsx            # React entry point
│       │   ├── App.tsx              # Root component
│       │   ├── routes.tsx           # React Router configuration
│       │   ├── contexts/
│       │   │   └── authContext.tsx  # Auth state (JWT tokens, user data)
│       │   ├── stores/              # Zustand stores
│       │   │   ├── authStore.ts     # Auth state
│       │   │   └── ...              # Other stores
│       │   ├── pages/               # Page components
│       │   │   ├── AdminPage/       # Admin UI (superuser only)
│       │   │   ├── FlowPage/        # Flow editor
│       │   │   ├── MainPage/        # Dashboard
│       │   │   └── ...
│       │   ├── components/          # Reusable components
│       │   ├── controllers/API/     # API client functions
│       │   └── types/               # TypeScript type definitions
│       ├── package.json             # Frontend dependencies
│       └── vite.config.mts          # Vite build configuration
├── docs/                            # Documentation
│   ├── README.md                    # Docs index
│   ├── prd.md                       # PRD location (currently named differently)
│   └── ...
├── docker/                          # Docker configurations
├── scripts/                         # Utility scripts
├── pyproject.toml                   # Python project metadata & deps
├── Makefile                         # Backend dev commands
├── Makefile.frontend                # Frontend dev commands
└── .env.example                     # Environment variable template
```

### Key Modules and Their Purpose

#### Backend Core Modules

**`src/backend/base/langflow/services/auth/`**
- **Purpose**: JWT-based authentication
- **Current Implementation**:
  - `utils.py`: JWT token creation/validation, password verification, user authentication
  - OAuth2 password bearer flow
  - API key authentication (header/query param)
  - Auto-login mode for development
- **CRITICAL**: No RBAC or fine-grained authorization. Only checks `is_superuser` flag.
- **Enhancement Needed**: Add RBAC enforcement, SSO integration, SCIM provisioning

**`src/backend/base/langflow/services/database/models/user/`**
- **Purpose**: User data model
- **Current Fields**:
  - `id` (UUID), `username`, `password` (hashed), `is_active`, `is_superuser`
  - `profile_image`, `store_api_key`, `last_login_at`
  - **Relationships**: `api_keys`, `flows`, `variables`, `folders`
- **CRITICAL**: No group membership, no role assignments
- **Enhancement Needed**: Add relationships to roles, groups, grants

**`src/backend/base/langflow/services/database/models/folder/`**
- **Purpose**: Project/Folder organization (equivalent to "Projects" in PRD)
- **Current Fields**:
  - `id`, `name`, `description`, `parent_id` (hierarchical), `user_id`
  - `auth_settings` (JSON field - currently unused)
- **Relationships**: `flows` (one-to-many), `children` (self-referential)
- **CRITICAL**: Projects are currently user-scoped only (no sharing/collaboration)
- **Enhancement Needed**: Leverage `auth_settings` for project-level RBAC config, add scope-based permissions

**`src/backend/base/langflow/services/database/models/flow/`**
- **Purpose**: Workflow definitions (DAG of components)
- **Current Fields**:
  - `id`, `name`, `description`, `data` (JSON graph), `user_id`, `folder_id`
  - `is_component` (boolean), `webhook`, `endpoint_name`, `mcp_enabled`
  - `access_type` (Enum: PRIVATE/PUBLIC) - basic access control
  - `locked` (boolean - prevents editing)
- **CRITICAL**: Access control is binary (public/private), no fine-grained permissions
- **Enhancement Needed**: Add scope-based permissions (read/update/delete/export/deploy)

**`src/backend/base/langflow/api/v1/`**
- **Purpose**: RESTful API endpoints
- **Current Endpoints**:
  - `login.py`: `/login`, `/auto_login`, `/refresh`, `/logout`
  - `users.py`: User CRUD (superuser only)
  - `projects.py`: Project CRUD (user's own projects)
  - `flows.py`: Flow CRUD, execution
  - `endpoints.py`: Component/endpoint management
  - `api_key.py`: API key generation
- **CRITICAL**: Authorization is basic (user owns resource or is superuser)
- **Enhancement Needed**: Add RBAC middleware to all endpoints, new RBAC admin endpoints

#### Frontend Core Modules

**`src/frontend/src/contexts/authContext.tsx`**
- **Purpose**: Global auth state (JWT tokens, user data)
- **Current State**:
  - Stores `accessToken`, `refreshToken`, `apiKey`, `userData`
  - Provides `login()`, `logout()`, `getUser()` functions
  - Uses cookies for token storage
- **CRITICAL**: No permission checking, no role awareness
- **Enhancement Needed**: Add permission checking helpers, role/permission state

**`src/frontend/src/stores/authStore.ts`**
- **Purpose**: Zustand store for auth (supplemental to context)
- **Current State**: `isAdmin` (boolean), `isAuthenticated`
- **Enhancement Needed**: Add `permissions`, `roles`, `effectivePermissions` state

**`src/frontend/src/pages/AdminPage/`**
- **Purpose**: Superuser administration UI
- **Current Features**: User management, system settings
- **Enhancement Needed**: Add RBAC management UI (roles, permissions, groups, audit logs)

---

## Data Models and APIs

### Data Models

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

### API Specifications

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

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Authorization System is Too Simple**
   - **Location**: `src/backend/base/langflow/services/auth/utils.py`
   - **Issue**: Only checks `is_superuser` boolean. No fine-grained permissions.
   - **Impact**: Cannot implement RBAC without major refactoring.
   - **Workaround**: Most endpoints check `user_id == resource.user_id OR is_superuser`.

2. **No Multi-Tenancy / Workspace Isolation**
   - **Issue**: Users can only see their own resources or all resources (if superuser).
   - **Impact**: Cannot implement workspace/project-based collaboration.
   - **PRD Requirement**: Workspaces, Projects, Flows need scope-based RBAC.

3. **API Key Scoping Missing**
   - **Location**: `src/backend/base/langflow/services/database/models/api_key/model.py`
   - **Issue**: API keys are global to user, not scoped to resources or permissions.
   - **PRD Requirement**: Story 4.2 requires scoped tokens.

4. **Folder `auth_settings` Field Unused**
   - **Location**: `src/backend/base/langflow/services/database/models/folder/model.py:14-18`
   - **Issue**: JSON field exists but no code reads/writes it.
   - **Opportunity**: Can be used for project-level RBAC overrides.

5. **No Audit Logging**
   - **Issue**: No immutable audit trail of user actions or RBAC changes.
   - **PRD Requirement**: Story 5.1 requires comprehensive audit logging.

6. **Frontend Permission Checks Inconsistent**
   - **Issue**: UI elements hidden/shown based on `isAdmin` boolean only.
   - **Impact**: Cannot implement granular UI permission guards.

### Workarounds and Gotchas

- **Auto-Login Mode**: `LANGFLOW_AUTO_LOGIN=true` bypasses authentication for development. **Do NOT use in production.** Use `LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true` for safer alternative (being deprecated in v1.6).

- **Database Migrations**: Use Alembic (`src/backend/base/langflow/alembic/`). Always generate migration after model changes: `alembic revision --autogenerate -m "description"`.

- **Folder vs Project Terminology**: Code uses "Folder", PRD uses "Project". They are the same entity (`Folder` model represents projects).

- **Environment Concept Missing**: PRD mentions "Environment" as a scope level (Story 2.1 @AC8), but no `Environment` model exists in codebase. This is a new concept to be added.

- **Component-Level Permissions**: PRD Story 2.1 @AC7 requires component-level permissions, but components are embedded in Flow `data` (JSON), not separate database entities. May need architectural decision on how to scope permissions to individual components.

---

## Integration Points and External Dependencies

### External Services (Planned)

Based on PRD, these integrations are REQUIRED but NOT YET IMPLEMENTED:

| Service       | Purpose                  | Integration Type | PRD Story | Status      |
| ------------- | ------------------------ | ---------------- | --------- | ----------- |
| SSO (SAML/OIDC) | Enterprise authentication | SAML 2.0/OIDC    | Story 2.2 | Not started |
| SCIM Provider | User/group provisioning  | SCIM 2.0 API     | Story 2.3 | Not started |
| SIEM/SOC      | Audit event streaming    | Webhook/Kafka    | NFR 5.7   | Not started |

### Internal Integration Points

**Database**:
- Configurable via `DATABASE_URL` env var
- Default: SQLite (`langflow.db`)
- Production: PostgreSQL recommended
- Async sessions via SQLModel/SQLAlchemy

**Frontend ↔ Backend Communication**:
- REST API on port 7860 (default)
- WebSocket for real-time flow execution updates (`/api/v1/chat`)
- CORS configured via settings
- Authentication via JWT cookies or API key headers

**Background Jobs**:
- Currently minimal async task handling
- **Needed for RBAC**: SCIM sync, audit log processing, token cleanup

---

## Development and Deployment

### Local Development Setup

**Prerequisites**:
- Python 3.10-3.13
- Node.js 18+ & npm
- `pipx` (optional, for `uv` installation)

**Steps** (from README):

```bash
# 1. Clone repository
git clone <repo-url>
cd LangBuilder

# 2. Install dependencies (backend + frontend)
make init

# 3. Run backend dev server (port 7860)
make backend

# 4. Run frontend dev server (port 3000, proxies to backend)
make frontend
```

**Environment Configuration**:
- Copy `.env.example` to `.env` in project root
- Key variables:
  - `LANGFLOW_DATABASE_URL` - Database connection string
  - `LANGFLOW_SECRET_KEY` - JWT signing secret
  - `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD` - Initial admin user
  - `LANGFLOW_AUTO_LOGIN` - Auto-login mode (dev only)

### Build and Deployment Process

**Build Frontend Static Files**:
```bash
make build_frontend
# Outputs to src/backend/base/langflow/frontend/ (served by backend)
```

**Production Build**:
```bash
# Backend package
uv build
pip install dist/*.whl

# Or Docker
docker build -t langbuilder .
docker run -p 7860:7860 langbuilder
```

**Deployment**:
- Single Python package includes both backend and frontend static files
- Typically deployed as Docker container or via render.yaml (Render.com)
- No separate frontend deployment needed

**Database Migrations**:
```bash
# Generate migration
cd src/backend/base/langflow
alembic revision --autogenerate -m "Add RBAC models"

# Apply migrations
alembic upgrade head
```

---

## Testing Reality

### Current Test Coverage

**Backend**:
- Location: `src/backend/tests/`
- Framework: pytest
- Coverage: Partial (unit tests for core components, integration tests minimal)
- Run: `make unit_tests`

**Frontend**:
- Location: `src/frontend/tests/`
- Framework: Jest + React Testing Library, Playwright (E2E)
- Coverage: Minimal
- Run: `npm test` (unit), `npm run test:e2e` (E2E)

**Missing Test Coverage for RBAC**:
- No tests for authorization logic (because it barely exists)
- No tests for permission enforcement
- No tests for scope resolution

**Testing Strategy for RBAC Implementation**:
1. Write unit tests for permission catalog, role builder, grant resolver
2. Write integration tests for RBAC enforcement at API level
3. Write E2E tests for Admin UI (role/permission management)
4. Add performance tests for permission evaluation (NFR: ≤100ms p95)

---

## RBAC Enhancement - Impact Analysis

### Architectural Gaps to Address

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

### Files That Will Need Modification

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

### New Files/Modules Needed

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

### Integration Considerations

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

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

**Backend Development**:
```bash
make init              # Install all dependencies
make backend           # Start backend dev server (auto-reload)
make unit_tests        # Run backend unit tests
make test              # Run all backend tests
make format            # Format Python code (ruff)
make lint              # Lint Python code
```

**Frontend Development**:
```bash
make frontend          # Start frontend dev server (Vite)
make build_frontend    # Build frontend static files
npm run type-check     # TypeScript type checking
npm run format         # Format with Biome
npm run test           # Run Jest tests
```

**Database**:
```bash
cd src/backend/base/langflow
alembic revision --autogenerate -m "description"  # Generate migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
```

**Docker**:
```bash
docker-compose up       # Run full stack in Docker
docker-compose build    # Rebuild containers
```

### Debugging and Troubleshooting

**Backend Logs**:
- Logs output to console (loguru)
- Set `LANGFLOW_LOG_LEVEL=DEBUG` for verbose logging
- Check `logs/` directory if file logging is enabled

**Frontend Dev Tools**:
- React DevTools browser extension
- Network tab for API request inspection
- Zustand DevTools (if enabled)

**Database Inspection**:
```bash
# SQLite
sqlite3 langflow.db
.tables
.schema user

# PostgreSQL
psql $DATABASE_URL
\dt
\d+ user
```

**Common Issues**:

1. **Auto-login not working**: Check `LANGFLOW_SUPERUSER` and `LANGFLOW_SUPERUSER_PASSWORD` env vars are set.

2. **CORS errors**: Verify `LANGFLOW_BACKEND_URL` and CORS settings in backend configuration.

3. **Migration conflicts**: If multiple devs create migrations, may need to merge migration files manually.

4. **Frontend build errors**: Clear `node_modules` and `package-lock.json`, then `npm install`.

5. **Database locked (SQLite)**: SQLite doesn't handle concurrent writes well. Use PostgreSQL for multi-user development.

---

## Summary

LangBuilder is a **brownfield Python/React application** with a **simple JWT-based authentication system** and **minimal authorization** (superuser vs regular user). The codebase is well-structured and follows modern patterns (FastAPI, SQLModel, React hooks, TypeScript), making it a solid foundation for RBAC enhancement.

**Key Strengths**:
- Clean separation of concerns (services, models, API, UI)
- Modern async Python stack
- Type safety (Pydantic, TypeScript)
- Existing database model relationships

**Key Gaps for RBAC**:
- No fine-grained permission system
- No scope hierarchy (workspace, environment concepts missing)
- No SSO/SCIM integration
- No audit logging
- No API token scoping

**Recommended Implementation Approach**:
1. **Phase 1**: Define RBAC database schema, create models (Roles, Permissions, Grants, Groups)
2. **Phase 2**: Build permission evaluation engine, integrate with existing auth
3. **Phase 3**: Add RBAC API endpoints, admin UI
4. **Phase 4**: Implement SSO/SCIM integrations
5. **Phase 5**: Add audit logging, compliance reporting
6. **Phase 6**: IaC support (YAML/Terraform)

The PRD's modular epic structure (Epics 1-5) aligns well with this phased approach. Each epic can be implemented incrementally while maintaining backward compatibility with existing user-based access control during transition.

# Source Tree and Module Organization

## Project Structure (Actual)

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

## Key Modules and Their Purpose

### Backend Core Modules

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

### Frontend Core Modules

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

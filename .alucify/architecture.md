# LangBuilder Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the LangBuilder codebase as of October 2025. LangBuilder is a full-stack AI agent platform (CloudGeometry distribution of the open-source project) that enables building, deploying, and managing LLM-powered workflows through a visual drag-and-drop interface and programmable framework.

CloudGeometry provides enterprise-ready enhancements, managed services, and deployment support for LangBuilder, building on the popular open-source foundation.

This is NOT an aspirational document - it reflects the reality of the system including technical debt, workarounds, and actual implementation patterns.

### Document Scope

Comprehensive documentation of the entire LangBuilder system including:
- Backend Python/FastAPI services
- Frontend React/TypeScript application
- Component architecture (82 active component categories, 24 deactivated)
- Database layer and models
- API structure and endpoints
- Build and deployment systems

### Change Log

| Date       | Version | Description                     | Author         |
| ---------- | ------- | ------------------------------- | -------------- |
| 2025-10-23 | 1.0     | Initial brownfield analysis     | Claude Code AI |
| 2025-10-23 | 1.1     | Audit corrections applied       | Claude Code AI |
| 2025-10-23 | 1.2     | Minor enhancements & clarifications | Claude Code AI |

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

**Backend Entry Points:**
- **Main Application Factory**: `src/backend/base/langbuilder/main.py` - FastAPI app creation and middleware setup
- **CLI Entry Point (Direct)**: `src/backend/base/langbuilder/__main__.py` - Main CLI implementation (849 lines, Typer-based)
- **CLI Launcher (macOS)**: `src/backend/base/langbuilder/langbuilder_launcher.py` - macOS fork-safety wrapper for Objective-C compatibility
- **CLI Commands**:
  - `langbuilder` - Main package entry point (via langbuilder_launcher for macOS compatibility)
  - `langbuilder-base` - Direct entry to base package (via __main__)
  - Available commands: `run`, `superuser`, `migration`, `api_key`, `copy_db`

**Frontend Entry Points:**
- **React Root**: `src/frontend/src/index.tsx` - React application initialization
- **Main App Component**: `src/frontend/src/App.tsx` - Root component with routing
- **API Client**: `src/frontend/src/controllers/API/api.tsx` - Axios client configuration
- **Vite Config**: `src/frontend/vite.config.mts` - Build configuration and dev proxy

**Configuration:**
- **Backend Config**: `.env.example` - Environment variable template
- **Python Dependencies**: `pyproject.toml` - Main package configuration
- **Python Base Dependencies**: `src/backend/base/pyproject.toml` - Base package configuration
- **Frontend Dependencies**: `src/frontend/package.json` - npm dependencies
- **Build Orchestration**: `Makefile` - Primary build tool
- **Frontend Build**: `Makefile.frontend` - Frontend-specific commands

**API Definitions:**
- **API v1 Endpoints**: `src/backend/base/langbuilder/api/v1/` - REST API routes (22 endpoint files)
- **API v2 Endpoints**: `src/backend/base/langbuilder/api/v2/` - V2 API routes (files, MCP)
- **Flow Management**: `src/backend/base/langbuilder/api/v1/flows.py`
- **Chat/Execution**: `src/backend/base/langbuilder/api/v1/chat.py`
- **MCP Server v1**: `src/backend/base/langbuilder/api/v1/mcp_projects.py`
- **MCP Server v2**: `src/backend/base/langbuilder/api/v2/mcp.py`
- **API Schemas**: `src/backend/base/langbuilder/api/v1/schemas.py`

**Database Models:**
- **Flow Model**: `src/backend/base/langbuilder/services/database/models/flow/model.py`
- **User Model**: `src/backend/base/langbuilder/services/database/models/user/`
- **Folder Model**: `src/backend/base/langbuilder/services/database/models/folder/`
- **Message Model**: `src/backend/base/langbuilder/services/database/models/message/`
- **File Model**: `src/backend/base/langbuilder/services/database/models/file/`
- **Variable Model**: `src/backend/base/langbuilder/services/database/models/variable/`
- **Transactions Model**: `src/backend/base/langbuilder/services/database/models/transactions/`
- **Vertex Builds Model**: `src/backend/base/langbuilder/services/database/models/vertex_builds/`

**Core Business Logic:**
- **Component System**: `src/backend/base/langbuilder/components/` - 82 active component categories
  - Additional: 24 deactivated components in `deactivated/` subdirectory
- **Flow Execution**: `src/backend/base/langbuilder/services/flow/` - Flow runner service
- **Graph Engine**: `src/backend/base/langbuilder/graph/` - Graph execution logic
- **Session Management**: `src/backend/base/langbuilder/services/session/`

**Development Rules:**
- **Backend Guidelines**: `.cursor/rules/backend_development.mdc`
- **Frontend Guidelines**: `.cursor/rules/frontend_development.mdc`
- **Testing Guidelines**: `.cursor/rules/testing.mdc`

## High Level Architecture

### Technical Summary

LangBuilder is a monolithic full-stack application with clear frontend/backend separation, communicating via REST API. The backend is built on FastAPI with async Python, using SQLAlchemy for database abstraction and LangChain for AI workflow orchestration. The frontend is a modern React SPA with TypeScript, using Vite for builds and React Flow for visual flow editing.

**Architecture Pattern**: Traditional client-server with API gateway pattern
**Communication**: RESTful HTTP/HTTPS with WebSocket support for real-time updates
**Data Flow**: User → React UI → Axios → FastAPI → Services → Database/LLMs

### Actual Tech Stack

#### Backend Stack

| Category              | Technology             | Version       | Notes                                      |
| --------------------- | ---------------------- | ------------- | ------------------------------------------ |
| Language              | Python                 | 3.10-3.13     | Multi-version support required             |
| Package Manager       | uv                     | >=0.4         | **REQUIRED** - faster than pip             |
| Web Framework         | FastAPI                | Latest        | Async-first ASGI framework                 |
| Server                | Uvicorn                | Latest        | ASGI server with auto-reload               |
| ORM                   | SQLAlchemy/SQLModel    | >=2.0.38      | Type-safe ORM with Pydantic integration    |
| Database (default)    | SQLite                 | 3.x           | File-based, development default            |
| Database (production) | PostgreSQL             | 13+           | Optional, recommended for production       |
| Migrations            | Alembic                | Latest        | Database schema migrations                 |
| Orchestration         | LangChain              | 0.3.23        | **CORE DEPENDENCY** - AI workflow engine   |
| Caching               | Redis (optional)       | >=5.2.1       | Optional, falls back to in-memory          |
| Validation            | Pydantic               | 2.x           | Data validation and settings management    |
| Logging               | Loguru                 | Latest        | Structured logging                         |
| Testing               | pytest                 | Latest        | Async test support with pytest-asyncio     |
| Type Checking         | mypy                   | Latest        | Static type analysis                       |
| Formatting            | Ruff                   | Latest        | Fast Python formatter/linter               |
| Observability         | LangSmith, LangFuse    | Latest        | Optional AI observability integrations     |

**Key LangChain Integrations:**
- `langchain-openai>=0.2.12` - OpenAI models
- `langchain-anthropic==0.3.14` - Anthropic/Claude models
- `langchain-google-genai==2.0.6` - Google Gemini
- `langchain-cohere==0.3.3` - Cohere models
- `langchain-mistralai==0.2.3` - Mistral AI
- `langchain-groq==0.2.1` - Groq
- `langchain-ollama==0.2.1` - Ollama local models
- `langchain-pinecone>=0.2.8` - Pinecone vector store
- `langchain-chroma==0.1.4` - Chroma vector store
- `langchain-community~=0.3.21` - Community integrations

#### Frontend Stack

| Category           | Technology              | Version  | Notes                                |
| ------------------ | ----------------------- | -------- | ------------------------------------ |
| Language           | TypeScript              | ^5.4.5   | Strict mode enabled                  |
| Runtime            | Node.js                 | 22.12    | LTS version required                 |
| Package Manager    | npm                     | 10.9     | Standard package manager             |
| Framework          | React                   | 18.3.1   | Functional components with hooks     |
| Build Tool         | Vite                    | 5.4.19   | Fast build and HMR                   |
| Compiler           | SWC                     | Latest   | Rust-based fast compilation          |
| State Management   | Zustand                 | 4.5.2    | Lightweight store                    |
| Data Fetching      | React Query (TanStack)  | 5.49.2   | Server state management              |
| HTTP Client        | Axios                   | 1.7.4    | Promise-based HTTP client            |
| Routing            | React Router DOM        | 6.23.1   | Client-side routing                  |
| UI Framework       | shadcn/ui + Radix UI    | Latest   | Accessible component library         |
| Styling            | Tailwind CSS            | 3.4.4    | Utility-first CSS                    |
| Form Handling      | React Hook Form         | 7.52.0   | Performant form validation           |
| Flow Visualization | React Flow (@xyflow)    | 12.3.6   | **CORE** - Visual flow editor        |
| Icons              | Lucide React            | 0.503.0  | Icon library                         |
| Testing (Unit)     | Jest                    | 30.0.3   | JavaScript testing framework         |
| Testing (E2E)      | Playwright              | 1.52.0   | Browser automation                   |
| Linting/Formatting | Biome                   | 2.1.1    | Rust-based fast formatter            |

### Repository Structure Reality Check

- **Type**: Monorepo with uv workspace
- **Package Manager**: uv for backend, npm for frontend
- **Build Tool**: Makefile orchestrates all build steps
- **Directory Structure**: Backend in `src/backend/`, frontend in `src/frontend/`

**Notable Structure Decisions:**
- Backend is split into two packages: `langbuilder` (main) and `langbuilder-base` (core)
- Frontend builds into `src/frontend/build/` which is copied to `src/backend/base/langbuilder/frontend/` for packaging
- Tests are in `src/backend/tests/` for backend, frontend tests adjacent to components
- Docker configurations in `docker/` directory
- Documentation in `docs/` (not comprehensive)

## Source Tree and Module Organization

### Project Structure (Actual)

```
langbuilder-cg.git/
├── .alucify/                       # Architecture documentation (NEW)
├── .cursor/                        # Cursor AI rules
│   └── rules/                      # Development guidelines
│       ├── backend_development.mdc
│       ├── frontend_development.mdc
│       ├── testing.mdc
│       └── icons.mdc
├── .github/                        # GitHub workflows (if present)
├── docker/                         # Docker configurations
│   ├── build_and_push.Dockerfile   # Main Dockerfile
│   ├── build_and_push_backend.Dockerfile
│   ├── frontend/                   # Frontend Docker configs
│   ├── dev.docker-compose.yml      # Dev compose
│   └── cdk-docker-compose.yml      # CDK deployment
├── docs/                           # Documentation (minimal)
├── scripts/                        # Utility scripts
│   ├── setup/                      # Setup scripts
│   └── aws/                        # AWS deployment scripts
├── src/
│   ├── backend/                    # Python backend
│   │   ├── base/                   # langbuilder-base package
│   │   │   ├── pyproject.toml      # Base package config
│   │   │   └── langbuilder/        # Core backend code
│   │   │       ├── __main__.py     # CLI entry point
│   │   │       ├── main.py         # FastAPI app factory
│   │   │       ├── api/            # API routers
│   │   │       │   ├── v1/         # API version 1 (22 endpoint files)
│   │   │       │   │   ├── chat.py          # Chat/execution endpoints
│   │   │       │   │   ├── flows.py         # Flow CRUD
│   │   │       │   │   ├── endpoints.py     # Endpoint management
│   │   │       │   │   ├── mcp_projects.py  # MCP server v1
│   │   │       │   │   ├── login.py         # Authentication
│   │   │       │   │   ├── users.py         # User management
│   │   │       │   │   ├── store.py         # Component store
│   │   │       │   │   ├── validate.py      # Validation endpoints
│   │   │       │   │   ├── variable.py      # Global variables
│   │   │       │   │   ├── voice_mode.py    # Voice mode
│   │   │       │   │   ├── callback.py      # Callbacks
│   │   │       │   │   ├── monitor.py       # Monitoring
│   │   │       │   │   └── ...
│   │   │       │   └── v2/         # API version 2 (ACTIVE)
│   │   │       │       ├── files.py         # V2 file operations
│   │   │       │       └── mcp.py           # V2 MCP server
│   │   │       ├── components/     # **CRITICAL** - 80+ component categories
│   │   │       │   ├── agents/     # Agent components
│   │   │       │   ├── models/     # LLM model wrappers
│   │   │       │   ├── prompts/    # Prompt templates
│   │   │       │   ├── tools/      # Tool components
│   │   │       │   ├── vectorstores/ # Vector DB integrations
│   │   │       │   ├── data/       # Data processing
│   │   │       │   ├── embeddings/ # Embedding models
│   │   │       │   ├── input_output/ # I/O components
│   │   │       │   ├── processing/ # Text processing
│   │   │       │   ├── anthropic/  # Claude integrations
│   │   │       │   ├── openai/     # OpenAI integrations
│   │   │       │   ├── google/     # Google integrations
│   │   │       │   ├── amazon/     # AWS integrations
│   │   │       │   ├── azure/      # Azure integrations
│   │   │       │   ├── crewai/     # CrewAI integration
│   │   │       │   ├── composio/   # Composio tools
│   │   │       │   └── ... (70+ more categories)
│   │   │       ├── services/       # Core services
│   │   │       │   ├── auth/       # Authentication service
│   │   │       │   ├── database/   # Database service & models
│   │   │       │   │   └── models/ # SQLModel definitions
│   │   │       │   │       ├── flow/           # Flow models
│   │   │       │   │       ├── user/           # User models
│   │   │       │   │       ├── folder/         # Folder models
│   │   │       │   │       ├── message/        # Message models
│   │   │       │   │       ├── api_key/        # API key models
│   │   │       │   │       ├── file/           # File upload models
│   │   │       │   │       ├── variable/       # Global variable models
│   │   │       │   │       ├── transactions/   # Transaction models
│   │   │       │   │       └── vertex_builds/  # Vertex build history
│   │   │       │   ├── flow/       # Flow execution service
│   │   │       │   ├── cache/      # Caching service
│   │   │       │   ├── session/    # Session management
│   │   │       │   ├── chat/       # Chat service
│   │   │       │   ├── socket/     # WebSocket service
│   │   │       │   ├── settings/   # Settings service
│   │   │       │   ├── job_queue/  # Background job queue
│   │   │       │   ├── deps.py     # Dependency injection
│   │   │       │   └── manager.py  # Service manager
│   │   │       ├── graph/          # Graph execution engine
│   │   │       ├── schema/         # Pydantic schemas
│   │   │       ├── interface/      # UI interface utilities
│   │   │       ├── processing/     # Flow processing logic
│   │   │       ├── logging/        # Logging configuration
│   │   │       ├── middleware/     # FastAPI middleware
│   │   │       ├── initial_setup/  # DB init & starter projects
│   │   │       ├── base/           # Base classes
│   │   │       ├── custom/         # Custom components
│   │   │       └── helpers/        # Utility helpers
│   │   ├── tests/                  # Backend tests
│   │   │   ├── unit/               # Unit tests
│   │   │   │   ├── components/     # Component tests
│   │   │   │   ├── template/       # Starter project tests
│   │   │   │   └── ...
│   │   │   ├── integration/        # Integration tests
│   │   │   ├── locust/             # Load tests
│   │   │   ├── conftest.py         # Pytest fixtures
│   │   │   └── base.py             # Test base classes
│   │   └── langbuilder/            # Main package wrapper
│   │       └── pyproject.toml      # Main package config
│   └── frontend/                   # React frontend
│       ├── package.json            # npm dependencies
│       ├── vite.config.mts         # Vite configuration
│       ├── tsconfig.json           # TypeScript config
│       ├── tailwind.config.ts      # Tailwind config
│       ├── public/                 # Static assets
│       └── src/
│           ├── index.tsx           # React entry point
│           ├── App.tsx             # Main app component
│           ├── pages/              # Page components (15 pages)
│           │   ├── FlowPage/       # Flow editor page
│           │   ├── MainPage/       # Main dashboard
│           │   ├── SettingsPage/   # Settings
│           │   ├── Playground/     # Interactive playground
│           │   ├── StorePage/      # Component marketplace
│           │   ├── LoginPage/      # Authentication
│           │   ├── AdminPage/      # Admin dashboard
│           │   └── ... (8 more pages)
│           ├── components/         # Reusable components
│           │   ├── ui/             # shadcn UI components
│           │   ├── core/           # Core components
│           │   ├── common/         # Common components
│           │   └── authorization/  # Auth components
│           ├── controllers/        # API integration
│           │   ├── API/            # Axios client
│           │   │   ├── api.tsx     # API client setup
│           │   │   └── queries/    # React Query hooks
│           │   └── ...
│           ├── stores/             # Zustand stores (17 stores)
│           │   ├── authStore.ts    # Auth state
│           │   ├── flowStore.ts    # Current flow state
│           │   ├── flowsManagerStore.ts # Multiple flows management
│           │   ├── utilityStore.ts # UI utilities
│           │   ├── darkStore.ts    # Theme state
│           │   ├── alertStore.ts   # Alerts/notifications
│           │   ├── messagesStore.ts # Chat messages
│           │   ├── foldersStore.tsx # Folder organization
│           │   ├── tweaksStore.ts  # Runtime parameter tweaks
│           │   ├── typesStore.ts   # Component types cache
│           │   ├── storeStore.ts   # Component marketplace
│           │   ├── voiceStore.ts   # Voice mode state
│           │   ├── locationStore.ts # Navigation/routing
│           │   ├── durationStore.ts # Duration tracking
│           │   ├── shortcuts.ts    # Keyboard shortcuts
│           │   └── globalVariablesStore/ # Global variables
│           ├── contexts/           # React contexts
│           ├── CustomNodes/        # Flow node components
│           ├── CustomEdges/        # Flow edge components
│           ├── modals/             # Modal dialogs
│           ├── icons/              # SVG icons (130+)
│           ├── types/              # TypeScript types
│           ├── utils/              # Utility functions
│           ├── hooks/              # Custom React hooks
│           ├── alerts/             # Alert/notification components
│           ├── shared/             # Shared utilities
│           ├── style/              # Global styles
│           ├── constants/          # Frontend constants
│           ├── helpers/            # Helper functions
│           ├── assets/             # Static assets
│           ├── routes.tsx          # Route definitions
│           ├── flow_constants.tsx  # Flow-specific constants
│           └── customization/      # Config & customization
├── pyproject.toml                  # Main Python project config
├── uv.lock                         # Locked Python dependencies
├── Makefile                        # **PRIMARY BUILD TOOL**
├── Makefile.frontend               # Frontend-specific make targets
├── .env.example                    # Environment variable template
├── CLAUDE.md                       # Claude Code guidance
└── README.md                       # Project README

```

### Key Modules and Their Purpose

#### Backend Core Modules

**Service Layer** (`src/backend/base/langbuilder/services/`):
- **Pattern**: Service layer pattern with dependency injection
- **database/**: SQLModel-based database service with models
- **flow/**: Flow execution service using LangChain runnables
- **cache/**: Caching abstraction (Redis, in-memory, async)
- **session/**: Session management for stateful flows
- **chat/**: Chat message handling and history
- **auth/**: JWT-based authentication
- **settings/**: Application settings with Pydantic
- **socket/**: WebSocket connections for real-time updates
- **job_queue/**: Background task processing

**Component System** (`src/backend/base/langbuilder/components/`):
- **Pattern**: Plugin-like architecture with auto-discovery via `__init__.py`
- **80+ categories**: Each subdirectory is a component category
- **Auto-reload**: Backend restarts when components change
- **Custom fields**: Each component defines its input/output schema
- **Version tracking**: Components track backward compatibility

**API Layer** (`src/backend/base/langbuilder/api/v1/`):
- **chat.py**: Flow execution, streaming, and build endpoints (25KB file - complex)
- **flows.py**: CRUD operations for flows (21KB)
- **endpoints.py**: REST endpoint management for flows (30KB)
- **mcp_projects.py**: MCP server implementation (32KB - significant)
- **login.py**: Authentication endpoints
- **users.py**: User management (admin only)
- **folders.py**: Folder organization
- **files.py**: File upload/download

**Graph Engine** (`src/backend/base/langbuilder/graph/`):
- **Purpose**: Executes flows as directed acyclic graphs
- **Based on**: LangChain's Runnable protocol
- **Supports**: Streaming, session state, tweaks (runtime params)

#### Frontend Core Modules

**State Management** (`src/frontend/src/stores/` - 17 Zustand stores):
- **authStore.ts**: User authentication state, tokens, login/logout
- **flowStore.ts**: Current flow state, nodes, edges, canvas operations
- **flowsManagerStore.ts**: Management of multiple flows
- **utilityStore.ts**: UI state (modals, notifications, loading states)
- **darkStore.ts**: Theme management (light/dark mode)
- **alertStore.ts**: Alert and notification management
- **messagesStore.ts**: Chat message history and state
- **foldersStore.tsx**: Folder organization and hierarchy
- **tweaksStore.ts**: Runtime parameter adjustments (tweaks)
- **typesStore.ts**: Cached component types for performance
- **storeStore.ts**: Component marketplace/store state
- **voiceStore.ts**: Voice mode features and state
- **locationStore.ts**: Navigation and routing state
- **durationStore.ts**: Performance duration tracking
- **shortcuts.ts**: Keyboard shortcut definitions and handlers
- **globalVariablesStore**: Global environment variables management

**API Integration** (`src/frontend/src/controllers/API/`):
- **api.tsx**: Axios instance with interceptors, auth headers, error handling
- **queries/**: React Query hooks for all backend endpoints
- **Pattern**: Each endpoint has a query hook and mutation hook

**Flow Editor** (`src/frontend/src/pages/FlowPage/`):
- **Uses**: React Flow library for visual editing
- **CustomNodes/**: Custom node renderers for each component type
- **CustomEdges/**: Custom edge renderers for connections
- **Pattern**: Canvas-based drag-and-drop with real-time updates

## Data Models and APIs

### Data Models

**Core Models** (see `src/backend/base/langbuilder/services/database/models/`):

Instead of duplicating model definitions, reference actual model files:

- **Flow Model**: `src/backend/base/langbuilder/services/database/models/flow/model.py`
  - Fields: `id`, `name`, `description`, `data` (JSON graph), `user_id`, `folder_id`, `endpoint_name`, `webhook`, `is_component`, `updated_at`, `created_at`
  - Relationships: belongs to user, belongs to folder, has many messages
  - Access: PUBLIC or PRIVATE

- **User Model**: `src/backend/base/langbuilder/services/database/models/user/`
  - JWT-based authentication
  - Superuser support
  - API key management

- **Folder Model**: `src/backend/base/langbuilder/services/database/models/folder/`
  - Hierarchical folder organization
  - User-scoped folders

- **Message Model**: `src/backend/base/langbuilder/services/database/models/message/`
  - Flow execution history
  - Session-based grouping
  - Sender tracking (user, AI, system)

- **API Key Model**: `src/backend/base/langbuilder/services/database/models/api_key/`
  - API key generation and validation
  - User-scoped keys

- **File Model**: `src/backend/base/langbuilder/services/database/models/file/`
  - File upload metadata
  - Associated with flows and messages

- **Variable Model**: `src/backend/base/langbuilder/services/database/models/variable/`
  - Global environment variables
  - User-scoped variable management

- **Transactions Model**: `src/backend/base/langbuilder/services/database/models/transactions/`
  - Database transaction tracking
  - Audit trail

- **Vertex Builds Model**: `src/backend/base/langbuilder/services/database/models/vertex_builds/`
  - Flow vertex execution history
  - Build artifacts and state

### API Specifications

**REST API Base**: `/api/v1/` (22 endpoint files) and `/api/v2/` (2 endpoint files)

**Authentication**:
- `POST /api/v1/login` - Login with username/password, returns JWT
- `GET /api/v1/auto_login` - Auto-login if enabled
- Token-based: Bearer token in Authorization header

**Flow Management** (v1):
- `GET /api/v1/flows/` - List user's flows
- `POST /api/v1/flows/` - Create flow
- `GET /api/v1/flows/{flow_id}` - Get flow details
- `PATCH /api/v1/flows/{flow_id}` - Update flow
- `DELETE /api/v1/flows/{flow_id}` - Delete flow

**Flow Execution** (v1):
- `POST /api/v1/build/{flow_id}/vertices` - Build flow graph
- `POST /api/v1/build/{flow_id}/flow` - Run entire flow
- `GET /api/v1/build/stream/{flow_id}` - Stream execution (SSE)
- `POST /api/v1/build/{job_id}/cancel` - Cancel running build

**Endpoints (REST API for flows)** (v1):
- `POST /api/v1/endpoints/` - Create REST endpoint from flow
- `GET /api/v1/endpoints/` - List endpoints
- `POST /api/v1/run/{endpoint_name}` - Execute flow via endpoint

**MCP Server** (v1 & v2):
- `GET /api/v1/mcp/projects` - List MCP projects (v1)
- `POST /api/v1/mcp/projects` - Create MCP project (v1)
- `GET /api/v1/mcp/sse` - MCP server-sent events (v1)
- `/api/v2/mcp/*` - V2 MCP endpoints (enhanced)

**Files** (v1 & v2):
- `/api/v1/files/*` - File upload/download (v1)
- `/api/v2/files/*` - V2 file operations (enhanced)

**Additional Endpoints** (v1):
- `/api/v1/store/*` - Component marketplace operations
- `/api/v1/validate/*` - Flow validation
- `/api/v1/variables/*` - Global variables CRUD
- `/api/v1/voice_mode/*` - Voice mode features
- `/api/v1/callback/*` - Webhook callbacks
- `/api/v1/monitor/*` - Monitoring and telemetry
- `/api/v1/folders/*` - Folder management
- `/api/v1/users/*` - User management (admin)
- `/api/v1/api_key/*` - API key management

**WebSocket**:
- `WS /api/v1/chat/{client_id}` - WebSocket connection for real-time updates

**API Response Format**:
```json
{
  "data": { ... },
  "message": "Success",
  "status_code": 200
}
```

**Error Response Format**:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## Technical Debt and Known Issues

### Critical Technical Debt

1. **Database Migration Management**
   - **Location**: Alembic migrations in `src/backend/base/langbuilder/alembic/`
   - **Issue**: Manual migration tracking, migrations can be fragile
   - **Impact**: Schema changes require careful coordination
   - **Workaround**: Use `make alembic-revision message="..."` and test thoroughly

2. **Component Version Compatibility**
   - **Location**: All components in `src/backend/base/langbuilder/components/`
   - **Issue**: Must maintain backward compatibility with older flow versions
   - **Impact**: Component changes require `file_names_mapping` for version tracking
   - **Testing**: Component tests require `VersionComponentMapping` fixtures

3. **Test Database Quirks**
   - **Location**: `src/backend/tests/unit/test_database.py`
   - **Issue**: Tests may fail in batch runs but pass individually
   - **Workaround**: Run database tests sequentially if needed
   - **Command**: `uv run pytest src/backend/tests/unit/test_database.py`

4. **Frontend Build Integration**
   - **Location**: `Makefile` targets `build_frontend`
   - **Issue**: Frontend build must complete before backend packaging
   - **Impact**: Build process is sequential, takes time
   - **Workaround**: Build frontend separately during development

5. **Starter Project Auto-formatting**
   - **Location**: `src/backend/base/langbuilder/initial_setup/`
   - **Issue**: Starter project files auto-format after `langbuilder run`
   - **Impact**: Git shows changes to starter projects even if not modified
   - **Workaround**: These changes can be committed or ignored

### Workarounds and Gotchas

1. **Environment Variable Loading**
   - **Issue**: Frontend and backend use different env loading mechanisms
   - **Frontend**: Vite uses `VITE_` prefix, loads from `.env` in project root
   - **Backend**: Uses `.env` directly, no prefix required
   - **Workaround**: Duplicate certain variables with different naming

2. **Port Requirements**
   - **Backend**: Defaults to port 7860 (configurable via `LANGBUILDER_PORT`)
   - **Frontend**: Defaults to port 3000 (configurable via `VITE_PORT`)
   - **Issue**: Port conflicts require manual kill: `lsof -t -i:7860 | xargs kill -9`
   - **Makefile handles this**: `make backend` and `make frontend` auto-kill processes

3. **uv Package Manager Requirement**
   - **CRITICAL**: `uv` is REQUIRED, pip will not work properly
   - **Reason**: Workspace dependencies and lock file format
   - **Install**: `pipx install uv` or `make setup_uv`

4. **Component Discovery**
   - **Issue**: New components not visible until backend restart AND browser refresh
   - **Pattern**: Edit → Save → Wait for backend restart → Refresh browser
   - **Auto-reload**: Backend uses `--reload` flag in development

5. **Format Before Lint**
   - **CRITICAL**: Always run `make format_backend` BEFORE `make lint`
   - **Reason**: Ruff formatter auto-fixes most style issues
   - **Impact**: Running lint first shows errors that formatter would fix
   - **Pre-commit**: Format → Lint → Test

6. **Async Test Patterns**
   - **Issue**: Context variables may not propagate in `asyncio.to_thread`
   - **Testing**: Test both direct event loop execution and threading patterns
   - **Markers**: Use `@pytest.mark.no_blockbuster` to skip blockbuster plugin

## Integration Points and External Dependencies

### External LLM Services

| Service     | Integration Type | Environment Variable     | Components Location                  |
| ----------- | ---------------- | ------------------------ | ------------------------------------ |
| OpenAI      | SDK              | `OPENAI_API_KEY`         | `components/openai/`                 |
| Anthropic   | SDK              | `ANTHROPIC_API_KEY`      | `components/anthropic/`              |
| Google      | SDK              | `GOOGLE_API_KEY`         | `components/google/`                 |
| Cohere      | SDK              | `COHERE_API_KEY`         | `components/cohere/`                 |
| Mistral     | SDK              | `MISTRAL_API_KEY`        | `components/mistralai/`              |
| Groq        | SDK              | `GROQ_API_KEY`           | `components/groq/`                   |
| AWS Bedrock | SDK              | AWS credentials          | `components/amazon/`                 |
| Azure       | SDK              | Azure credentials        | `components/azure/`                  |
| Ollama      | REST API         | `OLLAMA_BASE_URL`        | `components/ollama/`                 |

### Vector Databases

| Service     | Integration Type | Key Files                    | Notes                       |
| ----------- | ---------------- | ---------------------------- | --------------------------- |
| Pinecone    | SDK              | `components/vectorstores/`   | Requires API key            |
| Chroma      | SDK              | `langchain-chroma`           | Can run locally             |
| Weaviate    | SDK              | `weaviate-client==4.10.2`    | Self-hosted or cloud        |
| FAISS       | Library          | `faiss-cpu==1.9.0.post1`     | CPU-only, local             |
| Qdrant      | SDK              | `qdrant-client==1.9.2`       | Self-hosted or cloud        |
| Elasticsearch | SDK           | `elasticsearch==8.16.0`      | Requires running instance   |
| MongoDB     | SDK              | `langchain-mongodb`          | Vector search capability    |

### Observability & Monitoring

| Service   | Purpose       | Integration  | Configuration                        |
| --------- | ------------- | ------------ | ------------------------------------ |
| LangSmith | Tracing       | SDK          | `LANGSMITH_API_KEY`, project config  |
| LangFuse  | Observability | SDK          | `langfuse==2.53.9`                   |
| LangWatch | Monitoring    | SDK          | `langwatch==0.1.16`                  |

### Data Sources & Tools

| Category      | Examples                          | Location                    |
| ------------- | --------------------------------- | --------------------------- |
| Document Loaders | PDF, Markdown, HTML, etc.      | `components/data/`          |
| Web Scrapers  | Spider, Beautiful Soup           | `components/apify/`, etc.   |
| APIs          | Google Calendar, Slack, etc.     | Various component dirs      |
| Databases     | PostgreSQL, MySQL, MongoDB       | `components/data/`          |

### Internal Integration Points

**Frontend → Backend Communication**:
- **Protocol**: HTTP/HTTPS via Axios
- **Base URL**: `http://localhost:7860` (development), configurable via `BACKEND_URL`
- **Proxy**: Vite dev server proxies `/api/*` requests to backend (port 3000 → 7860)
- **Authentication**: JWT Bearer token in `Authorization` header
- **Error Handling**: Axios interceptors handle 401 (re-auth) and 403 (forbidden)

**Backend → Database**:
- **ORM**: SQLAlchemy 2.0 with SQLModel
- **Connection**: Async engine with connection pooling
- **Default**: SQLite file (`langbuilder.db`)
- **Production**: PostgreSQL recommended (`LANGBUILDER_DATABASE_URL`)

**Backend → Cache**:
- **Types**: Redis, AsyncInMemoryCache, ThreadingInMemoryCache
- **Configuration**: `LANGBUILDER_CACHE_TYPE` (async, memory, redis)
- **LangChain Cache**: SQLiteCache for LLM response caching

**Real-time Updates**:
- **WebSocket**: `/api/v1/chat/{client_id}`
- **Server-Sent Events**: `/api/v1/build/stream/{flow_id}` for flow execution
- **MCP SSE**: `/api/v1/mcp/sse` for MCP server events

## Development and Deployment

### Local Development Setup

**Prerequisites**:
1. **Python 3.10-3.13**: Required version range
2. **uv package manager**: Install with `pipx install uv` or `make setup_uv`
3. **Node.js 22.12 LTS**: Frontend requirement
4. **npm 10.9**: Comes with Node.js

**Initial Setup** (one-time):
```bash
# Install all dependencies
make init

# This runs:
# - make install_backend    (uv sync)
# - make install_frontend   (npm install)
# - uvx pre-commit install  (git hooks)
```

**Development Mode** (daily workflow):

Terminal 1 - Backend:
```bash
make backend                 # Starts on port 7860 with auto-reload
# Or with options:
make backend port=8000       # Custom port
make backend login=true      # Force auto-login
make backend env=.env.local  # Custom env file
```

Terminal 2 - Frontend:
```bash
make frontend                # Starts on port 3000 with HMR
```

**Access**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:7860
- API Docs: http://localhost:7860/api/v1/docs (Swagger UI)
- Health Check: http://localhost:7860/health

### Known Issues with Setup

1. **First Run**: Frontend may take 2-3 minutes to install dependencies
2. **Port Conflicts**: If ports are in use, run `make backend` or `make frontend` again (Makefile kills processes)
3. **uv Not Found**: Install with `pipx install uv` first
4. **Node Version**: Use nvm or similar to ensure Node 22.12 LTS

### Build and Deployment Process

**Full Build** (for packaging):
```bash
make build base=1 main=1      # Build both packages
# This runs:
# 1. Install frontend dependencies
# 2. Build frontend (Vite)
# 3. Copy build to backend
# 4. Build langbuilder-base package
# 5. Build langbuilder package
```

**Docker Build**:
```bash
make docker_build             # Build main Docker image
make docker_build_backend     # Build backend image
make docker_build_frontend    # Build frontend image
```

**Docker Compose**:
```bash
make docker_compose_up        # Run with docker-compose
make dcdev_up                 # Development compose
```

**Deployment Environments**:
- **Development**: SQLite database, in-memory cache, auto-login enabled
- **Staging**: PostgreSQL, Redis cache, authentication required
- **Production**: PostgreSQL, Redis cache, observability enabled, scaled workers

**Environment Variables for Deployment**:
```bash
LANGBUILDER_DATABASE_URL=postgresql://user:pass@host:5432/db
LANGBUILDER_CACHE_TYPE=redis
LANGBUILDER_REDIS_HOST=redis-host
LANGBUILDER_AUTO_LOGIN=false
LANGBUILDER_SUPERUSER=admin
LANGBUILDER_SUPERUSER_PASSWORD=secure-password
LANGBUILDER_WORKERS=4
```

## Testing Reality

### Current Test Coverage

**Backend**:
- **Unit Tests**: `src/backend/tests/unit/` - Component and service tests
- **Coverage**: Varies by module, component tests comprehensive
- **Integration Tests**: `src/backend/tests/integration/` - Minimal, API key required
- **Load Tests**: `src/backend/tests/locust/` - Locust-based

**Frontend**:
- **Unit Tests**: Jest tests adjacent to components
- **E2E Tests**: Playwright in `src/frontend/tests/` (minimal)
- **Coverage**: Not comprehensive

### Running Tests

**Backend Unit Tests**:
```bash
make unit_tests              # All tests in parallel
make unit_tests async=false  # Sequential
make unit_tests lf=true      # Last failed only
make unit_tests ff=true      # Failed first

# Specific test file
uv run pytest src/backend/tests/unit/components/test_my_component.py

# Specific test method
uv run pytest src/backend/tests/unit/test_file.py::test_method_name

# With verbose output
uv run pytest -v src/backend/tests/unit/
```

**Backend Integration Tests**:
```bash
make integration_tests                 # All integration tests
make integration_tests_no_api_keys     # Without API key tests
make integration_tests_api_keys        # Only API key tests
```

**Frontend Tests**:
```bash
make test_frontend                     # Jest unit tests
make test_frontend_watch               # Watch mode
make test_frontend_coverage            # With coverage
make tests_frontend                    # Playwright e2e
make tests_frontend UI=true            # Playwright UI mode
```

**Template Tests**:
```bash
make template_tests                    # Test starter projects
```

**Load Tests**:
```bash
make locust locust_users=10 locust_spawn_rate=1 locust_api_key=xxx locust_flow_id=yyy
```

### Test Quirks and Workarounds

1. **Database Tests**: `test_database.py` may fail in batch, run individually
2. **Component Version Tests**: Require `VersionComponentMapping` fixture
3. **Async Tests**: Use `@pytest.mark.asyncio` decorator
4. **API Key Tests**: Marked with `@pytest.mark.api_key_required`, skipped by default
5. **Blockbuster**: Use `@pytest.mark.no_blockbuster` to skip blockbuster plugin
6. **Test Duration**: Tests are sorted by duration, slow tests run first

### Test Base Classes

**ComponentTestBase Family** (`src/backend/tests/base.py`):
- `ComponentTestBase`: Base class with version testing
- `ComponentTestBaseWithClient`: Includes FastAPI test client
- `ComponentTestBaseWithoutClient`: No client, pure logic testing

**Required Fixtures**:
```python
@pytest.fixture
def component_class(self):
    return MyComponent

@pytest.fixture
def default_kwargs(self):
    return {"input_value": "test"}

@pytest.fixture
def file_names_mapping(self):
    return [
        VersionComponentMapping(version="1.1.1", module="module", file_name="file.py"),
    ]
```

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

**Development**:
```bash
make init                     # Initial setup (one-time)
make backend                  # Start backend dev server
make frontend                 # Start frontend dev server
make run_cli                  # Build and run full application
```

**Code Quality**:
```bash
make format_backend           # Format Python (run FIRST)
make format_frontend          # Format TypeScript/JavaScript
make lint                     # Run mypy type checking
make codespell                # Check spelling
make fix_codespell            # Fix spelling errors
```

**Testing**:
```bash
make unit_tests               # Backend unit tests
make integration_tests        # Backend integration tests
make test_frontend            # Frontend Jest tests
make tests_frontend           # Frontend Playwright tests
make template_tests           # Starter project tests
```

**Building**:
```bash
make build_frontend           # Build frontend static files
make build base=1             # Build langbuilder-base package
make build main=1             # Build langbuilder package
make build base=1 main=1      # Build both
```

**Database**:
```bash
make alembic-revision message="Add field"  # Create migration
make alembic-upgrade                        # Upgrade database
make alembic-downgrade                      # Downgrade one version
make alembic-current                        # Show current version
make alembic-history                        # Show migration history
```

**Version Management**:
```bash
make patch v=1.5.0            # Update version across all projects
```

**Cleanup**:
```bash
make clean_python_cache       # Remove Python cache
make clean_npm_cache          # Remove npm cache
make clean_all                # Clean everything
```

**Docker**:
```bash
make docker_build             # Build Docker image
make docker_compose_up        # Run with compose
make dcdev_up                 # Development compose
```

### Debugging and Troubleshooting

**Backend Debugging**:
```bash
# Debug mode with verbose logging
make backend log_level=debug

# Check logs (if configured)
tail -f logs/langbuilder.log

# Test database connection
uv run python -c "from langbuilder.services.database import get_db_service; print('OK')"
```

**Frontend Debugging**:
```bash
# Type checking
cd src/frontend && npm run type-check

# Check for format issues
make format_frontend_check

# Clear cache and rebuild
rm -rf src/frontend/node_modules src/frontend/build
make install_frontend
make build_frontend
```

**Common Issues**:

1. **"uv: command not found"**
   - Solution: `pipx install uv` or `make setup_uv`

2. **"Port 7860 already in use"**
   - Solution: `lsof -t -i:7860 | xargs kill -9` (or run `make backend` again)

3. **"Frontend not updating"**
   - Solution: Clear browser cache, ensure Vite dev server is running
   - Check: `http://localhost:3000` should show frontend

4. **"Component not appearing in UI"**
   - Solution: Restart backend, refresh browser
   - Check: Component added to `__init__.py`?

5. **"Database migration conflict"**
   - Solution: Check `make alembic-current`, then `make alembic-upgrade`
   - Nuclear option: Delete `langbuilder.db` and restart

6. **"Import errors in tests"**
   - Solution: Ensure `PYTHONPATH=src/backend/base:$PYTHONPATH`
   - Tests should use `uv run pytest`

7. **"Frontend build fails"**
   - Solution: Check Node.js version (must be 22.12 LTS)
   - Clear: `rm -rf src/frontend/node_modules && make install_frontend`

### Environment Variables Quick Reference

**Backend** (`.env` file):
```bash
LANGBUILDER_DATABASE_URL=sqlite:///./langbuilder.db
LANGBUILDER_CACHE_TYPE=async           # async, memory, redis
LANGBUILDER_AUTO_LOGIN=true            # true, false
LANGBUILDER_SUPERUSER=admin
LANGBUILDER_SUPERUSER_PASSWORD=password
LANGBUILDER_PORT=7860
LANGBUILDER_HOST=0.0.0.0
LANGBUILDER_LOG_LEVEL=info             # debug, info, warning, error, critical
LANGBUILDER_WORKERS=1                  # Number of worker processes
```

**Frontend** (Vite environment variables):
```bash
VITE_PROXY_TARGET=http://localhost:7860
VITE_PORT=3000
```

### Performance Tuning

**Backend**:
- Increase workers: `LANGBUILDER_WORKERS=4`
- Use PostgreSQL instead of SQLite for production
- Enable Redis caching: `LANGBUILDER_CACHE_TYPE=redis`
- Configure connection pooling in database settings

**Frontend**:
- Production build: `make build_frontend` (minified, optimized)
- Lazy loading: Already implemented for routes
- Code splitting: Vite handles automatically

## Conclusion

This brownfield architecture document represents the LangBuilder system as it exists today. Key takeaways:

1. **Full-stack monorepo** with clear frontend/backend separation
2. **Component-based architecture** with 82 active component categories (24 deactivated)
3. **LangChain-powered** AI workflow orchestration
4. **FastAPI + React** modern tech stack
5. **uv + Makefile** build system (uv is mandatory)
6. **Format-first development** (`make format_backend` before everything)
7. **CloudGeometry distribution** with enterprise enhancements

**For new developers**:
- Start with `make init`
- Read `.cursor/rules/` for detailed guidelines
- Run `make backend` and `make frontend` in separate terminals
- Always format before committing

**For AI agents**:
- Component system is auto-discovered via `__init__.py`
- Tests require `ComponentTestBase` fixtures
- Database models are in `services/database/models/`
- API endpoints are in `api/v1/`
- Frontend state is in Zustand stores

This document will be updated as the system evolves.

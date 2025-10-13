# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LangBuilder is a Python/React web application for building language model workflows (fork of LangFlow). It uses FastAPI for the backend, React/TypeScript for the frontend, and follows an async-first architecture with SQLModel for database access.

**Tech Stack:**
- Backend: Python 3.10-3.13 (requires-python >=3.10,<3.14), FastAPI, SQLModel/SQLAlchemy async, JWT authentication
- Frontend: React 18, TypeScript, Vite, Zustand state management, Tailwind CSS
- Database: SQLite (dev), PostgreSQL (production)
- Package Managers: `uv` (Python package manager, >=0.4 required), `npm` (Node.js)

## Essential Commands

### Development Setup
```bash
make init              # Install all dependencies (backend + frontend)
make backend           # Run backend dev server (port 7860, auto-reload)
make frontend          # Run frontend dev server (port 3000, hot-reload)
```

### Code Quality (CRITICAL: Run in this order)
```bash
make format_backend    # Format Python code (run FIRST, before linting)
make format_frontend   # Format TypeScript/JavaScript code
make lint              # Run type checking and linting
make unit_tests        # Run backend unit tests
```

**Important:** Always run `make format_backend` before `make lint` to auto-fix most style issues.

### Testing
```bash
make unit_tests                    # Run all backend unit tests
make integration_tests             # Run integration tests
make test_frontend                 # Run frontend Jest tests
make tests_frontend                # Run frontend Playwright e2e tests

# Run single test file
uv run pytest src/backend/tests/unit/test_specific.py

# Run specific test method
uv run pytest src/backend/tests/unit/test_component.py::test_method -v

# Pass custom args to pytest
make unit_tests args="-k test_pattern -v"
```

### Database Migrations
```bash
cd src/backend/base/langflow
alembic revision --autogenerate -m "description"  # Generate migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
alembic current                                   # Show current revision
alembic history --verbose                         # Show migration history
```

**Note:** Alembic commands must be run from `src/backend/base/langflow/` directory or use the `make alembic-*` commands

### Build & Deployment
```bash
make build_frontend    # Build frontend static files
make build             # Build Python packages
```

### Version Management
```bash
make patch v=1.5.0     # Update version across all projects (pyproject.toml, package.json, etc.)
```

## Architecture Overview

### Monorepo Structure
```
LangBuilder/
├── src/backend/base/langflow/    # Core backend package
│   ├── main.py                   # FastAPI app initialization
│   ├── api/v1/                   # REST API endpoints
│   ├── services/
│   │   ├── auth/                 # JWT authentication
│   │   └── database/models/      # SQLModel database models
│   ├── components/               # LangChain component library
│   └── graph/                    # Workflow execution engine
└── src/frontend/src/
    ├── pages/                    # Page components
    ├── components/               # Reusable UI components
    ├── contexts/authContext.tsx  # Auth state
    ├── stores/                   # Zustand stores
    └── controllers/API/          # API client functions
```

### Key Entry Points
- **Backend:** `src/backend/base/langflow/main.py` - FastAPI app
- **Frontend:** `src/frontend/src/index.tsx` - React entry
- **CLI:** `src/backend/base/langflow/__main__.py`

### Database Models Location
All SQLModel models: `src/backend/base/langflow/services/database/models/`
- `user/` - User authentication and profiles
- `flow/` - Workflow definitions
- `folder/` - Project organization (called "Folders" in code, "Projects" in UI)
- `api_key/` - API tokens

### API Endpoints
REST API under `src/backend/base/langflow/api/v1/`:
- `login.py` - Authentication (JWT)
- `users.py` - User management
- `projects.py` - Project CRUD
- `flows.py` - Flow CRUD and execution
- `api_key.py` - API key management

## Development Patterns

### Backend Component Development

Components live in `src/backend/base/langflow/components/` organized by category (agents, data, embeddings, models, etc.).

When adding components:
1. Add to appropriate subdirectory
2. Update `__init__.py` with alphabetical imports
3. Backend auto-restarts on save
4. Refresh browser to see changes

### Async Patterns (Critical)

All async methods must properly handle cleanup:

```python
async def run(self) -> MessageType:
    """Main execution method."""
    try:
        result = await self.async_operation()
        return result
    except asyncio.CancelledError:
        await self.cleanup()
        raise
```

Use `asyncio.create_task()` for background work with proper cleanup.

### Authentication & Authorization

**Current State:** Basic JWT authentication with binary `is_superuser` flag.
- No fine-grained RBAC currently implemented
- Most endpoints check `user_id == resource.user_id OR is_superuser`
- Auth middleware: `src/backend/base/langflow/services/auth/utils.py`

**Planned Enhancement:** Comprehensive RBAC system (see `docs/architecture.md` and `docs/RBAC_IMPLEMENTATION_PLAN.md`)

### Frontend State Management

Use Zustand stores for global state:

```typescript
// stores/myStore.ts
import { create } from 'zustand';

export const useMyStore = create<MyState>((set) => ({
  value: '',
  setValue: (value) => set({ value }),
}));
```

Auth state: `src/frontend/src/contexts/authContext.tsx`

## Testing Requirements

### Backend Testing

**Base Classes:** Use `ComponentTestBaseWithClient` or `ComponentTestBaseWithoutClient` from `src/backend/tests/base.py`

Required fixtures for component tests:
```python
from tests.base import ComponentTestBaseWithClient

class TestMyComponent(ComponentTestBaseWithClient):
    @pytest.fixture
    def component_class(self):
        return MyComponent

    @pytest.fixture
    def default_kwargs(self):
        return {"param": "value"}

    @pytest.fixture
    def file_names_mapping(self):
        return [
            VersionComponentMapping(
                version="1.1.1",
                module="my_module",
                file_name="my_component.py"
            ),
        ]
```

**Async Tests:** Use `@pytest.mark.asyncio` for async test functions

**Markers:**
- `@pytest.mark.api_key_required` - Tests requiring external API keys
- `@pytest.mark.no_blockbuster` - Skip blockbuster plugin
- `@pytest.mark.asyncio` - Async test functions
- `@pytest.mark.benchmark` - Performance benchmark tests
- `@pytest.mark.noclient` - Skip client fixture creation

**Test Parameters:**
- `async=true` - Run tests in parallel with pytest-xdist (default)
- `lf=true` - Run last failed tests first
- `ff=true` - Run previously failed tests first (default)

**Known Issues:**
- `test_database.py` may fail in batch but pass individually
- Run sequentially if needed: `uv run pytest src/backend/tests/unit/test_database.py`

### Frontend Testing

```bash
make test_frontend         # Run Jest unit tests
make test_frontend_watch   # Watch mode
make tests_frontend        # Run Playwright e2e tests
```

**Note:** Frontend commands are defined in `Makefile.frontend` and included automatically

## Important Caveats

### Environment Configuration
- Copy `.env.example` to `.env` for local development
- Key variables:
  - `LANGFLOW_DATABASE_URL` - Database connection
  - `LANGFLOW_SECRET_KEY` - JWT signing secret
  - `LANGFLOW_SUPERUSER` / `LANGFLOW_SUPERUSER_PASSWORD` - Initial admin
  - `LANGFLOW_AUTO_LOGIN` - Auto-login mode (dev only, DO NOT use in production)

### Terminology Differences
- Code uses "Folder" model, but UI/docs often say "Project" - they're the same entity
- "Component" can mean either: (1) React component, or (2) LangChain workflow component

### Database Migrations
Always generate migrations after model changes:
```bash
cd src/backend/base/langflow
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

### Frontend Build Integration
- Production: Frontend builds to `src/backend/base/langflow/frontend/` and is served by backend
- Development: Frontend runs on port 3000, proxies API calls to backend on port 7860

## Cursor Rules Integration

This project has comprehensive Cursor rules in `.cursor/rules/`:
- `backend_development.mdc` - Python/FastAPI patterns
- `frontend_development.mdc` - React/TypeScript patterns
- `testing.mdc` - Testing best practices
- `icons.mdc` - Icon handling guidelines

These rules provide detailed guidance on:
- Component structure and imports
- Async/await patterns and cleanup
- Testing fixtures and base classes
- State management with Zustand
- Styling with Tailwind CSS

## RBAC Implementation Context

**Current State:** Basic user/superuser roles only

**Planned Enhancement:** Full RBAC system with:
- Hierarchical scopes (Workspace > Project > Environment > Flow > Component)
- Custom roles and permission sets
- SSO/SCIM integration
- Audit logging

See comprehensive design in:
- `docs/architecture.md` - Current brownfield architecture analysis
- `docs/RBAC_IMPLEMENTATION_PLAN.md` - Implementation roadmap
- `docs/PRD _ Granular Access Control & RBAC – LangBuilder.md` - Product requirements

**Key Areas for RBAC:**
- New models needed: Role, Permission, Grant, Group, ServiceAccount, AuditLog
- Auth middleware enhancements: Permission evaluation engine
- API endpoint guards: Add RBAC checks to all resource endpoints
- Frontend: Permission-aware UI components and route guards

## Code Quality Standards

**Pre-commit Workflow:**
1. Run `make format_backend` (FIRST - auto-fixes most issues)
2. Run `make lint`
3. Run `make unit_tests`
4. Commit changes

**Ruff Configuration:** `pyproject.toml` - line length 120, Google docstring convention

**TypeScript:** Strict mode enabled, ESLint configured

**Testing:** Comprehensive unit tests required for all new components. If incomplete, create manual testing documentation (`.md` file with testing steps).

## Performance & Load Testing

### Locust Load Testing
```bash
make locust \
  locust_users=10 \
  locust_spawn_rate=1 \
  locust_host=http://localhost:7860 \
  locust_api_key=your-api-key \
  locust_flow_id=your-flow-id
```

Additional parameters:
- `locust_headless=true` - Run without web UI (default: true)
- `locust_time=300s` - Test duration
- `locust_min_wait=2000` - Min wait time between requests (ms)
- `locust_max_wait=5000` - Max wait time between requests (ms)
- `locust_request_timeout=30.0` - Request timeout (seconds)

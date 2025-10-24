# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About LangBuilder

LangBuilder is a full-stack AI agent platform for building, deploying, and managing LLM-powered workflows. It provides a visual flow builder (React/TypeScript frontend) and a robust execution engine (Python/FastAPI backend) based on LangChain.

**Key Components:**
- **Visual Builder**: Drag-and-drop interface for creating AI workflows
- **80+ Integrations**: LLM providers (OpenAI, Claude, Gemini, etc.), vector databases, data sources, tools
- **Multi-agent orchestration**: Complex workflows with conversation management
- **API & MCP Server**: Deploy flows as REST APIs or MCP server tools
- **Enterprise-ready**: Authentication, RBAC, scalability, observability

## Technology Stack

**Backend:**
- Python 3.10-3.13, FastAPI, LangChain 0.3.23
- Package manager: `uv` (required)
- Database: SQLAlchemy/SQLModel (SQLite default, PostgreSQL optional)
- Testing: pytest with async support

**Frontend:**
- React 18.3.1 + TypeScript, Vite 5.4
- State: Zustand, Data fetching: React Query + Axios
- UI: shadcn/ui + Radix UI + Tailwind CSS
- Flow visualization: React Flow 11
- Node.js v22.12 LTS, npm 10.9

## Common Development Commands

### Initial Setup
```bash
make init                    # Install all dependencies (backend + frontend)
```

### Development Servers
```bash
make backend                 # Start FastAPI on port 7860 (with auto-reload)
make frontend                # Start Vite dev server on port 3000 (with HMR)
```

**Development workflow:** Run both `make backend` and `make frontend` in separate terminals. Frontend proxies API requests to backend.

### Building
```bash
make build_frontend          # Build frontend static files
make build_langbuilder_base  # Build langbuilder-base package
make build_langbuilder       # Build langbuilder package
```

### Code Quality (CRITICAL - Run before commits)
```bash
# Backend (run in this order!)
make format_backend          # Format Python code (run FIRST - auto-fixes most issues)
make lint                    # Run mypy type checking
make unit_tests              # Run backend unit tests

# Frontend
make format_frontend         # Format TypeScript/JavaScript with Biome
make test_frontend           # Run Jest unit tests
make tests_frontend          # Run Playwright e2e tests
```

**Important:** Always run `make format_backend` FIRST before linting or committing. It auto-corrects most style issues and saves significant time.

### Testing
```bash
# Backend tests
make unit_tests              # All backend unit tests (parallel with pytest-xdist)
make unit_tests async=false  # Run tests sequentially
make unit_tests lf=true      # Run last-failed tests only
make integration_tests       # Integration tests (requires additional setup)

# Frontend tests
make test_frontend           # Jest unit tests
make test_frontend_watch     # Jest in watch mode
make test_frontend_coverage  # With coverage report
make tests_frontend          # Playwright e2e tests
make tests_frontend UI=true  # Playwright with UI mode

# Run specific test file
uv run pytest src/backend/tests/unit/test_specific.py
make test_frontend_file path/to/test.ts
```

### Running the Application
```bash
make run_cli                 # Build frontend and run full application
uv run langbuilder run       # Run LangBuilder (after building frontend)
```

### Database Migrations
```bash
make alembic-revision message="Description"  # Create new migration
make alembic-upgrade                          # Upgrade to latest
make alembic-downgrade                        # Downgrade one version
make alembic-current                          # Show current revision
```

### Docker
```bash
make docker_build            # Build Docker image
make docker_compose_up       # Run with docker-compose
```

### Version Management
```bash
make patch v=1.5.0           # Update version across all projects
```

## Architecture Overview

### Directory Structure

```
├── src/backend/base/langbuilder/     # Core backend
│   ├── api/                          # API endpoints (v1, v2)
│   ├── components/                   # 80+ component categories
│   ├── services/                     # Core services (database, flow, cache, session)
│   ├── schema/                       # Pydantic models
│   ├── graph/                        # Graph execution engine
│   └── initial_setup/                # Database initialization
├── src/frontend/src/
│   ├── pages/                        # Page-level components
│   ├── components/                   # Reusable UI components
│   ├── controllers/API/              # Axios client and React Query hooks
│   ├── stores/                       # Zustand state management
│   ├── CustomNodes/                  # Flow node visualizations
│   └── types/                        # TypeScript type definitions
└── tests/                            # Backend tests
```

### Key Architectural Patterns

**Backend:**
- **Service Layer Pattern**: Domain services in `services/` (database, flow, cache, session)
- **Component System**: 80+ components in `components/` (agents, models, tools, vectorstores, etc.)
  - Each component has display properties, input/output specs, custom field typing
  - Auto-discovered via `__init__.py` files
- **Flow Execution**: `FlowRunner` service executes flows based on LangChain's Runnable protocol
- **Database Models**: SQLModel in `services/database/models/` (flow, user, folder, api_key)
- **API Versioning**: `/api/v1/` and `/api/v2/` endpoints

**Frontend:**
- **State Management**: Zustand stores (authStore, flowStore, utilityStore, darkStore)
- **Data Fetching**: React Query hooks in `controllers/API/queries/`
- **Component Structure**: Pages → Reusable components → Domain-specific components
- **Flow Visualization**: React Flow for drag-and-drop graph editor
- **Routing**: React Router v6 with lazy loading

**Communication:**
- Frontend Axios client → `/api/v1/*` endpoints → FastAPI handlers
- JWT authentication with Bearer tokens (stored in cookies)
- WebSocket support for real-time updates

## Component Development

### Adding Backend Components

1. **Location**: `src/backend/base/langbuilder/components/{category}/`
2. **Update imports**: Add to `__init__.py` (alphabetically)
3. **Testing**: Create unit test in `src/backend/tests/unit/components/`
   - Use `ComponentTestBaseWithClient` or `ComponentTestBaseWithoutClient`
   - Provide fixtures: `component_class`, `default_kwargs`, `file_names_mapping`
4. **Refresh**: Backend auto-restarts on save, refresh browser to see changes

Example test structure:
```python
from tests.base import ComponentTestBaseWithClient, VersionComponentMapping

class TestMyComponent(ComponentTestBaseWithClient):
    @pytest.fixture
    def component_class(self):
        return MyComponent

    @pytest.fixture
    def default_kwargs(self):
        return {"input_value": "test"}

    @pytest.fixture
    def file_names_mapping(self):
        return [
            VersionComponentMapping(version="1.1.1", module="my_module", file_name="my_component.py"),
        ]
```

### Async Patterns (Important)

LangBuilder uses async extensively. Follow these patterns:

```python
# Component async methods
async def run(self) -> MessageType:
    result = await self.async_operation()
    return result

# Background tasks with proper cleanup
async def process_in_background(self):
    task = asyncio.create_task(self.heavy_operation())
    try:
        result = await task
        return result
    except asyncio.CancelledError:
        await self.cleanup()
        raise

# Queue operations (non-blocking)
async def queue_processing(self):
    queue = asyncio.Queue()
    queue.put_nowait(data)
    try:
        result = await asyncio.wait_for(queue.get(), timeout=5.0)
        return result
    except asyncio.TimeoutError:
        raise ComponentError("Processing timeout")
```

## Frontend Development

### State Management

```typescript
// Using Zustand stores
import { useMyStore } from '@/stores/myStore';

export function MyComponent() {
  const { value, setValue } = useMyStore();
  return <input value={value} onChange={(e) => setValue(e.target.value)} />;
}
```

### API Integration

```typescript
// Using React Query hooks
import { api } from '@/controllers/API';

export async function createFlow(flowData: FlowData) {
  const response = await api.post('/flows/', flowData);
  return response.data;
}
```

### Styling

Use Tailwind CSS with the `cn` utility for conditional classes:

```typescript
import { cn } from '@/utils/cn';

<button className={cn(
  'rounded-md font-medium transition-colors',
  variant === 'primary' ? 'bg-blue-600 text-white' : 'bg-gray-200'
)} />
```

## Testing Guidelines

### Backend Testing Requirements

- **Minimum requirement**: Comprehensive unit tests for all new components
- **Test base classes**: Use `ComponentTestBaseWithClient` or `ComponentTestBaseWithoutClient`
- **Required fixtures**: `component_class`, `default_kwargs`, `file_names_mapping`
- **Version compatibility**: Provide `VersionComponentMapping` for backward compatibility

**Known quirks:**
- `test_database.py` may fail in batch runs but pass individually
- Use `@pytest.mark.no_blockbuster` to skip blockbuster plugin when needed
- Database tests may need sequential execution: `uv run pytest src/backend/tests/unit/test_database.py`

### Frontend Testing

- Jest for unit tests
- Playwright for e2e tests
- Use `@testing-library/react` for component testing

## Important Configuration Files

- **pyproject.toml**: Python dependencies, tool configs (ruff, mypy, pytest)
- **uv.lock**: Locked Python dependencies
- **Makefile**: Primary build orchestrator
- **Makefile.frontend**: Frontend-specific commands
- **src/frontend/package.json**: Frontend dependencies and scripts
- **src/frontend/vite.config.mts**: Vite configuration with API proxy

## Cursor Rules Integration

This repository has detailed Cursor rules in `.cursor/rules/`:
- **backend_development.mdc**: Backend patterns, component structure, async development
- **frontend_development.mdc**: React/TypeScript patterns, state management, styling
- **testing.mdc**: Testing patterns, async testing, version compatibility
- **icons.mdc**: Icon management

Refer to these files for detailed development guidelines specific to each domain.

## Pre-Commit Workflow

**Backend:**
1. Run `make format_backend` (FIRST - saves time)
2. Run `make lint`
3. Run `make unit_tests`
4. Commit changes

**Frontend:**
1. Run `make format_frontend`
2. Run `make lint`
3. Test changes in browser
4. Commit changes

## Common Tasks

### Running a Single Test
```bash
# Backend
uv run pytest src/backend/tests/unit/components/test_my_component.py::test_specific_method

# Frontend
make test_frontend_file src/components/MyComponent.test.ts
```

### Debugging Backend
```bash
# Run with debug logging
make backend log_level=debug

# Run with specific env file
make backend env=.env.local

# Run with multiple workers
make backend workers=4
```

### Debugging Frontend
```bash
# Run with specific flags
make run_frontend FRONTEND_START_FLAGS="--port 3001"

# Type checking
cd src/frontend && npm run type-check
```

### Adding Dependencies
```bash
# Backend (main project)
make add main="package-name"

# Backend (base project)
make add base="package-name"

# Backend (dev dependencies)
make add devel="package-name"

# Frontend
cd src/frontend && npm install package-name
```

### Clean Project
```bash
make clean_python_cache   # Remove Python cache files
make clean_npm_cache      # Remove npm cache and node_modules
make clean_all            # Clean everything
```

## Environment Variables

Backend reads from `.env` file. Key variables:
- `LANGBUILDER_AUTO_LOGIN`: Enable auto-login (true/false)
- Database connection strings
- API keys for external services

Frontend uses Vite environment variables (prefix with `VITE_`).

## Notes

- **uv is required**: Install with `make setup_uv` or `pipx install uv`
- **Node.js v22.12 LTS required** for frontend development
- **Format early, format often**: `make format_backend` before any commit
- **Hot reload**: Backend auto-reloads, frontend has HMR (Hot Module Replacement)
- **Starter project files** auto-format after `langbuilder run` - these changes can be committed or ignored
- **API proxy**: Frontend dev server proxies `/api/*` requests to backend on port 7860

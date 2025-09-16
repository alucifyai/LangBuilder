# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Backend Development
- **Install backend dependencies**: `make install_backend`
- **Run backend server**: `make backend`
- **Run backend tests**: `make unit_tests`
- **Run integration tests**: `make integration_tests`
- **Format backend code**: `make format_backend`
- **Lint backend code**: `make lint`

### Frontend Development
- **Install frontend dependencies**: `make install_frontend`
- **Build frontend**: `make build_frontend`
- **Run frontend in dev mode**: `make frontend`
- **Format frontend code**: `make format_frontend`
- **Run frontend unit tests**: `make test_frontend`
- **Run frontend e2e tests**: `make tests_frontend`

### Full Development Workflow
- **Initialize project**: `make init` (installs all dependencies)
- **Run complete application**: `make run_cli`
- **Run all tests**: `make tests`

### Code Quality
- **Format all code**: `make format`
- **Type checking**: Available via `npm run type-check` in frontend
- **Linting**: Backend uses ruff, frontend uses biome

## Architecture Overview

### Project Structure
This is **Langflow** - a Python-based low-code platform for building AI workflows and applications, currently implementing comprehensive RBAC (Role-Based Access Control) features.

**Monorepo Structure:**
- `src/backend/` - Python backend with FastAPI
  - `src/backend/base/` - Core langflow-base package
  - `src/backend/langflow/` - Main langflow package
  - `src/backend/tests/` - Backend tests (unit, integration)
- `src/frontend/` - React/TypeScript frontend application
- `docs/` - Documentation
- `scripts/` - Deployment and utility scripts
- `AppGraph/` - RBAC architecture documentation and workflow analysis

### Technology Stack
- **Backend**: Python 3.10+ with FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18+ with TypeScript, Vite build system, Tailwind CSS
- **Database**: Supports PostgreSQL (primary), SQLite for development
- **Package Management**:
  - Backend: `uv` (Python package manager)
  - Frontend: `npm`
- **Testing**:
  - Backend: pytest with coverage reporting
  - Frontend: Jest (unit), Playwright (e2e)

### Key Dependencies & Frameworks
- **LangChain**: Core AI/ML framework integration
- **Pydantic**: Data validation and settings management
- **Zustand**: Frontend state management
- **React Flow**: Visual flow builder components
- **Material-UI & Radix-UI**: UI component libraries

### RBAC Implementation Context
The codebase is currently implementing a comprehensive RBAC system with:
- Hierarchical permissions and role management
- Multi-workspace/project organization
- Enterprise SSO integration (OIDC/SAML)
- Audit logging and compliance features
- GraphQL schema with type-safe operations

See `RBAC_IMPLEMENTATION_PLAN.md` for detailed implementation strategy and `AppGraph/` directory for architectural analysis.

### Development Notes
- Uses **uv** for Python dependency management (faster than pip/poetry)
- Frontend uses Vite for fast development builds
- Database migrations handled via Alembic (see `make alembic-*` commands)
- Comprehensive testing with parallel execution support
- Docker support for production deployment

### Testing Strategy
- Backend: Unit tests with pytest, integration tests, coverage reporting
- Frontend: Jest unit tests, Playwright e2e tests
- BDD testing for RBAC workflows using pytest-bdd
- Load testing available with Locust (`make locust`)
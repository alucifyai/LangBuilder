# LangBuilder

A visual framework for building language model workflows and applications, forked from LangFlow.

## Overview

LangBuilder is a Python/React web application that provides a visual interface for creating, managing, and deploying language model workflows. It uses FastAPI for the backend and React/TypeScript for the frontend.

## Features

- **Visual Workflow Builder**: Drag-and-drop interface for creating LangChain workflows
- **Component Library**: Extensive library of pre-built components for LLMs, agents, embeddings, and more
- **Multi-tenancy**: Workspace-based organization with RBAC (Role-Based Access Control)
- **API Integration**: RESTful API for programmatic access
- **Real-time Execution**: Execute workflows and see results in real-time
- **MCP Server Support**: Integration with Model Context Protocol servers

## Tech Stack

- **Backend**: Python 3.10-3.13, FastAPI, SQLModel/SQLAlchemy async, JWT authentication
- **Frontend**: React 18, TypeScript, Vite, Zustand state management, Tailwind CSS
- **Database**: SQLite (development), PostgreSQL (production)
- **Package Managers**: `uv` (Python), `npm` (Node.js)

## Quick Start

### Prerequisites

- Python 3.10-3.13
- Node.js 18+
- `uv` package manager (>= 0.4)
- `npm` or `yarn`

### Installation

```bash
# Install all dependencies (backend + frontend)
make init

# Run backend development server (port 7860)
make backend

# Run frontend development server (port 3000)
make frontend
```

### Development Commands

```bash
# Code quality
make format_backend    # Format Python code (run FIRST)
make format_frontend   # Format TypeScript code
make lint              # Run type checking and linting

# Testing
make unit_tests        # Run backend unit tests
make test_frontend     # Run frontend Jest tests
make tests_frontend    # Run frontend Playwright e2e tests

# Build
make build_frontend    # Build frontend static files
make build             # Build Python packages
```

### Database Migrations

```bash
cd src/backend/base/langflow
alembic revision --autogenerate -m "description"  # Generate migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
```

## Project Structure

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
    ├── contexts/                 # React contexts (auth, theme)
    ├── stores/                   # Zustand stores
    └── controllers/API/          # API client functions
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
LANGFLOW_DATABASE_URL=sqlite:///./langflow.db
LANGFLOW_SECRET_KEY=your-secret-key-here
LANGFLOW_SUPERUSER=admin
LANGFLOW_SUPERUSER_PASSWORD=admin
```

**⚠️ Important**: Never use `LANGFLOW_AUTO_LOGIN=true` in production.

## Documentation

For detailed documentation, see:
- `CLAUDE.md` - Development guide for Claude Code
- `docs/architecture.md` - System architecture
- `docs/RBAC_IMPLEMENTATION_PLAN.md` - RBAC implementation details

## Contributing

This is a fork of LangFlow with enhanced RBAC capabilities and multi-tenancy support.

### Code Quality Standards

Before committing:
1. Run `make format_backend` (auto-fixes most issues)
2. Run `make lint`
3. Run `make unit_tests`
4. Ensure all tests pass

## License

See LICENSE file for details.

## Acknowledgments

Based on [LangFlow](https://github.com/logspace-ai/langflow) - An open-source visual framework for building LangChain applications.

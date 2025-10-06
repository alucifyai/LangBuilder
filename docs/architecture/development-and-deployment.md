# Development and Deployment

## Local Development Setup

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

## Build and Deployment Process

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

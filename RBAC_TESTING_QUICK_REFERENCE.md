# RBAC Testing Quick Reference

Quick commands and tests for validating RBAC Phase 1 implementation.

## 🚀 Quick Start

### Activate Virtual Environment First!
```bash
# IMPORTANT: Always activate the virtual environment first
source .venv/bin/activate
```

### Run Automated Validation
```bash
# Run the comprehensive validation script
python validate_rbac_phase1.py
```

## 📋 Common Test Commands

### 1. Test Model Imports
```bash
# Quick test - all models should import without errors
python -c "from langflow.services.database.models.rbac import *; print('✅ All RBAC models imported')"
```

### 2. Test API Endpoints
```bash
# Check that API routers load
python -c "from langflow.api.v1.rbac import workspaces, projects, roles; print('✅ API routers loaded')"
```

### 3. Test Permission System
```bash
# Verify permission checker works
python -c "from langflow.api.v1.rbac.dependencies import PermissionChecker; print('✅ Permission system loaded')"
```

### 4. Test Specific Models
```bash
# Workspace model
python -c "from langflow.services.database.models.rbac.workspace import Workspace, WorkspaceCreate; print('✅ Workspace models OK')"

# Project model
python -c "from langflow.services.database.models.rbac.project import Project, ProjectCreate; print('✅ Project models OK')"

# Role model
python -c "from langflow.services.database.models.rbac.role import Role, SYSTEM_ROLES; print('✅ Role models OK')"
```

## 🔍 Detailed Testing

### Database Migration Test
```bash
# Check if migrations are up to date
uv run alembic check

# Run migrations (creates tables)
uv run alembic upgrade head

# Rollback if needed
uv run alembic downgrade -1
```

### Interactive Python Testing
```python
# Start Python interpreter with activated venv
python

# Test creating workspace
from langflow.services.database.models.rbac.workspace import WorkspaceCreate
workspace = WorkspaceCreate(
    name="Test Workspace",
    description="Testing RBAC"
)
print(f"Created workspace: {workspace.name}")

# Test permission enums
from langflow.services.database.models.rbac.environment import EnvironmentType
print(f"Environment types: {list(EnvironmentType)}")

# Test role types
from langflow.services.database.models.rbac.role import RoleType, SYSTEM_ROLES
print(f"Role types: {list(RoleType)}")
print(f"System roles: {list(SYSTEM_ROLES.keys())}")
```

## 🧪 Unit Test Commands

### Run All RBAC Tests
```bash
# If pytest is available
pytest src/backend/tests/ -k rbac -v

# Run with coverage
pytest src/backend/tests/ -k rbac --cov=src/backend/base/langflow/api/v1/rbac
```

### Test Specific Components
```bash
# Test models only
pytest src/backend/tests/unit/database/ -k rbac -v

# Test API endpoints only
pytest src/backend/tests/unit/api/v1/rbac/ -v

# Test services only
pytest src/backend/tests/unit/services/ -k rbac -v
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "No module named 'langflow'" Error
```bash
# Solution: Activate virtual environment
source .venv/bin/activate
python validate_rbac_phase1.py
```

#### 2. Import Errors for RBAC Models
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Ensure you're in the project root
pwd  # Should show /Users/dongmingjiang/GB/LangBuilder

# Try importing with full path
cd /Users/dongmingjiang/GB/LangBuilder
source .venv/bin/activate
python -c "from langflow.services.database.models.rbac import *"
```

#### 3. Database Connection Issues
```bash
# Set test database URL
export LANGFLOW_DATABASE_URL="sqlite:///test.db"

# Run migrations
uv run alembic upgrade head

# Check tables were created
sqlite3 test.db ".tables"
```

#### 4. Permission Denied Errors
```bash
# Make scripts executable
chmod +x validate_rbac_phase1.py

# Run with Python explicitly
python validate_rbac_phase1.py
```

## 📊 Expected Test Results

When running `validate_rbac_phase1.py`, you should see:

```
🚀 Starting RBAC Phase 1 Validation
==================================================
🔍 Testing imports...
  ✅ All RBAC model imports successful
  ✅ All RBAC API imports successful

🔍 Testing model instantiation...
  ✅ WorkspaceCreate model instantiated successfully
  ✅ ProjectCreate model instantiated successfully
  ✅ EnvironmentCreate model instantiated successfully
  ✅ RoleCreate model instantiated successfully

🔍 Testing API router setup...
  ✅ All API routers properly configured
  ✅ All API router tags properly set

🔍 Testing PermissionChecker logic...
  ✅ Superuser permission logic working
  ✅ Owner permission logic working
  ✅ Access control logic working

🔍 Testing model validation...
  ✅ Valid workspace creation works
  ✅ Empty workspace name properly rejected
  ✅ Valid environment name accepted
  ✅ Invalid environment name properly rejected

🔍 Testing metadata field resolution...
  ✅ Workspace metadata field properly renamed
  ✅ Project metadata field properly renamed
  ✅ Role metadata field properly renamed

🔍 Testing enum definitions...
  ✅ EnvironmentType enum working
  ✅ RoleType enum working
  ✅ GroupType enum working
  ✅ AuditEventType enum working

==================================================
📊 Validation Results: 7/7 tests passed
🎉 RBAC Phase 1 validation SUCCESSFUL!
```

## 🚦 Quick Status Check

Run this one-liner to check RBAC status:
```bash
source .venv/bin/activate && python -c "
try:
    from langflow.services.database.models.rbac import *
    from langflow.api.v1.rbac import workspaces, projects, roles
    print('✅ RBAC Phase 1: OPERATIONAL')
except Exception as e:
    print(f'❌ RBAC Phase 1: FAILED - {e}')
"
```

## 📝 Notes

- Always run tests with virtual environment activated
- The validation script doesn't require a running server
- Database migrations need to be run separately
- For full integration testing, the API server needs to be running

## 🛠️ Development Testing

### Start Development Server with RBAC
```bash
# Activate venv
source .venv/bin/activate

# Run migrations
uv run alembic upgrade head

# Start server
uv run langflow run --dev

# API will be available at http://localhost:7860
```

### Test API Endpoints with curl
```bash
# Test workspace creation (requires authentication)
curl -X POST http://localhost:7860/api/v1/rbac/workspaces \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"name": "Test Workspace", "description": "Testing RBAC"}'

# List workspaces
curl http://localhost:7860/api/v1/rbac/workspaces \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## ✅ Validation Checklist

- [ ] Virtual environment activated
- [ ] Validation script runs without errors
- [ ] All 7 tests pass
- [ ] Models import successfully
- [ ] API routers configured
- [ ] Permission checker works
- [ ] Model validation works
- [ ] Metadata fields resolved
- [ ] Enums properly defined
- [ ] Database migrations run (optional)
- [ ] API endpoints accessible (optional)

---

**Remember**: Always activate the virtual environment (`.venv`) before running any tests!
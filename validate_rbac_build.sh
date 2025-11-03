#!/bin/bash
# RBAC Build Validation Script
# Validates Phase 1 & 2 implementation (Tasks 1.1-2.3)
# Usage: ./validate_rbac_build.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 RBAC MVP Build Validation Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Track results
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Function to run a check
run_check() {
    local check_name="$1"
    local check_command="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

# Function to run a check with output
run_check_with_output() {
    local check_name="$1"
    local check_command="$2"

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -n "Checking: $check_name... "

    OUTPUT=$(eval "$check_command" 2>&1)
    RESULT=$?

    if [ $RESULT -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
        if [ ! -z "$OUTPUT" ]; then
            echo "    Output: $OUTPUT"
        fi
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "    Error: $OUTPUT"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Phase 1: Core RBAC Data Model and Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Task 1.1: RBAC Database Models"
echo "────────────────────────────────"
run_check "RBAC model.py syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/services/database/models/rbac/model.py"

run_check "RBAC crud.py syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/services/database/models/rbac/crud.py"

run_check "RBAC models import" \
    "uv run python3 -c 'from langbuilder.services.database.models.rbac import Role, Permission, RolePermission, UserRoleAssignment'"

run_check "RBAC enums import" \
    "uv run python3 -c 'from langbuilder.services.database.models.rbac import RoleEnum, PermissionEnum, ScopeTypeEnum'"

run_check_with_output "RBAC models registered" \
    "uv run python3 -c 'from langbuilder.services.database.models import Role, Permission; print(\"✓ Registered\")'"

echo ""

echo "Task 1.2: Alembic Migration (Schema)"
echo "────────────────────────────────"
run_check "Schema migration file syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/alembic/versions/d6c803ed2d15*.py"

echo -n "Checking: Schema migration in Alembic... "
cd src/backend/base/langbuilder
if uv run alembic history | grep -q "d6c803ed2d15"; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
cd - > /dev/null

echo ""

echo "Task 1.3: Seed Script"
echo "────────────────────────────────"
run_check "Seed script syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/initial_setup/rbac_seed.py"

run_check "Seed script import" \
    "uv run python3 -c 'from langbuilder.initial_setup.rbac_seed import seed_rbac_data'"

echo ""

echo "Task 1.4 & 1.5: RBACService"
echo "────────────────────────────────"
run_check "RBACService syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/services/rbac/service.py"

run_check "RBACServiceFactory syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/services/rbac/factory.py"

run_check "RBACService import" \
    "uv run python3 -c 'from langbuilder.services.rbac import RBACService'"

run_check "RBACService methods exist" \
    "uv run python3 -c 'from langbuilder.services.rbac import RBACService; assert hasattr(RBACService, \"can_access\"); assert hasattr(RBACService, \"assign_role\")'"

run_check "RBACService dependency injection" \
    "uv run python3 -c 'from langbuilder.services.deps import get_rbac_service'"

echo ""

echo "Task 1.6: Data Migration"
echo "────────────────────────────────"
run_check "Data migration file syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/alembic/versions/a1b2c3d4e5f6*.py"

echo -n "Checking: Data migration in Alembic... "
cd src/backend/base/langbuilder
if uv run alembic history | grep -q "a1b2c3d4e5f6"; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
else
    echo -e "${RED}❌ FAIL${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
cd - > /dev/null

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Phase 2: RBAC API Endpoints and Enforcement"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Task 2.1: RBAC Management API"
echo "────────────────────────────────"
run_check "RBAC API syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/api/v1/rbac.py"

run_check "RBAC API router import" \
    "uv run python3 -c 'from langbuilder.api.v1.rbac import router'"

run_check "RBAC schemas import" \
    "uv run python3 -c 'from langbuilder.api.v1.schemas import AssignmentCreate, AssignmentResponse'"

run_check "RBAC router registered" \
    "uv run python3 -c 'from langbuilder.api.v1 import rbac_router'"

echo ""

echo "Task 2.2: Flow CRUD RBAC Integration"
echo "────────────────────────────────"
run_check "Flows API syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/api/v1/flows.py"

run_check "Flows API imports RBAC" \
    "uv run python3 -c 'import inspect; from langbuilder.api.v1 import flows; source = inspect.getsource(flows); assert \"RBACService\" in source'"

echo ""

echo "Task 2.3: Project CRUD RBAC Integration"
echo "────────────────────────────────"
run_check "Projects API syntax" \
    "uv run python3 -m py_compile src/backend/base/langbuilder/api/v1/projects.py"

run_check "Projects API imports RBAC" \
    "uv run python3 -c 'import inspect; from langbuilder.api.v1 import projects; source = inspect.getsource(projects); assert \"RBACService\" in source'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏗️ Application Integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

run_check "FastAPI app imports successfully" \
    "uv run python3 -c 'from langbuilder.main import create_app'"

run_check "ServiceType enum has RBAC_SERVICE" \
    "uv run python3 -c 'from langbuilder.services.schema import ServiceType; assert hasattr(ServiceType, \"RBAC_SERVICE\")'"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total Checks: $TOTAL_CHECKS"
echo -e "${GREEN}Passed: $PASSED_CHECKS${NC}"
echo -e "${RED}Failed: $FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ ALL CHECKS PASSED - BUILD IS VALID!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Phase 1 & 2 implementation is ready for:"
    echo "  • Database migrations (alembic upgrade head)"
    echo "  • Running tests (pytest)"
    echo "  • Starting the application (uvicorn)"
    echo "  • Phase 3 development (Frontend RBAC)"
    echo ""
    exit 0
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ SOME CHECKS FAILED - REVIEW ERRORS ABOVE${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Run 'uv sync' to install dependencies"
    echo "  • Ensure you're in the project root directory"
    echo "  • Check Python version (3.10+ required)"
    echo ""
    exit 1
fi

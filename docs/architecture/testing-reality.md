# Testing Reality

## Current Test Coverage

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

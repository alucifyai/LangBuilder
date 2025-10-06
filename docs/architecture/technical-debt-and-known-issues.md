# Technical Debt and Known Issues

## Critical Technical Debt

1. **Authorization System is Too Simple**
   - **Location**: `src/backend/base/langflow/services/auth/utils.py`
   - **Issue**: Only checks `is_superuser` boolean. No fine-grained permissions.
   - **Impact**: Cannot implement RBAC without major refactoring.
   - **Workaround**: Most endpoints check `user_id == resource.user_id OR is_superuser`.

2. **No Multi-Tenancy / Workspace Isolation**
   - **Issue**: Users can only see their own resources or all resources (if superuser).
   - **Impact**: Cannot implement workspace/project-based collaboration.
   - **PRD Requirement**: Workspaces, Projects, Flows need scope-based RBAC.

3. **API Key Scoping Missing**
   - **Location**: `src/backend/base/langflow/services/database/models/api_key/model.py`
   - **Issue**: API keys are global to user, not scoped to resources or permissions.
   - **PRD Requirement**: Story 4.2 requires scoped tokens.

4. **Folder `auth_settings` Field Unused**
   - **Location**: `src/backend/base/langflow/services/database/models/folder/model.py:14-18`
   - **Issue**: JSON field exists but no code reads/writes it.
   - **Opportunity**: Can be used for project-level RBAC overrides.

5. **No Audit Logging**
   - **Issue**: No immutable audit trail of user actions or RBAC changes.
   - **PRD Requirement**: Story 5.1 requires comprehensive audit logging.

6. **Frontend Permission Checks Inconsistent**
   - **Issue**: UI elements hidden/shown based on `isAdmin` boolean only.
   - **Impact**: Cannot implement granular UI permission guards.

## Workarounds and Gotchas

- **Auto-Login Mode**: `LANGFLOW_AUTO_LOGIN=true` bypasses authentication for development. **Do NOT use in production.** Use `LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true` for safer alternative (being deprecated in v1.6).

- **Database Migrations**: Use Alembic (`src/backend/base/langflow/alembic/`). Always generate migration after model changes: `alembic revision --autogenerate -m "description"`.

- **Folder vs Project Terminology**: Code uses "Folder", PRD uses "Project". They are the same entity (`Folder` model represents projects).

- **Environment Concept Missing**: PRD mentions "Environment" as a scope level (Story 2.1 @AC8), but no `Environment` model exists in codebase. This is a new concept to be added.

- **Component-Level Permissions**: PRD Story 2.1 @AC7 requires component-level permissions, but components are embedded in Flow `data` (JSON), not separate database entities. May need architectural decision on how to scope permissions to individual components.

---

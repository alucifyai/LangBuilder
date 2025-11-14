# Backend Build Issue Resolution Guide

**Document Version**: 1.0
**Date**: 2025-11-06
**Phase**: Post-Phase-1 (Tasks 1.1-1.7)
**Purpose**: Guide for building the backend after completing Phase-1 RBAC implementation

---

## Overview

This document provides a comprehensive checklist and troubleshooting guide for building the backend after completing Phase-1 RBAC implementation (Tasks 1.1-1.7). It documents the issues encountered during our first build and provides step-by-step resolution.

---

## Critical Pre-Build Steps

### 1. Verify Migration Files Are Correct

**Issue We Hit**: The data migration had async/event loop conflicts and missing seed data dependency.

**What to Check**:

```bash
# Check that c62fe238bf8b_add_rbac_tables.py includes seed data
grep -A 5 "Seeding RBAC data" src/backend/base/langbuilder/alembic/versions/c62fe238bf8b_add_rbac_tables.py
```

**Must Have**:
- ✅ Table creation (role, permission, role_permission, user_role_assignment)
- ✅ **Seed data insertion** (4 roles, 8 permissions, role-permission mappings)
- ✅ All in the SAME migration file

**Why**: The data migration (d73ae349cf9c) depends on seed data existing. If seed data isn't created first, the migration will fail with "Required roles not found in database".

**Expected Seed Data**:
- **4 Roles**: Admin, Owner, Editor, Viewer (all with `is_system=True`)
- **8 Permissions**: Create_Flow, Read_Flow, Update_Flow, Delete_Flow, Create_Project, Read_Project, Update_Project, Delete_Project
- **24 Role-Permission Mappings**:
  - Admin: All 8 permissions
  - Owner: All 8 permissions
  - Editor: 6 permissions (no Delete)
  - Viewer: 2 permissions (Read only)

---

### 2. Verify Data Migration Uses Sync Operations

**Issue We Hit**: `asyncio.run()` cannot be called from within Alembic's already-running event loop, causing `RuntimeError`.

**What to Check**:

```bash
# Check that d73ae349cf9c_migrate_existing_users_to_rbac.py uses synchronous SQL
grep "asyncio.run" src/backend/base/langbuilder/alembic/versions/d73ae349cf9c_migrate_existing_users_to_rbac.py
```

**Should Return**: Nothing (no asyncio.run calls found)

**Must Have**:
- ✅ Uses `connection.execute(text(...))` for all DB operations
- ✅ NO `asyncio.run()` calls
- ✅ NO `async/await` in the `upgrade()` function
- ✅ Works with the sync connection from `op.get_bind()`

**Why**: Alembic already runs migrations in an async context via `asyncio.run(_run_async_migrations())` in `env.py`. Attempting to create a nested event loop with another `asyncio.run()` causes a RuntimeError.

**Correct Pattern**:

```python
def upgrade() -> None:
    connection = op.get_bind()

    # Use synchronous SQL operations
    result = connection.execute(text("SELECT id FROM role WHERE name = 'Admin'"))
    admin_role = result.fetchone()

    # Insert with parameters
    connection.execute(text(
        "INSERT INTO user_role_assignment (id, user_id, role_id, ...) "
        "VALUES (:id, :user_id, :role_id, ...)"
    ), {"id": str(uuid4()), "user_id": user_id, "role_id": admin_role[0]})
```

---

### 3. Check for Migration Branch Conflicts

**Issue We Hit**: RBAC migrations branched from an old revision (`fd531f8868b1`), while the main codebase continued with another branch ending at `3162e83e485f`. This created multiple heads.

**What to Check**:

```bash
cd src/backend/base/langbuilder/
uv run alembic heads
```

**Expected Output Before Fix**: Should show **TWO heads**:
```
3162e83e485f (head)  # Main branch head
d73ae349cf9c (head)  # RBAC branch head
```

**Error When Running Upgrade**:
```
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head';
please specify a specific target revision, '<branchname>@head' to narrow to a specific head,
or 'heads' for all heads
```

**Action Required**: Create a merge migration:

```bash
cd src/backend/base/langbuilder/
uv run alembic merge -m "merge rbac and main branches" 3162e83e485f d73ae349cf9c
```

This creates a merge migration (e.g., `19db92f8586c_merge_rbac_and_main_branches.py`) that combines both branches.

**After Merge Check**:
```bash
uv run alembic heads
# Should show: 19db92f8586c (head)  # Single merged head
```

**Why**: Alembic cannot determine which migration path to follow when multiple heads exist. The merge migration resolves the ambiguity by creating a single path forward.

**Understanding the Migration Tree**:
```
fd531f8868b1 (common ancestor)
    |
    +-- 1ef9c4f3765d --> ... --> 3162e83e485f (main branch)
    |
    +-- c62fe238bf8b --> d73ae349cf9c (RBAC branch)

After merge:
    3162e83e485f + d73ae349cf9c --> 19db92f8586c (merged)
```

---

### 4. Run Migrations in Clean State

**Recommended Steps**:

```bash
# Step 1: Check current migration status
cd src/backend/base/langbuilder/
uv run alembic current

# Step 2: Check for multiple heads
uv run alembic heads

# Step 3: If multiple heads exist, create merge migration (see step 3 above)

# Step 4: Run upgrade
cd ../../../../  # Back to project root
make alembic-upgrade

# Step 5: Verify success
cd src/backend/base/langbuilder/
uv run alembic current
# Should show: 19db92f8586c (head) (mergepoint)
```

**Expected Migration Order**:
1. **c62fe238bf8b** - Creates RBAC tables + seeds data
   - Creates: role, permission, role_permission, user_role_assignment tables
   - Inserts: 4 roles, 8 permissions, 24 mappings
2. **d73ae349cf9c** - Migrates existing users to RBAC
   - Assigns global Admin role to superusers
   - Assigns Owner role to users for their flows/projects
   - Marks Starter Project assignments as immutable
3. **19db92f8586c** - Merges branches (if needed)
   - No-op migration that resolves branch conflict

**Expected Log Output During Upgrade**:

```
INFO  [alembic.runtime.migration] Running upgrade fd531f8868b1 -> c62fe238bf8b, Add RBAC tables
INFO  | Seeding RBAC data...
DEBUG | Created role: Admin
DEBUG | Created role: Owner
DEBUG | Created role: Editor
DEBUG | Created role: Viewer
DEBUG | Created permission: Create_Flow
...
INFO  | RBAC seed data created successfully

INFO  [alembic.runtime.migration] Running upgrade c62fe238bf8b -> d73ae349cf9c, Migrate existing users to RBAC
INFO  | Running RBAC data migration...
DEBUG | Admin role ID: xxx, Owner role ID: yyy
DEBUG | Found 0 users to migrate  # Or however many users exist
INFO  | RBAC migration successful: X assignments created, Y skipped

INFO  [alembic.runtime.migration] Running upgrade 3162e83e485f, d73ae349cf9c -> 19db92f8586c, merge rbac and main branches
```

---

### 5. Verify Database State

After migrations complete, verify the data:

**For SQLite (default)**:

```bash
# Check your database location (default or from .env)
sqlite3 src/backend/base/langbuilder/langbuilder.db

# Run verification queries:
.tables
# Should show: role, permission, role_permission, user_role_assignment (among others)

SELECT COUNT(*) FROM role;
# Should return: 4

SELECT COUNT(*) FROM permission;
# Should return: 8

SELECT COUNT(*) FROM role_permission;
# Should return: 24

SELECT name FROM role;
# Should show: Admin, Owner, Editor, Viewer

SELECT name FROM permission;
# Should show: Create_Flow, Read_Flow, Update_Flow, Delete_Flow,
#              Create_Project, Read_Project, Update_Project, Delete_Project

.quit
```

**For PostgreSQL**:

```bash
psql -h localhost -U postgres -d langbuilder

SELECT COUNT(*) FROM role;
SELECT COUNT(*) FROM permission;
SELECT COUNT(*) FROM role_permission;
SELECT name FROM role;
SELECT name FROM permission;

\q
```

**Must Have**:
- ✅ 4 roles (Admin, Owner, Editor, Viewer)
- ✅ 8 permissions (CRUD for Flow and Project)
- ✅ 24 role-permission mappings
- ✅ 0+ user_role_assignments (depends on existing users)

**Role-Permission Mapping Verification**:

```sql
-- Should return 8 permissions for Admin
SELECT p.name
FROM role r
JOIN role_permission rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE r.name = 'Admin';

-- Should return 8 permissions for Owner
SELECT p.name
FROM role r
JOIN role_permission rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE r.name = 'Owner';

-- Should return 6 permissions for Editor (no Delete)
SELECT p.name
FROM role r
JOIN role_permission rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE r.name = 'Editor';

-- Should return 2 permissions for Viewer (Read only)
SELECT p.name
FROM role r
JOIN role_permission rp ON r.id = rp.role_id
JOIN permission p ON rp.permission_id = p.id
WHERE r.name = 'Viewer';
```

---

### 6. Environment Configuration (Optional but Recommended)

```bash
# Create .env from example
cp .env.example .env

# Edit .env to set (optional for testing):
nano .env
```

**Recommended .env Settings for RBAC Testing**:

```bash
# Database Configuration
LANGBUILDER_DATABASE_URL=sqlite:///./langbuilder.db
# Or for PostgreSQL:
# LANGBUILDER_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/langbuilder

# Authentication Configuration
LANGBUILDER_AUTO_LOGIN=false  # Set to false to test login with RBAC

# Superuser Credentials (required if AUTO_LOGIN=false)
LANGBUILDER_SUPERUSER=admin
LANGBUILDER_SUPERUSER_PASSWORD=changeme123

# Server Configuration
LANGBUILDER_HOST=0.0.0.0
LANGBUILDER_PORT=7860
LANGBUILDER_LOG_LEVEL=debug

# Caching
LANGBUILDER_CACHE_TYPE=memory
```

**Why**: While `make backend` auto-creates an empty `.env`, having proper configuration helps with:
- Testing different authentication modes
- Verifying RBAC role assignments for superusers vs regular users
- Debugging with appropriate log levels

---

### 7. Build the Backend

Once all pre-build steps are complete:

```bash
make backend
```

**What `make backend` Does**:
1. Runs `setup_env` - Creates empty `.env` if missing
2. Runs `install_backend` - Syncs dependencies using `uv sync --frozen --extra "postgresql"`
3. Kills any process on port 7860
4. Starts uvicorn server with hot-reload enabled
5. Sets `PYTHONPATH=src/backend/base:$PYTHONPATH`
6. Runs on `http://0.0.0.0:7860` by default

**What to Watch For in Logs**:

✅ **Good Signs**:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:7860 (Press CTRL+C to quit)
```

✅ **Expected RBAC Messages** (if startup integration is enabled):
```
INFO  | Initializing RBAC seed data...
INFO  | RBAC seed data already exists, skipping initialization
```
This is GOOD - means seed data from migration is detected and startup doesn't duplicate it.

⚠️ **Warnings (Safe to Ignore)**:
```
SAWarning: WARNING: SQL-parsed foreign key constraint '('user_id', 'user', 'id')'
could not be located in PRAGMA foreign_keys for table flow
```
This is a SQLAlchemy warning about foreign key introspection on SQLite - safe to ignore.

❌ **Error Signs**:

**Error 1 - Missing Seed Data**:
```
ValueError: Required roles not found in database
ValueError: Admin and Owner roles not found. Run RBAC seed data initialization first.
```
**Solution**: Go back to Step 1 - seed data wasn't created in the migration.

**Error 2 - Async Event Loop Conflict**:
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```
**Solution**: Go back to Step 2 - data migration uses async incorrectly.

**Error 3 - Port Already in Use**:
```
ERROR:    [Errno 48] Address already in use
```
**Solution**:
```bash
# Kill process on port 7860
lsof -ti:7860 | xargs kill -9
# Then retry: make backend
```

**Error 4 - Database Connection**:
```
sqlalchemy.exc.OperationalError: unable to open database file
```
**Solution**: Check database path in `.env` and ensure directory exists.

---

## Common Issues & Solutions

### Issue 1: "Multiple head revisions are present"

**Full Error Message**:
```bash
make alembic-upgrade
ERROR [alembic.util.messaging] Multiple head revisions are present for given argument 'head';
please specify a specific target revision, '<branchname>@head' to narrow to a specific head,
or 'heads' for all heads
  FAILED: Multiple head revisions are present for given argument 'head'
make: *** [alembic-upgrade] Error 255
```

**Root Cause**:
- RBAC migrations branched from an older revision
- Main codebase continued with separate migrations
- Both branches have their own "head" (latest revision)
- Alembic doesn't know which path to follow

**Diagnosis**:
```bash
cd src/backend/base/langbuilder/
uv run alembic heads
# Output shows multiple heads:
# 3162e83e485f (head)
# d73ae349cf9c (head)
```

**Solution**: Create a merge migration

```bash
cd src/backend/base/langbuilder/

# Create merge migration (replace IDs with your actual head IDs)
uv run alembic merge -m "merge rbac and main branches" 3162e83e485f d73ae349cf9c

# This creates a new migration file like:
# 19db92f8586c_merge_rbac_and_main_branches.py

# Verify single head now exists
uv run alembic heads
# Should show: 19db92f8586c (head)

# Now upgrade works
cd ../../../../
make alembic-upgrade
```

**Prevention**:
- Keep migration branches in sync
- Regularly merge feature branches into main
- Check `alembic heads` before creating new migrations

---

### Issue 2: "Required roles not found in database"

**Full Error Message**:
```bash
make alembic-upgrade
INFO  [alembic.runtime.migration] Running upgrade c62fe238bf8b -> d73ae349cf9c, Migrate existing users to RBAC
ERROR | Admin and Owner roles not found. Run RBAC seed data initialization first.
ValueError: Required roles not found in database
make: *** [alembic-upgrade] Error 1
```

**Root Cause**:
- The RBAC table creation migration (`c62fe238bf8b`) created empty tables
- Seed data (predefined roles and permissions) was NOT inserted
- The data migration (`d73ae349cf9c`) expects Admin and Owner roles to exist
- Without seed data, the query `SELECT id FROM role WHERE name = 'Admin'` returns None

**Diagnosis**:
```bash
# Check if migration file includes seed data
grep -A 10 "Seeding RBAC data" src/backend/base/langbuilder/alembic/versions/c62fe238bf8b_add_rbac_tables.py

# If nothing found, seed data is missing

# Check database state
sqlite3 src/backend/base/langbuilder/langbuilder.db "SELECT COUNT(*) FROM role;"
# Returns: 0  (bad - should be 4)
```

**Solution Option A - Fix Migration and Rerun** (Recommended):

1. **Add seed data to the migration**:

Edit `c62fe238bf8b_add_rbac_tables.py` and add seed data insertion at the end of `upgrade()`:

```python
def upgrade() -> None:
    # ... existing table creation code ...

    # Add this at the end:
    logger.info("Seeding RBAC data...")
    connection = op.get_bind()

    # Insert roles
    roles = [
        {"id": str(uuid4()), "name": "Admin", "description": "...", "is_system": True},
        {"id": str(uuid4()), "name": "Owner", "description": "...", "is_system": True},
        {"id": str(uuid4()), "name": "Editor", "description": "...", "is_system": True},
        {"id": str(uuid4()), "name": "Viewer", "description": "...", "is_system": True},
    ]
    for role in roles:
        connection.execute(text(
            "INSERT INTO role (id, name, description, is_system) VALUES (:id, :name, :description, :is_system)"
        ), role)

    # Insert permissions... (see full implementation in original migration)
    # Insert role-permission mappings... (see full implementation)

    logger.info("RBAC seed data created successfully")
```

2. **Rollback and re-run**:

```bash
cd src/backend/base/langbuilder/

# Rollback to before RBAC migrations
uv run alembic downgrade fd531f8868b1

# Now upgrade with the fixed migration
cd ../../../../
make alembic-upgrade
```

**Solution Option B - Manual Seed** (Quick Fix):

If you can't modify the migration:

```bash
# Run the RBAC seed data initialization from application startup
cd src/backend/base/langbuilder/

# Create a temporary script
cat > seed_rbac.py << 'EOF'
import asyncio
from langbuilder.services.database import get_session
from langbuilder.initial_setup.rbac_setup import initialize_rbac_data

async def main():
    async with get_session() as session:
        await initialize_rbac_data(session)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run it
uv run python seed_rbac.py

# Clean up
rm seed_rbac.py
```

**Prevention**:
- Always include seed data in the same migration that creates the tables
- Test migrations on a clean database before committing
- Add verification queries to migration to ensure seed data exists

---

### Issue 3: "RuntimeError: asyncio.run() cannot be called from a running event loop"

**Full Error Message**:
```bash
make alembic-upgrade
INFO  [alembic.runtime.migration] Running upgrade c62fe238bf8b -> d73ae349cf9c, Migrate existing users to RBAC
ERROR | Error during RBAC data migration
RuntimeError: asyncio.run() cannot be called from a running event loop
Traceback (most recent call last):
  ...
  File ".../d73ae349cf9c_migrate_existing_users_to_rbac.py", line 81, in upgrade
    asyncio.run(run_migration())
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Root Cause**:
- Alembic's `env.py` runs migrations using `asyncio.run(_run_async_migrations())`
- This creates an event loop for the entire migration process
- The data migration tried to create a NESTED event loop with another `asyncio.run()`
- Python's asyncio doesn't support nested event loops

**Technical Explanation**:

```python
# In alembic/env.py:
def run_migrations_online() -> None:
    asyncio.run(_run_async_migrations())  # Creates event loop
        # Inside this event loop:
        -> context.run_migrations()
            -> Your migration's upgrade() function
                -> asyncio.run(run_migration())  # ERROR: Already in event loop!
```

**Diagnosis**:

```bash
# Check if migration uses asyncio.run
grep -n "asyncio.run" src/backend/base/langbuilder/alembic/versions/d73ae349cf9c_migrate_existing_users_to_rbac.py

# Check if migration uses async/await
grep -n "async def\|await " src/backend/base/langbuilder/alembic/versions/d73ae349cf9c_migrate_existing_users_to_rbac.py
```

**Solution**: Rewrite migration to use synchronous operations

**BEFORE (Broken)**:

```python
def upgrade() -> None:
    async def run_migration():
        engine = create_async_engine(...)
        async with AsyncSession(engine) as session:
            result = await migrate_existing_users_to_rbac(session)
            # ... async operations ...

    asyncio.run(run_migration())  # ERROR!
```

**AFTER (Fixed)**:

```python
def upgrade() -> None:
    connection = op.get_bind()  # Get sync connection from Alembic

    # Use synchronous SQL operations
    admin_role = connection.execute(text(
        "SELECT id FROM role WHERE name = 'Admin'"
    )).fetchone()

    owner_role = connection.execute(text(
        "SELECT id FROM role WHERE name = 'Owner'"
    )).fetchone()

    users = connection.execute(text(
        "SELECT id, username, is_superuser FROM user"
    )).fetchall()

    for user in users:
        user_id, username, is_superuser = user

        if is_superuser:
            connection.execute(text(
                "INSERT INTO user_role_assignment (...) VALUES (...)"
            ), {"id": str(uuid4()), "user_id": user_id, ...})
```

**Key Changes**:
1. Remove all `async`/`await` keywords
2. Replace `AsyncSession` with `connection = op.get_bind()`
3. Replace `await session.exec(select(...))` with `connection.execute(text(...))`
4. Use `text()` from SQLAlchemy for parameterized queries
5. Use `.fetchone()` or `.fetchall()` to get results

**Testing the Fix**:

```bash
# After fixing the migration, test it
cd src/backend/base/langbuilder/

# If migration already partially ran, rollback first
uv run alembic downgrade c62fe238bf8b

# Then upgrade with the fixed migration
cd ../../../../
make alembic-upgrade
```

**Prevention**:
- Avoid async operations in Alembic migrations
- Use synchronous SQL via `connection.execute(text(...))`
- Test migrations in isolation before integrating

---

### Issue 4: Port 7860 Already in Use

**Error Message**:
```bash
make backend
ERROR:    [Errno 48] Address already in use
```

**Root Cause**: Another process is already using port 7860 (likely a previous backend instance that wasn't properly shut down).

**Diagnosis**:
```bash
# Find process using port 7860
lsof -ti:7860

# Get details about the process
lsof -i:7860
```

**Solution**:

```bash
# Kill the process
lsof -ti:7860 | xargs kill -9

# Or kill all Python processes (use with caution!)
pkill -9 python

# Then retry
make backend
```

**Note**: The Makefile already includes this logic:
```makefile
backend: setup_env install_backend
    @-kill -9 $$(lsof -t -i:7860) || true
    # ... starts backend ...
```

If you still get the error, the kill command might have failed.

**Prevention**:
- Always use `Ctrl+C` to stop the backend gracefully
- Check for running processes before starting: `lsof -i:7860`

---

### Issue 5: Database Connection Errors

**Error Message**:
```bash
sqlalchemy.exc.OperationalError: unable to open database file
```

**Root Cause**:
- Database file path is incorrect
- Database directory doesn't exist
- Permissions issue

**Diagnosis**:

```bash
# Check database path in .env
grep LANGBUILDER_DATABASE_URL .env

# Check if database exists
ls -la src/backend/base/langbuilder/langbuilder.db

# Check if directory exists
ls -la src/backend/base/langbuilder/
```

**Solution**:

```bash
# If directory doesn't exist, create it
mkdir -p src/backend/base/langbuilder/

# Ensure correct path in .env
echo "LANGBUILDER_DATABASE_URL=sqlite:///./langbuilder.db" >> .env

# Run migrations to create database
make alembic-upgrade
```

---

## Quick Validation Checklist

Before running `make backend`, verify:

- [ ] **Migration Files Reviewed**
  - [ ] `c62fe238bf8b_add_rbac_tables.py` includes seed data insertion
  - [ ] `d73ae349cf9c_migrate_existing_users_to_rbac.py` uses sync operations only
  - [ ] No `asyncio.run()` calls in migration files
  - [ ] All imports are correct (`from uuid import uuid4`, `from sqlalchemy import text`)

- [ ] **Migration State Clean**
  - [ ] `alembic heads` shows only ONE head (or two before merge)
  - [ ] If two heads exist, merge migration created
  - [ ] `alembic current` shows expected revision

- [ ] **Migrations Successful**
  - [ ] `make alembic-upgrade` completed without errors
  - [ ] Logs show "RBAC seed data created successfully"
  - [ ] Logs show "RBAC migration successful"

- [ ] **Database State Verified**
  - [ ] 4 roles exist (Admin, Owner, Editor, Viewer)
  - [ ] 8 permissions exist (CRUD for Flow and Project)
  - [ ] 24 role-permission mappings exist
  - [ ] User role assignments match expected (based on existing users)

- [ ] **Environment Configured**
  - [ ] `.env` file exists
  - [ ] Database URL is correct
  - [ ] Authentication settings configured (if needed)

- [ ] **No Port Conflicts**
  - [ ] Port 7860 is not in use: `lsof -i:7860` returns nothing

**If all checkboxes pass** → `make backend` should work perfectly!

---

## Ideal Workflow Summary

```bash
# ============================================
# STEP 1: AFTER PHASE-1 CODE GENERATION
# ============================================
cd /path/to/LangBuilder

# ============================================
# STEP 2: REVIEW MIGRATION FILES (MANUAL)
# ============================================

# Check seed data in first RBAC migration
grep -A 5 "Seeding RBAC data" src/backend/base/langbuilder/alembic/versions/c62fe238bf8b_add_rbac_tables.py

# Check for async issues in data migration
grep "asyncio.run\|async def\|await " src/backend/base/langbuilder/alembic/versions/d73ae349cf9c_migrate_existing_users_to_rbac.py

# ============================================
# STEP 3: CHECK FOR BRANCH CONFLICTS
# ============================================
cd src/backend/base/langbuilder/
uv run alembic heads
# Expected: Two heads (3162e83e485f and d73ae349cf9c)

# ============================================
# STEP 4: MERGE BRANCHES IF NEEDED
# ============================================
uv run alembic merge -m "merge rbac and main branches" 3162e83e485f d73ae349cf9c
# This creates a merge migration (e.g., 19db92f8586c)

uv run alembic heads
# Expected: One head (19db92f8586c)

# ============================================
# STEP 5: RUN MIGRATIONS
# ============================================
cd ../../../../  # Back to project root
make alembic-upgrade

# Watch for success messages:
# - "RBAC seed data created successfully"
# - "RBAC migration successful: X assignments created, Y skipped"

# ============================================
# STEP 6: VERIFY DATABASE STATE
# ============================================
cd src/backend/base/langbuilder/
uv run alembic current
# Should show: 19db92f8586c (head) (mergepoint)

sqlite3 langbuilder.db "SELECT COUNT(*) FROM role;"        # Should return: 4
sqlite3 langbuilder.db "SELECT COUNT(*) FROM permission;"  # Should return: 8
sqlite3 langbuilder.db "SELECT COUNT(*) FROM role_permission;"  # Should return: 24

# ============================================
# STEP 7: CONFIGURE ENVIRONMENT (OPTIONAL)
# ============================================
cd ../../../../  # Back to project root
cp .env.example .env
nano .env  # Edit as needed

# ============================================
# STEP 8: BUILD BACKEND
# ============================================
make backend

# Watch for success messages:
# - "INFO:     Application startup complete."
# - "INFO:     Uvicorn running on http://0.0.0.0:7860"

# ============================================
# STEP 9: VERIFY BACKEND IS RUNNING
# ============================================
curl http://localhost:7860/health  # Or appropriate health endpoint

# ============================================
# SUCCESS! Backend running with RBAC Phase-1 complete
# ============================================
```

---

## Key Lessons Learned

### 1. **Seed Data Must Be in Schema Migration**

**Problem**: Originally, seed data initialization was only in the application startup code (`rbac_setup.py`). The data migration depended on this seed data existing, but it wouldn't exist until the app started.

**Solution**: Include seed data insertion directly in the table creation migration (`c62fe238bf8b`). This ensures roles and permissions exist before the data migration runs.

**Takeaway**: When a migration depends on reference data, include that data in the migration itself, not in application startup code.

---

### 2. **Avoid Async in Alembic Migrations**

**Problem**: Alembic already runs in an async context. Using `asyncio.run()` within a migration creates a nested event loop, which Python doesn't support.

**Solution**: Use synchronous SQL operations via `connection.execute(text(...))`. This works within Alembic's existing async context.

**Takeaway**: Alembic migrations should always use synchronous database operations, even if the application uses async.

---

### 3. **Merge Branches Proactively**

**Problem**: RBAC migrations branched from an older revision while the main codebase continued separately. This created multiple heads, preventing `alembic upgrade head` from working.

**Solution**: Check for multiple heads before running upgrades. Create merge migrations to combine branches.

**Takeaway**: When working with feature branches that include migrations, merge them into main regularly to avoid head conflicts.

---

### 4. **Test Migrations in Clean State**

**Problem**: Some issues only appear when migrations run on a fresh database. Testing on a database that already has some migrations applied can mask problems.

**Solution**: Test migrations on a clean database (or use a separate test database) before committing.

**Takeaway**: Always test migrations from scratch to catch dependency issues early.

---

### 5. **Verify at Each Step**

**Problem**: Running all steps in sequence without verification can lead to cascading errors that are hard to debug.

**Solution**: Check `alembic current`, `alembic heads`, and database state after each migration step.

**Takeaway**: Incremental verification catches issues early and makes debugging easier.

---

## Additional Resources

### Alembic Commands Reference

```bash
# Check current revision
alembic current

# List all heads
alembic heads

# Show migration history
alembic history --verbose

# Upgrade to latest
alembic upgrade head

# Downgrade by one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Create merge migration
alembic merge -m "merge message" <head1> <head2>

# Create new migration
alembic revision --autogenerate -m "migration message"
```

### Database Inspection Commands

**SQLite**:
```bash
sqlite3 langbuilder.db

.tables                          # List all tables
.schema role                     # Show schema for role table
SELECT * FROM alembic_version;   # Show current migration version
SELECT COUNT(*) FROM role;       # Count roles
.quit
```

**PostgreSQL**:
```bash
psql -h localhost -U postgres -d langbuilder

\dt                              -- List all tables
\d role                          -- Show schema for role table
SELECT * FROM alembic_version;   -- Show current migration version
SELECT COUNT(*) FROM role;       -- Count roles
\q
```

### Makefile Targets Reference

```bash
make help                # Show all available commands
make install_backend     # Install backend dependencies
make alembic-current     # Show current migration
make alembic-history     # Show migration history
make alembic-upgrade     # Upgrade to latest migration
make alembic-downgrade   # Downgrade by one revision
make backend             # Build and start backend server
```

---

## Troubleshooting Decision Tree

```
┌─────────────────────────┐
│   make alembic-upgrade  │
└───────────┬─────────────┘
            │
            ├─── "Multiple head revisions" ────────┐
            │                                       │
            │                                       ▼
            │                           Create merge migration
            │                           alembic merge -m "..." <head1> <head2>
            │
            ├─── "Required roles not found" ───────┐
            │                                       │
            │                                       ▼
            │                           Check c62fe238bf8b migration
            │                           Add seed data insertion
            │                           Rollback & re-run
            │
            ├─── "asyncio.run() error" ────────────┐
            │                                       │
            │                                       ▼
            │                           Check d73ae349cf9c migration
            │                           Rewrite to use sync operations
            │                           Rollback & re-run
            │
            └─── SUCCESS ─────────────┐
                                      │
                                      ▼
                              Verify database state
                              └─ 4 roles?
                              └─ 8 permissions?
                              └─ 24 mappings?
                                      │
                                      ▼
                                 make backend
                                      │
                                      ├─── Port 7860 in use ──────┐
                                      │                            │
                                      │                            ▼
                                      │                    lsof -ti:7860 | xargs kill -9
                                      │
                                      └─── SUCCESS ────────────────┐
                                                                    │
                                                                    ▼
                                                    Backend running on :7860
                                                    Phase-1 Complete! 🎉
```

---

## Conclusion

This document captures the complete resolution process for building the backend after Phase-1 RBAC implementation. By following these steps and using this checklist, you should be able to avoid the common pitfalls and successfully build the backend with RBAC functionality.

**Key Takeaways**:
1. ✅ Include seed data in table creation migrations
2. ✅ Use synchronous operations in Alembic migrations
3. ✅ Merge migration branches proactively
4. ✅ Verify database state at each step
5. ✅ Test migrations on clean databases

**Next Steps After Successful Build**:
- Proceed to Phase-2: RBAC Service and API implementation
- Test RBAC role assignments with different user types
- Verify permission checks work correctly
- Begin Phase-3: Frontend integration

---

**Document Maintained By**: Development Team
**Last Updated**: 2025-11-06
**Status**: Active
**Version**: 1.0

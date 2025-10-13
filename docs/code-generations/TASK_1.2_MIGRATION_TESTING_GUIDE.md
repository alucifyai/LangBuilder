# Task 1.2 Database Migration Testing Guide

**Migration File:** `0b4b33664011_add_rbac_models_with_workspace_groups.py`
**Revision ID:** 0b4b33664011
**Revises:** fd531f8868b1
**Date:** 2025-10-11

---

## Overview

This document provides comprehensive testing procedures for the RBAC database migration. The migration adds 13 new tables and modifies 3 existing tables to support enterprise-grade role-based access control.

**What This Migration Does:**
- Creates 13 new RBAC tables (Role, Permission, Workspace, UserGroup, Environment, Invitation, etc.)
- Modifies api_key, folder, and flow tables to add RBAC support
- Performs data migration: creates "Default Workspace" for existing users
- Assigns all existing users as owners of the default workspace
- Assigns all existing folders to the default workspace

---

## Prerequisites

### Required Environment

- Python 3.10-3.13
- Virtual environment activated
- Alembic installed (via `uv` package manager)
- Database: SQLite (dev) or PostgreSQL (production)

### Setup Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify Alembic is available
alembic --version

# Navigate to Alembic directory
cd src/backend/base/langflow
```

---

## Test Scenario 1: Fresh Database (No Existing Users)

### Purpose
Verify the migration creates all tables correctly on a brand new database without any existing data.

### Test Steps

```bash
# 1. Remove any existing database
rm -f langflow.db langflow.db-* 2>/dev/null

# 2. Run migration
alembic upgrade head

# 3. Verify migration completed successfully
# Expected output: "Running upgrade fd531f8868b1 -> 0b4b33664011, Add RBAC models with workspace, groups, and environments"
```

### Verification Queries

```bash
# Check all RBAC tables were created
sqlite3 langflow.db <<EOF
.tables
-- Expected tables:
-- workspace, workspace_member, user_group, user_group_member
-- role, permission, role_permission, role_assignment
-- service_account, audit_log, sso_integration
-- environment, invitation
EOF

# Verify no default workspace was created (since no users exist)
sqlite3 langflow.db "SELECT COUNT(*) as workspace_count FROM workspace;"
-- Expected: 0

# Verify folder.workspace_id column exists and is NOT NULL
sqlite3 langflow.db "PRAGMA table_info(folder);"
-- Expected: workspace_id column with NOT NULL constraint

# Verify flow.environment_id column exists and IS NULL (optional)
sqlite3 langflow.db "PRAGMA table_info(flow);"
-- Expected: environment_id column with nullable=True

# Verify api_key has RBAC columns
sqlite3 langflow.db "PRAGMA table_info(api_key);"
-- Expected: workspace_id, scope_type, scope_id, scoped_permissions, service_account_id
```

### Success Criteria

- ✅ All 13 new tables created
- ✅ All indexes created
- ✅ All foreign keys created
- ✅ Modified tables have new columns
- ✅ No default workspace created (no existing users)
- ✅ folder.workspace_id is NOT NULL
- ✅ flow.environment_id is nullable

---

## Test Scenario 2: Existing Database with Users

### Purpose
Verify the data migration creates a default workspace and assigns existing users and folders correctly.

### Test Setup

```bash
# 1. Remove any existing database
rm -f langflow_test.db langflow_test.db-* 2>/dev/null

# 2. Create a database with existing users and folders (simulate production)
# Run migrations up to the point before RBAC migration
alembic downgrade fd531f8868b1

# 3. Create test users and folders
sqlite3 langflow.db <<EOF
-- Create test users
INSERT INTO user (id, username, password, is_active, is_superuser, create_at, updated_at, profile_image, store_api_key)
VALUES
('11111111-1111-1111-1111-111111111111', 'user1', '\$2b\$12\$hashedpassword', 1, 0, datetime('now'), datetime('now'), NULL, NULL),
('22222222-2222-2222-2222-222222222222', 'user2', '\$2b\$12\$hashedpassword', 1, 0, datetime('now'), datetime('now'), NULL, NULL),
('33333333-3333-3333-3333-333333333333', 'admin', '\$2b\$12\$hashedpassword', 1, 1, datetime('now'), datetime('now'), NULL, NULL);

-- Create test folders
INSERT INTO folder (id, name, user_id, parent_id, description)
VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Project 1', '11111111-1111-1111-1111-111111111111', NULL, 'User1 project'),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'Project 2', '22222222-2222-2222-2222-222222222222', NULL, 'User2 project'),
('cccccccc-cccc-cccc-cccc-cccccccccccc', 'Admin Project', '33333333-3333-3333-3333-333333333333', NULL, 'Admin project');

-- Verify test data
SELECT COUNT(*) as user_count FROM user;
-- Expected: 3
SELECT COUNT(*) as folder_count FROM folder;
-- Expected: 3
EOF
```

### Migration Execution

```bash
# Run the RBAC migration
alembic upgrade head
```

### Verification Queries

```bash
# 1. Verify default workspace was created
sqlite3 langflow.db "SELECT * FROM workspace WHERE slug='default';"
-- Expected: 1 row with name='Default Workspace'

# 2. Verify all users are workspace members with 'owner' role
sqlite3 langflow.db "SELECT COUNT(*) as member_count FROM workspace_member WHERE role='owner';"
-- Expected: 3

# 3. Verify each user is a member of the default workspace
sqlite3 langflow.db <<EOF
SELECT
    u.username,
    wm.role,
    w.name as workspace_name
FROM user u
JOIN workspace_member wm ON u.id = wm.user_id
JOIN workspace w ON wm.workspace_id = w.id
WHERE w.slug = 'default'
ORDER BY u.username;
EOF
-- Expected: 3 rows (admin, user1, user2)

# 4. Verify all folders are assigned to default workspace
sqlite3 langflow.db <<EOF
SELECT
    f.name as folder_name,
    w.name as workspace_name
FROM folder f
JOIN workspace w ON f.workspace_id = w.id
WHERE w.slug = 'default';
EOF
-- Expected: 3 rows (Project 1, Project 2, Admin Project)

# 5. Verify folder.workspace_id is NOT NULL
sqlite3 langflow.db "SELECT COUNT(*) as folders_without_workspace FROM folder WHERE workspace_id IS NULL;"
-- Expected: 0

# 6. Verify foreign keys are working
sqlite3 langflow.db "PRAGMA foreign_key_check(folder);"
-- Expected: Empty result (no FK violations)
```

### Success Criteria

- ✅ "Default Workspace" created with slug='default'
- ✅ All 3 existing users are workspace members
- ✅ All users have role='owner' in default workspace
- ✅ All 3 folders assigned to default workspace
- ✅ No folders have NULL workspace_id
- ✅ All foreign keys valid

---

## Test Scenario 3: Migration Rollback

### Purpose
Verify the migration can be safely rolled back without data loss.

### Test Steps

```bash
# 1. Verify current migration
alembic current
-- Expected: 0b4b33664011 (head)

# 2. Perform rollback
alembic downgrade -1
-- Expected: Rolling back to fd531f8868b1

# 3. Verify rollback completed
alembic current
-- Expected: fd531f8868b1
```

### Verification After Rollback

```bash
# 1. Verify RBAC tables were dropped
sqlite3 langflow.db ".tables" | grep -E "(workspace|role|permission|user_group|environment|invitation|service_account|audit_log|sso_integration)"
-- Expected: No matches (all RBAC tables dropped)

# 2. Verify existing tables are intact
sqlite3 langflow.db "SELECT COUNT(*) as user_count FROM user;"
-- Expected: 3 (users still exist)

sqlite3 langflow.db "SELECT COUNT(*) as folder_count FROM folder;"
-- Expected: 3 (folders still exist)

# 3. Verify RBAC columns were removed from existing tables
sqlite3 langflow.db "PRAGMA table_info(api_key);" | grep -E "(workspace_id|scope_type|service_account_id)"
-- Expected: No matches

sqlite3 langflow.db "PRAGMA table_info(folder);" | grep "workspace_id"
-- Expected: No match

sqlite3 langflow.db "PRAGMA table_info(flow);" | grep "environment_id"
-- Expected: No match
```

### Re-apply Migration

```bash
# Re-apply the migration to verify idempotency
alembic upgrade head
-- Expected: Success, default workspace recreated

# Verify everything is correct again
sqlite3 langflow.db "SELECT COUNT(*) FROM workspace WHERE slug='default';"
-- Expected: 1
```

### Success Criteria

- ✅ Rollback completes without errors
- ✅ All RBAC tables dropped
- ✅ Existing user and folder data intact
- ✅ RBAC columns removed from modified tables
- ✅ Migration can be re-applied successfully
- ✅ Data migration repeats correctly (idempotent)

---

## Test Scenario 4: PostgreSQL Production Database

### Purpose
Verify the migration works correctly on PostgreSQL (production database).

### Prerequisites

```bash
# Install PostgreSQL adapter
uv pip install psycopg2-binary

# Set database URL
export LANGFLOW_DATABASE_URL="postgresql://user:password@localhost:5432/langflow_test"
```

### Test Steps

```bash
# 1. Create fresh PostgreSQL database
psql -U postgres -c "DROP DATABASE IF EXISTS langflow_test;"
psql -U postgres -c "CREATE DATABASE langflow_test;"

# 2. Run migration
alembic upgrade head

# 3. Verify with PostgreSQL
psql -U postgres -d langflow_test -c "\dt"
-- Expected: All RBAC tables listed

# 4. Test with existing data (same as Scenario 2, but using psql)
psql -U postgres -d langflow_test <<EOF
-- Insert test users
INSERT INTO "user" (id, username, password, is_active, is_superuser, create_at, updated_at)
VALUES
('11111111-1111-1111-1111-111111111111', 'pguser1', '\$2b\$12\$hash', true, false, NOW(), NOW()),
('22222222-2222-2222-2222-222222222222', 'pguser2', '\$2b\$12\$hash', true, false, NOW(), NOW());

-- Verify gen_random_uuid() works in data migration
SELECT COUNT(*) FROM workspace_member;
EOF
-- Expected: 2 (one for each user)
```

### PostgreSQL-Specific Verifications

```bash
# Verify gen_random_uuid() was used correctly
psql -U postgres -d langflow_test -c "SELECT id FROM workspace_member LIMIT 1;"
-- Expected: Valid UUID

# Verify database locks work
psql -U postgres -d langflow_test -c "SELECT pg_advisory_xact_lock(112233);"
-- Expected: Lock acquired

# Verify indexes exist
psql -U postgres -d langflow_test -c "\di" | grep -E "(workspace|role|permission)"
-- Expected: Multiple index entries
```

### Success Criteria

- ✅ Migration works on PostgreSQL
- ✅ gen_random_uuid() used correctly for PostgreSQL
- ✅ Foreign keys created successfully
- ✅ Indexes created correctly
- ✅ Data migration works with PostgreSQL syntax

---

## Test Scenario 5: Idempotency Test

### Purpose
Verify the migration is idempotent and can handle tables that already exist.

### Test Steps

```bash
# 1. Run migration twice (should handle gracefully)
alembic downgrade fd531f8868b1
alembic upgrade head
alembic upgrade head  # Second run should be a no-op
-- Expected: "Target database is up to date" or similar

# 2. Manually create a table that the migration creates
sqlite3 langflow.db "CREATE TABLE IF NOT EXISTS test_workspace (id TEXT PRIMARY KEY);"
alembic downgrade fd531f8868b1
# Now upgrade - migration should check for existing tables
alembic upgrade head
-- Expected: No errors, uses "if not in existing_tables" checks
```

### Success Criteria

- ✅ Migration handles existing tables gracefully
- ✅ Running upgrade twice doesn't cause errors
- ✅ Table existence checks work correctly

---

## Test Scenario 6: Large Data Volume Test

### Purpose
Verify the migration performs well with large amounts of data.

### Test Setup

```bash
# Create 1000 test users and 5000 folders
python <<EOF
import sqlite3
from uuid import uuid4
from datetime import datetime

conn = sqlite3.connect('langflow.db')
cursor = conn.cursor()

# Create 1000 users
for i in range(1000):
    user_id = str(uuid4())
    cursor.execute(
        "INSERT INTO user (id, username, password, is_active, is_superuser, create_at, updated_at) "
        "VALUES (?, ?, ?, 1, 0, ?, ?)",
        (user_id, f'user{i}', '\$2b\$12\$hash', datetime.now(), datetime.now())
    )

    # Create 5 folders per user
    for j in range(5):
        folder_id = str(uuid4())
        cursor.execute(
            "INSERT INTO folder (id, name, user_id, description) "
            "VALUES (?, ?, ?, ?)",
            (folder_id, f'Folder {i}-{j}', user_id, f'Test folder {j}')
        )

conn.commit()
conn.close()
print("Created 1000 users and 5000 folders")
EOF
```

### Migration Execution

```bash
# Run migration with timing
time alembic upgrade head
-- Expected: Completes in <30 seconds
```

### Verification

```bash
# Verify all users became workspace members
sqlite3 langflow.db "SELECT COUNT(*) FROM workspace_member;"
-- Expected: 1000

# Verify all folders have workspace_id
sqlite3 langflow.db "SELECT COUNT(*) FROM folder WHERE workspace_id IS NOT NULL;"
-- Expected: 5000
```

### Success Criteria

- ✅ Migration completes in reasonable time (<1 minute)
- ✅ All 1000 users assigned to default workspace
- ✅ All 5000 folders assigned to default workspace
- ✅ No performance issues or timeouts

---

## Common Issues and Troubleshooting

### Issue 1: "Target database is not up to date"

**Symptom:** Alembic refuses to run migration

**Solution:**
```bash
# Check current revision
alembic current

# If database is behind, upgrade to latest
alembic upgrade head

# If database is ahead, downgrade first
alembic downgrade fd531f8868b1
```

### Issue 2: Foreign Key Constraint Violations

**Symptom:** Migration fails with FK constraint errors

**Solution:**
```bash
# For SQLite, ensure foreign keys are enabled
sqlite3 langflow.db "PRAGMA foreign_keys = ON;"

# For PostgreSQL, check if referenced tables exist
psql -d langflow_test -c "\dt"
```

### Issue 3: "Table already exists"

**Symptom:** Migration fails because table exists

**Solution:**
The migration should handle this gracefully with `if "table_name" not in existing_tables` checks. If not, manually drop the conflicting table:

```bash
sqlite3 langflow.db "DROP TABLE IF EXISTS problematic_table;"
alembic upgrade head
```

### Issue 4: Data Migration Takes Too Long

**Symptom:** Migration hangs on data migration step

**Solution:**
```bash
# Check if migration is still running
ps aux | grep alembic

# If stuck, may need to optimize bulk insert for large datasets
# Consider breaking into smaller batches
```

### Issue 5: Rollback Fails

**Symptom:** `alembic downgrade` fails

**Solution:**
```bash
# Check which tables exist
sqlite3 langflow.db ".tables"

# Manually drop RBAC tables if needed
sqlite3 langflow.db <<EOF
DROP TABLE IF EXISTS invitation;
DROP TABLE IF EXISTS environment;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS sso_integration;
DROP TABLE IF EXISTS role_assignment;
DROP TABLE IF EXISTS service_account;
DROP TABLE IF EXISTS role_permission;
DROP TABLE IF EXISTS permission;
DROP TABLE IF EXISTS role;
DROP TABLE IF EXISTS user_group_member;
DROP TABLE IF EXISTS user_group;
DROP TABLE IF EXISTS workspace_member;
DROP TABLE IF EXISTS workspace;
EOF

# Mark migration as rolled back
alembic stamp fd531f8868b1
```

---

## Automated Test Script

Save this as `test_migration.sh` for automated testing:

```bash
#!/bin/bash
set -e

echo "=== RBAC Migration Test Suite ==="

# Test 1: Fresh database
echo "Test 1: Fresh database"
rm -f langflow.db langflow.db-*
alembic upgrade head
sqlite3 langflow.db "SELECT COUNT(*) FROM workspace;" | grep -q "0" && echo "✅ No default workspace on fresh DB" || echo "❌ FAIL"

# Test 2: With existing users
echo "Test 2: Existing users"
alembic downgrade fd531f8868b1
sqlite3 langflow.db <<EOF
INSERT INTO user (id, username, password, is_active, is_superuser, create_at, updated_at)
VALUES ('11111111-1111-1111-1111-111111111111', 'testuser', '\$2b\$12\$hash', 1, 0, datetime('now'), datetime('now'));
EOF
alembic upgrade head
sqlite3 langflow.db "SELECT COUNT(*) FROM workspace WHERE slug='default';" | grep -q "1" && echo "✅ Default workspace created" || echo "❌ FAIL"
sqlite3 langflow.db "SELECT COUNT(*) FROM workspace_member;" | grep -q "1" && echo "✅ User assigned to workspace" || echo "❌ FAIL"

# Test 3: Rollback
echo "Test 3: Rollback"
alembic downgrade -1
sqlite3 langflow.db ".tables" | grep -q "workspace" && echo "❌ FAIL - workspace table still exists" || echo "✅ Rollback successful"

# Test 4: Re-apply
echo "Test 4: Re-apply migration"
alembic upgrade head
sqlite3 langflow.db "SELECT COUNT(*) FROM workspace;" | grep -q "1" && echo "✅ Migration re-applied successfully" || echo "❌ FAIL"

echo "=== All tests completed ==="
```

---

## Success Criteria Checklist

### Migration Generation
- [x] Migration file created with correct revision ID
- [x] All 13 new tables defined
- [x] All table modifications defined
- [x] Data migration logic included
- [x] Rollback (downgrade) logic complete

### Fresh Database Test
- [ ] All RBAC tables created
- [ ] All indexes created
- [ ] All foreign keys created
- [ ] No default workspace created
- [ ] folder.workspace_id is NOT NULL
- [ ] flow.environment_id is nullable

### Existing Data Test
- [ ] Default workspace created
- [ ] All existing users assigned to workspace
- [ ] All users have 'owner' role
- [ ] All existing folders assigned to workspace
- [ ] No folders have NULL workspace_id

### Rollback Test
- [ ] All RBAC tables dropped
- [ ] RBAC columns removed from modified tables
- [ ] Existing data intact
- [ ] Migration can be re-applied

### Production Readiness
- [ ] Works on SQLite
- [ ] Works on PostgreSQL
- [ ] Handles large datasets (1000+ users)
- [ ] Idempotent (can run multiple times)
- [ ] Error handling works

---

## Next Steps

After successful migration testing:

1. **Task 1.3:** Seed system roles and permissions
2. **Task 1.4:** Implement RBAC API endpoints
3. **Task 1.5:** Add permission checking middleware
4. **Task 1.6:** Frontend RBAC guards and components

---

## References

- **Migration File:** `src/backend/base/langflow/alembic/versions/0b4b33664011_add_rbac_models_with_workspace_groups.py`
- **Implementation Plan:** `docs/implementation-plans/RBAC_IMPLEMENTATION_PLAN_V3_FINAL.md` (Task 1.2, lines 618-791)
- **Model Definitions:** `src/backend/base/langflow/services/database/models/`
- **Alembic Documentation:** https://alembic.sqlalchemy.org/

---

**End of Testing Guide**

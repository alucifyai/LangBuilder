# Langflow Scripts

Utility scripts for database migrations, maintenance tasks, and administrative operations.

## Available Scripts

### migrate_user_emails.py

**Purpose:** Populate email field for existing users who have null email values.

**Why Needed:** Task 3.9 added an email field to enable email-based invitation matching (PRD Story 1.1 @AC6). Existing users need email addresses for the invitation workflow to function correctly.

**Status:** ✅ Production Ready

#### Quick Start

**Dry Run (Preview Changes):**
```bash
export LANGFLOW_DATABASE_URL="postgresql://user:pass@localhost/langflow"
python -m langflow.scripts.migrate_user_emails --dry-run
```

**Execute Migration:**
```bash
python -m langflow.scripts.migrate_user_emails
```

**Custom Email Domain:**
```bash
python -m langflow.scripts.migrate_user_emails --domain company.com
```

#### Full Documentation

See comprehensive documentation:
- **Implementation Report:** `docs/code-generations/TASK_3.9_GAP_FIX_IMPLEMENTATION_REPORT.md`
- **Help Command:** `python -m langflow.scripts.migrate_user_emails --help`

#### Features

- ✅ **Safe Dry-Run Mode** - Preview changes before applying
- ✅ **Smart Email Derivation** - Derives emails from usernames intelligently
- ✅ **Validation** - Ensures all emails are valid format
- ✅ **Error Handling** - Continues on individual failures
- ✅ **Statistics** - Detailed migration statistics
- ✅ **Logging** - Comprehensive audit trail
- ✅ **CLI Interface** - Easy command-line usage

#### When to Run

- **Required:** Before production deployment of Task 3.9 (Invitation Management API)
- **Required:** When upgrading from pre-Task 3.9 database
- **Optional:** After importing users from external systems

#### Exit Codes

- `0` - Success (all users migrated or no migration needed)
- `1` - Failure (errors occurred or database URL not provided)

---

## Adding New Scripts

When adding new scripts to this package:

1. Create script file in `src/backend/base/langflow/scripts/`
2. Add CLI entry point with `if __name__ == "__main__":`
3. Create comprehensive tests in `src/backend/tests/unit/scripts/`
4. Document usage in this README
5. Add to `__init__.py` if needed for imports

## Script Guidelines

- **Use async/await** for database operations
- **Provide dry-run mode** for destructive operations
- **Include comprehensive logging** with loguru
- **Collect statistics** for audit trail
- **Handle errors gracefully** - don't stop on first failure
- **Support environment variables** for configuration
- **Provide CLI interface** with argparse
- **Document thoroughly** with docstrings and README

---

For more information, see the main Langflow documentation at `docs/`.

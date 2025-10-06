# Appendix - Useful Commands and Scripts

## Frequently Used Commands

**Backend Development**:
```bash
make init              # Install all dependencies
make backend           # Start backend dev server (auto-reload)
make unit_tests        # Run backend unit tests
make test              # Run all backend tests
make format            # Format Python code (ruff)
make lint              # Lint Python code
```

**Frontend Development**:
```bash
make frontend          # Start frontend dev server (Vite)
make build_frontend    # Build frontend static files
npm run type-check     # TypeScript type checking
npm run format         # Format with Biome
npm run test           # Run Jest tests
```

**Database**:
```bash
cd src/backend/base/langflow
alembic revision --autogenerate -m "description"  # Generate migration
alembic upgrade head                              # Apply migrations
alembic downgrade -1                              # Rollback one migration
```

**Docker**:
```bash
docker-compose up       # Run full stack in Docker
docker-compose build    # Rebuild containers
```

## Debugging and Troubleshooting

**Backend Logs**:
- Logs output to console (loguru)
- Set `LANGFLOW_LOG_LEVEL=DEBUG` for verbose logging
- Check `logs/` directory if file logging is enabled

**Frontend Dev Tools**:
- React DevTools browser extension
- Network tab for API request inspection
- Zustand DevTools (if enabled)

**Database Inspection**:
```bash
# SQLite
sqlite3 langflow.db
.tables
.schema user

# PostgreSQL
psql $DATABASE_URL
\dt
\d+ user
```

**Common Issues**:

1. **Auto-login not working**: Check `LANGFLOW_SUPERUSER` and `LANGFLOW_SUPERUSER_PASSWORD` env vars are set.

2. **CORS errors**: Verify `LANGFLOW_BACKEND_URL` and CORS settings in backend configuration.

3. **Migration conflicts**: If multiple devs create migrations, may need to merge migration files manually.

4. **Frontend build errors**: Clear `node_modules` and `package-lock.json`, then `npm install`.

5. **Database locked (SQLite)**: SQLite doesn't handle concurrent writes well. Use PostgreSQL for multi-user development.

---

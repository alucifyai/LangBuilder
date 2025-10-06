# Integration Points and External Dependencies

## External Services (Planned)

Based on PRD, these integrations are REQUIRED but NOT YET IMPLEMENTED:

| Service       | Purpose                  | Integration Type | PRD Story | Status      |
| ------------- | ------------------------ | ---------------- | --------- | ----------- |
| SSO (SAML/OIDC) | Enterprise authentication | SAML 2.0/OIDC    | Story 2.2 | Not started |
| SCIM Provider | User/group provisioning  | SCIM 2.0 API     | Story 2.3 | Not started |
| SIEM/SOC      | Audit event streaming    | Webhook/Kafka    | NFR 5.7   | Not started |

## Internal Integration Points

**Database**:
- Configurable via `DATABASE_URL` env var
- Default: SQLite (`langflow.db`)
- Production: PostgreSQL recommended
- Async sessions via SQLModel/SQLAlchemy

**Frontend ↔ Backend Communication**:
- REST API on port 7860 (default)
- WebSocket for real-time flow execution updates (`/api/v1/chat`)
- CORS configured via settings
- Authentication via JWT cookies or API key headers

**Background Jobs**:
- Currently minimal async task handling
- **Needed for RBAC**: SCIM sync, audit log processing, token cleanup

---

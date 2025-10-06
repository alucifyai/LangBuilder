/**
 * TypeScript type definitions for Audit Log.
 *
 * Generated from backend Pydantic schemas in:
 * src/backend/base/langflow/api/v1/audit.py
 * src/backend/base/langflow/services/database/models/audit/model.py
 */

/**
 * Audit action types enum.
 * Maps to AuditAction enum in backend.
 */
export enum AuditAction {
  ROLE_CREATED = "role_created",
  ROLE_UPDATED = "role_updated",
  ROLE_DELETED = "role_deleted",
  GRANT_CREATED = "grant_created",
  GRANT_REVOKED = "grant_revoked",
  PERMISSION_CREATED = "permission_created",
  INVITE_CREATED = "invite_created",
  INVITE_ACCEPTED = "invite_accepted",
}

/**
 * Audit log entry response from backend API.
 * Maps to AuditLogResponse Pydantic schema.
 */
export interface AuditLog {
  id: string;
  timestamp: string; // ISO 8601 datetime
  actor_id: string; // UUID of user who performed action
  action: AuditAction;
  resource_type: string; // "role", "grant", "permission", etc.
  resource_id: string;
  before_state: Record<string, any> | null;
  after_state: Record<string, any> | null;
  metadata: Record<string, any> | null;
}

/**
 * Response from list audit logs endpoint.
 * Maps to AuditLogsListResponse Pydantic schema.
 */
export interface AuditLogsListResponse {
  total_count: number;
  logs: AuditLog[];
}

/**
 * Query parameters for filtering audit logs.
 */
export interface AuditLogFilters {
  resource_type?: string;
  resource_id?: string;
  action?: AuditAction;
  actor_id?: string;
  start_date?: string; // ISO 8601 datetime
  end_date?: string; // ISO 8601 datetime
  limit?: number;
}

/**
 * Audit log diff item for displaying changes.
 */
export interface AuditLogDiff {
  field: string;
  before: any;
  after: any;
  changed: boolean;
}

/**
 * Role state from audit log (before/after).
 */
export interface AuditRoleState {
  name: string;
  permissions: string[];
  version: number;
}

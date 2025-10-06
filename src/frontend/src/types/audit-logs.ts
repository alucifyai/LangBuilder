/**
 * Enhanced Audit Log Types
 * Comprehensive audit logging for compliance and security
 */

export interface AuditLog {
  id: string;
  event_type: string;
  action: string;
  severity: string;
  status: string;
  actor_id: string | null;
  actor_type: string | null;
  actor_email: string | null;
  target_id: string | null;
  target_type: string | null;
  target_name: string | null;
  organization_id: string | null;
  workspace_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  session_id: string | null;
  request_id: string | null;
  changes: Record<string, any> | null;
  metadata: Record<string, any> | null;
  error_code: string | null;
  error_message: string | null;
  compliance_tags: string[] | null;
  retention_days: number | null;
  timestamp: string; // ISO datetime
}

export interface AuditLogListResponse {
  logs: AuditLog[];
  total: number;
  limit: number;
  offset: number;
}

export interface SecurityEventsSummary {
  total_events: number;
  critical_count: number;
  error_count: number;
  warning_count: number;
  failed_auth_count: number;
  events: AuditLog[];
}

export interface ExportAuditLogsRequest {
  export_type: string;
  format: "json" | "csv";
  start_date: string; // ISO datetime
  end_date: string; // ISO datetime
  filters?: Record<string, any>;
  reason?: string;
}

export interface AuditLogExport {
  id: string;
  export_type: string;
  format: string;
  start_date: string;
  end_date: string;
  record_count: number;
  file_hash: string | null;
  exported_by: string;
  reason: string | null;
  created_at: string;
}

export interface FailedAuthAttempt {
  count: number;
  first_attempt: string;
  last_attempt: string;
  attempts: AuditLog[];
}

export interface FailedAuthByIP {
  [ip: string]: FailedAuthAttempt;
}

// Filter options
export interface AuditLogFilters {
  event_type?: string;
  action?: string;
  actor_id?: string;
  target_id?: string;
  target_type?: string;
  organization_id?: string;
  workspace_id?: string;
  severity?: string;
  status?: string;
  ip_address?: string;
  start_date?: string;
  end_date?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

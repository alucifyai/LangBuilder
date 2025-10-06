/**
 * API client for Enhanced Audit Logs
 */

import axios from "axios";
import type {
  AuditLog,
  AuditLogExport,
  AuditLogFilters,
  AuditLogListResponse,
  ExportAuditLogsRequest,
  FailedAuthByIP,
  SecurityEventsSummary,
} from "../types/audit-logs";

const API_BASE = "/api/v1/audit-logs";

/**
 * List audit logs with filtering and pagination
 */
export async function listAuditLogs(
  filters: AuditLogFilters = {}
): Promise<AuditLogListResponse> {
  const response = await axios.get<AuditLogListResponse>(API_BASE, {
    params: filters,
  });
  return response.data;
}

/**
 * Get a specific audit log entry
 */
export async function getAuditLog(logId: string): Promise<AuditLog> {
  const response = await axios.get<AuditLog>(`${API_BASE}/${logId}`);
  return response.data;
}

/**
 * Get audit logs for a specific actor
 */
export async function getAuditLogsByActor(
  actorId: string,
  limit: number = 100
): Promise<AuditLog[]> {
  const response = await axios.get<AuditLog[]>(`${API_BASE}/actor/${actorId}`, {
    params: { limit },
  });
  return response.data;
}

/**
 * Get audit logs for a specific target resource
 */
export async function getAuditLogsByTarget(
  targetId: string,
  targetType?: string,
  limit: number = 100
): Promise<AuditLog[]> {
  const response = await axios.get<AuditLog[]>(
    `${API_BASE}/target/${targetId}`,
    {
      params: { target_type: targetType, limit },
    }
  );
  return response.data;
}

/**
 * Get security events summary
 */
export async function getSecurityEvents(
  hours: number = 24
): Promise<SecurityEventsSummary> {
  const response = await axios.get<SecurityEventsSummary>(
    `${API_BASE}/security/events`,
    {
      params: { hours },
    }
  );
  return response.data;
}

/**
 * Get failed authentication attempts grouped by IP
 */
export async function getFailedAuthAttempts(
  hours: number = 24,
  minAttempts: number = 3
): Promise<FailedAuthByIP> {
  const response = await axios.get<FailedAuthByIP>(
    `${API_BASE}/security/failed-auth`,
    {
      params: { hours, min_attempts: minAttempts },
    }
  );
  return response.data;
}

/**
 * Export audit logs
 */
export async function exportAuditLogs(
  request: ExportAuditLogsRequest
): Promise<Blob> {
  const response = await axios.post(`${API_BASE}/export`, request, {
    responseType: "blob",
  });
  return response.data;
}

/**
 * List audit log export history
 */
export async function listAuditExports(
  exportedBy?: string,
  exportType?: string,
  limit: number = 50
): Promise<AuditLogExport[]> {
  const response = await axios.get<AuditLogExport[]>(
    `${API_BASE}/exports/history`,
    {
      params: { exported_by: exportedBy, export_type: exportType, limit },
    }
  );
  return response.data;
}

/**
 * Clean up old audit logs
 */
export async function cleanupOldAuditLogs(
  retentionDays: number = 90
): Promise<{ deleted_count: number; message: string }> {
  const response = await axios.post<{ deleted_count: number; message: string }>(
    `${API_BASE}/cleanup`,
    null,
    {
      params: { retention_days: retentionDays },
    }
  );
  return response.data;
}

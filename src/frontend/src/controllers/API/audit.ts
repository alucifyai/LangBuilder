/**
 * API client functions for Audit Log.
 *
 * Provides functions to interact with audit log endpoints:
 * - GET /api/v1/audit/ - List audit logs with filtering
 * - GET /api/v1/audit/{audit_id} - Get a specific audit log entry
 */

import { BASE_URL_API } from "../../constants/constants";
import { api } from "./api";
import type {
  AuditLog,
  AuditLogFilters,
  AuditLogsListResponse,
} from "../../types/audit";

const AUDIT_ENDPOINT = `${BASE_URL_API}audit/`;

/**
 * List audit logs with optional filtering.
 *
 * @param filters - Optional filters for querying audit logs
 * @returns Promise with audit logs list response
 * @throws Error if request fails or user is not admin
 */
export async function listAuditLogs(
  filters?: AuditLogFilters
): Promise<AuditLogsListResponse> {
  try {
    const params = new URLSearchParams();

    if (filters?.resource_type) {
      params.append("resource_type", filters.resource_type);
    }
    if (filters?.resource_id) {
      params.append("resource_id", filters.resource_id);
    }
    if (filters?.action) {
      params.append("action", filters.action);
    }
    if (filters?.actor_id) {
      params.append("actor_id", filters.actor_id);
    }
    if (filters?.start_date) {
      params.append("start_date", filters.start_date);
    }
    if (filters?.end_date) {
      params.append("end_date", filters.end_date);
    }
    if (filters?.limit) {
      params.append("limit", filters.limit.toString());
    }

    const url = params.toString()
      ? `${AUDIT_ENDPOINT}?${params.toString()}`
      : AUDIT_ENDPOINT;

    const response = await api.get<AuditLogsListResponse>(url);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view audit logs");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch audit logs"
    );
  }
}

/**
 * Get a specific audit log entry by ID.
 *
 * @param auditId - Audit log entry ID to fetch
 * @returns Promise with audit log data
 * @throws Error if request fails or audit log not found
 */
export async function getAuditLog(auditId: string): Promise<AuditLog> {
  try {
    const response = await api.get<AuditLog>(`${AUDIT_ENDPOINT}${auditId}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Audit log entry not found");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view audit logs");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch audit log"
    );
  }
}

/**
 * List audit logs for a specific resource.
 *
 * Convenience function for filtering by resource type and ID.
 *
 * @param resourceType - Resource type (e.g., "role", "grant")
 * @param resourceId - Optional resource ID
 * @param limit - Optional limit (default: 100)
 * @returns Promise with audit logs for the resource
 */
export async function listAuditLogsForResource(
  resourceType: string,
  resourceId?: string,
  limit: number = 100
): Promise<AuditLogsListResponse> {
  return listAuditLogs({
    resource_type: resourceType,
    resource_id: resourceId,
    limit,
  });
}

/**
 * List audit logs for a specific actor (user).
 *
 * Convenience function for filtering by actor ID.
 *
 * @param actorId - User ID who performed actions
 * @param limit - Optional limit (default: 100)
 * @returns Promise with audit logs for the actor
 */
export async function listAuditLogsByActor(
  actorId: string,
  limit: number = 100
): Promise<AuditLogsListResponse> {
  return listAuditLogs({
    actor_id: actorId,
    limit,
  });
}

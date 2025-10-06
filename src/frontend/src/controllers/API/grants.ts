/**
 * API client functions for Grant Management.
 *
 * Provides functions to interact with grant (role assignment) endpoints:
 * - POST /api/v1/grants/ - Create a new grant
 * - GET /api/v1/grants/{grant_id} - Get a specific grant
 * - GET /api/v1/grants/ - List grants with filtering
 * - PATCH /api/v1/grants/{grant_id} - Update a grant
 * - DELETE /api/v1/grants/{grant_id} - Revoke a grant
 */

import { BASE_URL_API } from "../../constants/constants";
import { api } from "./api";
import type {
  Grant,
  GrantCreateRequest,
  GrantUpdateRequest,
  GrantsListResponse,
  GrantFilters,
  PrincipalType,
  ScopeType,
} from "../../types/grant";

const GRANTS_ENDPOINT = `${BASE_URL_API}grants/`;

/**
 * Create a new grant (role assignment).
 *
 * @param data - Grant creation data
 * @returns Promise with created grant
 * @throws Error if request fails or validation errors occur
 */
export async function createGrant(data: GrantCreateRequest): Promise<Grant> {
  try {
    const response = await api.post<Grant>(GRANTS_ENDPOINT, data);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      const detail = error.response?.data?.detail || "";
      if (detail.includes("Role")) {
        throw new Error("Selected role not found");
      }
      if (detail.includes("User")) {
        throw new Error("Selected user not found");
      }
      throw new Error(detail);
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to create grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to create grant"
    );
  }
}

/**
 * Get a specific grant by ID.
 *
 * @param grantId - Grant ID to fetch
 * @returns Promise with grant data
 * @throws Error if request fails or grant not found
 */
export async function getGrant(grantId: string): Promise<Grant> {
  try {
    const response = await api.get<Grant>(`${GRANTS_ENDPOINT}${grantId}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Grant not found");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch grant"
    );
  }
}

/**
 * List grants with optional filtering.
 *
 * @param filters - Optional filters for querying grants
 * @returns Promise with grants list response
 * @throws Error if request fails
 */
export async function listGrants(
  filters?: GrantFilters
): Promise<GrantsListResponse> {
  try {
    const params = new URLSearchParams();

    if (filters?.principal_type) {
      params.append("principal_type", filters.principal_type);
    }
    if (filters?.principal_id) {
      params.append("principal_id", filters.principal_id);
    }
    if (filters?.scope_type) {
      params.append("scope_type", filters.scope_type);
    }
    if (filters?.scope_id) {
      params.append("scope_id", filters.scope_id);
    }
    if (filters?.role_id) {
      params.append("role_id", filters.role_id);
    }

    const url = params.toString()
      ? `${GRANTS_ENDPOINT}?${params.toString()}`
      : GRANTS_ENDPOINT;

    const response = await api.get<GrantsListResponse>(url);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch grants"
    );
  }
}

/**
 * Update a grant (change expiration or scope).
 *
 * @param grantId - Grant ID to update
 * @param data - Grant update data
 * @returns Promise with updated grant
 * @throws Error if request fails or grant not found
 */
export async function updateGrant(
  grantId: string,
  data: GrantUpdateRequest
): Promise<Grant> {
  try {
    const response = await api.patch<Grant>(`${GRANTS_ENDPOINT}${grantId}`, data);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Grant not found");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to update grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to update grant"
    );
  }
}

/**
 * Revoke a grant (delete).
 *
 * @param grantId - Grant ID to revoke
 * @returns Promise that resolves when grant is revoked
 * @throws Error if request fails
 */
export async function revokeGrant(grantId: string): Promise<void> {
  try {
    await api.delete(`${GRANTS_ENDPOINT}${grantId}`);
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Grant not found");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to revoke grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to revoke grant"
    );
  }
}

/**
 * List grants for a specific principal.
 *
 * Convenience function for filtering by principal type and ID.
 *
 * @param principalType - Principal type (user, group, service_account)
 * @param principalId - Principal ID
 * @returns Promise with grants for the principal
 */
export async function listGrantsForPrincipal(
  principalType: PrincipalType,
  principalId: string
): Promise<GrantsListResponse> {
  try {
    const response = await api.get<GrantsListResponse>(
      `${GRANTS_ENDPOINT}principal/${principalType}/${principalId}`
    );
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch grants for principal"
    );
  }
}

/**
 * List grants for a specific scope.
 *
 * Convenience function for filtering by scope type and ID.
 *
 * @param scopeType - Scope type (workspace, project, environment, flow, component)
 * @param scopeId - Scope ID
 * @returns Promise with grants for the scope
 */
export async function listGrantsForScope(
  scopeType: ScopeType,
  scopeId: string
): Promise<GrantsListResponse> {
  try {
    const response = await api.get<GrantsListResponse>(
      `${GRANTS_ENDPOINT}scope/${scopeType}/${scopeId}`
    );
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view grants");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch grants for scope"
    );
  }
}

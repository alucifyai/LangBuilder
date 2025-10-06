/**
 * API client functions for Role Management.
 *
 * Provides functions to interact with role management endpoints:
 * - GET /api/v1/roles/ - List all roles
 * - POST /api/v1/roles/ - Create a new role
 * - GET /api/v1/roles/{role_id} - Get a specific role
 * - PATCH /api/v1/roles/{role_id} - Update a role
 * - DELETE /api/v1/roles/{role_id} - Delete a role
 */

import { BASE_URL_API } from "../../constants/constants";
import { api } from "./api";
import type {
  Role,
  RoleCreateRequest,
  RoleUpdateRequest,
  RolesListResponse,
} from "../../types/role";

const ROLES_ENDPOINT = `${BASE_URL_API}roles/`;

/**
 * List all roles.
 *
 * @returns Promise with roles list response
 * @throws Error if request fails or user is not admin
 */
export async function listRoles(): Promise<RolesListResponse> {
  try {
    const response = await api.get<RolesListResponse>(ROLES_ENDPOINT);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view roles");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch roles"
    );
  }
}

/**
 * Get a specific role by ID.
 *
 * @param roleId - Role ID to fetch
 * @returns Promise with role data
 * @throws Error if request fails or role not found
 */
export async function getRole(roleId: string): Promise<Role> {
  try {
    const response = await api.get<Role>(`${ROLES_ENDPOINT}${roleId}`);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Role not found");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to view roles");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to fetch role"
    );
  }
}

/**
 * Create a new role.
 *
 * @param data - Role creation data (name and permissions)
 * @returns Promise with created role
 * @throws Error if request fails or validation fails
 */
export async function createRole(data: RoleCreateRequest): Promise<Role> {
  try {
    const response = await api.post<Role>(ROLES_ENDPOINT, data);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 409) {
      throw new Error("Role name must be unique");
    }
    if (error.response?.status === 400) {
      const detail = error.response?.data?.detail || "";
      if (detail.includes("Unknown permission id")) {
        throw new Error("Invalid permission selected");
      }
      throw new Error(detail || "Invalid role data");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to create roles");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to create role"
    );
  }
}

/**
 * Update an existing role.
 *
 * @param roleId - Role ID to update
 * @param data - Role update data (name and/or permissions)
 * @returns Promise with updated role
 * @throws Error if request fails or validation fails
 */
export async function updateRole(
  roleId: string,
  data: RoleUpdateRequest
): Promise<Role> {
  try {
    const response = await api.patch<Role>(`${ROLES_ENDPOINT}${roleId}`, data);
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Role not found");
    }
    if (error.response?.status === 409) {
      throw new Error("Role name must be unique");
    }
    if (error.response?.status === 400) {
      const detail = error.response?.data?.detail || "";
      if (detail.includes("Unknown permission id")) {
        throw new Error("Invalid permission selected");
      }
      throw new Error(detail || "Invalid role data");
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to update roles");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to update role"
    );
  }
}

/**
 * Delete a role.
 *
 * @param roleId - Role ID to delete
 * @returns Promise that resolves when deletion is complete
 * @throws Error if request fails or role has active grants
 */
export async function deleteRole(roleId: string): Promise<void> {
  try {
    await api.delete(`${ROLES_ENDPOINT}${roleId}`);
  } catch (error: any) {
    if (error.response?.status === 404) {
      throw new Error("Role not found");
    }
    if (error.response?.status === 409) {
      const detail = error.response?.data?.detail || "";
      // Extract grant count from error message if available
      const match = detail.match(/(\d+) active grants/);
      const count = match ? match[1] : "";
      throw new Error(
        count
          ? `Cannot delete role: ${count} active grants exist`
          : "Cannot delete role: Active grants exist"
      );
    }
    if (error.response?.status === 403) {
      throw new Error("Admin privileges required to delete roles");
    }
    throw new Error(
      error.response?.data?.detail || "Failed to delete role"
    );
  }
}

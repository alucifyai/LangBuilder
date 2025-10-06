/**
 * TypeScript type definitions for Role Management.
 *
 * Generated from backend Pydantic schemas in:
 * src/backend/base/langflow/api/v1/roles.py
 */

/**
 * Role response from backend API.
 * Maps to RoleResponse Pydantic schema.
 */
export interface Role {
  id: string;
  name: string;
  permissions: string[];
  version: number;
  created_at: string; // ISO 8601 datetime
  updated_at: string; // ISO 8601 datetime
}

/**
 * Request payload for creating a new role.
 * Maps to RoleCreate Pydantic schema.
 */
export interface RoleCreateRequest {
  name: string;
  permissions: string[];
}

/**
 * Request payload for updating a role.
 * Maps to RoleUpdate Pydantic schema.
 */
export interface RoleUpdateRequest {
  name?: string;
  permissions?: string[];
}

/**
 * Response from list roles endpoint.
 * Maps to RolesListResponse Pydantic schema.
 */
export interface RolesListResponse {
  total_count: number;
  roles: Role[];
}

/**
 * Permission definition from permission catalog.
 */
export interface Permission {
  id: string; // e.g., "flows:create", "deploy_environment"
  resource_type: string;
  action: string;
  description: string;
}

/**
 * Permission list response.
 */
export interface PermissionsListResponse {
  total_count: number;
  permissions: Permission[];
}

/**
 * Form state for role creation/editing.
 */
export interface RoleFormData {
  name: string;
  permissions: string[];
}

/**
 * Error response from role API endpoints.
 */
export interface RoleApiError {
  detail: string;
}

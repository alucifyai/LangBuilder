/**
 * TypeScript types for RBAC API requests and responses.
 * Maps to backend Pydantic schemas in langbuilder.api.v1.schemas
 */

/**
 * Role enumeration matching backend RoleEnum
 */
export type RoleEnum = "Admin" | "Owner" | "Editor" | "Viewer";

/**
 * Permission enumeration matching backend PermissionEnum
 */
export type PermissionEnum = "CREATE" | "READ" | "UPDATE" | "DELETE";

/**
 * Scope type enumeration matching backend ScopeTypeEnum
 */
export type ScopeTypeEnum = "GLOBAL" | "PROJECT" | "FLOW";

/**
 * Role response type matching backend RoleRead schema
 */
export interface RoleRead {
  /** UUID of the role */
  id: string;
  name: RoleEnum;
  description: string;
}

/**
 * Assignment create request matching backend AssignmentCreate schema
 */
export interface AssignmentCreate {
  /** UUID of the user */
  user_id: string;
  role_name: RoleEnum;
  scope_type: ScopeTypeEnum;
  /** UUID of the scope (project or flow), null for GLOBAL scope */
  scope_id?: string | null;
}

/**
 * Assignment update request matching backend AssignmentUpdate schema
 */
export interface AssignmentUpdate {
  new_role_name: RoleEnum;
}

/**
 * Assignment response matching backend AssignmentResponse schema
 */
export interface AssignmentResponse {
  /** UUID of the assignment */
  id: string;
  /** UUID of the user */
  user_id: string;
  /** UUID of the role */
  role_id: string;
  role_name: RoleEnum;
  scope_type: ScopeTypeEnum;
  /** UUID of the scope (project or flow), null for GLOBAL scope */
  scope_id: string | null;
  is_immutable: boolean;
  created_at: string;
}

/**
 * Permission check request matching backend PermissionCheckRequest schema
 */
export interface PermissionCheckRequest {
  permission: PermissionEnum;
  scope_type: ScopeTypeEnum;
  /** UUID of the scope (project or flow), null for GLOBAL scope */
  scope_id?: string | null;
}

/**
 * Permission check response matching backend PermissionCheckResponse schema
 */
export interface PermissionCheckResponse {
  has_permission: boolean;
  /** UUID of the user */
  user_id: string;
  permission: PermissionEnum;
  scope_type: ScopeTypeEnum;
  /** UUID of the scope (project or flow), null for GLOBAL scope */
  scope_id: string | null;
}

/**
 * Filter parameters for GET /assignments endpoint
 */
export interface AssignmentFilters {
  /** UUID of the user to filter by */
  user_id?: string;
  role_name?: RoleEnum;
  scope_type?: ScopeTypeEnum;
  /** UUID of the scope (project or flow) to filter by */
  scope_id?: string;
}

/**
 * Grant (Role Assignment) Types
 *
 * Types for managing role grants (assignments of roles to principals within scopes).
 */

export enum PrincipalType {
  USER = "user",
  GROUP = "group",
  SERVICE_ACCOUNT = "service_account",
}

export enum ScopeType {
  WORKSPACE = "workspace",
  PROJECT = "project",
  ENVIRONMENT = "environment",
  FLOW = "flow",
  COMPONENT = "component",
}

export interface Grant {
  id: string;
  principal_type: PrincipalType;
  principal_id: string;
  role_id: string;
  scope_type: ScopeType;
  scope_id: string;
  created_at: string;
  expires_at: string | null;
}

export interface GrantCreateRequest {
  principal_type: PrincipalType;
  principal_id: string;
  role_id: string;
  scope_type: ScopeType;
  scope_id: string;
  expires_at?: string | null;
}

export interface GrantUpdateRequest {
  expires_at?: string | null;
  scope_type?: ScopeType;
  scope_id?: string;
}

export interface GrantsListResponse {
  grants: Grant[];
}

export interface GrantFormData {
  principal_type: PrincipalType;
  principal_id: string;
  role_id: string;
  scope_type: ScopeType;
  scope_id: string;
  expires_at: string | null;
}

export interface GrantFilters {
  principal_type?: PrincipalType;
  principal_id?: string;
  scope_type?: ScopeType;
  scope_id?: string;
  role_id?: string;
}

export interface GrantApiError {
  detail: string;
}

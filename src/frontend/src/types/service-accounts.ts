/**
 * Service Accounts and API Tokens Types
 */

export interface ServiceAccountCreate {
  name: string;
  description?: string;
  organization_id: string;
}

export interface ServiceAccountUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface ServiceAccountResponse {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  created_by: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
}

export interface TokenCreateRequest {
  name: string;
  scopes: string[];
  expires_in_days?: number;
}

export interface TokenResponse {
  id: string;
  service_account_id: string;
  name: string;
  token_prefix: string;
  scopes: string[];
  expires_at?: string;
  last_used_at?: string;
  last_used_ip?: string;
  use_count: number;
  is_active: boolean;
  created_at: string;
  created_by: string;
}

export interface TokenCreateResponse extends TokenResponse {
  token: string; // Only returned once!
}

export interface TokenRevokeRequest {
  reason?: string;
}

export enum TokenScope {
  READ = "read",
  WRITE = "write",
  ADMIN = "admin",
  FLOWS_READ = "flows:read",
  FLOWS_WRITE = "flows:write",
  PROJECTS_READ = "projects:read",
  PROJECTS_WRITE = "projects:write",
}

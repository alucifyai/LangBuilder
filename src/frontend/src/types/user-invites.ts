/**
 * User Invites Types
 */

export enum InviteStatus {
  PENDING = "pending",
  ACCEPTED = "accepted",
  EXPIRED = "expired",
  REVOKED = "revoked",
}

export interface InviteCreate {
  email: string;
  role_ids: string[];
  expires_in_days?: number;
}

export interface InviteResponse {
  id: string;
  email: string;
  invited_by: string;
  organization_id: string;
  role_ids: string[];
  status: InviteStatus;
  invite_url: string;
  created_at: string;
  expires_at: string;
  accepted_at?: string;
  revoked_at?: string;
}

export interface AcceptInviteRequest {
  username: string;
  password: string;
}

export interface RevokeInviteRequest {
  reason?: string;
}

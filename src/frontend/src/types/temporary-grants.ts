/**
 * Temporary Grants Types
 * Time-limited role assignments with auto-expiration
 */

export interface TemporaryGrant {
  id: string;
  grant_id: string;
  starts_at: string; // ISO datetime
  expires_at: string; // ISO datetime
  auto_revoke: boolean;
  notify_before_expiry: boolean;
  notification_hours: number;
  is_expired: boolean;
  expired_at: string | null; // ISO datetime
  notified_at: string | null; // ISO datetime
  extension_count: number;
  max_extensions: number | null;
  extended_by: string | null;
  reason: string | null;
  created_by: string;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface CreateTemporaryGrantRequest {
  grant_id: string;
  expires_at: string; // ISO datetime
  starts_at?: string; // ISO datetime
  auto_revoke?: boolean;
  notify_before_expiry?: boolean;
  notification_hours?: number;
  max_extensions?: number | null;
  reason?: string | null;
}

export interface ExtendTemporaryGrantRequest {
  new_expires_at: string; // ISO datetime
}

export interface ExpirationProcessResult {
  processed_count: number;
  message: string;
}

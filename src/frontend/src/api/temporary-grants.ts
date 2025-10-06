/**
 * API client for Temporary Grants
 */

import axios from "axios";
import type {
  CreateTemporaryGrantRequest,
  ExpirationProcessResult,
  ExtendTemporaryGrantRequest,
  TemporaryGrant,
} from "../types/temporary-grants";

const API_BASE = "/api/v1/temporary-grants";

/**
 * Create a new temporary grant
 */
export async function createTemporaryGrant(
  request: CreateTemporaryGrantRequest
): Promise<TemporaryGrant> {
  const response = await axios.post<TemporaryGrant>(API_BASE, request);
  return response.data;
}

/**
 * List all temporary grants
 */
export async function listTemporaryGrants(
  includeExpired: boolean = false
): Promise<TemporaryGrant[]> {
  const response = await axios.get<TemporaryGrant[]>(API_BASE, {
    params: { include_expired: includeExpired },
  });
  return response.data;
}

/**
 * List grants expiring soon
 */
export async function listExpiringSoon(
  hours: number = 24
): Promise<TemporaryGrant[]> {
  const response = await axios.get<TemporaryGrant[]>(
    `${API_BASE}/expiring-soon`,
    {
      params: { hours },
    }
  );
  return response.data;
}

/**
 * Get temporary grant by ID
 */
export async function getTemporaryGrant(
  tempGrantId: string
): Promise<TemporaryGrant> {
  const response = await axios.get<TemporaryGrant>(
    `${API_BASE}/${tempGrantId}`
  );
  return response.data;
}

/**
 * Get temporary grant by base grant ID
 */
export async function getTemporaryGrantByGrant(
  grantId: string
): Promise<TemporaryGrant> {
  const response = await axios.get<TemporaryGrant>(
    `${API_BASE}/grant/${grantId}`
  );
  return response.data;
}

/**
 * Extend a temporary grant's expiration
 */
export async function extendTemporaryGrant(
  tempGrantId: string,
  request: ExtendTemporaryGrantRequest
): Promise<TemporaryGrant> {
  const response = await axios.post<TemporaryGrant>(
    `${API_BASE}/${tempGrantId}/extend`,
    request
  );
  return response.data;
}

/**
 * Manually expire a temporary grant
 */
export async function expireGrant(
  tempGrantId: string
): Promise<TemporaryGrant> {
  const response = await axios.post<TemporaryGrant>(
    `${API_BASE}/${tempGrantId}/expire`
  );
  return response.data;
}

/**
 * Process all expired grants (admin/scheduled job)
 */
export async function processExpiredGrants(): Promise<ExpirationProcessResult> {
  const response = await axios.post<ExpirationProcessResult>(
    `${API_BASE}/process-expired`
  );
  return response.data;
}

/**
 * Delete temporary grant tracking
 */
export async function deleteTemporaryGrant(
  tempGrantId: string
): Promise<void> {
  await axios.delete(`${API_BASE}/${tempGrantId}`);
}

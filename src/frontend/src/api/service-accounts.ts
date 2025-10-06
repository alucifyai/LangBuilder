/**
 * Service Accounts API Client
 */

import axios from "axios";
import type {
  ServiceAccountCreate,
  ServiceAccountResponse,
  ServiceAccountUpdate,
  TokenCreateRequest,
  TokenCreateResponse,
  TokenResponse,
  TokenRevokeRequest,
} from "../types/service-accounts";

const API_BASE = "/api/v1/service-accounts";

// Service Account Operations
export async function createServiceAccount(
  data: ServiceAccountCreate
): Promise<ServiceAccountResponse> {
  const response = await axios.post<ServiceAccountResponse>(API_BASE, data);
  return response.data;
}

export async function listServiceAccounts(
  organizationId: string,
  skip: number = 0,
  limit: number = 100
): Promise<ServiceAccountResponse[]> {
  const response = await axios.get<ServiceAccountResponse[]>(API_BASE, {
    params: { organization_id: organizationId, skip, limit },
  });
  return response.data;
}

export async function getServiceAccount(
  accountId: string
): Promise<ServiceAccountResponse> {
  const response = await axios.get<ServiceAccountResponse>(
    `${API_BASE}/${accountId}`
  );
  return response.data;
}

export async function updateServiceAccount(
  accountId: string,
  updates: ServiceAccountUpdate
): Promise<ServiceAccountResponse> {
  const response = await axios.patch<ServiceAccountResponse>(
    `${API_BASE}/${accountId}`,
    updates
  );
  return response.data;
}

export async function deleteServiceAccount(accountId: string): Promise<void> {
  await axios.delete(`${API_BASE}/${accountId}`);
}

// API Token Operations
export async function createAPIToken(
  accountId: string,
  data: TokenCreateRequest
): Promise<TokenCreateResponse> {
  const response = await axios.post<TokenCreateResponse>(
    `${API_BASE}/${accountId}/tokens`,
    data
  );
  return response.data;
}

export async function listAPITokens(
  accountId: string,
  includeRevoked: boolean = false
): Promise<TokenResponse[]> {
  const response = await axios.get<TokenResponse[]>(
    `${API_BASE}/${accountId}/tokens`,
    {
      params: { include_revoked: includeRevoked },
    }
  );
  return response.data;
}

export async function revokeAPIToken(
  accountId: string,
  tokenId: string,
  data: TokenRevokeRequest
): Promise<TokenResponse> {
  const response = await axios.post<TokenResponse>(
    `${API_BASE}/${accountId}/tokens/${tokenId}/revoke`,
    data
  );
  return response.data;
}

export async function deleteAPIToken(
  accountId: string,
  tokenId: string
): Promise<void> {
  await axios.delete(`${API_BASE}/${accountId}/tokens/${tokenId}`);
}

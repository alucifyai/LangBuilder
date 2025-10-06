/**
 * SSO API Client
 */

import axios from "axios";
import {
  SSOAuthResponse,
  SSOConfigCreate,
  SSOConfigResponse,
  SSOConfigUpdate,
  SSOEnforcementResponse,
  SSOLoginRequest,
  SSOLoginResponse,
} from "../types/sso";

const API_BASE = "/api/v1/sso";
const API_ADMIN_BASE = "/api/v1/sso/admin";

/**
 * Initiate SSO login flow
 */
export async function initiateSSOLogin(
  request: SSOLoginRequest
): Promise<SSOLoginResponse> {
  const response = await axios.post<SSOLoginResponse>(
    `${API_BASE}/login`,
    request
  );
  return response.data;
}

/**
 * Process OIDC callback (called by redirect handler)
 */
export async function processOIDCCallback(
  code: string,
  state: string | null,
  domain: string
): Promise<SSOAuthResponse> {
  const params = new URLSearchParams();
  params.append("code", code);
  params.append("domain", domain);
  if (state) {
    params.append("state", state);
  }

  const response = await axios.post<SSOAuthResponse>(
    `${API_BASE}/callback/oidc?${params.toString()}`
  );
  return response.data;
}

/**
 * Process SAML callback (called by form post handler)
 */
export async function processSAMLCallback(
  samlResponse: string,
  relayState: string | null,
  domain: string
): Promise<SSOAuthResponse> {
  const params = new URLSearchParams();
  params.append("SAMLResponse", samlResponse);
  params.append("domain", domain);
  if (relayState) {
    params.append("RelayState", relayState);
  }

  const response = await axios.post<SSOAuthResponse>(
    `${API_BASE}/callback/saml?${params.toString()}`
  );
  return response.data;
}

/**
 * Check SSO enforcement level for a domain
 */
export async function checkSSOEnforcement(
  domain: string
): Promise<SSOEnforcementResponse> {
  const response = await axios.get<SSOEnforcementResponse>(
    `${API_BASE}/enforcement/${encodeURIComponent(domain)}`
  );
  return response.data;
}

/**
 * Get SAML SP metadata for IdP configuration
 */
export async function getSAMLMetadata(organizationId: string): Promise<string> {
  const response = await axios.get<string>(
    `${API_BASE}/metadata/${encodeURIComponent(organizationId)}`,
    {
      responseType: "text",
    }
  );
  return response.data;
}

// ============================================================================
// SSO Admin API
// ============================================================================

/**
 * Create SSO configuration (admin only)
 */
export async function createSSOConfig(
  request: SSOConfigCreate
): Promise<SSOConfigResponse> {
  const response = await axios.post<SSOConfigResponse>(
    `${API_ADMIN_BASE}/configs`,
    request
  );
  return response.data;
}

/**
 * Get SSO configuration by ID (admin only)
 */
export async function getSSOConfig(
  configId: string
): Promise<SSOConfigResponse> {
  const response = await axios.get<SSOConfigResponse>(
    `${API_ADMIN_BASE}/configs/${configId}`
  );
  return response.data;
}

/**
 * Get SSO configuration by organization (admin only)
 */
export async function getSSOConfigByOrg(
  organizationId: string
): Promise<SSOConfigResponse> {
  const response = await axios.get<SSOConfigResponse>(
    `${API_ADMIN_BASE}/orgs/${encodeURIComponent(organizationId)}/config`
  );
  return response.data;
}

/**
 * Update SSO configuration (admin only)
 */
export async function updateSSOConfig(
  configId: string,
  updates: SSOConfigUpdate
): Promise<SSOConfigResponse> {
  const response = await axios.patch<SSOConfigResponse>(
    `${API_ADMIN_BASE}/configs/${configId}`,
    updates
  );
  return response.data;
}

/**
 * Delete SSO configuration (admin only)
 */
export async function deleteSSOConfig(configId: string): Promise<void> {
  await axios.delete(`${API_ADMIN_BASE}/configs/${configId}`);
}

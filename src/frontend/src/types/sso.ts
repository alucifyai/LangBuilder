/**
 * SSO Authentication Types
 */

export enum SSOProvider {
  OIDC = "oidc",
  SAML = "saml",
}

export enum SSOEnforcement {
  DISABLED = "disabled",
  OPTIONAL = "optional",
  ENFORCED = "enforced",
}

export interface SSOLoginRequest {
  domain: string;
  redirect_uri: string;
  state?: string;
}

export interface SSOLoginResponse {
  provider: SSOProvider;
  redirect_url: string;
  state?: string;
  request_id?: string;
}

export interface SSOAuthResponse {
  user_id: string;
  email: string;
  session_token: string;
  expires_at: string;
  mfa_verified?: boolean;
}

export interface SSOEnforcementResponse {
  enforcement: SSOEnforcement;
  enabled: boolean;
  message: string;
}

export interface SSOConfigBase {
  domain: string;
  provider_type: SSOProvider;
  enforcement: SSOEnforcement;
  enabled: boolean;

  // OIDC fields
  oidc_issuer?: string;
  oidc_client_id?: string;
  oidc_client_secret?: string;
  oidc_authorization_endpoint?: string;
  oidc_token_endpoint?: string;
  oidc_userinfo_endpoint?: string;
  oidc_jwks_uri?: string;

  // SAML fields
  saml_entity_id?: string;
  saml_sso_url?: string;
  saml_x509_cert?: string;
  saml_slo_url?: string;

  // Attribute mapping
  email_attribute?: string;
  name_attribute?: string;
  groups_attribute?: string;

  // Session settings
  session_timeout_minutes: number;
  allow_clock_skew_seconds: number;
}

export interface SSOConfigCreate extends SSOConfigBase {
  organization_id: string;
}

export interface SSOConfigUpdate {
  domain?: string;
  enforcement?: SSOEnforcement;
  enabled?: boolean;

  // OIDC fields
  oidc_issuer?: string;
  oidc_client_id?: string;
  oidc_client_secret?: string;
  oidc_authorization_endpoint?: string;
  oidc_token_endpoint?: string;
  oidc_userinfo_endpoint?: string;
  oidc_jwks_uri?: string;

  // SAML fields
  saml_entity_id?: string;
  saml_sso_url?: string;
  saml_x509_cert?: string;
  saml_slo_url?: string;

  // Attribute mapping
  email_attribute?: string;
  name_attribute?: string;
  groups_attribute?: string;

  // Session settings
  session_timeout_minutes?: number;
  allow_clock_skew_seconds?: number;
}

export interface SSOConfigResponse extends SSOConfigBase {
  id: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

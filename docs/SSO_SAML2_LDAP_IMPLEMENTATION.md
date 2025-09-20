# SAML2 and LDAP SSO Implementation

This document describes the newly implemented SAML2 and LDAP SSO providers for the LangBuilder RBAC system.

## Overview

The SSO system now supports four protocols:
- **OIDC/OpenID Connect** ✅ (Previously implemented)
- **OAuth2** ✅ (Previously implemented)
- **SAML2** ✅ (Newly implemented)
- **LDAP** ✅ (Newly implemented)

## SAML2 Provider Implementation

### Features
- **Full SAML2 Support**: Implements SAML2 authentication flows with proper XML handling
- **XML Signature Validation**: Verifies SAML assertions using IDP certificates
- **Metadata Generation**: Auto-generates service provider metadata
- **Multiple Bindings**: Supports HTTP-POST and HTTP-Redirect bindings
- **Flexible Configuration**: Supports various SAML2 identity providers

### Key Components

#### SAML2Provider Class
- **Location**: `src/backend/base/langflow/services/auth/saml2_provider.py`
- **Features**:
  - AuthnRequest generation with proper XML structure
  - SAML assertion parsing and validation
  - XML signature verification
  - Conditions validation (time bounds, audience)
  - Attribute extraction and mapping
  - Service provider metadata generation

#### Configuration Fields
```python
# Required fields in SSOConfiguration
saml2_entity_id: str              # Service provider entity ID
saml2_sso_url: str               # IDP SSO endpoint
saml2_name_id_format: str        # NameID format preference
saml2_acs_url: str               # Assertion consumer service URL

# Optional fields
saml2_slo_url: str               # IDP logout endpoint
saml2_metadata_url: str          # IDP metadata endpoint
saml2_certificate: str           # SP certificate for signing
saml2_private_key: str           # SP private key for signing
saml2_idp_certificate: str       # IDP certificate for verification
saml2_signature_algorithm: str   # Signature algorithm (default: RSA_SHA256)
saml2_digest_algorithm: str      # Digest algorithm (default: SHA256)
```

#### Authentication Flow
1. **Initiate Flow**: Generate signed SAML AuthnRequest
2. **User Authentication**: User authenticates with IDP
3. **Callback Handling**: Receive and validate SAML response
4. **Assertion Validation**: Verify signatures and conditions
5. **Claims Extraction**: Extract user attributes from assertion

### Usage Example
```python
# Initialize SAML2 provider
from langflow.services.auth.saml2_provider import SAML2Provider

provider = SAML2Provider(saml2_configuration)

# Initiate authentication flow
auth_url = await provider.initiate_flow(
    redirect_uri="https://app.example.com/auth/callback",
    state="csrf-state-token",
    nonce="replay-protection-nonce"
)

# Handle callback
result = await provider.handle_callback(
    authorization_code="base64_encoded_saml_response",
    state="csrf-state-token",
    nonce="replay-protection-nonce"
)

# Generate metadata
metadata_xml = await provider.get_metadata()
```

## LDAP Provider Implementation

### Features
- **Directory Service Integration**: Connect to Active Directory, OpenLDAP, etc.
- **Connection Pooling**: Efficient connection management with failover
- **Flexible Authentication**: Supports SIMPLE, NTLM, SASL authentication
- **Group Membership**: Automatic group discovery and role mapping
- **User Synchronization**: Bulk user and group retrieval for sync operations
- **Connection Testing**: Built-in connection health checks

### Key Components

#### LDAPProvider Class
- **Location**: `src/backend/base/langflow/services/auth/ldap_provider.py`
- **Features**:
  - Direct credential authentication
  - User search and attribute extraction
  - Group membership resolution
  - Connection pooling with high availability
  - Flexible search filters and attribute mapping

#### Configuration Fields
```python
# Required fields in SSOConfiguration
ldap_server: str                 # LDAP server hostname(s) - comma-separated
ldap_bind_dn: str               # Service account DN
ldap_bind_password: str         # Service account password
ldap_base_dn: str               # Base distinguished name

# Optional fields
ldap_port: int                  # LDAP port (default: 389)
ldap_use_ssl: bool              # Use SSL/LDAPS (default: False)
ldap_use_tls: bool              # Start TLS (default: False)
ldap_user_search_base: str      # User search base DN
ldap_group_search_base: str     # Group search base DN
ldap_user_search_filter: str    # User search filter
ldap_group_search_filter: str   # Group search filter
ldap_user_attributes: list      # Attributes to retrieve
ldap_auth_method: str           # Authentication method (SIMPLE, NTLM, SASL)
```

#### Authentication Flow
1. **Search User**: Find user DN using search filter
2. **Bind Authentication**: Attempt to bind with user credentials
3. **Group Discovery**: Search for user's group memberships
4. **Claims Extraction**: Map LDAP attributes to user claims
5. **Role Mapping**: Extract roles from group names

### Usage Example
```python
# Initialize LDAP provider
from langflow.services.auth.ldap_provider import LDAPProvider

provider = LDAPProvider(ldap_configuration)

# Test connection
is_connected = await provider.test_connection()

# Authenticate user
result = await provider.authenticate_user(
    username="johndoe",
    password="user_password"
)

# Get all users (for synchronization)
users = await provider.get_all_users(page_size=1000)

# Get all groups (for synchronization)
groups = await provider.get_all_groups(page_size=1000)
```

## SSO Service Integration

### New Methods
The SSO service has been extended with new methods to support SAML2 and LDAP:

```python
# LDAP direct authentication
result = await sso_service.authenticate_ldap_user(
    session=db_session,
    provider_id="ldap-provider-id",
    username="user@domain.com",
    password="password"
)

# SAML2 metadata generation
metadata_xml = await sso_service.get_saml2_metadata(
    session=db_session,
    provider_id="saml2-provider-id",
    redirect_uri="https://app.example.com/auth/callback"
)

# LDAP connection testing
is_healthy = await sso_service.test_ldap_connection(
    session=db_session,
    provider_id="ldap-provider-id"
)
```

## Dependencies

The following new dependencies have been added to support SAML2 and LDAP:

```toml
# SAML2 and LDAP SSO dependencies
"lxml>=5.3.0,<6.0.0",        # XML processing for SAML2
"ldap3>=2.9.1,<3.0.0",       # LDAP client library
"signxml>=4.0.2,<5.0.0",     # XML signature handling
```

## Testing

### Unit Tests
- **SAML2**: `tests/unit/services/auth/test_saml2_provider.py`
- **LDAP**: `tests/unit/services/auth/test_ldap_provider.py`

### Integration Tests
- **Combined**: `tests/integration/services/auth/test_sso_saml2_ldap_integration.py`

### Test Coverage
- SAML2 authentication flows and edge cases
- LDAP authentication and error handling
- XML signature validation and security checks
- Connection pooling and failover scenarios
- Configuration validation and error scenarios

## Security Considerations

### SAML2 Security
- **XML Signature Verification**: Validates IDP signatures using certificates
- **Assertion Conditions**: Validates time bounds and audience restrictions
- **Replay Protection**: Uses nonce validation to prevent replay attacks
- **CSRF Protection**: State parameter validation for flow integrity

### LDAP Security
- **Encrypted Connections**: Supports SSL/TLS encryption
- **Credential Protection**: Secure handling of service account credentials
- **Connection Security**: Proper connection lifecycle management
- **Input Validation**: LDAP injection prevention through proper escaping

## Configuration Examples

### SAML2 Configuration
```python
{
    "name": "Azure AD SAML2",
    "protocol": "saml2",
    "is_active": True,
    "saml2_entity_id": "langflow-production",
    "saml2_sso_url": "https://login.microsoftonline.com/tenant-id/saml2",
    "saml2_name_id_format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
    "saml2_acs_url": "https://app.langflow.com/auth/saml/callback",
    "saml2_metadata_url": "https://login.microsoftonline.com/tenant-id/federationmetadata/2007-06/federationmetadata.xml",
    "attribute_mapping": {
        "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
        "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        "groups": "http://schemas.microsoft.com/ws/2008/06/identity/claims/groups"
    }
}
```

### LDAP Configuration
```python
{
    "name": "Active Directory",
    "protocol": "ldap",
    "is_active": True,
    "ldap_server": "dc1.corp.example.com,dc2.corp.example.com",
    "ldap_port": 389,
    "ldap_use_tls": True,
    "ldap_bind_dn": "cn=langflow-service,ou=service-accounts,dc=corp,dc=example,dc=com",
    "ldap_bind_password": "service-account-password",
    "ldap_base_dn": "dc=corp,dc=example,dc=com",
    "ldap_user_search_base": "ou=users,dc=corp,dc=example,dc=com",
    "ldap_group_search_base": "ou=groups,dc=corp,dc=example,dc=com",
    "ldap_user_search_filter": "(|(sAMAccountName={username})(userPrincipalName={username}))",
    "ldap_group_search_filter": "(&(objectClass=group)(member={user_dn}))",
    "ldap_user_attributes": ["sAMAccountName", "userPrincipalName", "cn", "mail", "memberOf"],
    "attribute_mapping": {
        "email": "userPrincipalName",
        "name": "cn",
        "given_name": "givenName",
        "family_name": "sn"
    }
}
```

## Troubleshooting

### SAML2 Issues
- **Invalid Signature**: Check IDP certificate configuration
- **Expired Assertion**: Verify time synchronization between SP and IDP
- **Invalid Audience**: Ensure entity ID matches IDP configuration
- **Metadata Issues**: Validate XML structure and certificate embedding

### LDAP Issues
- **Connection Failed**: Check server hostname, port, and network connectivity
- **Authentication Failed**: Verify service account credentials and permissions
- **User Not Found**: Check search base DN and search filter syntax
- **SSL/TLS Issues**: Validate certificate trust and encryption settings

### Common Solutions
- Enable debug logging for detailed error information
- Use connection testing endpoints to validate configuration
- Verify attribute mapping between provider and Langflow expectations
- Check firewall and network security group rules

## Conclusion

The SAML2 and LDAP implementations provide enterprise-grade SSO capabilities, completing the authentication provider support for major enterprise identity systems. Both implementations follow security best practices and integrate seamlessly with the existing RBAC system.

For additional support or questions, refer to the test files for usage examples and consult the API documentation for detailed parameter descriptions.
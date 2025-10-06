"""
SAML 2.0 Authentication Provider

Handles SAML authentication flow.
"""

import base64
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from xml.etree import ElementTree as ET

from langflow.services.database.models.sso.model import SSOConfiguration

# SAML namespaces
NAMESPACES = {
    "samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
    "saml": "urn:oasis:names:tc:SAML:2.0:assertion",
    "ds": "http://www.w3.org/2000/09/xmldsig#",
}


class SAMLProvider:
    """SAML 2.0 authentication provider."""

    def __init__(self, config: SSOConfiguration):
        """Initialize SAML provider with configuration."""
        if not config.saml_entity_id:
            raise ValueError("SAML entity ID is required")
        if not config.saml_sso_url:
            raise ValueError("SAML SSO URL is required")
        if not config.saml_x509_cert:
            raise ValueError("SAML X.509 certificate is required")

        self.config = config
        self.entity_id = config.saml_entity_id
        self.sso_url = config.saml_sso_url
        self.x509_cert = config.saml_x509_cert
        self.slo_url = config.saml_slo_url

    def generate_authn_request(
        self,
        sp_entity_id: str,
        acs_url: str,
        relay_state: str | None = None,
    ) -> tuple[str, str]:
        """
        Generate SAML AuthnRequest for SP-initiated flow.

        Args:
            sp_entity_id: Service Provider entity ID
            acs_url: Assertion Consumer Service URL (callback)
            relay_state: Optional state to preserve

        Returns:
            Tuple of (request_id, base64_encoded_request)
        """
        request_id = f"__{secrets.token_hex(16)}"
        issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.sso_url}"
    AssertionConsumerServiceURL="{acs_url}"
    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{sp_entity_id}</saml:Issuer>
    <samlp:NameIDPolicy
        Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
        AllowCreate="true"/>
</samlp:AuthnRequest>"""

        # Base64 encode and deflate (simplified - production would use proper deflate)
        encoded_request = base64.b64encode(authn_request.encode()).decode()

        return request_id, encoded_request

    def parse_saml_response(self, saml_response: str) -> dict[str, Any]:
        """
        Parse and extract data from SAML Response.

        Args:
            saml_response: Base64-encoded SAML Response XML

        Returns:
            Dictionary with assertion data

        Raises:
            ValueError: If response is invalid
        """
        try:
            # Decode base64
            xml_data = base64.b64decode(saml_response)
            root = ET.fromstring(xml_data)

            # Extract response ID and status
            response_id = root.get("ID")
            in_response_to = root.get("InResponseTo")

            # Check status
            status_elem = root.find(".//samlp:Status/samlp:StatusCode", NAMESPACES)
            if status_elem is None:
                raise ValueError("No status found in SAML response")

            status_code = status_elem.get("Value")
            if status_code != "urn:oasis:names:tc:SAML:2.0:status:Success":
                raise ValueError(f"SAML authentication failed: {status_code}")

            # Extract assertion
            assertion_elem = root.find(".//saml:Assertion", NAMESPACES)
            if assertion_elem is None:
                raise ValueError("No assertion found in SAML response")

            assertion_id = assertion_elem.get("ID")
            issue_instant = assertion_elem.get("IssueInstant")

            # Extract subject
            subject_elem = assertion_elem.find(".//saml:Subject/saml:NameID", NAMESPACES)
            if subject_elem is None:
                raise ValueError("No subject found in assertion")

            subject = subject_elem.text

            # Extract conditions
            conditions = self._extract_conditions(assertion_elem)

            # Extract attributes
            attributes = self._extract_attributes(assertion_elem)

            return {
                "response_id": response_id,
                "assertion_id": assertion_id,
                "in_response_to": in_response_to,
                "subject": subject,
                "issue_instant": issue_instant,
                "conditions": conditions,
                "attributes": attributes,
            }

        except ET.ParseError as e:
            raise ValueError(f"Invalid SAML XML: {e}")

    def _extract_conditions(self, assertion_elem: ET.Element) -> dict[str, Any]:
        """Extract conditions from assertion."""
        conditions_elem = assertion_elem.find(".//saml:Conditions", NAMESPACES)
        if conditions_elem is None:
            return {}

        not_before = conditions_elem.get("NotBefore")
        not_on_or_after = conditions_elem.get("NotOnOrAfter")

        return {
            "not_before": not_before,
            "not_on_or_after": not_on_or_after,
        }

    def _extract_attributes(self, assertion_elem: ET.Element) -> dict[str, Any]:
        """Extract attributes from assertion."""
        attributes = {}

        attr_stmt = assertion_elem.find(".//saml:AttributeStatement", NAMESPACES)
        if attr_stmt is not None:
            for attr in attr_stmt.findall(".//saml:Attribute", NAMESPACES):
                name = attr.get("Name")
                values = []
                for value in attr.findall(".//saml:AttributeValue", NAMESPACES):
                    if value.text:
                        values.append(value.text)

                # Store single value or list
                attributes[name] = values[0] if len(values) == 1 else values

        return attributes

    def validate_assertion_timing(
        self,
        conditions: dict[str, Any],
        allow_clock_skew: int = 300,
    ) -> bool:
        """
        Validate assertion timing with clock skew tolerance.

        Args:
            conditions: Conditions from assertion
            allow_clock_skew: Allowed clock skew in seconds

        Returns:
            True if timing is valid
        """
        now = datetime.now(timezone.utc)
        skew = timedelta(seconds=allow_clock_skew)

        # Check NotBefore
        if "not_before" in conditions and conditions["not_before"]:
            not_before = datetime.fromisoformat(
                conditions["not_before"].replace("Z", "+00:00")
            )
            if now + skew < not_before:
                return False

        # Check NotOnOrAfter
        if "not_on_or_after" in conditions and conditions["not_on_or_after"]:
            not_on_or_after = datetime.fromisoformat(
                conditions["not_on_or_after"].replace("Z", "+00:00")
            )
            if now - skew >= not_on_or_after:
                return False

        return True

    def verify_signature(self, xml_data: str) -> bool:
        """
        Verify SAML assertion signature using IdP certificate.

        Note: This is a simplified placeholder. Production implementation
        would use proper XML signature verification libraries like xmlsec.

        Args:
            xml_data: SAML response XML

        Returns:
            True if signature is valid
        """
        # TODO: Implement proper XML signature verification
        # For now, return True (insecure - for demo only)
        # Production should use: python3-saml or xmlsec library
        return True

    def extract_user_attributes(self, assertion_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract user attributes from SAML assertion.

        Args:
            assertion_data: Parsed SAML assertion

        Returns:
            Dictionary with email, name, groups, etc.
        """
        attributes = assertion_data.get("attributes", {})

        email_attr = self.config.email_attribute or "email"
        name_attr = self.config.name_attribute or "name"
        groups_attr = self.config.groups_attribute or "groups"

        # Extract with fallbacks
        email = attributes.get(email_attr) or assertion_data.get("subject")
        name = attributes.get(name_attr)
        groups = attributes.get(groups_attr, [])

        # Ensure groups is a list
        if isinstance(groups, str):
            groups = [groups]

        return {
            "email": email,
            "name": name,
            "groups": groups,
            "sub": assertion_data.get("subject"),
            "mfa_verified": False,  # SAML doesn't directly indicate MFA
        }

    def generate_logout_request(
        self,
        sp_entity_id: str,
        name_id: str,
        session_index: str | None = None,
    ) -> str:
        """
        Generate SAML LogoutRequest for Single Logout (SLO).

        Args:
            sp_entity_id: Service Provider entity ID
            name_id: User's NameID from assertion
            session_index: Optional session index

        Returns:
            Base64-encoded logout request
        """
        request_id = f"__{secrets.token_hex(16)}"
        issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        session_index_xml = (
            f'<samlp:SessionIndex>{session_index}</samlp:SessionIndex>'
            if session_index
            else ""
        )

        logout_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:LogoutRequest
    xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
    ID="{request_id}"
    Version="2.0"
    IssueInstant="{issue_instant}"
    Destination="{self.slo_url}">
    <saml:Issuer>{sp_entity_id}</saml:Issuer>
    <saml:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">
        {name_id}
    </saml:NameID>
    {session_index_xml}
</samlp:LogoutRequest>"""

        return base64.b64encode(logout_request.encode()).decode()

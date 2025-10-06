/**
 * SSO Login Button Component
 *
 * Displays SSO login button based on domain enforcement level
 */

import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { checkSSOEnforcement, initiateSSOLogin } from "../../api/sso";
import { SSOEnforcement } from "../../types/sso";
import useAlertStore from "../../stores/alertStore";

interface SSOButtonProps {
  onSSOInitiated?: () => void;
}

export default function SSOButton({ onSSOInitiated }: SSOButtonProps) {
  const [domain, setDomain] = useState("");
  const [isChecking, setIsChecking] = useState(false);
  const [showDomainInput, setShowDomainInput] = useState(false);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const handleSSOLogin = async () => {
    if (!domain.trim()) {
      setErrorData({
        title: "SSO Login Error",
        list: ["Please enter your company domain"],
      });
      return;
    }

    setIsChecking(true);
    try {
      // Check if SSO is enabled for this domain
      const enforcement = await checkSSOEnforcement(domain.trim());

      if (enforcement.enforcement === SSOEnforcement.DISABLED) {
        setErrorData({
          title: "SSO Not Available",
          list: ["SSO is not configured for this domain"],
        });
        setIsChecking(false);
        return;
      }

      // Generate state for CSRF protection
      const state = generateRandomState();
      sessionStorage.setItem("sso_state", state);
      sessionStorage.setItem("sso_domain", domain.trim());

      // Initiate SSO login
      const redirectUri = `${window.location.origin}/sso/callback`;
      const result = await initiateSSOLogin({
        domain: domain.trim(),
        redirect_uri: redirectUri,
        state,
      });

      // Store request ID for SAML
      if (result.request_id) {
        sessionStorage.setItem("sso_request_id", result.request_id);
      }

      onSSOInitiated?.();

      // Redirect to IdP
      window.location.href = result.redirect_url;
    } catch (error: any) {
      setErrorData({
        title: "SSO Login Error",
        list: [error?.response?.data?.detail || "Failed to initiate SSO login"],
      });
      setIsChecking(false);
    }
  };

  return (
    <div className="w-full space-y-3">
      {!showDomainInput ? (
        <Button
          className="w-full"
          variant="outline"
          type="button"
          onClick={() => setShowDomainInput(true)}
        >
          Sign in with SSO
        </Button>
      ) : (
        <>
          <div className="space-y-2">
            <label className="text-sm font-medium">Company Domain</label>
            <Input
              type="text"
              placeholder="acme.com"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  handleSSOLogin();
                }
              }}
              disabled={isChecking}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Enter your company domain to sign in with SSO
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              className="flex-1"
              type="button"
              onClick={handleSSOLogin}
              disabled={isChecking || !domain.trim()}
            >
              {isChecking ? "Connecting..." : "Continue with SSO"}
            </Button>
            <Button
              variant="outline"
              type="button"
              onClick={() => {
                setShowDomainInput(false);
                setDomain("");
              }}
              disabled={isChecking}
            >
              Cancel
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

/**
 * Generate random state for CSRF protection
 */
function generateRandomState(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
    ""
  );
}

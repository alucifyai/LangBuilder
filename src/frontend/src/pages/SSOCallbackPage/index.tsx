/**
 * SSO Callback Page
 *
 * Handles OIDC and SAML callbacks after IdP authentication
 */

import { useContext, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import LangflowLogo from "@/assets/LangflowLogo.svg?react";
import { processOIDCCallback, processSAMLCallback } from "../../api/sso";
import { AuthContext } from "../../contexts/authContext";
import useAlertStore from "../../stores/alertStore";

export default function SSOCallbackPage(): JSX.Element {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useContext(AuthContext);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const [status, setStatus] = useState<"processing" | "success" | "error">(
    "processing"
  );
  const [errorMessage, setErrorMessage] = useState<string>("");

  useEffect(() => {
    handleCallback();
  }, []);

  async function handleCallback() {
    try {
      // Retrieve stored domain and state
      const storedDomain = sessionStorage.getItem("sso_domain");
      const storedState = sessionStorage.getItem("sso_state");

      if (!storedDomain) {
        throw new Error("SSO session not found. Please try logging in again.");
      }

      // Check for OIDC callback (code parameter)
      const code = searchParams.get("code");
      const state = searchParams.get("state");

      if (code) {
        // OIDC callback
        await handleOIDCCallback(code, state, storedState, storedDomain);
        return;
      }

      // Check for SAML callback (SAMLResponse parameter)
      const samlResponse = searchParams.get("SAMLResponse");
      const relayState = searchParams.get("RelayState");

      if (samlResponse) {
        // SAML callback
        await handleSAMLCallback(samlResponse, relayState, storedDomain);
        return;
      }

      // No valid callback parameters
      throw new Error("Invalid SSO callback. Missing authentication response.");
    } catch (error: any) {
      console.error("SSO callback error:", error);
      setStatus("error");
      setErrorMessage(
        error?.response?.data?.detail ||
          error.message ||
          "SSO authentication failed"
      );

      setErrorData({
        title: "SSO Authentication Failed",
        list: [errorMessage || "An error occurred during SSO login"],
      });

      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate("/login");
      }, 3000);
    }
  }

  async function handleOIDCCallback(
    code: string,
    state: string | null,
    storedState: string | null,
    domain: string
  ) {
    // Validate state (CSRF protection)
    if (storedState && state !== storedState) {
      throw new Error("Invalid state parameter. Possible CSRF attack.");
    }

    // Process OIDC callback
    const result = await processOIDCCallback(code, state, domain);

    // Clear SSO session storage
    sessionStorage.removeItem("sso_domain");
    sessionStorage.removeItem("sso_state");

    // Store session token and login
    login(result.session_token, "sso", result.session_token);

    setStatus("success");

    // Redirect to main page
    setTimeout(() => {
      navigate("/");
    }, 1000);
  }

  async function handleSAMLCallback(
    samlResponse: string,
    relayState: string | null,
    domain: string
  ) {
    // Process SAML callback
    const result = await processSAMLCallback(samlResponse, relayState, domain);

    // Clear SSO session storage
    sessionStorage.removeItem("sso_domain");
    sessionStorage.removeItem("sso_state");
    sessionStorage.removeItem("sso_request_id");

    // Store session token and login
    login(result.session_token, "sso", result.session_token);

    setStatus("success");

    // Redirect to main page
    setTimeout(() => {
      navigate("/");
    }, 1000);
  }

  return (
    <div className="flex h-screen w-full flex-col items-center justify-center bg-muted">
      <div className="flex w-96 flex-col items-center justify-center gap-4 rounded-lg bg-background p-8 shadow-lg">
        <LangflowLogo
          title="Langflow logo"
          className="h-10 w-10 scale-[1.5]"
        />

        {status === "processing" && (
          <>
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <span className="text-lg font-medium text-primary">
              Completing SSO authentication...
            </span>
            <p className="text-center text-sm text-muted-foreground">
              Please wait while we verify your credentials
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
              <svg
                className="h-8 w-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <span className="text-lg font-medium text-green-600">
              Authentication successful!
            </span>
            <p className="text-center text-sm text-muted-foreground">
              Redirecting to your dashboard...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
              <svg
                className="h-8 w-8 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <span className="text-lg font-medium text-red-600">
              Authentication failed
            </span>
            <p className="text-center text-sm text-muted-foreground">
              {errorMessage}
            </p>
            <p className="text-center text-xs text-muted-foreground">
              Redirecting to login page...
            </p>
          </>
        )}
      </div>
    </div>
  );
}

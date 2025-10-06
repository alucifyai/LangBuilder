/**
 * Create SSO Configuration Modal
 */

import { useState } from "react";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Textarea } from "../ui/textarea";
import { createSSOConfig } from "../../api/sso";
import { SSOEnforcement, SSOProvider, type SSOConfigCreate } from "../../types/sso";
import useAlertStore from "../../stores/alertStore";

interface CreateSSOConfigModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateSSOConfigModal({
  open,
  onClose,
  onSuccess,
}: CreateSSOConfigModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const [formData, setFormData] = useState<Partial<SSOConfigCreate>>({
    provider_type: SSOProvider.OIDC,
    enforcement: SSOEnforcement.OPTIONAL,
    enabled: true,
    session_timeout_minutes: 480,
    allow_clock_skew_seconds: 300,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Validate required fields
      if (!formData.organization_id || !formData.domain) {
        throw new Error("Organization ID and domain are required");
      }

      if (formData.provider_type === SSOProvider.OIDC) {
        if (
          !formData.oidc_issuer ||
          !formData.oidc_client_id ||
          !formData.oidc_client_secret
        ) {
          throw new Error("OIDC issuer, client ID, and client secret are required");
        }
      } else if (formData.provider_type === SSOProvider.SAML) {
        if (
          !formData.saml_entity_id ||
          !formData.saml_sso_url ||
          !formData.saml_x509_cert
        ) {
          throw new Error("SAML entity ID, SSO URL, and X.509 certificate are required");
        }
      }

      await createSSOConfig(formData as SSOConfigCreate);

      setSuccessData({
        title: "SSO Configuration Created",
      });

      onSuccess();
    } catch (error: any) {
      setErrorData({
        title: "Failed to create SSO configuration",
        list: [error?.response?.data?.detail || error.message],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create SSO Configuration</DialogTitle>
          <DialogDescription>
            Configure a new SSO provider for your organization
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="organization_id">
                Organization ID <span className="text-destructive">*</span>
              </Label>
              <Input
                id="organization_id"
                value={formData.organization_id || ""}
                onChange={(e) =>
                  setFormData({ ...formData, organization_id: e.target.value })
                }
                placeholder="org-123"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="domain">
                Domain <span className="text-destructive">*</span>
              </Label>
              <Input
                id="domain"
                value={formData.domain || ""}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                placeholder="acme.com"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="provider_type">Provider Type</Label>
              <Select
                value={formData.provider_type}
                onValueChange={(value) =>
                  setFormData({ ...formData, provider_type: value as SSOProvider })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SSOProvider.OIDC}>OIDC / OAuth 2.0</SelectItem>
                  <SelectItem value={SSOProvider.SAML}>SAML 2.0</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="enforcement">Enforcement</Label>
              <Select
                value={formData.enforcement}
                onValueChange={(value) =>
                  setFormData({ ...formData, enforcement: value as SSOEnforcement })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={SSOEnforcement.OPTIONAL}>Optional</SelectItem>
                  <SelectItem value={SSOEnforcement.ENFORCED}>Enforced</SelectItem>
                  <SelectItem value={SSOEnforcement.DISABLED}>Disabled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {formData.provider_type === SSOProvider.OIDC && (
            <>
              <div className="space-y-2">
                <Label htmlFor="oidc_issuer">
                  OIDC Issuer URL <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="oidc_issuer"
                  value={formData.oidc_issuer || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, oidc_issuer: e.target.value })
                  }
                  placeholder="https://idp.example.com"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="oidc_client_id">
                    Client ID <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="oidc_client_id"
                    value={formData.oidc_client_id || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, oidc_client_id: e.target.value })
                    }
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="oidc_client_secret">
                    Client Secret <span className="text-destructive">*</span>
                  </Label>
                  <Input
                    id="oidc_client_secret"
                    type="password"
                    value={formData.oidc_client_secret || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, oidc_client_secret: e.target.value })
                    }
                    required
                  />
                </div>
              </div>
            </>
          )}

          {formData.provider_type === SSOProvider.SAML && (
            <>
              <div className="space-y-2">
                <Label htmlFor="saml_entity_id">
                  SAML Entity ID <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="saml_entity_id"
                  value={formData.saml_entity_id || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, saml_entity_id: e.target.value })
                  }
                  placeholder="https://idp.example.com/saml"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="saml_sso_url">
                  SAML SSO URL <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="saml_sso_url"
                  value={formData.saml_sso_url || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, saml_sso_url: e.target.value })
                  }
                  placeholder="https://idp.example.com/sso/saml"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="saml_x509_cert">
                  X.509 Certificate <span className="text-destructive">*</span>
                </Label>
                <Textarea
                  id="saml_x509_cert"
                  value={formData.saml_x509_cert || ""}
                  onChange={(e) =>
                    setFormData({ ...formData, saml_x509_cert: e.target.value })
                  }
                  placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
                  rows={5}
                  required
                />
              </div>
            </>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Configuration"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

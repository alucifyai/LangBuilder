/**
 * Edit SSO Configuration Modal
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
import { updateSSOConfig } from "../../api/sso";
import { SSOEnforcement, type SSOConfigResponse, type SSOConfigUpdate } from "../../types/sso";
import useAlertStore from "../../stores/alertStore";

interface EditSSOConfigModalProps {
  config: SSOConfigResponse;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function EditSSOConfigModal({
  config,
  open,
  onClose,
  onSuccess,
}: EditSSOConfigModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const [formData, setFormData] = useState<SSOConfigUpdate>({
    enforcement: config.enforcement,
    enabled: config.enabled,
    session_timeout_minutes: config.session_timeout_minutes,
    allow_clock_skew_seconds: config.allow_clock_skew_seconds,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await updateSSOConfig(config.id, formData);

      setSuccessData({
        title: "SSO Configuration Updated",
      });

      onSuccess();
    } catch (error: any) {
      setErrorData({
        title: "Failed to update SSO configuration",
        list: [error?.response?.data?.detail || error.message],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit SSO Configuration</DialogTitle>
          <DialogDescription>
            Update enforcement and session settings for {config.domain}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="enforcement">Enforcement Level</Label>
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

          <div className="space-y-2">
            <Label htmlFor="enabled">Status</Label>
            <Select
              value={formData.enabled ? "enabled" : "disabled"}
              onValueChange={(value) =>
                setFormData({ ...formData, enabled: value === "enabled" })
              }
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="enabled">Enabled</SelectItem>
                <SelectItem value="disabled">Disabled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="session_timeout_minutes">
                Session Timeout (min)
              </Label>
              <Input
                id="session_timeout_minutes"
                type="number"
                value={formData.session_timeout_minutes || 480}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    session_timeout_minutes: parseInt(e.target.value),
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="allow_clock_skew_seconds">
                Clock Skew (sec)
              </Label>
              <Input
                id="allow_clock_skew_seconds"
                type="number"
                value={formData.allow_clock_skew_seconds || 300}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    allow_clock_skew_seconds: parseInt(e.target.value),
                  })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

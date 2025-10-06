/**
 * Create Service Account Modal
 */

import { useState } from "react";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { createServiceAccount } from "../../api/service-accounts";
import type { ServiceAccountCreate } from "../../types/service-accounts";
import useAlertStore from "../../stores/alertStore";

interface CreateServiceAccountModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateServiceAccountModal({
  open,
  onClose,
  onSuccess,
}: CreateServiceAccountModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const [formData, setFormData] = useState<ServiceAccountCreate>({
    name: "",
    description: "",
    organization_id: "default", // TODO: Get from context
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await createServiceAccount(formData);
      setSuccessData({ title: "Service Account Created" });
      onSuccess();
    } catch (error: any) {
      setErrorData({
        title: "Failed to create service account",
        list: [error?.response?.data?.detail || error.message],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Service Account</DialogTitle>
          <DialogDescription>
            Service accounts are used for API access by automated systems
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name <span className="text-destructive">*</span></Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="my-api-service"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Description of this service account"
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

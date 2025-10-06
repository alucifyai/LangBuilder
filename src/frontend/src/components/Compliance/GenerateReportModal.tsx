/**
 * Generate Report Modal
 * Form for creating new compliance reports
 */

import React, { useState } from "react";
import type { GenerateReportRequest } from "../../types/compliance";
import { generateReport } from "../../api/compliance";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

interface GenerateReportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function GenerateReportModal({
  open,
  onOpenChange,
  onSuccess,
}: GenerateReportModalProps) {
  const [formData, setFormData] = useState<GenerateReportRequest>({
    name: "",
    report_type: "soc2",
    period_start: "",
    period_end: "",
    framework_version: "",
    description: "",
    organization_id: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Remove empty optional fields
      const request: GenerateReportRequest = {
        name: formData.name,
        report_type: formData.report_type,
        period_start: formData.period_start,
        period_end: formData.period_end,
      };

      if (formData.framework_version) {
        request.framework_version = formData.framework_version;
      }
      if (formData.description) {
        request.description = formData.description;
      }
      if (formData.organization_id) {
        request.organization_id = formData.organization_id;
      }

      await generateReport(request);
      onSuccess();
      onOpenChange(false);
      // Reset form
      setFormData({
        name: "",
        report_type: "soc2",
        period_start: "",
        period_end: "",
        framework_version: "",
        description: "",
        organization_id: "",
      });
    } catch (error) {
      console.error("Failed to generate report:", error);
      alert("Failed to generate report");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Generate Compliance Report</DialogTitle>
          <DialogDescription>
            Create a new compliance report for a specific framework and time
            period
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Report Name *</Label>
              <Input
                id="name"
                placeholder="Q4 2024 SOC2 Type II Report"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="report_type">Report Type *</Label>
              <Select
                value={formData.report_type}
                onValueChange={(value: any) =>
                  setFormData({ ...formData, report_type: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="soc2">SOC2</SelectItem>
                  <SelectItem value="gdpr">GDPR</SelectItem>
                  <SelectItem value="iso27001">ISO 27001</SelectItem>
                  <SelectItem value="access">Access Review</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="period_start">Period Start *</Label>
                <Input
                  id="period_start"
                  type="date"
                  value={formData.period_start}
                  onChange={(e) =>
                    setFormData({ ...formData, period_start: e.target.value })
                  }
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="period_end">Period End *</Label>
                <Input
                  id="period_end"
                  type="date"
                  value={formData.period_end}
                  onChange={(e) =>
                    setFormData({ ...formData, period_end: e.target.value })
                  }
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="framework_version">Framework Version</Label>
              <Input
                id="framework_version"
                placeholder="e.g., Type II, 2022, etc."
                value={formData.framework_version}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    framework_version: e.target.value,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="organization_id">Organization ID</Label>
              <Input
                id="organization_id"
                placeholder="Optional organization identifier"
                value={formData.organization_id}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    organization_id: e.target.value,
                  })
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Brief description of the report scope and purpose..."
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
              />
            </div>

            {formData.report_type === "soc2" && (
              <div className="bg-blue-50 border border-blue-200 rounded p-3">
                <p className="text-sm text-blue-800">
                  <strong>SOC2 Report:</strong> This will analyze trust service
                  criteria including security, availability, processing
                  integrity, confidentiality, and privacy controls.
                </p>
              </div>
            )}

            {formData.report_type === "gdpr" && (
              <div className="bg-green-50 border border-green-200 rounded p-3">
                <p className="text-sm text-green-800">
                  <strong>GDPR Report:</strong> This will assess compliance with
                  data protection regulations including consent, data subject
                  rights, and breach notification.
                </p>
              </div>
            )}

            {formData.report_type === "access" && (
              <div className="bg-orange-50 border border-orange-200 rounded p-3">
                <p className="text-sm text-orange-800">
                  <strong>Access Report:</strong> This will analyze access
                  patterns, privilege usage, and identify potential access
                  violations or anomalies.
                </p>
              </div>
            )}
          </div>

          <DialogFooter className="mt-6">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Generating..." : "Generate Report"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

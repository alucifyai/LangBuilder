/**
 * Create Campaign Modal
 * Create a new access review campaign
 */

import React, { useState } from "react";
import type { CreateCampaignRequest } from "../../types/access-reviews";
import { createCampaign } from "../../api/access-reviews";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Checkbox } from "../ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

interface CreateCampaignModalProps {
  onCampaignCreated: () => void;
}

export function CreateCampaignModal({
  onCampaignCreated,
}: CreateCampaignModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [startDate, setStartDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [complianceFramework, setComplianceFramework] = useState<string>("");
  const [autoRevoke, setAutoRevoke] = useState(false);

  const resetForm = () => {
    setName("");
    setDescription("");
    setStartDate("");
    setDueDate("");
    setComplianceFramework("");
    setAutoRevoke(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const request: CreateCampaignRequest = {
        name,
        start_date: new Date(startDate).toISOString(),
        due_date: new Date(dueDate).toISOString(),
        description: description || undefined,
        compliance_framework: complianceFramework || undefined,
        auto_revoke_on_no_response: autoRevoke,
        scope_type: "organization",
      };

      await createCampaign(request);
      setIsOpen(false);
      resetForm();
      onCampaignCreated();
    } catch (error) {
      console.error("Failed to create campaign:", error);
      alert("Failed to create campaign");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>Create Campaign</Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create Access Review Campaign</DialogTitle>
          <DialogDescription>
            Launch a periodic access certification campaign for compliance
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">
              Campaign Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="name"
              placeholder="Q1 2025 Access Review"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Quarterly access review for SOC2 compliance..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="start-date">
                Start Date <span className="text-red-500">*</span>
              </Label>
              <Input
                id="start-date"
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="due-date">
                Due Date <span className="text-red-500">*</span>
              </Label>
              <Input
                id="due-date"
                type="datetime-local"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                min={startDate}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="framework">Compliance Framework</Label>
            <Select value={complianceFramework} onValueChange={setComplianceFramework}>
              <SelectTrigger>
                <SelectValue placeholder="Select framework (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">None</SelectItem>
                <SelectItem value="SOC2">SOC2</SelectItem>
                <SelectItem value="ISO27001">ISO 27001</SelectItem>
                <SelectItem value="GDPR">GDPR</SelectItem>
                <SelectItem value="HIPAA">HIPAA</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Checkbox
              id="auto-revoke"
              checked={autoRevoke}
              onCheckedChange={(checked) => setAutoRevoke(checked === true)}
            />
            <Label htmlFor="auto-revoke" className="font-normal">
              Auto-revoke access for items not reviewed by due date
            </Label>
          </div>

          <div className="rounded-lg bg-yellow-50 p-3 text-sm">
            <p className="font-semibold text-yellow-900">⚠️ Important:</p>
            <p className="text-yellow-800 mt-1">
              Once activated, reviewers will need to approve or revoke each access grant.
              If auto-revoke is enabled, any grants not reviewed by the due date will be
              automatically revoked.
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create Campaign"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

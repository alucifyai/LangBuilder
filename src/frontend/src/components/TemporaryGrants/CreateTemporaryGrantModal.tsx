/**
 * Create Temporary Grant Modal
 * Form for creating time-limited role assignments
 */

import React, { useState } from "react";
import type { CreateTemporaryGrantRequest } from "../../types/temporary-grants";
import { createTemporaryGrant } from "../../api/temporary-grants";
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

interface CreateTemporaryGrantModalProps {
  onGrantCreated: () => void;
}

export function CreateTemporaryGrantModal({
  onGrantCreated,
}: CreateTemporaryGrantModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state
  const [grantId, setGrantId] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [expiresAt, setExpiresAt] = useState("");
  const [autoRevoke, setAutoRevoke] = useState(true);
  const [notifyBeforeExpiry, setNotifyBeforeExpiry] = useState(true);
  const [notificationHours, setNotificationHours] = useState(24);
  const [maxExtensions, setMaxExtensions] = useState<number | null>(null);
  const [reason, setReason] = useState("");

  const resetForm = () => {
    setGrantId("");
    setStartsAt("");
    setExpiresAt("");
    setAutoRevoke(true);
    setNotifyBeforeExpiry(true);
    setNotificationHours(24);
    setMaxExtensions(null);
    setReason("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const request: CreateTemporaryGrantRequest = {
        grant_id: grantId,
        expires_at: new Date(expiresAt).toISOString(),
        starts_at: startsAt ? new Date(startsAt).toISOString() : undefined,
        auto_revoke: autoRevoke,
        notify_before_expiry: notifyBeforeExpiry,
        notification_hours: notificationHours,
        max_extensions: maxExtensions,
        reason: reason || null,
      };

      await createTemporaryGrant(request);
      setIsOpen(false);
      resetForm();
      onGrantCreated();
    } catch (error) {
      console.error("Failed to create temporary grant:", error);
      alert("Failed to create temporary grant. Please check all fields.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>Create Temporary Grant</Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Temporary Grant</DialogTitle>
          <DialogDescription>
            Create a time-limited role assignment that automatically expires.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Grant ID */}
          <div className="space-y-2">
            <Label htmlFor="grant-id">
              Grant ID <span className="text-red-500">*</span>
            </Label>
            <Input
              id="grant-id"
              placeholder="Enter existing grant ID"
              value={grantId}
              onChange={(e) => setGrantId(e.target.value)}
              required
            />
            <p className="text-sm text-gray-500">
              The base grant to make temporary
            </p>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="starts-at">Starts At</Label>
              <Input
                id="starts-at"
                type="datetime-local"
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
              />
              <p className="text-sm text-gray-500">
                Leave empty to start immediately
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="expires-at">
                Expires At <span className="text-red-500">*</span>
              </Label>
              <Input
                id="expires-at"
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                min={new Date().toISOString().slice(0, 16)}
                required
              />
            </div>
          </div>

          {/* Quick Presets */}
          <div className="space-y-2">
            <Label>Quick Duration Presets</Label>
            <div className="flex gap-2 flex-wrap">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  const date = new Date();
                  date.setHours(date.getHours() + 1);
                  setExpiresAt(date.toISOString().slice(0, 16));
                }}
              >
                1 Hour
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  const date = new Date();
                  date.setDate(date.getDate() + 1);
                  setExpiresAt(date.toISOString().slice(0, 16));
                }}
              >
                1 Day
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  const date = new Date();
                  date.setDate(date.getDate() + 7);
                  setExpiresAt(date.toISOString().slice(0, 16));
                }}
              >
                1 Week
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  const date = new Date();
                  date.setMonth(date.getMonth() + 1);
                  setExpiresAt(date.toISOString().slice(0, 16));
                }}
              >
                1 Month
              </Button>
            </div>
          </div>

          {/* Auto Revoke */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="auto-revoke"
              checked={autoRevoke}
              onCheckedChange={(checked) => setAutoRevoke(checked === true)}
            />
            <Label htmlFor="auto-revoke" className="font-normal">
              Automatically revoke grant on expiration
            </Label>
          </div>

          {/* Notifications */}
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="notify-before-expiry"
                checked={notifyBeforeExpiry}
                onCheckedChange={(checked) =>
                  setNotifyBeforeExpiry(checked === true)
                }
              />
              <Label htmlFor="notify-before-expiry" className="font-normal">
                Send notification before expiration
              </Label>
            </div>

            {notifyBeforeExpiry && (
              <div className="ml-6 space-y-2">
                <Label htmlFor="notification-hours">
                  Notification Hours Before Expiry
                </Label>
                <Input
                  id="notification-hours"
                  type="number"
                  min={1}
                  max={168}
                  value={notificationHours}
                  onChange={(e) =>
                    setNotificationHours(parseInt(e.target.value))
                  }
                />
              </div>
            )}
          </div>

          {/* Max Extensions */}
          <div className="space-y-2">
            <Label htmlFor="max-extensions">
              Maximum Extensions (optional)
            </Label>
            <Input
              id="max-extensions"
              type="number"
              min={0}
              placeholder="Unlimited"
              value={maxExtensions ?? ""}
              onChange={(e) =>
                setMaxExtensions(
                  e.target.value ? parseInt(e.target.value) : null
                )
              }
            />
            <p className="text-sm text-gray-500">
              Leave empty for unlimited extensions
            </p>
          </div>

          {/* Reason */}
          <div className="space-y-2">
            <Label htmlFor="reason">Reason</Label>
            <Textarea
              id="reason"
              placeholder="Why is this temporary grant needed?"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
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
              {isSubmitting ? "Creating..." : "Create Temporary Grant"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

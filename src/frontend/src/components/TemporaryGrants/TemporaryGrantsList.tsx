/**
 * Temporary Grants List Component
 * Displays and manages time-limited role assignments
 */

import React, { useState } from "react";
import type { TemporaryGrant } from "../../types/temporary-grants";
import {
  deleteTemporaryGrant,
  expireGrant,
  extendTemporaryGrant,
  processExpiredGrants,
} from "../../api/temporary-grants";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
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
import { Textarea } from "../ui/textarea";

interface TemporaryGrantsListProps {
  grants: TemporaryGrant[];
  onGrantCreated: () => void;
  onGrantUpdated: () => void;
  onGrantDeleted: () => void;
}

export function TemporaryGrantsList({
  grants,
  onGrantCreated,
  onGrantUpdated,
  onGrantDeleted,
}: TemporaryGrantsListProps) {
  const [isExtendModalOpen, setIsExtendModalOpen] = useState(false);
  const [selectedGrant, setSelectedGrant] = useState<TemporaryGrant | null>(
    null
  );
  const [newExpirationDate, setNewExpirationDate] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTimeRemaining = (expiresAt: string) => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diff = expiry.getTime() - now.getTime();

    if (diff <= 0) return "Expired";

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h`;
    return "< 1h";
  };

  const handleExtendGrant = (grant: TemporaryGrant) => {
    setSelectedGrant(grant);
    // Set default to 7 days from now
    const defaultExpiry = new Date();
    defaultExpiry.setDate(defaultExpiry.getDate() + 7);
    setNewExpirationDate(defaultExpiry.toISOString().slice(0, 16));
    setIsExtendModalOpen(true);
  };

  const handleExtendSubmit = async () => {
    if (!selectedGrant || !newExpirationDate) return;

    try {
      await extendTemporaryGrant(selectedGrant.id, {
        new_expires_at: new Date(newExpirationDate).toISOString(),
      });
      setIsExtendModalOpen(false);
      setSelectedGrant(null);
      setNewExpirationDate("");
      onGrantUpdated();
    } catch (error) {
      console.error("Failed to extend grant:", error);
      alert("Failed to extend grant. Check max extensions limit.");
    }
  };

  const handleExpireNow = async (grantId: string) => {
    if (!confirm("Are you sure you want to expire this grant immediately?"))
      return;

    try {
      await expireGrant(grantId);
      onGrantUpdated();
    } catch (error) {
      console.error("Failed to expire grant:", error);
      alert("Failed to expire grant");
    }
  };

  const handleDelete = async (grantId: string) => {
    if (
      !confirm(
        "Are you sure you want to delete this temporary grant tracking?"
      )
    )
      return;

    try {
      await deleteTemporaryGrant(grantId);
      onGrantDeleted();
    } catch (error) {
      console.error("Failed to delete grant:", error);
      alert("Failed to delete grant");
    }
  };

  const handleProcessExpired = async () => {
    setIsProcessing(true);
    try {
      const result = await processExpiredGrants();
      alert(result.message);
      onGrantUpdated();
    } catch (error) {
      console.error("Failed to process expired grants:", error);
      alert("Failed to process expired grants");
    } finally {
      setIsProcessing(false);
    }
  };

  const getStatusBadge = (grant: TemporaryGrant) => {
    if (grant.is_expired) {
      return <Badge variant="destructive">Expired</Badge>;
    }

    const now = new Date();
    const expiry = new Date(grant.expires_at);
    const start = new Date(grant.starts_at);

    if (now < start) {
      return <Badge variant="secondary">Scheduled</Badge>;
    }

    const hoursRemaining =
      (expiry.getTime() - now.getTime()) / (1000 * 60 * 60);

    if (hoursRemaining <= 24) {
      return <Badge variant="warning">Expiring Soon</Badge>;
    }

    return <Badge variant="success">Active</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Temporary Grants</h2>
        <Button
          onClick={handleProcessExpired}
          disabled={isProcessing}
          variant="outline"
        >
          {isProcessing ? "Processing..." : "Process Expired Grants"}
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Grant ID</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Starts At</TableHead>
              <TableHead>Expires At</TableHead>
              <TableHead>Time Remaining</TableHead>
              <TableHead>Extensions</TableHead>
              <TableHead>Reason</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {grants.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-gray-500">
                  No temporary grants found
                </TableCell>
              </TableRow>
            ) : (
              grants.map((grant) => (
                <TableRow key={grant.id}>
                  <TableCell className="font-mono text-xs">
                    {grant.grant_id.slice(0, 8)}...
                  </TableCell>
                  <TableCell>{getStatusBadge(grant)}</TableCell>
                  <TableCell className="text-sm">
                    {formatDateTime(grant.starts_at)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDateTime(grant.expires_at)}
                  </TableCell>
                  <TableCell>
                    <span
                      className={
                        grant.is_expired
                          ? "text-red-600 font-semibold"
                          : "text-gray-700"
                      }
                    >
                      {getTimeRemaining(grant.expires_at)}
                    </span>
                  </TableCell>
                  <TableCell>
                    {grant.extension_count}
                    {grant.max_extensions !== null &&
                      ` / ${grant.max_extensions}`}
                  </TableCell>
                  <TableCell className="max-w-xs truncate">
                    {grant.reason || "-"}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      {!grant.is_expired && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleExtendGrant(grant)}
                            disabled={
                              grant.max_extensions !== null &&
                              grant.extension_count >= grant.max_extensions
                            }
                          >
                            Extend
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleExpireNow(grant.id)}
                          >
                            Expire Now
                          </Button>
                        </>
                      )}
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDelete(grant.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Extend Grant Modal */}
      <Dialog open={isExtendModalOpen} onOpenChange={setIsExtendModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Extend Temporary Grant</DialogTitle>
            <DialogDescription>
              Set a new expiration date for this temporary grant.
            </DialogDescription>
          </DialogHeader>

          {selectedGrant && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-gray-50 p-3">
                <p className="text-sm">
                  <strong>Current Expiration:</strong>{" "}
                  {formatDateTime(selectedGrant.expires_at)}
                </p>
                <p className="text-sm">
                  <strong>Extensions:</strong> {selectedGrant.extension_count}
                  {selectedGrant.max_extensions !== null &&
                    ` / ${selectedGrant.max_extensions}`}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-expiration">New Expiration Date</Label>
                <Input
                  id="new-expiration"
                  type="datetime-local"
                  value={newExpirationDate}
                  onChange={(e) => setNewExpirationDate(e.target.value)}
                  min={new Date().toISOString().slice(0, 16)}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsExtendModalOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleExtendSubmit}>Extend Grant</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

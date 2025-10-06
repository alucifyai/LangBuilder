/**
 * User Invites List Component
 */

import { useState } from "react";
import { Button } from "../ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Badge } from "../ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import type { InviteResponse, InviteStatus } from "../../types/user-invites";
import { createInvite, revokeInvite } from "../../api/user-invites";
import useAlertStore from "../../stores/alertStore";

interface InvitesListProps {
  invites: InviteResponse[];
  onInviteCreated: () => void;
  onInviteRevoked: () => void;
}

export default function InvitesList({
  invites,
  onInviteCreated,
  onInviteRevoked,
}: InvitesListProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const handleCreate = async () => {
    if (!email.trim()) {
      setErrorData({ title: "Email is required", list: [] });
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await createInvite({
        email: email.trim(),
        role_ids: [], // Default empty - can be extended
        expires_in_days: 7,
      });

      setSuccessData({ title: "Invite Sent" });
      setEmail("");
      setShowCreateModal(false);
      onInviteCreated();

      // Show invite URL
      navigator.clipboard.writeText(result.invite_url);
      setSuccessData({ title: "Invite URL copied to clipboard" });
    } catch (error: any) {
      setErrorData({
        title: "Failed to create invite",
        list: [error?.response?.data?.detail || error.message],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRevoke = async (inviteId: string) => {
    try {
      await revokeInvite(inviteId, { reason: "Revoked by admin" });
      setSuccessData({ title: "Invite Revoked" });
      onInviteRevoked();
    } catch (error: any) {
      setErrorData({
        title: "Failed to revoke invite",
        list: [error?.response?.data?.detail || error.message],
      });
    }
  };

  const getStatusBadge = (status: InviteStatus) => {
    const colors = {
      pending: "bg-blue-100 text-blue-800",
      accepted: "bg-green-100 text-green-800",
      expired: "bg-gray-100 text-gray-800",
      revoked: "bg-red-100 text-red-800",
    };
    return <Badge className={colors[status]}>{status}</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">User Invites</h2>
          <p className="text-sm text-muted-foreground">
            Invite new users to join the platform
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Send Invite</Button>
      </div>

      {invites.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <h3 className="text-lg font-semibold">No invites yet</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Send an invite to add new users
          </p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Expires</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {invites.map((invite) => (
              <TableRow key={invite.id}>
                <TableCell className="font-medium">{invite.email}</TableCell>
                <TableCell>{getStatusBadge(invite.status)}</TableCell>
                <TableCell className="text-sm">
                  {new Date(invite.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell className="text-sm">
                  {new Date(invite.expires_at).toLocaleDateString()}
                </TableCell>
                <TableCell>
                  {invite.status === "pending" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRevoke(invite.id)}
                    >
                      Revoke
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send User Invite</DialogTitle>
            <DialogDescription>
              Invite a new user to join the platform
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={isSubmitting}>
              {isSubmitting ? "Sending..." : "Send Invite"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

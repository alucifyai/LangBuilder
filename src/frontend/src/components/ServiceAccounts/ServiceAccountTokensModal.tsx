/**
 * Service Account Tokens Management Modal
 */

import { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "../ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Badge } from "../ui/badge";
import { createAPIToken, listAPITokens, revokeAPIToken } from "../../api/service-accounts";
import type { ServiceAccountResponse, TokenResponse, TokenScope } from "../../types/service-accounts";
import useAlertStore from "../../stores/alertStore";
import { Input } from "../ui/input";
import { Label } from "../ui/label";

interface ServiceAccountTokensModalProps {
  account: ServiceAccountResponse;
  open: boolean;
  onClose: () => void;
}

export default function ServiceAccountTokensModal({
  account,
  open,
  onClose,
}: ServiceAccountTokensModalProps) {
  const [tokens, setTokens] = useState<TokenResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTokenName, setNewTokenName] = useState("");
  const [newToken, setNewToken] = useState<string | null>(null);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  useEffect(() => {
    if (open) {
      loadTokens();
    }
  }, [open, account.id]);

  const loadTokens = async () => {
    setIsLoading(true);
    try {
      const data = await listAPITokens(account.id);
      setTokens(data);
    } catch (error: any) {
      setErrorData({
        title: "Failed to load tokens",
        list: [error?.response?.data?.detail || error.message],
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateToken = async () => {
    if (!newTokenName.trim()) {
      setErrorData({ title: "Token name is required", list: [] });
      return;
    }

    try {
      const result = await createAPIToken(account.id, {
        name: newTokenName,
        scopes: ["read", "write"], // Default scopes
        expires_in_days: 90,
      });

      setNewToken(result.token);
      setNewTokenName("");
      setShowCreateForm(false);
      await loadTokens();
      setSuccessData({ title: "API Token Created" });
    } catch (error: any) {
      setErrorData({
        title: "Failed to create token",
        list: [error?.response?.data?.detail || error.message],
      });
    }
  };

  const handleRevoke = async (tokenId: string) => {
    try {
      await revokeAPIToken(account.id, tokenId, { reason: "Revoked by user" });
      await loadTokens();
      setSuccessData({ title: "Token Revoked" });
    } catch (error: any) {
      setErrorData({
        title: "Failed to revoke token",
        list: [error?.response?.data?.detail || error.message],
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>API Tokens - {account.name}</DialogTitle>
          <DialogDescription>
            Manage API tokens for this service account
          </DialogDescription>
        </DialogHeader>

        {newToken && (
          <div className="rounded-lg border bg-yellow-50 p-4 space-y-2">
            <p className="font-semibold text-yellow-900">
              ⚠️ Save this token - it won't be shown again!
            </p>
            <div className="flex gap-2">
              <Input value={newToken} readOnly className="font-mono text-sm" />
              <Button
                onClick={() => {
                  navigator.clipboard.writeText(newToken);
                  setSuccessData({ title: "Token copied to clipboard" });
                }}
              >
                Copy
              </Button>
            </div>
            <Button variant="outline" size="sm" onClick={() => setNewToken(null)}>
              I've saved it
            </Button>
          </div>
        )}

        <div className="space-y-4">
          {!showCreateForm ? (
            <Button onClick={() => setShowCreateForm(true)}>Create New Token</Button>
          ) : (
            <div className="rounded-lg border p-4 space-y-3">
              <Label>Token Name</Label>
              <Input
                value={newTokenName}
                onChange={(e) => setNewTokenName(e.target.value)}
                placeholder="production-api-token"
              />
              <div className="flex gap-2">
                <Button onClick={handleCreateToken}>Create</Button>
                <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          )}

          {isLoading ? (
            <p>Loading tokens...</p>
          ) : tokens.length === 0 ? (
            <p className="text-sm text-muted-foreground">No tokens yet</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Token Prefix</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tokens.map((token) => (
                  <TableRow key={token.id}>
                    <TableCell className="font-medium">{token.name}</TableCell>
                    <TableCell className="font-mono text-sm">{token.token_prefix}...</TableCell>
                    <TableCell>
                      <Badge className={token.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                        {token.is_active ? "Active" : "Revoked"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {token.last_used_at ? new Date(token.last_used_at).toLocaleDateString() : "Never"}
                    </TableCell>
                    <TableCell>
                      {token.is_active && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRevoke(token.id)}
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
        </div>
      </DialogContent>
    </Dialog>
  );
}

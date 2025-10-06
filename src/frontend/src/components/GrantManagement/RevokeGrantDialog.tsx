/**
 * RevokeGrantDialog Component
 *
 * Confirmation dialog for revoking a grant.
 * Features:
 * - Display grant details
 * - Warning about permanent action
 * - Cancel and Confirm actions
 * - Loading state during revocation
 */

import { AlertTriangle } from "lucide-react";
import type { Grant } from "../../types/grant";

interface RevokeGrantDialogProps {
  grant: Grant;
  roleName: string;
  onConfirm: () => void;
  onCancel: () => void;
  isRevoking: boolean;
}

const PRINCIPAL_TYPE_LABELS = {
  user: "User",
  group: "Group",
  service_account: "Service Account",
};

const SCOPE_TYPE_LABELS = {
  workspace: "Workspace",
  project: "Project",
  environment: "Environment",
  flow: "Flow",
  component: "Component",
};

export function RevokeGrantDialog({
  grant,
  roleName,
  onConfirm,
  onCancel,
  isRevoking,
}: RevokeGrantDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-background border rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-start gap-3 p-6 border-b">
          <div className="p-2 bg-destructive/10 rounded-full">
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold">Revoke Grant</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Are you sure you want to revoke this role assignment?
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Grant details */}
          <div className="p-4 bg-muted/50 rounded-md space-y-2">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="text-muted-foreground">Principal:</div>
              <div className="font-medium">
                {PRINCIPAL_TYPE_LABELS[grant.principal_type]}
              </div>

              <div className="text-muted-foreground">Role:</div>
              <div className="font-medium">{roleName}</div>

              <div className="text-muted-foreground">Scope:</div>
              <div className="font-medium">
                {SCOPE_TYPE_LABELS[grant.scope_type]} - {grant.scope_id}
              </div>

              {grant.expires_at && (
                <>
                  <div className="text-muted-foreground">Expires:</div>
                  <div className="font-medium">
                    {new Date(grant.expires_at).toLocaleDateString()}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Warning */}
          <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
            <p className="text-sm text-destructive font-medium">
              ⚠️ Warning: This action cannot be undone
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              The principal will immediately lose access to resources within this scope.
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 p-6 border-t">
          <button
            type="button"
            onClick={onCancel}
            disabled={isRevoking}
            className="px-4 py-2 border rounded-md hover:bg-accent disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isRevoking}
            className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 disabled:opacity-50"
          >
            {isRevoking ? "Revoking..." : "Revoke Grant"}
          </button>
        </div>
      </div>
    </div>
  );
}

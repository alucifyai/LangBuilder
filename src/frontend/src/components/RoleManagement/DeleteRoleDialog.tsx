/**
 * DeleteRoleDialog Component
 *
 * Confirmation dialog for role deletion.
 * Features:
 * - Warning about active grants if any exist
 * - Display role name being deleted
 * - Cancel and Confirm Delete actions
 * - Loading state during deletion
 */

import { AlertTriangle } from "lucide-react";

interface DeleteRoleDialogProps {
  roleName: string;
  activeGrantsCount: number;
  onConfirm: () => void;
  onCancel: () => void;
  isDeleting: boolean;
}

export function DeleteRoleDialog({
  roleName,
  activeGrantsCount,
  onConfirm,
  onCancel,
  isDeleting,
}: DeleteRoleDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-background border rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-start gap-3 p-6 border-b">
          <div className="p-2 bg-destructive/10 rounded-full">
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold">Delete Role</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Are you sure you want to delete "{roleName}"?
            </p>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-3">
          {activeGrantsCount > 0 ? (
            <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-sm text-destructive font-medium">
                ⚠️ Warning: This role has {activeGrantsCount} active grant
                {activeGrantsCount !== 1 ? "s" : ""}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Deleting this role will fail because users are currently assigned to it.
                Please remove all grants first.
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              This action cannot be undone. The role will be permanently removed from the system.
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 p-6 border-t">
          <button
            type="button"
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 border rounded-md hover:bg-accent disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isDeleting || activeGrantsCount > 0}
            className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 disabled:opacity-50"
          >
            {isDeleting ? "Deleting..." : "Delete Role"}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * AuditLogDiffModal Component
 *
 * Displays before/after state comparison for audit log entries.
 * Features:
 * - Side-by-side diff view
 * - Highlight changed fields
 * - Support for role and grant state changes
 */

import { X, ArrowRight } from "lucide-react";
import type { AuditLog, AuditRoleState } from "../../types/audit";

interface AuditLogDiffModalProps {
  log: AuditLog;
  onClose: () => void;
}

export function AuditLogDiffModal({ log, onClose }: AuditLogDiffModalProps) {
  const beforeState = log.before_state as AuditRoleState | null;
  const afterState = log.after_state as AuditRoleState | null;

  // Helper to compare values
  const hasChanged = (field: keyof AuditRoleState): boolean => {
    if (!beforeState || !afterState) return false;

    const before = beforeState[field];
    const after = afterState[field];

    // Handle array comparison (permissions)
    if (Array.isArray(before) && Array.isArray(after)) {
      return JSON.stringify([...before].sort()) !== JSON.stringify([...after].sort());
    }

    return before !== after;
  };

  // Render permission diff
  const renderPermissionsDiff = () => {
    if (!beforeState?.permissions || !afterState?.permissions) return null;

    const before = new Set(beforeState.permissions);
    const after = new Set(afterState.permissions);
    const added = [...after].filter((p) => !before.has(p));
    const removed = [...before].filter((p) => !after.has(p));
    const unchanged = [...before].filter((p) => after.has(p));

    return (
      <div className="space-y-2">
        {removed.length > 0 && (
          <div>
            <p className="text-xs font-medium text-red-600 mb-1">Removed:</p>
            <div className="flex flex-wrap gap-1">
              {removed.map((perm) => (
                <span
                  key={perm}
                  className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded line-through"
                >
                  {perm}
                </span>
              ))}
            </div>
          </div>
        )}
        {added.length > 0 && (
          <div>
            <p className="text-xs font-medium text-green-600 mb-1">Added:</p>
            <div className="flex flex-wrap gap-1">
              {added.map((perm) => (
                <span
                  key={perm}
                  className="inline-block px-2 py-1 text-xs bg-green-100 text-green-800 rounded"
                >
                  {perm}
                </span>
              ))}
            </div>
          </div>
        )}
        {unchanged.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1">Unchanged:</p>
            <div className="flex flex-wrap gap-1">
              {unchanged.map((perm) => (
                <span
                  key={perm}
                  className="inline-block px-2 py-1 text-xs bg-muted text-muted-foreground rounded"
                >
                  {perm}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-4xl max-h-[80vh] bg-background border rounded-lg shadow-lg flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h3 className="text-lg font-semibold">Audit Log Details</h3>
            <p className="text-sm text-muted-foreground">
              {formatTimestamp(log.timestamp)}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded-md"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 p-4 bg-muted/50 rounded-md">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Action</p>
              <p className="text-sm font-medium">{log.action.replace("_", " ").toUpperCase()}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Actor ID</p>
              <p className="text-sm font-mono truncate">{log.actor_id}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Resource Type</p>
              <p className="text-sm font-medium">{log.resource_type}</p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Resource ID</p>
              <p className="text-sm font-mono truncate">{log.resource_id}</p>
            </div>
          </div>

          {/* State changes */}
          {beforeState && afterState && (
            <div className="space-y-4">
              <h4 className="font-semibold">Changes</h4>

              {/* Name change */}
              {hasChanged("name") && (
                <div className="border rounded-md p-4">
                  <p className="text-sm font-medium mb-2">Name</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 px-3 py-2 bg-red-50 border border-red-200 rounded text-sm">
                      <span className="line-through text-red-700">{beforeState.name}</span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1 px-3 py-2 bg-green-50 border border-green-200 rounded text-sm">
                      <span className="text-green-700">{afterState.name}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Version change */}
              {hasChanged("version") && (
                <div className="border rounded-md p-4">
                  <p className="text-sm font-medium mb-2">Version</p>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 px-3 py-2 bg-muted border rounded text-sm">
                      v{beforeState.version}
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1 px-3 py-2 bg-green-50 border border-green-200 rounded text-sm">
                      <span className="text-green-700">v{afterState.version}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Permissions change */}
              {hasChanged("permissions") && (
                <div className="border rounded-md p-4">
                  <p className="text-sm font-medium mb-3">Permissions</p>
                  {renderPermissionsDiff()}
                </div>
              )}
            </div>
          )}

          {/* Creation state (no before state) */}
          {!beforeState && afterState && (
            <div className="space-y-4">
              <h4 className="font-semibold">Created State</h4>
              <div className="border rounded-md p-4 space-y-3">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Name</p>
                  <p className="text-sm font-medium">{afterState.name}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Version</p>
                  <p className="text-sm">v{afterState.version}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Permissions</p>
                  <div className="flex flex-wrap gap-1">
                    {afterState.permissions.map((perm) => (
                      <span
                        key={perm}
                        className="inline-block px-2 py-1 text-xs bg-primary/10 text-primary rounded"
                      >
                        {perm}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Deletion state (no after state) */}
          {beforeState && !afterState && (
            <div className="space-y-4">
              <h4 className="font-semibold">Deleted State</h4>
              <div className="border border-red-200 rounded-md p-4 bg-red-50 space-y-3">
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Name</p>
                  <p className="text-sm font-medium line-through">{beforeState.name}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground">Version</p>
                  <p className="text-sm line-through">v{beforeState.version}</p>
                </div>
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-2">Permissions</p>
                  <div className="flex flex-wrap gap-1">
                    {beforeState.permissions.map((perm) => (
                      <span
                        key={perm}
                        className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded line-through"
                      >
                        {perm}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Metadata */}
          {log.metadata && Object.keys(log.metadata).length > 0 && (
            <div className="space-y-2">
              <h4 className="font-semibold">Additional Metadata</h4>
              <pre className="p-3 bg-muted rounded-md text-xs overflow-x-auto">
                {JSON.stringify(log.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

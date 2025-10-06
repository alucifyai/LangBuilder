/**
 * AuditLogView Component
 *
 * Displays audit logs with filtering and pagination.
 * Features:
 * - Table view of audit log entries
 * - Filter by action type, date range, actor
 * - Pagination controls
 * - Click to view diff modal for updates
 */

import { useState, useEffect } from "react";
import { Calendar, Filter, RefreshCw, Eye } from "lucide-react";
import type { AuditLog, AuditLogFilters, AuditAction } from "../../types/audit";
import { listAuditLogs } from "../../controllers/API/audit";
import { AuditLogDiffModal } from "./AuditLogDiffModal";

const ACTION_LABELS: Record<AuditAction, string> = {
  role_created: "Role Created",
  role_updated: "Role Updated",
  role_deleted: "Role Deleted",
  grant_created: "Grant Created",
  grant_updated: "Grant Updated",
  grant_deleted: "Grant Deleted",
  grant_revoked: "Grant Revoked",
  permission_checked: "Permission Checked",
};

const ACTION_COLORS: Record<AuditAction, string> = {
  role_created: "bg-green-100 text-green-800",
  role_updated: "bg-blue-100 text-blue-800",
  role_deleted: "bg-red-100 text-red-800",
  grant_created: "bg-green-100 text-green-800",
  grant_updated: "bg-blue-100 text-blue-800",
  grant_deleted: "bg-red-100 text-red-800",
  grant_revoked: "bg-orange-100 text-orange-800",
  permission_checked: "bg-gray-100 text-gray-800",
};

export function AuditLogView() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  // Filter state
  const [filters, setFilters] = useState<AuditLogFilters>({
    limit: 50,
  });
  const [showFilters, setShowFilters] = useState(false);

  // Fetch logs
  const fetchLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await listAuditLogs(filters);
      setLogs(response.logs);
    } catch (err: any) {
      setError(err.message || "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filters]);

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Handle filter changes
  const handleFilterChange = (key: keyof AuditLogFilters, value: any) => {
    setFilters({ ...filters, [key]: value || undefined });
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({ limit: 50 });
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading audit logs...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-destructive">{error}</p>
        <button
          onClick={fetchLogs}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Audit Logs</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-3 py-2 border rounded-md hover:bg-accent"
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button
            onClick={fetchLogs}
            className="flex items-center gap-2 px-3 py-2 border rounded-md hover:bg-accent"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="p-4 border rounded-md bg-muted/50 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Action filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Action</label>
              <select
                value={filters.action || ""}
                onChange={(e) => handleFilterChange("action", e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All actions</option>
                {Object.entries(ACTION_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            {/* Start date filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Start Date</label>
              <input
                type="datetime-local"
                value={filters.start_date || ""}
                onChange={(e) => handleFilterChange("start_date", e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* End date filter */}
            <div>
              <label className="block text-sm font-medium mb-1">End Date</label>
              <input
                type="datetime-local"
                value={filters.end_date || ""}
                onChange={(e) => handleFilterChange("end_date", e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Resource type filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Resource Type</label>
              <select
                value={filters.resource_type || ""}
                onChange={(e) => handleFilterChange("resource_type", e.target.value)}
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All types</option>
                <option value="role">Role</option>
                <option value="grant">Grant</option>
              </select>
            </div>

            {/* Resource ID filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Resource ID</label>
              <input
                type="text"
                value={filters.resource_id || ""}
                onChange={(e) => handleFilterChange("resource_id", e.target.value)}
                placeholder="Enter resource ID..."
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Actor ID filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Actor ID</label>
              <input
                type="text"
                value={filters.actor_id || ""}
                onChange={(e) => handleFilterChange("actor_id", e.target.value)}
                placeholder="Enter user ID..."
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <button
              onClick={clearFilters}
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Clear all filters
            </button>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium">Limit:</label>
              <select
                value={filters.limit || 50}
                onChange={(e) => handleFilterChange("limit", parseInt(e.target.value))}
                className="px-3 py-1 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={500}>500</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Audit logs table */}
      <div className="border rounded-md">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Timestamp</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Action</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Resource</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Actor</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  No audit logs found.
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <tr key={log.id} className="border-t hover:bg-muted/50">
                  <td className="px-4 py-3 text-sm">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-block px-2 py-1 text-xs font-medium rounded ${
                        ACTION_COLORS[log.action]
                      }`}
                    >
                      {ACTION_LABELS[log.action]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="font-medium">{log.resource_type}</div>
                    <div className="text-xs text-muted-foreground truncate max-w-[200px]">
                      {log.resource_id}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground truncate max-w-[150px]">
                    {log.actor_id}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {log.action.includes("updated") && log.before_state && log.after_state && (
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="p-2 hover:bg-accent rounded-md"
                        title="View changes"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Result count */}
      <div className="text-sm text-muted-foreground">
        Showing {logs.length} log{logs.length !== 1 ? "s" : ""}
      </div>

      {/* Diff modal */}
      {selectedLog && (
        <AuditLogDiffModal
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </div>
  );
}

/**
 * Enhanced Audit Log Viewer
 * Comprehensive audit log viewing with filtering, search, and export
 */

import React, { useState, useEffect } from "react";
import type { AuditLog, AuditLogFilters } from "../../types/audit-logs";
import {
  listAuditLogs,
  exportAuditLogs,
  getSecurityEvents,
} from "../../api/audit-logs";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

export function EnhancedAuditLogView() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  // Filters
  const [filters, setFilters] = useState<AuditLogFilters>({
    limit: 50,
    offset: 0,
  });
  const [searchTerm, setSearchTerm] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  // Export
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("json");
  const [exportReason, setExportReason] = useState("");
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    loadLogs();
  }, [filters]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const response = await listAuditLogs(filters);
      setLogs(response.logs);
      setTotal(response.total);
    } catch (error) {
      console.error("Failed to load audit logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setFilters({
      ...filters,
      search: searchTerm || undefined,
      event_type: eventTypeFilter || undefined,
      severity: severityFilter || undefined,
      status: statusFilter || undefined,
      offset: 0,
    });
  };

  const handleClearFilters = () => {
    setSearchTerm("");
    setEventTypeFilter("");
    setSeverityFilter("");
    setStatusFilter("");
    setFilters({ limit: 50, offset: 0 });
  };

  const handleViewDetails = (log: AuditLog) => {
    setSelectedLog(log);
    setIsDetailModalOpen(true);
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const now = new Date();
      const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

      const blob = await exportAuditLogs({
        export_type: "compliance",
        format: exportFormat,
        start_date: thirtyDaysAgo.toISOString(),
        end_date: now.toISOString(),
        reason: exportReason || undefined,
      });

      // Download file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${Date.now()}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setIsExportModalOpen(false);
      setExportReason("");
    } catch (error) {
      console.error("Failed to export logs:", error);
      alert("Failed to export audit logs");
    } finally {
      setIsExporting(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, "default" | "destructive" | "warning" | "success"> = {
      critical: "destructive",
      error: "destructive",
      warning: "warning",
      info: "default",
    };
    return (
      <Badge variant={variants[severity] || "default"}>
        {severity.toUpperCase()}
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    return (
      <Badge variant={status === "success" ? "success" : "destructive"}>
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Enhanced Audit Logs</h2>
          <p className="text-sm text-gray-500 mt-1">
            Comprehensive security and compliance audit trail
          </p>
        </div>
        <Button onClick={() => setIsExportModalOpen(true)}>Export Logs</Button>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-4 gap-4 p-4 border rounded-lg bg-gray-50">
        <div className="space-y-2">
          <Label>Search</Label>
          <Input
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>

        <div className="space-y-2">
          <Label>Event Type</Label>
          <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
            <SelectTrigger>
              <SelectValue placeholder="All events" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All events</SelectItem>
              <SelectItem value="auth">Authentication</SelectItem>
              <SelectItem value="access">Access</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="config">Configuration</SelectItem>
              <SelectItem value="security">Security</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Severity</Label>
          <Select value={severityFilter} onValueChange={setSeverityFilter}>
            <SelectTrigger>
              <SelectValue placeholder="All severities" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All severities</SelectItem>
              <SelectItem value="info">Info</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="error">Error</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label>Status</Label>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger>
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All statuses</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failure">Failure</SelectItem>
              <SelectItem value="partial">Partial</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="col-span-4 flex gap-2">
          <Button onClick={handleSearch}>Apply Filters</Button>
          <Button variant="outline" onClick={handleClearFilters}>
            Clear Filters
          </Button>
          <div className="ml-auto text-sm text-gray-600 flex items-center">
            Showing {logs.length} of {total} logs
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Timestamp</TableHead>
              <TableHead>Event</TableHead>
              <TableHead>Action</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Target</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>IP Address</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : logs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className="text-center text-gray-500">
                  No audit logs found
                </TableCell>
              </TableRow>
            ) : (
              logs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="text-sm">
                    {formatTimestamp(log.timestamp)}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{log.event_type}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {log.action}
                  </TableCell>
                  <TableCell className="text-sm">
                    {log.actor_email || log.actor_id || "-"}
                  </TableCell>
                  <TableCell className="text-sm">
                    {log.target_name || log.target_type || "-"}
                  </TableCell>
                  <TableCell>{getStatusBadge(log.status)}</TableCell>
                  <TableCell>{getSeverityBadge(log.severity)}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {log.ip_address || "-"}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleViewDetails(log)}
                    >
                      Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center">
        <Button
          variant="outline"
          disabled={filters.offset === 0}
          onClick={() =>
            setFilters({
              ...filters,
              offset: Math.max(0, (filters.offset || 0) - (filters.limit || 50)),
            })
          }
        >
          Previous
        </Button>
        <span className="text-sm text-gray-600">
          Page {Math.floor((filters.offset || 0) / (filters.limit || 50)) + 1}
        </span>
        <Button
          variant="outline"
          disabled={(filters.offset || 0) + logs.length >= total}
          onClick={() =>
            setFilters({
              ...filters,
              offset: (filters.offset || 0) + (filters.limit || 50),
            })
          }
        >
          Next
        </Button>
      </div>

      {/* Detail Modal */}
      <Dialog open={isDetailModalOpen} onOpenChange={setIsDetailModalOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Audit Log Details</DialogTitle>
            <DialogDescription>
              Complete information about this audit event
            </DialogDescription>
          </DialogHeader>

          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-gray-600">Event ID</Label>
                  <p className="font-mono text-sm">{selectedLog.id}</p>
                </div>
                <div>
                  <Label className="text-gray-600">Timestamp</Label>
                  <p>{formatTimestamp(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <Label className="text-gray-600">Event Type</Label>
                  <p>{selectedLog.event_type}</p>
                </div>
                <div>
                  <Label className="text-gray-600">Action</Label>
                  <p>{selectedLog.action}</p>
                </div>
                <div>
                  <Label className="text-gray-600">Status</Label>
                  <p>{getStatusBadge(selectedLog.status)}</p>
                </div>
                <div>
                  <Label className="text-gray-600">Severity</Label>
                  <p>{getSeverityBadge(selectedLog.severity)}</p>
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-semibold mb-2">Actor Information</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-600">Actor Email</Label>
                    <p>{selectedLog.actor_email || "-"}</p>
                  </div>
                  <div>
                    <Label className="text-gray-600">Actor ID</Label>
                    <p className="font-mono text-sm">
                      {selectedLog.actor_id || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-gray-600">IP Address</Label>
                    <p className="font-mono text-sm">
                      {selectedLog.ip_address || "-"}
                    </p>
                  </div>
                  <div>
                    <Label className="text-gray-600">Session ID</Label>
                    <p className="font-mono text-sm">
                      {selectedLog.session_id || "-"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-semibold mb-2">Target Information</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-600">Target Name</Label>
                    <p>{selectedLog.target_name || "-"}</p>
                  </div>
                  <div>
                    <Label className="text-gray-600">Target Type</Label>
                    <p>{selectedLog.target_type || "-"}</p>
                  </div>
                  <div className="col-span-2">
                    <Label className="text-gray-600">Target ID</Label>
                    <p className="font-mono text-sm">
                      {selectedLog.target_id || "-"}
                    </p>
                  </div>
                </div>
              </div>

              {selectedLog.changes && (
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-2">Changes</h4>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.changes, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.metadata && (
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-2">Metadata</h4>
                  <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.error_message && (
                <div className="border-t pt-4">
                  <h4 className="font-semibold mb-2 text-red-600">
                    Error Details
                  </h4>
                  <div className="bg-red-50 p-3 rounded">
                    <p className="text-sm">
                      <strong>Code:</strong> {selectedLog.error_code}
                    </p>
                    <p className="text-sm mt-2">
                      <strong>Message:</strong> {selectedLog.error_message}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setIsDetailModalOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Export Modal */}
      <Dialog open={isExportModalOpen} onOpenChange={setIsExportModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Audit Logs</DialogTitle>
            <DialogDescription>
              Export audit logs for compliance or investigation purposes
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Export Format</Label>
              <Select
                value={exportFormat}
                onValueChange={(v) => setExportFormat(v as "json" | "csv")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="csv">CSV</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Reason for Export</Label>
              <Input
                placeholder="e.g., SOC2 audit, security investigation..."
                value={exportReason}
                onChange={(e) => setExportReason(e.target.value)}
              />
            </div>

            <div className="text-sm text-gray-600">
              <p>Export will include logs from the last 30 days.</p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsExportModalOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleExport} disabled={isExporting}>
              {isExporting ? "Exporting..." : "Export"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

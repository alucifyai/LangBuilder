import { useContext, useEffect, useRef, useState } from "react";
import PaginatorComponent from "@/components/common/paginatorComponent";
import {
  useGetAuditLogs,
  useGetAuditLog,
  useExportAuditLogs,
  AuditEventType,
  ActorType,
  AuditOutcome,
  getEventTypeColor,
  getOutcomeColor,
  formatEventType,
  formatActorType,
} from "@/controllers/API/queries/rbac/use-audit-logs";
import { useGetWorkspaces } from "@/controllers/API/queries/rbac";
import type { AuditLog } from "@/controllers/API/queries/rbac/use-audit-logs";
import CustomLoader from "@/customization/components/custom-loader";
import IconComponent from "../../../../components/common/genericIconComponent";
import ShadTooltip from "../../../../components/common/shadTooltipComponent";
import { Button } from "../../../../components/ui/button";
import { Input } from "../../../../components/ui/input";
import { Label } from "../../../../components/ui/label";
import { Badge } from "../../../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../../../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../../../components/ui/dialog";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../../components/ui/card";
import { DatePicker } from "../../../../components/ui/date-picker";
import {
  PAGINATION_PAGE,
  PAGINATION_ROWS_COUNT,
  PAGINATION_SIZE,
} from "../../../../constants/constants";
import { AuthContext } from "../../../../contexts/authContext";
import useAlertStore from "../../../../stores/alertStore";

export default function AuditLogsPage() {
  const [inputValue, setInputValue] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState("");
  const [size, setPageSize] = useState(PAGINATION_SIZE);
  const [index, setPageIndex] = useState(PAGINATION_PAGE);
  const [totalRowsCount, setTotalRowsCount] = useState(0);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [showLogDetails, setShowLogDetails] = useState(false);
  const [showExportDialog, setShowExportDialog] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    event_type: "" as AuditEventType | "",
    actor_type: "" as ActorType | "",
    outcome: "" as AuditOutcome | "",
    start_date: "",
    end_date: "",
    resource_type: "",
  });

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const { userData } = useContext(AuthContext);

  const auditLogsList = useRef<AuditLog[]>([]);
  const workspaceList = useRef<any[]>([]);

  const [filterAuditLogsList, setFilterAuditLogsList] = useState(
    auditLogsList.current,
  );

  // API hooks
  const { mutate: mutateGetAuditLogs, isPending, isIdle } = useGetAuditLogs({});
  const { mutate: mutateGetAuditLog } = useGetAuditLog({});
  const { mutate: mutateExportAuditLogs } = useExportAuditLogs({});
  const { mutate: mutateGetWorkspaces } = useGetWorkspaces({});

  useEffect(() => {
    getWorkspaces();
  }, []);

  useEffect(() => {
    if (workspaceList.current.length > 0 && !selectedWorkspace) {
      setSelectedWorkspace(workspaceList.current[0].id);
    }
  }, [workspaceList.current]);

  useEffect(() => {
    if (selectedWorkspace) {
      getAuditLogs();
    }
  }, [selectedWorkspace, filters, index, size]);

  function getWorkspaces() {
    mutateGetWorkspaces(
      { skip: 0, limit: 1000 },
      {
        onSuccess: (data) => {
          workspaceList.current = data.workspaces;
          if (data.workspaces.length > 0 && !selectedWorkspace) {
            setSelectedWorkspace(data.workspaces[0].id);
          }
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load workspaces",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function getAuditLogs() {
    if (!selectedWorkspace) return;

    const params = {
      workspace_id: selectedWorkspace,
      page: index,
      page_size: size,
      search: inputValue || undefined,
      ...Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== "")
      ),
    };

    mutateGetAuditLogs(params, {
      onSuccess: (data) => {
        setTotalRowsCount(data.total_count);
        auditLogsList.current = data.audit_logs;
        setFilterAuditLogsList(data.audit_logs);
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to load audit logs",
          list: [error.message || "Unknown error occurred"],
        });
      },
    });
  }

  function handleViewLogDetails(log: AuditLog) {
    setSelectedLog(log);
    setShowLogDetails(true);

    // Optionally fetch more details
    mutateGetAuditLog(
      { log_id: log.id },
      {
        onSuccess: (detailedLog) => {
          setSelectedLog(detailedLog);
        },
        onError: (error) => {
          console.warn("Failed to load detailed log:", error);
        },
      },
    );
  }

  function handleExportLogs() {
    if (!selectedWorkspace) return;

    const exportData = {
      workspace_id: selectedWorkspace,
      format: "csv" as const,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
      event_types: filters.event_type ? [filters.event_type] : undefined,
      actor_types: filters.actor_type ? [filters.actor_type] : undefined,
      outcomes: filters.outcome ? [filters.outcome] : undefined,
      include_metadata: true,
      include_sensitive: false,
    };

    mutateExportAuditLogs(exportData, {
      onSuccess: (result) => {
        setSuccessData({
          title: "Export started",
          list: [`Export ID: ${result.export_id}`, "Download will be available shortly"],
        });
        setShowExportDialog(false);
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to export audit logs",
          list: [error.message || "Unknown error occurred"],
        });
      },
    });
  }

  function handleChangePagination(pageIndex: number, pageSize: number) {
    setPageSize(pageSize);
    setPageIndex(pageIndex);
  }

  function handleFilterChange(key: string, value: string) {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPageIndex(1); // Reset to first page when filtering
  }

  function handleSearchChange(value: string) {
    setInputValue(value);
    // Debounce the search
    setTimeout(() => {
      getAuditLogs();
    }, 300);
  }

  function clearFilters() {
    setFilters({
      event_type: "",
      actor_type: "",
      outcome: "",
      start_date: "",
      end_date: "",
      resource_type: "",
    });
    setInputValue("");
  }

  const hasFilters = Object.values(filters).some(v => v !== "") || inputValue !== "";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <IconComponent name="FileText" className="w-6 h-6" />
          <h2 className="text-2xl font-bold">Audit Logs</h2>
        </div>

        <Button onClick={() => setShowExportDialog(true)}>
          <IconComponent name="Download" className="w-4 h-4 mr-2" />
          Export Logs
        </Button>
      </div>

      {/* Workspace Selection */}
      <div className="flex items-center gap-4">
        <Label htmlFor="workspace-select" className="text-sm font-medium">
          Workspace:
        </Label>
        <Select value={selectedWorkspace} onValueChange={setSelectedWorkspace}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select workspace" />
          </SelectTrigger>
          <SelectContent>
            {workspaceList.current.map((workspace) => (
              <SelectItem key={workspace.id} value={workspace.id}>
                {workspace.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Filters</CardTitle>
            {hasFilters && (
              <Button variant="outline" size="sm" onClick={clearFilters}>
                Clear Filters
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <Label htmlFor="search">Search</Label>
              <Input
                id="search"
                placeholder="Search logs..."
                value={inputValue}
                onChange={(e) => handleSearchChange(e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="event-type">Event Type</Label>
              <Select
                value={filters.event_type}
                onValueChange={(value) => handleFilterChange("event_type", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All events" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Events</SelectItem>
                  {Object.values(AuditEventType).map((type) => (
                    <SelectItem key={type} value={type}>
                      {formatEventType(type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="actor-type">Actor Type</Label>
              <Select
                value={filters.actor_type}
                onValueChange={(value) => handleFilterChange("actor_type", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All actors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Actors</SelectItem>
                  {Object.values(ActorType).map((type) => (
                    <SelectItem key={type} value={type}>
                      {formatActorType(type)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="outcome">Outcome</Label>
              <Select
                value={filters.outcome}
                onValueChange={(value) => handleFilterChange("outcome", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All outcomes" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Outcomes</SelectItem>
                  {Object.values(AuditOutcome).map((outcome) => (
                    <SelectItem key={outcome} value={outcome}>
                      {outcome.charAt(0).toUpperCase() + outcome.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="start-date">Start Date</Label>
              <Input
                id="start-date"
                type="date"
                value={filters.start_date}
                onChange={(e) => handleFilterChange("start_date", e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="end-date">End Date</Label>
              <Input
                id="end-date"
                type="date"
                value={filters.end_date}
                onChange={(e) => handleFilterChange("end_date", e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="resource-type">Resource Type</Label>
              <Input
                id="resource-type"
                placeholder="e.g., workspace, role"
                value={filters.resource_type}
                onChange={(e) => handleFilterChange("resource_type", e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs Table */}
      {isPending || isIdle ? (
        <div className="flex h-64 w-full items-center justify-center">
          <CustomLoader remSize={12} />
        </div>
      ) : auditLogsList.current.length === 0 && !isIdle ? (
        <div className="text-center py-12">
          <IconComponent name="FileText" className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No audit logs found</h3>
          <p className="text-muted-foreground mb-4">
            No audit logs match your current filters.
          </p>
        </div>
      ) : (
        <>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Event</TableHead>
                  <TableHead>Actor</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Outcome</TableHead>
                  <TableHead>IP Address</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filterAuditLogsList.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      <div className="text-sm">
                        <div>{new Date(log.timestamp).toLocaleDateString()}</div>
                        <div className="text-muted-foreground">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`border-${getEventTypeColor(log.event_type)}-500`}
                        >
                          {formatEventType(log.event_type)}
                        </Badge>
                        <span className="text-sm text-muted-foreground">
                          {log.action}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">
                          {log.actor_name || log.actor_id || "Unknown"}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {formatActorType(log.actor_type)}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        {log.resource_name && (
                          <div className="font-medium">{log.resource_name}</div>
                        )}
                        {log.resource_type && (
                          <div className="text-sm text-muted-foreground">
                            {log.resource_type}
                          </div>
                        )}
                        {!log.resource_name && !log.resource_type && (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          log.outcome === AuditOutcome.SUCCESS
                            ? "default"
                            : log.outcome === AuditOutcome.FAILURE ||
                              log.outcome === AuditOutcome.ERROR
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {log.outcome.charAt(0).toUpperCase() + log.outcome.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-mono">
                        {log.ip_address || "-"}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <ShadTooltip content="View details">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewLogDetails(log)}
                        >
                          <IconComponent name="Eye" className="h-4 w-4" />
                        </Button>
                      </ShadTooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <PaginatorComponent
            pageIndex={index}
            pageSize={size}
            totalRowsCount={totalRowsCount}
            paginate={handleChangePagination}
            rowsCount={PAGINATION_ROWS_COUNT}
          />
        </>
      )}

      {/* Log Details Modal */}
      <Dialog open={showLogDetails} onOpenChange={setShowLogDetails}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Audit Log Details</DialogTitle>
            <DialogDescription>
              Detailed information about this audit event
            </DialogDescription>
          </DialogHeader>

          {selectedLog && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Event Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <Label className="text-sm font-medium">Event Type</Label>
                      <p>{formatEventType(selectedLog.event_type)}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Action</Label>
                      <p>{selectedLog.action}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Outcome</Label>
                      <Badge variant={
                        selectedLog.outcome === AuditOutcome.SUCCESS
                          ? "default"
                          : "destructive"
                      }>
                        {selectedLog.outcome}
                      </Badge>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Timestamp</Label>
                      <p>{new Date(selectedLog.timestamp).toLocaleString()}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Actor Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <Label className="text-sm font-medium">Actor Type</Label>
                      <p>{formatActorType(selectedLog.actor_type)}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Actor Name</Label>
                      <p>{selectedLog.actor_name || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Actor Email</Label>
                      <p>{selectedLog.actor_email || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Actor ID</Label>
                      <p className="font-mono text-sm">{selectedLog.actor_id || "-"}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Resource Information</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <Label className="text-sm font-medium">Resource Type</Label>
                      <p>{selectedLog.resource_type || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Resource Name</Label>
                      <p>{selectedLog.resource_name || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Resource ID</Label>
                      <p className="font-mono text-sm">{selectedLog.resource_id || "-"}</p>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Technical Details</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <Label className="text-sm font-medium">IP Address</Label>
                      <p className="font-mono">{selectedLog.ip_address || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">User Agent</Label>
                      <p className="text-sm break-all">{selectedLog.user_agent || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">API Endpoint</Label>
                      <p className="font-mono text-sm">{selectedLog.api_endpoint || "-"}</p>
                    </div>
                    <div>
                      <Label className="text-sm font-medium">Request ID</Label>
                      <p className="font-mono text-sm">{selectedLog.request_id || "-"}</p>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {selectedLog.error_message && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base text-red-600">Error Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div>
                      <Label className="text-sm font-medium">Error Message</Label>
                      <p className="text-red-600">{selectedLog.error_message}</p>
                    </div>
                    {selectedLog.error_code && (
                      <div className="mt-2">
                        <Label className="text-sm font-medium">Error Code</Label>
                        <p className="font-mono">{selectedLog.error_code}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Metadata</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-sm bg-muted p-4 rounded overflow-x-auto">
                      {JSON.stringify(selectedLog.metadata, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Export Audit Logs</DialogTitle>
            <DialogDescription>
              Export audit logs matching your current filters
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              This will export all audit logs that match your current filter criteria.
              The export will be generated in CSV format and available for download.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowExportDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleExportLogs}>
                <IconComponent name="Download" className="w-4 h-4 mr-2" />
                Start Export
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

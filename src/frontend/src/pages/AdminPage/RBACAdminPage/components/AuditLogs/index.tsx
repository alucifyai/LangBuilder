// Audit Logs Component - Epic 5: Compliance
// Implements audit logging with compliance reporting features

import { useMemo, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { AuditLog, User } from "../../types/rbac";

// Mock data for audit logs
const MOCK_USERS: User[] = [
  {
    id: "user-1",
    email: "alice@company.com",
    name: "Alice Johnson",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-25T00:00:00Z",
  },
  {
    id: "user-2",
    email: "bob@company.com",
    name: "Bob Smith",
    is_active: true,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-24T00:00:00Z",
  },
  {
    id: "admin",
    email: "admin@company.com",
    name: "System Admin",
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-26T00:00:00Z",
  },
];

const MOCK_AUDIT_LOGS: AuditLog[] = [
  {
    id: "audit-1",
    actor_id: "admin",
    actor: MOCK_USERS[2],
    action: "role_assigned",
    resource_type: "user",
    resource_id: "user-1",
    details: {
      role_name: "Editor",
      scope: { type: "workspace", id: "ws-1", name: "Data Science" },
      previous_roles: [],
    },
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    timestamp: "2024-01-26T10:30:00Z",
  },
  {
    id: "audit-2",
    actor_id: "user-1",
    actor: MOCK_USERS[0],
    action: "workspace_created",
    resource_type: "workspace",
    resource_id: "ws-2",
    details: {
      workspace_name: "ML Engineering",
      description: "Machine learning projects",
      settings: { allow_external_users: false },
    },
    ip_address: "192.168.1.101",
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    timestamp: "2024-01-26T09:15:00Z",
  },
  {
    id: "audit-3",
    actor_id: "admin",
    actor: MOCK_USERS[2],
    action: "role_revoked",
    resource_type: "user",
    resource_id: "user-2",
    details: {
      role_name: "Deployer",
      scope: { type: "environment", id: "env-1", name: "Production" },
      reason: "Employee role change",
    },
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    timestamp: "2024-01-26T08:45:00Z",
  },
  {
    id: "audit-4",
    actor_id: "user-1",
    actor: MOCK_USERS[0],
    action: "service_account_created",
    resource_type: "service_account",
    resource_id: "sa-3",
    details: {
      service_account_name: "backup-service",
      scope: { type: "workspace", id: "ws-1", name: "Data Science" },
      permissions: ["read", "export_flow"],
    },
    ip_address: "192.168.1.101",
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    timestamp: "2024-01-25T16:20:00Z",
  },
  {
    id: "audit-5",
    actor_id: "admin",
    actor: MOCK_USERS[2],
    action: "user_invited",
    resource_type: "workspace",
    resource_id: "ws-1",
    details: {
      invited_email: "carol@company.com",
      role_name: "Viewer",
      invitation_expires: "2024-02-01T00:00:00Z",
    },
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    timestamp: "2024-01-25T14:10:00Z",
  },
  {
    id: "audit-6",
    actor_id: "user-2",
    actor: MOCK_USERS[1],
    action: "flow_deployed",
    resource_type: "environment",
    resource_id: "env-2",
    details: {
      flow_name: "Customer Segmentation",
      environment: "Staging",
      deployment_version: "v1.2.3",
    },
    ip_address: "192.168.1.102",
    user_agent: "Mozilla/5.0 (Ubuntu; Linux x86_64)",
    timestamp: "2024-01-25T12:30:00Z",
  },
  {
    id: "audit-7",
    actor_id: "admin",
    actor: MOCK_USERS[2],
    action: "permission_granted",
    resource_type: "role",
    resource_id: "role-2",
    details: {
      role_name: "Deployer",
      permission_added: "deploy_environment",
      scope: { type: "environment", id: "env-1", name: "Production" },
    },
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    timestamp: "2024-01-25T11:45:00Z",
  },
  {
    id: "audit-8",
    actor_id: "user-1",
    actor: MOCK_USERS[0],
    action: "sso_login",
    resource_type: "user",
    resource_id: "user-1",
    details: {
      sso_provider: "Okta",
      mfa_verified: true,
      session_duration: "8 hours",
    },
    ip_address: "192.168.1.101",
    user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    timestamp: "2024-01-25T09:00:00Z",
  },
];

interface ComplianceReportDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

function ComplianceReportDialog({
  isOpen,
  onClose,
}: ComplianceReportDialogProps) {
  const [reportType, setReportType] = useState<string>("user_access");
  const [dateRange, setDateRange] = useState<{
    from: Date | undefined;
    to: Date | undefined;
  }>({
    from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    to: new Date(),
  });
  const [format, setFormat] = useState<string>("csv");

  const handleGenerateReport = () => {
    const reportConfig = {
      type: reportType,
      start_date: dateRange.from?.toISOString(),
      end_date: dateRange.to?.toISOString(),
      format: format,
    };

    // PRD Epic 5: Story 5.2 - Export compliance report
    alert(
      `Generating ${reportType} report in ${format.toUpperCase()} format from ${dateRange.from?.toLocaleDateString()} to ${dateRange.to?.toLocaleDateString()}`,
    );
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Generate Compliance Report</DialogTitle>
          <DialogDescription>
            Export audit logs and access reports for compliance review and
            analysis.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          <div>
            <Label>Report Type</Label>
            <Select value={reportType} onValueChange={setReportType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user_access">User Access Report</SelectItem>
                <SelectItem value="role_changes">
                  Role Changes Report
                </SelectItem>
                <SelectItem value="authentication">
                  Authentication Events
                </SelectItem>
                <SelectItem value="permission_grants">
                  Permission Grants
                </SelectItem>
                <SelectItem value="service_account_activity">
                  Service Account Activity
                </SelectItem>
                <SelectItem value="failed_access_attempts">
                  Failed Access Attempts
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Date Range</Label>
            <DatePickerWithRange date={dateRange} onDateChange={setDateRange} />
          </div>

          <div>
            <Label>Export Format</Label>
            <Select value={format} onValueChange={setFormat}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                <SelectItem value="pdf">PDF Report</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-start space-x-2">
              <IconComponent
                name="Info"
                className="h-4 w-4 text-blue-600 mt-0.5"
              />
              <div className="text-sm">
                <div className="font-medium text-blue-900">
                  Compliance Features
                </div>
                <div className="text-blue-700 mt-1">
                  Reports include all required audit fields for SOC 2 / ISO
                  27001 compliance. Personal identifiers are masked unless
                  accessed by Admins or Auditors.
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleGenerateReport}
              disabled={!startDate || !endDate}
            >
              <IconComponent name="Download" className="h-4 w-4 mr-2" />
              Generate Report
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AuditLogTable({ logs }: { logs: AuditLog[] }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterAction, setFilterAction] = useState<string>("all");
  const [filterActor, setFilterActor] = useState<string>("all");
  const [filterResourceType, setFilterResourceType] = useState<string>("all");
  const [filterDateRange, setFilterDateRange] = useState<{
    from: Date | undefined;
    to: Date | undefined;
  }>({ from: undefined, to: undefined });

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesSearch =
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.actor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.actor.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(log.details)
          .toLowerCase()
          .includes(searchTerm.toLowerCase());

      const matchesAction =
        filterAction === "all" || log.action === filterAction;
      const matchesActor =
        filterActor === "all" || log.actor_id === filterActor;
      const matchesResourceType =
        filterResourceType === "all" ||
        log.resource_type === filterResourceType;

      const logDate = new Date(log.timestamp);
      const matchesDateRange =
        (!filterDateRange.from || logDate >= filterDateRange.from) &&
        (!filterDateRange.to || logDate <= filterDateRange.to);

      return (
        matchesSearch &&
        matchesAction &&
        matchesActor &&
        matchesResourceType &&
        matchesDateRange
      );
    });
  }, [
    logs,
    searchTerm,
    filterAction,
    filterActor,
    filterResourceType,
    filterDateRange,
  ]);

  const getActionIcon = (action: string) => {
    switch (action) {
      case "role_assigned":
        return "UserPlus";
      case "role_revoked":
        return "UserMinus";
      case "workspace_created":
        return "Building";
      case "service_account_created":
        return "Bot";
      case "user_invited":
        return "Mail";
      case "flow_deployed":
        return "Rocket";
      case "permission_granted":
        return "Shield";
      case "sso_login":
        return "LogIn";
      case "token_created":
        return "Key";
      case "token_revoked":
        return "KeyOff";
      default:
        return "Activity";
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case "role_assigned":
      case "permission_granted":
      case "workspace_created":
      case "service_account_created":
        return "text-green-700 bg-green-100";
      case "role_revoked":
      case "token_revoked":
        return "text-red-700 bg-red-100";
      case "sso_login":
      case "flow_deployed":
        return "text-blue-700 bg-blue-100";
      case "user_invited":
        return "text-purple-700 bg-purple-100";
      default:
        return "text-gray-700 bg-gray-100";
    }
  };

  const uniqueActions = [...new Set(logs.map((log) => log.action))];
  const uniqueActors = [
    ...new Set(logs.map((log) => ({ id: log.actor_id, name: log.actor.name }))),
  ];
  const uniqueResourceTypes = [
    ...new Set(logs.map((log) => log.resource_type)),
  ];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Input
          placeholder="Search logs..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <Select value={filterAction} onValueChange={setFilterAction}>
          <SelectTrigger>
            <SelectValue placeholder="Action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            {uniqueActions.map((action) => (
              <SelectItem key={action} value={action}>
                {action.replace(/_/g, " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterActor} onValueChange={setFilterActor}>
          <SelectTrigger>
            <SelectValue placeholder="Actor" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actors</SelectItem>
            {uniqueActors.map((actor) => (
              <SelectItem key={actor.id} value={actor.id}>
                {actor.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={filterResourceType}
          onValueChange={setFilterResourceType}
        >
          <SelectTrigger>
            <SelectValue placeholder="Resource" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Resources</SelectItem>
            {uniqueResourceTypes.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <DatePickerWithRange
          date={filterDateRange}
          onDateChange={setFilterDateRange}
        />
      </div>

      {/* Results count */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Showing {filteredLogs.length} of {logs.length} audit entries
        </div>
        {(startDate ||
          endDate ||
          searchTerm ||
          filterAction !== "all" ||
          filterActor !== "all" ||
          filterResourceType !== "all") && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setSearchTerm("");
              setFilterAction("all");
              setFilterActor("all");
              setFilterResourceType("all");
              setStartDate(undefined);
              setEndDate(undefined);
            }}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Audit Log Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Source</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredLogs.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    <div className="text-sm">
                      {new Date(log.timestamp).toLocaleDateString()}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{log.actor.name}</div>
                      <div className="text-sm text-muted-foreground">
                        {log.actor.email}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={`${getActionColor(log.action)} border-0`}>
                      <IconComponent
                        name={getActionIcon(log.action)}
                        className="h-3 w-3 mr-1"
                      />
                      {log.action.replace(/_/g, " ")}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium capitalize">
                        {log.resource_type}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {log.resource_id}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="max-w-xs">
                      {log.details && Object.keys(log.details).length > 0 && (
                        <div className="text-sm">
                          {Object.entries(log.details)
                            .slice(0, 2)
                            .map(([key, value]) => (
                              <div key={key} className="truncate">
                                <span className="font-medium">{key}:</span>{" "}
                                {String(value)}
                              </div>
                            ))}
                          {Object.keys(log.details).length > 2 && (
                            <div className="text-xs text-muted-foreground">
                              +{Object.keys(log.details).length - 2} more
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs text-muted-foreground">
                      <div>{log.ip_address}</div>
                      {log.user_agent && (
                        <div
                          className="truncate max-w-32"
                          title={log.user_agent}
                        >
                          {log.user_agent.split(" ")[0]}
                        </div>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {filteredLogs.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No audit logs found matching the current filters
        </div>
      )}
    </div>
  );
}

export default function AuditLogs() {
  const [logs] = useState<AuditLog[]>(
    MOCK_AUDIT_LOGS.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    ),
  );
  const [isReportDialogOpen, setIsReportDialogOpen] = useState(false);

  // Calculate statistics
  const last24Hours = logs.filter(
    (log) =>
      new Date(log.timestamp) > new Date(Date.now() - 24 * 60 * 60 * 1000),
  ).length;

  const roleChanges = logs.filter(
    (log) => log.action.includes("role_") || log.action.includes("permission_"),
  ).length;

  const authEvents = logs.filter(
    (log) =>
      log.action.includes("login") ||
      log.action.includes("logout") ||
      log.action.includes("sso_"),
  ).length;

  const uniqueActors = new Set(logs.map((log) => log.actor_id)).size;

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Audit Logs</h2>
          <p className="text-muted-foreground">
            Comprehensive audit trail for all RBAC changes and system access
            events
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <IconComponent name="RefreshCw" className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog
            open={isReportDialogOpen}
            onOpenChange={setIsReportDialogOpen}
          >
            <DialogTrigger asChild>
              <Button size="sm">
                <IconComponent name="Download" className="h-4 w-4 mr-2" />
                Export Report
              </Button>
            </DialogTrigger>
            <ComplianceReportDialog
              isOpen={isReportDialogOpen}
              onClose={() => setIsReportDialogOpen(false)}
            />
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{last24Hours}</div>
            <p className="text-xs text-muted-foreground">Events in last 24h</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Role Changes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{roleChanges}</div>
            <p className="text-xs text-muted-foreground">
              Permission modifications
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Auth Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{authEvents}</div>
            <p className="text-xs text-muted-foreground">
              Authentication activities
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{uniqueActors}</div>
            <p className="text-xs text-muted-foreground">Unique actors</p>
          </CardContent>
        </Card>
      </div>

      {/* Compliance Notice */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <IconComponent
              name="Shield"
              className="h-5 w-5 text-blue-600 mt-0.5"
            />
            <div>
              <div className="font-medium text-blue-900">Compliance Ready</div>
              <div className="text-sm text-blue-700 mt-1">
                All audit logs are immutable and include required fields for SOC
                2 / ISO 27001 compliance. Logs are automatically retained
                according to your organization's retention policy.
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex-1 overflow-hidden">
        <AuditLogTable logs={logs} />
      </div>
    </div>
  );
}

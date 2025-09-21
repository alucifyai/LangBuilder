// Role Assignments Component - Epic 2: AC1-AC9
// Implements role assignments with scope-based permissions

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import IconComponent from "@/components/common/genericIconComponent";
import {
  RoleAssignment,
  Role,
  User,
  UserGroup,
  ServiceAccount,
  Scope,
  ScopeType,
  Workspace,
  Project,
  Environment,
  CreateRoleAssignmentRequest,
} from "../../types/rbac";

// Mock data
const MOCK_USERS: User[] = [
  { id: "user-1", email: "alice@company.com", name: "Alice Johnson", is_active: true, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-25T00:00:00Z" },
  { id: "user-2", email: "bob@company.com", name: "Bob Smith", is_active: true, created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-24T00:00:00Z" },
  { id: "user-3", email: "carol@company.com", name: "Carol Davis", is_active: true, created_at: "2024-01-03T00:00:00Z", updated_at: "2024-01-23T00:00:00Z" },
];

const MOCK_USER_GROUPS: UserGroup[] = [
  { id: "group-1", name: "Data Team", description: "Data science team", member_count: 5, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-20T00:00:00Z" },
  { id: "group-2", name: "Platform", description: "Platform engineering", member_count: 3, created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-21T00:00:00Z" },
];

const MOCK_SERVICE_ACCOUNTS: ServiceAccount[] = [
  { id: "sa-1", name: "ci-bot", description: "CI/CD automation", is_active: true, token_count: 2, created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-25T00:00:00Z" },
];

const MOCK_ROLES: Role[] = [
  { id: "role-1", name: "Editor", description: "Can edit flows", permissions: [], is_system_role: true, version: 1, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z", created_by: "system" },
  { id: "role-2", name: "Viewer", description: "Read-only access", permissions: [], is_system_role: true, version: 1, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-01T00:00:00Z", created_by: "system" },
  { id: "role-3", name: "Deployer", description: "Can deploy", permissions: [], is_system_role: false, version: 1, created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-02T00:00:00Z", created_by: "user-1" },
];

const MOCK_WORKSPACES: Workspace[] = [
  { id: "ws-1", name: "Data Science", owner_id: "user-1", member_count: 12, project_count: 8, settings: {}, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-15T00:00:00Z" },
  { id: "ws-2", name: "ML Engineering", owner_id: "user-2", member_count: 6, project_count: 4, settings: {}, created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-20T00:00:00Z" },
];

const MOCK_PROJECTS: Project[] = [
  { id: "proj-1", name: "Customer Analytics", workspace_id: "ws-1", workspace: MOCK_WORKSPACES[0], owner_id: "user-1", environment_count: 3, flow_count: 12, created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-25T00:00:00Z" },
  { id: "proj-2", name: "Fraud Detection", workspace_id: "ws-1", workspace: MOCK_WORKSPACES[0], owner_id: "user-2", environment_count: 2, flow_count: 8, created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-24T00:00:00Z" },
];

const MOCK_ENVIRONMENTS: Environment[] = [
  { id: "env-1", name: "Production", project_id: "proj-1", project: MOCK_PROJECTS[0], environment_type: "production", configuration: {}, created_at: "2024-01-03T00:00:00Z", updated_at: "2024-01-24T00:00:00Z" },
  { id: "env-2", name: "Staging", project_id: "proj-1", project: MOCK_PROJECTS[0], environment_type: "staging", configuration: {}, created_at: "2024-01-03T00:00:00Z", updated_at: "2024-01-25T00:00:00Z" },
];

const MOCK_ASSIGNMENTS: RoleAssignment[] = [
  {
    id: "assign-1",
    principal_type: "user",
    principal_id: "user-1",
    principal: MOCK_USERS[0],
    role_id: "role-1",
    role: MOCK_ROLES[0],
    scope: { type: "workspace", id: "ws-1", name: "Data Science" },
    created_at: "2024-01-10T00:00:00Z",
    created_by: "admin",
  },
  {
    id: "assign-2",
    principal_type: "group",
    principal_id: "group-1",
    principal: MOCK_USER_GROUPS[0],
    role_id: "role-2",
    role: MOCK_ROLES[1],
    scope: { type: "project", id: "proj-1", name: "Customer Analytics" },
    created_at: "2024-01-11T00:00:00Z",
    created_by: "admin",
  },
  {
    id: "assign-3",
    principal_type: "user",
    principal_id: "user-2",
    principal: MOCK_USERS[1],
    role_id: "role-3",
    role: MOCK_ROLES[2],
    scope: { type: "environment", id: "env-1", name: "Production" },
    expires_at: "2025-06-30T00:00:00Z",
    created_at: "2024-01-12T00:00:00Z",
    created_by: "admin",
  },
];

interface AssignmentBuilderProps {
  assignment?: RoleAssignment;
  onSave: (assignmentData: CreateRoleAssignmentRequest) => void;
  onCancel: () => void;
}

function AssignmentBuilder({ assignment, onSave, onCancel }: AssignmentBuilderProps) {
  const [principalType, setPrincipalType] = useState<"user" | "group" | "service_account">(
    assignment?.principal_type || "user"
  );
  const [principalId, setPrincipalId] = useState(assignment?.principal_id || "");
  const [roleId, setRoleId] = useState(assignment?.role_id || "");
  const [scopeType, setScopeType] = useState<ScopeType>(assignment?.scope.type || "workspace");
  const [scopeId, setScopeId] = useState(assignment?.scope.id || "");
  const [expiresAt, setExpiresAt] = useState<{from: Date | undefined, to: Date | undefined}>({
    from: assignment?.expires_at ? new Date(assignment.expires_at) : undefined,
    to: undefined
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const getPrincipals = () => {
    switch (principalType) {
      case "user": return MOCK_USERS;
      case "group": return MOCK_USER_GROUPS;
      case "service_account": return MOCK_SERVICE_ACCOUNTS;
    }
  };

  const getScopes = () => {
    switch (scopeType) {
      case "workspace": return MOCK_WORKSPACES;
      case "project": return MOCK_PROJECTS;
      case "environment": return MOCK_ENVIRONMENTS;
      default: return [];
    }
  };

  const handleSave = () => {
    const newErrors: Record<string, string> = {};

    if (!principalId) newErrors.principal = "Please select a principal";
    if (!roleId) newErrors.role = "Please select a role";
    if (!scopeId) newErrors.scope = "Please select a scope";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    const selectedScope = getScopes().find((s: any) => s.id === scopeId);

    const assignmentData: CreateRoleAssignmentRequest = {
      principal_type: principalType,
      principal_id: principalId,
      role_id: roleId,
      scope: {
        type: scopeType,
        id: scopeId,
        name: selectedScope?.name || "",
      },
      expires_at: expiresAt?.from?.toISOString(),
    };

    onSave(assignmentData);
  };

  return (
    <div className="space-y-6">
      {/* Principal Selection */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium">Principal</h4>
        <div>
          <Label>Principal Type</Label>
          <Select value={principalType} onValueChange={(value) => {
            setPrincipalType(value as any);
            setPrincipalId("");
          }}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user">User</SelectItem>
              <SelectItem value="group">User Group</SelectItem>
              <SelectItem value="service_account">Service Account</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Select {principalType === "group" ? "Group" : principalType === "service_account" ? "Service Account" : "User"}</Label>
          <Select value={principalId} onValueChange={setPrincipalId}>
            <SelectTrigger className={errors.principal ? "border-red-500" : ""}>
              <SelectValue placeholder="Select principal..." />
            </SelectTrigger>
            <SelectContent>
              {getPrincipals().map((principal: any) => (
                <SelectItem key={principal.id} value={principal.id}>
                  {principal.name} {principal.email && `(${principal.email})`}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.principal && <p className="text-sm text-red-500 mt-1">{errors.principal}</p>}
        </div>
      </div>

      <Separator />

      {/* Role Selection */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium">Role</h4>
        <div>
          <Label>Select Role</Label>
          <Select value={roleId} onValueChange={setRoleId}>
            <SelectTrigger className={errors.role ? "border-red-500" : ""}>
              <SelectValue placeholder="Select role..." />
            </SelectTrigger>
            <SelectContent>
              {MOCK_ROLES.map((role) => (
                <SelectItem key={role.id} value={role.id}>
                  <div className="flex items-center justify-between w-full">
                    <span>{role.name}</span>
                    {role.is_system_role && (
                      <Badge variant="outline" className="ml-2 text-xs">System</Badge>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.role && <p className="text-sm text-red-500 mt-1">{errors.role}</p>}
        </div>
      </div>

      <Separator />

      {/* Scope Selection - PRD: Hierarchical scoping */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium">Scope</h4>
        <div>
          <Label>Scope Level</Label>
          <Select value={scopeType} onValueChange={(value) => {
            setScopeType(value as ScopeType);
            setScopeId("");
          }}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="workspace">Workspace</SelectItem>
              <SelectItem value="project">Project</SelectItem>
              <SelectItem value="environment">Environment</SelectItem>
              <SelectItem value="flow">Flow</SelectItem>
              <SelectItem value="component">Component</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground mt-1">
            Higher scopes grant access to all lower scopes (inheritance)
          </p>
        </div>

        <div>
          <Label>Select {scopeType}</Label>
          <Select value={scopeId} onValueChange={setScopeId}>
            <SelectTrigger className={errors.scope ? "border-red-500" : ""}>
              <SelectValue placeholder={`Select ${scopeType}...`} />
            </SelectTrigger>
            <SelectContent>
              {getScopes().map((scope: any) => (
                <SelectItem key={scope.id} value={scope.id}>
                  {scope.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.scope && <p className="text-sm text-red-500 mt-1">{errors.scope}</p>}
        </div>
      </div>

      <Separator />

      {/* Optional Expiration - PRD AC3: Time-bound grants */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium">Expiration (Optional)</h4>
        <div>
          <Label>Expires At</Label>
          <DatePickerWithRange
            date={expiresAt}
            onDateChange={setExpiresAt}
          />
          <p className="text-sm text-muted-foreground mt-1">
            Assignment will automatically expire on this date
          </p>
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave}>
          {assignment ? "Update Assignment" : "Create Assignment"}
        </Button>
      </div>
    </div>
  );
}

function AssignmentTable({ assignments, onRevoke }: { assignments: RoleAssignment[], onRevoke: (id: string) => void }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPrincipalType, setFilterPrincipalType] = useState<string>("all");
  const [filterScope, setFilterScope] = useState<string>("all");

  const filteredAssignments = useMemo(() => {
    return assignments.filter((assignment) => {
      const principalName =
        assignment.principal_type === "user" ?
          `${(assignment.principal as User).name} ${(assignment.principal as User).email}` :
        assignment.principal_type === "group" ?
          (assignment.principal as UserGroup).name :
          (assignment.principal as ServiceAccount).name;

      const matchesSearch =
        principalName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        assignment.role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        assignment.scope.name.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesPrincipalType =
        filterPrincipalType === "all" || assignment.principal_type === filterPrincipalType;

      const matchesScope =
        filterScope === "all" || assignment.scope.type === filterScope;

      return matchesSearch && matchesPrincipalType && matchesScope;
    });
  }, [assignments, searchTerm, filterPrincipalType, filterScope]);

  const getPrincipalDisplay = (assignment: RoleAssignment) => {
    switch (assignment.principal_type) {
      case "user":
        const user = assignment.principal as User;
        return (
          <div>
            <div className="font-medium">{user.name}</div>
            <div className="text-sm text-muted-foreground">{user.email}</div>
          </div>
        );
      case "group":
        const group = assignment.principal as UserGroup;
        return (
          <div>
            <div className="font-medium flex items-center">
              <IconComponent name="Users" className="h-4 w-4 mr-1" />
              {group.name}
            </div>
            <div className="text-sm text-muted-foreground">
              {group.member_count} members
            </div>
          </div>
        );
      case "service_account":
        const sa = assignment.principal as ServiceAccount;
        return (
          <div>
            <div className="font-medium flex items-center">
              <IconComponent name="Bot" className="h-4 w-4 mr-1" />
              {sa.name}
            </div>
            <div className="text-sm text-muted-foreground">
              Service Account
            </div>
          </div>
        );
    }
  };

  const getScopeIcon = (type: string) => {
    switch (type) {
      case "workspace": return "Building";
      case "project": return "Folder";
      case "environment": return "Server";
      case "flow": return "GitBranch";
      case "component": return "Box";
      default: return "Circle";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Input
          placeholder="Search assignments..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filterPrincipalType} onValueChange={setFilterPrincipalType}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="user">Users</SelectItem>
            <SelectItem value="group">Groups</SelectItem>
            <SelectItem value="service_account">Service Accounts</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filterScope} onValueChange={setFilterScope}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by scope" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Scopes</SelectItem>
            <SelectItem value="workspace">Workspace</SelectItem>
            <SelectItem value="project">Project</SelectItem>
            <SelectItem value="environment">Environment</SelectItem>
            <SelectItem value="flow">Flow</SelectItem>
            <SelectItem value="component">Component</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Principal</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-20">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAssignments.map((assignment) => (
                <TableRow key={assignment.id}>
                  <TableCell>{getPrincipalDisplay(assignment)}</TableCell>
                  <TableCell>
                    <Badge variant={assignment.role.is_system_role ? "secondary" : "default"}>
                      {assignment.role.name}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <IconComponent
                        name={getScopeIcon(assignment.scope.type)}
                        className="h-4 w-4 text-muted-foreground"
                      />
                      <div>
                        <div className="font-medium">{assignment.scope.name}</div>
                        <div className="text-xs text-muted-foreground capitalize">
                          {assignment.scope.type}
                        </div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {assignment.expires_at ? (
                      new Date(assignment.expires_at) > new Date() ? (
                        <Badge variant="outline" className="text-yellow-700">
                          Expires {new Date(assignment.expires_at).toLocaleDateString()}
                        </Badge>
                      ) : (
                        <Badge variant="destructive">Expired</Badge>
                      )
                    ) : (
                      <Badge variant="outline" className="text-green-700">Active</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {new Date(assignment.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onRevoke(assignment.id)}
                      title="Revoke Assignment"
                    >
                      <IconComponent name="X" className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default function RoleAssignments() {
  const [assignments, setAssignments] = useState<RoleAssignment[]>(MOCK_ASSIGNMENTS);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const handleCreateAssignment = (assignmentData: CreateRoleAssignmentRequest) => {
    const principal =
      assignmentData.principal_type === "user" ?
        MOCK_USERS.find(u => u.id === assignmentData.principal_id) :
      assignmentData.principal_type === "group" ?
        MOCK_USER_GROUPS.find(g => g.id === assignmentData.principal_id) :
        MOCK_SERVICE_ACCOUNTS.find(s => s.id === assignmentData.principal_id);

    const role = MOCK_ROLES.find(r => r.id === assignmentData.role_id);

    const newAssignment: RoleAssignment = {
      id: `assign-${Date.now()}`,
      principal_type: assignmentData.principal_type,
      principal_id: assignmentData.principal_id,
      principal: principal!,
      role_id: assignmentData.role_id,
      role: role!,
      scope: assignmentData.scope,
      expires_at: assignmentData.expires_at,
      created_at: new Date().toISOString(),
      created_by: "current-user",
    };

    setAssignments([...assignments, newAssignment]);
    setIsCreateDialogOpen(false);
  };

  const handleRevokeAssignment = (assignmentId: string) => {
    // PRD AC4: Revoke assignment
    if (confirm("Are you sure you want to revoke this role assignment?")) {
      setAssignments(assignments.filter(a => a.id !== assignmentId));
    }
  };

  // Calculate stats
  const userAssignments = assignments.filter(a => a.principal_type === "user").length;
  const groupAssignments = assignments.filter(a => a.principal_type === "group").length;
  const serviceAccountAssignments = assignments.filter(a => a.principal_type === "service_account").length;
  const expiringAssignments = assignments.filter(a => a.expires_at).length;

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Role Assignments</h2>
          <p className="text-muted-foreground">
            Assign roles to users, groups, and service accounts with scope-based permissions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <IconComponent name="RefreshCw" className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <IconComponent name="Plus" className="h-4 w-4 mr-2" />
                Create Assignment
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Role Assignment</DialogTitle>
                <DialogDescription>
                  Assign a role to a user, group, or service account within a specific scope.
                </DialogDescription>
              </DialogHeader>
              <AssignmentBuilder
                onSave={handleCreateAssignment}
                onCancel={() => setIsCreateDialogOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">User Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{userAssignments}</div>
            <p className="text-xs text-muted-foreground">Direct user roles</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Group Assignments</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{groupAssignments}</div>
            <p className="text-xs text-muted-foreground">Group-based roles</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Service Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceAccountAssignments}</div>
            <p className="text-xs text-muted-foreground">Automated access</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Time-bound</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{expiringAssignments}</div>
            <p className="text-xs text-muted-foreground">With expiration</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 overflow-hidden">
        <AssignmentTable
          assignments={assignments}
          onRevoke={handleRevokeAssignment}
        />
      </div>
    </div>
  );
}
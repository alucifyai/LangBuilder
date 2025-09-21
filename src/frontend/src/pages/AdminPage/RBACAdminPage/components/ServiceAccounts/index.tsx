// Service Accounts Component - Epic 2: Service account management
// Implements service accounts with scoped API tokens

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
import { Checkbox } from "@/components/ui/checkbox";
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
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  CreateServiceAccountRequest,
  PermissionAction,
  Scope,
  ServiceAccount,
} from "../../types/rbac";

// Mock data
const MOCK_SERVICE_ACCOUNTS: ServiceAccount[] = [
  {
    id: "sa-1",
    name: "ci-bot",
    description: "CI/CD automation bot",
    is_active: true,
    token_count: 2,
    last_used: "2024-01-25T14:30:00Z",
    created_at: "2024-01-05T00:00:00Z",
    updated_at: "2024-01-25T14:30:00Z",
  },
  {
    id: "sa-2",
    name: "monitoring-service",
    description: "System monitoring and alerting",
    is_active: true,
    token_count: 1,
    last_used: "2024-01-26T09:15:00Z",
    created_at: "2024-01-10T00:00:00Z",
    updated_at: "2024-01-26T09:15:00Z",
  },
  {
    id: "sa-3",
    name: "data-sync",
    description: "Data synchronization service",
    is_active: false,
    token_count: 0,
    created_at: "2024-01-15T00:00:00Z",
    updated_at: "2024-01-20T00:00:00Z",
  },
  {
    id: "sa-4",
    name: "backup-service",
    description: "Automated backup and recovery",
    is_active: true,
    token_count: 1,
    last_used: "2024-01-24T02:00:00Z",
    created_at: "2024-01-12T00:00:00Z",
    updated_at: "2024-01-24T02:00:00Z",
  },
];

// Mock tokens for service accounts
const MOCK_TOKENS = [
  {
    id: "token-1",
    service_account_id: "sa-1",
    name: "Production Deploy",
    scope: { type: "environment", id: "env-prod", name: "Production" },
    permissions: ["deploy_environment", "read"],
    expires_at: "2024-06-01T00:00:00Z",
    created_at: "2024-01-05T00:00:00Z",
    last_used: "2024-01-25T14:30:00Z",
  },
  {
    id: "token-2",
    service_account_id: "sa-1",
    name: "Read Access",
    scope: { type: "project", id: "proj-1", name: "Customer Analytics" },
    permissions: ["read"],
    created_at: "2024-01-10T00:00:00Z",
    last_used: "2024-01-24T10:00:00Z",
  },
  {
    id: "token-3",
    service_account_id: "sa-2",
    name: "Monitoring",
    scope: { type: "workspace", id: "ws-1", name: "Data Science" },
    permissions: ["read"],
    created_at: "2024-01-10T00:00:00Z",
    last_used: "2024-01-26T09:15:00Z",
  },
  {
    id: "token-4",
    service_account_id: "sa-4",
    name: "Backup Token",
    scope: { type: "workspace", id: "ws-1", name: "Data Science" },
    permissions: ["read", "export_flow"],
    created_at: "2024-01-12T00:00:00Z",
    last_used: "2024-01-24T02:00:00Z",
  },
];

interface ServiceAccountBuilderProps {
  serviceAccount?: ServiceAccount;
  onSave: (data: CreateServiceAccountRequest) => void;
  onCancel: () => void;
}

function ServiceAccountBuilder({
  serviceAccount,
  onSave,
  onCancel,
}: ServiceAccountBuilderProps) {
  const [name, setName] = useState(serviceAccount?.name || "");
  const [description, setDescription] = useState(
    serviceAccount?.description || "",
  );
  const [isActive, setIsActive] = useState(serviceAccount?.is_active ?? true);

  // Scope and permissions for initial token
  const [scopeType, setScopeType] = useState<
    "workspace" | "project" | "environment"
  >("workspace");
  const [scopeId, setScopeId] = useState("");
  const [selectedPermissions, setSelectedPermissions] = useState<
    Set<PermissionAction>
  >(new Set(["read"]));

  const [nameError, setNameError] = useState("");

  const availablePermissions: PermissionAction[] = [
    "read",
    "create",
    "update",
    "delete",
    "export_flow",
    "deploy_environment",
    "invite_users",
    "modify_component_settings",
    "manage_tokens",
  ];

  const mockScopes = {
    workspace: [
      { id: "ws-1", name: "Data Science" },
      { id: "ws-2", name: "ML Engineering" },
    ],
    project: [
      { id: "proj-1", name: "Customer Analytics" },
      { id: "proj-2", name: "Fraud Detection" },
    ],
    environment: [
      { id: "env-1", name: "Production" },
      { id: "env-2", name: "Staging" },
    ],
  };

  const handlePermissionToggle = (permission: PermissionAction) => {
    const newSelected = new Set(selectedPermissions);
    if (newSelected.has(permission)) {
      newSelected.delete(permission);
    } else {
      newSelected.add(permission);
    }
    setSelectedPermissions(newSelected);
  };

  const handleSave = () => {
    if (!name.trim()) {
      setNameError("Service account name is required");
      return;
    }

    if (!scopeId) {
      setNameError("Please select a scope for the initial token");
      return;
    }

    setNameError("");

    const selectedScope = mockScopes[scopeType].find((s) => s.id === scopeId);

    const data: CreateServiceAccountRequest = {
      name: name.trim(),
      description: description.trim() || undefined,
      scope: {
        type: scopeType,
        id: scopeId,
        name: selectedScope?.name || "",
      },
      permissions: Array.from(selectedPermissions),
    };

    onSave(data);
  };

  const getPermissionIcon = (permission: PermissionAction) => {
    switch (permission) {
      case "read":
        return "Eye";
      case "create":
        return "Plus";
      case "update":
        return "Edit";
      case "delete":
        return "Trash2";
      case "export_flow":
        return "Download";
      case "deploy_environment":
        return "Rocket";
      case "invite_users":
        return "UserPlus";
      case "modify_component_settings":
        return "Settings";
      case "manage_tokens":
        return "Key";
      default:
        return "Shield";
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        <div>
          <Label htmlFor="sa-name">Service Account Name *</Label>
          <Input
            id="sa-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., ci-bot, monitoring-service"
            className={nameError ? "border-red-500" : ""}
          />
          {nameError && (
            <p className="text-sm text-red-500 mt-1">{nameError}</p>
          )}
        </div>
        <div>
          <Label htmlFor="sa-description">Description</Label>
          <Textarea
            id="sa-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter service account description"
            rows={3}
          />
        </div>
        <div className="flex items-center justify-between p-4 border rounded-lg">
          <div>
            <Label className="text-sm font-medium">Active</Label>
            <p className="text-sm text-muted-foreground">
              Service account can authenticate and use tokens
            </p>
          </div>
          <Switch checked={isActive} onCheckedChange={setIsActive} />
        </div>
      </div>

      <Separator />

      {/* Initial Token Configuration - PRD: Scoped permissions */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium">Initial API Token</h4>
        <p className="text-sm text-muted-foreground">
          Configure the scope and permissions for the first API token.
          Additional tokens can be created later.
        </p>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label>Scope Type</Label>
            <Select
              value={scopeType}
              onValueChange={(value: any) => {
                setScopeType(value);
                setScopeId("");
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="workspace">Workspace</SelectItem>
                <SelectItem value="project">Project</SelectItem>
                <SelectItem value="environment">Environment</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Select {scopeType}</Label>
            <Select value={scopeId} onValueChange={setScopeId}>
              <SelectTrigger>
                <SelectValue placeholder={`Select ${scopeType}...`} />
              </SelectTrigger>
              <SelectContent>
                {mockScopes[scopeType].map((scope) => (
                  <SelectItem key={scope.id} value={scope.id}>
                    {scope.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <Label className="text-base font-medium">Permissions</Label>
          <p className="text-sm text-muted-foreground mb-3">
            Select permissions for this service account within the chosen scope
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {availablePermissions.map((permission) => (
              <div
                key={permission}
                className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-muted/50"
              >
                <Checkbox
                  id={permission}
                  checked={selectedPermissions.has(permission)}
                  onCheckedChange={() => handlePermissionToggle(permission)}
                />
                <div className="flex-1 min-w-0">
                  <Label
                    htmlFor={permission}
                    className="text-sm font-medium cursor-pointer flex items-center"
                  >
                    <IconComponent
                      name={getPermissionIcon(permission)}
                      className="h-4 w-4 mr-2"
                    />
                    {permission}
                  </Label>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          disabled={!name.trim() || !scopeId || selectedPermissions.size === 0}
        >
          {serviceAccount ? "Update Service Account" : "Create Service Account"}
        </Button>
      </div>
    </div>
  );
}

interface TokensDialogProps {
  serviceAccount: ServiceAccount;
  isOpen: boolean;
  onClose: () => void;
}

function TokensDialog({ serviceAccount, isOpen, onClose }: TokensDialogProps) {
  const [isCreateTokenOpen, setIsCreateTokenOpen] = useState(false);

  const serviceAccountTokens = MOCK_TOKENS.filter(
    (t) => t.service_account_id === serviceAccount.id,
  );

  const handleCreateToken = () => {
    setIsCreateTokenOpen(true);
  };

  const handleRevokeToken = (tokenId: string) => {
    if (
      confirm(
        "Are you sure you want to revoke this token? This action cannot be undone.",
      )
    ) {
      alert(`Token ${tokenId} revoked`);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>API Tokens for {serviceAccount.name}</DialogTitle>
          <DialogDescription>
            Manage API tokens with scoped permissions for this service account
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h4 className="font-medium">Active Tokens</h4>
              <p className="text-sm text-muted-foreground">
                {serviceAccountTokens.length} tokens configured
              </p>
            </div>
            <Button onClick={handleCreateToken} size="sm">
              <IconComponent name="Plus" className="h-4 w-4 mr-2" />
              Create Token
            </Button>
          </div>

          <div className="space-y-3">
            {serviceAccountTokens.map((token) => (
              <Card key={token.id}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <h5 className="font-medium">{token.name}</h5>
                        <Badge variant="outline" className="text-xs">
                          {token.scope.type}: {token.scope.name}
                        </Badge>
                      </div>
                      <div className="flex items-center space-x-4 mt-2 text-sm text-muted-foreground">
                        <span>Permissions: {token.permissions.join(", ")}</span>
                        {token.last_used && (
                          <span>
                            Last used:{" "}
                            {new Date(token.last_used).toLocaleDateString()}
                          </span>
                        )}
                        {token.expires_at && (
                          <span>
                            Expires:{" "}
                            {new Date(token.expires_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        <IconComponent name="Copy" className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRevokeToken(token.id)}
                      >
                        <IconComponent name="Trash2" className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {serviceAccountTokens.length === 0 && (
              <div className="text-center py-8 text-muted-foreground">
                No tokens created yet
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ServiceAccountTable({
  serviceAccounts,
  onEdit,
  onDelete,
  onToggleActive,
  onViewTokens,
}: {
  serviceAccounts: ServiceAccount[];
  onEdit: (sa: ServiceAccount) => void;
  onDelete: (saId: string) => void;
  onToggleActive: (saId: string) => void;
  onViewTokens: (sa: ServiceAccount) => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterActive, setFilterActive] = useState<string>("all");

  const filteredServiceAccounts = useMemo(() => {
    return serviceAccounts.filter((sa) => {
      const matchesSearch =
        sa.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (sa.description?.toLowerCase().includes(searchTerm.toLowerCase()) ??
          false);

      const matchesActive =
        filterActive === "all" ||
        (filterActive === "active" && sa.is_active) ||
        (filterActive === "inactive" && !sa.is_active);

      return matchesSearch && matchesActive;
    });
  }, [serviceAccounts, searchTerm, filterActive]);

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Input
          placeholder="Search service accounts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filterActive} onValueChange={setFilterActive}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Service Account</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Tokens</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredServiceAccounts.map((sa) => (
                <TableRow key={sa.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium flex items-center">
                        <IconComponent name="Bot" className="h-4 w-4 mr-2" />
                        {sa.name}
                      </div>
                      {sa.description && (
                        <div className="text-sm text-muted-foreground">
                          {sa.description}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={sa.is_active ? "outline" : "secondary"}>
                      {sa.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewTokens(sa)}
                      className="p-0 h-auto font-normal"
                    >
                      {sa.token_count} tokens
                    </Button>
                  </TableCell>
                  <TableCell>
                    {sa.last_used ? (
                      <span className="text-sm">
                        {new Date(sa.last_used).toLocaleDateString()}
                      </span>
                    ) : (
                      <span className="text-sm text-muted-foreground">
                        Never
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    {new Date(sa.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onToggleActive(sa.id)}
                        title={sa.is_active ? "Deactivate" : "Activate"}
                      >
                        <IconComponent
                          name={sa.is_active ? "Pause" : "Play"}
                          className="h-4 w-4"
                        />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(sa)}
                        title="Edit"
                      >
                        <IconComponent name="Edit" className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(sa.id)}
                        title="Delete"
                      >
                        <IconComponent name="Trash2" className="h-4 w-4" />
                      </Button>
                    </div>
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

export default function ServiceAccounts() {
  const [serviceAccounts, setServiceAccounts] = useState<ServiceAccount[]>(
    MOCK_SERVICE_ACCOUNTS,
  );
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingServiceAccount, setEditingServiceAccount] =
    useState<ServiceAccount | null>(null);
  const [viewTokensServiceAccount, setViewTokensServiceAccount] =
    useState<ServiceAccount | null>(null);

  const handleCreateServiceAccount = (data: CreateServiceAccountRequest) => {
    const newServiceAccount: ServiceAccount = {
      id: `sa-${Date.now()}`,
      name: data.name,
      description: data.description,
      is_active: true,
      token_count: 1, // Initial token
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setServiceAccounts([...serviceAccounts, newServiceAccount]);
    setIsCreateDialogOpen(false);

    // Show success message with token creation info
    alert(
      `Service account "${data.name}" created successfully with initial token scoped to ${data.scope.type}: ${data.scope.name}`,
    );
  };

  const handleUpdateServiceAccount = (data: CreateServiceAccountRequest) => {
    if (!editingServiceAccount) return;

    const updatedServiceAccount: ServiceAccount = {
      ...editingServiceAccount,
      name: data.name,
      description: data.description,
      updated_at: new Date().toISOString(),
    };

    setServiceAccounts(
      serviceAccounts.map((sa) =>
        sa.id === editingServiceAccount.id ? updatedServiceAccount : sa,
      ),
    );
    setEditingServiceAccount(null);
  };

  const handleDeleteServiceAccount = (saId: string) => {
    if (
      confirm(
        "Are you sure you want to delete this service account? All associated tokens will be revoked.",
      )
    ) {
      setServiceAccounts(serviceAccounts.filter((sa) => sa.id !== saId));
    }
  };

  const handleToggleActive = (saId: string) => {
    setServiceAccounts(
      serviceAccounts.map((sa) =>
        sa.id === saId
          ? {
              ...sa,
              is_active: !sa.is_active,
              updated_at: new Date().toISOString(),
            }
          : sa,
      ),
    );
  };

  // Calculate statistics
  const activeAccounts = serviceAccounts.filter((sa) => sa.is_active).length;
  const totalTokens = serviceAccounts.reduce(
    (sum, sa) => sum + sa.token_count,
    0,
  );
  const recentlyUsed = serviceAccounts.filter(
    (sa) =>
      sa.last_used &&
      new Date(sa.last_used) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
  ).length;

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Service Account Management</h2>
          <p className="text-muted-foreground">
            Create and manage service accounts with scoped API tokens for
            automated systems
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <IconComponent name="RefreshCw" className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog
            open={isCreateDialogOpen}
            onOpenChange={setIsCreateDialogOpen}
          >
            <DialogTrigger asChild>
              <Button size="sm">
                <IconComponent name="Plus" className="h-4 w-4 mr-2" />
                Create Service Account
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Service Account</DialogTitle>
                <DialogDescription>
                  Create a service account for automated systems with scoped
                  permissions.
                </DialogDescription>
              </DialogHeader>
              <ServiceAccountBuilder
                onSave={handleCreateServiceAccount}
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
            <CardTitle className="text-sm font-medium">
              Total Accounts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{serviceAccounts.length}</div>
            <p className="text-xs text-muted-foreground">Service accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeAccounts}</div>
            <p className="text-xs text-muted-foreground">Active accounts</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTokens}</div>
            <p className="text-xs text-muted-foreground">API tokens issued</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Recently Used</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentlyUsed}</div>
            <p className="text-xs text-muted-foreground">Used in last 7 days</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 overflow-hidden">
        <ServiceAccountTable
          serviceAccounts={serviceAccounts}
          onEdit={setEditingServiceAccount}
          onDelete={handleDeleteServiceAccount}
          onToggleActive={handleToggleActive}
          onViewTokens={setViewTokensServiceAccount}
        />
      </div>

      {/* Edit Service Account Dialog */}
      <Dialog
        open={!!editingServiceAccount}
        onOpenChange={() => setEditingServiceAccount(null)}
      >
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Edit Service Account: {editingServiceAccount?.name}
            </DialogTitle>
            <DialogDescription>
              Modify service account settings.
            </DialogDescription>
          </DialogHeader>
          {editingServiceAccount && (
            <ServiceAccountBuilder
              serviceAccount={editingServiceAccount}
              onSave={handleUpdateServiceAccount}
              onCancel={() => setEditingServiceAccount(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* View Tokens Dialog */}
      {viewTokensServiceAccount && (
        <TokensDialog
          serviceAccount={viewTokensServiceAccount}
          isOpen={!!viewTokensServiceAccount}
          onClose={() => setViewTokensServiceAccount(null)}
        />
      )}
    </div>
  );
}

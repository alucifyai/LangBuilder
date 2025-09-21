// Permission Management Component - Epic 1: Story 1.1 (AC1-AC8)
// Implements permission catalog with CRUD and extended actions

import { useEffect, useMemo, useState } from "react";
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
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useGetPermissions } from "@/controllers/API/queries/rbac";
import useAuthStore from "@/stores/authStore";
import AuthenticationModal from "../../../RBAC/components/AuthenticationModal";
import PermissionEditModal from "../../../RBAC/components/PermissionEditModal";
import ConfirmDeleteModal from "../../../RBAC/components/ConfirmDeleteModal";
import {
  CRUDAction,
  ExtendedAction,
  Permission,
  PermissionAction,
} from "../../types/rbac";

// Mock permission catalog data (PRD AC1: CRUD + Extended actions)
const MOCK_PERMISSIONS: Permission[] = [
  // CRUD actions
  {
    id: "perm-1",
    action: "create",
    resource_type: "flow",
    description: "Create new flows",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-2",
    action: "read",
    resource_type: "flow",
    description: "View and read flows",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-3",
    action: "update",
    resource_type: "flow",
    description: "Modify existing flows",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-4",
    action: "delete",
    resource_type: "flow",
    description: "Delete flows",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  // Extended actions (PRD AC1)
  {
    id: "perm-5",
    action: "export_flow",
    resource_type: "flow",
    description: "Export flows to external formats",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-6",
    action: "deploy_environment",
    resource_type: "environment",
    description: "Deploy to environments",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-7",
    action: "invite_users",
    resource_type: "workspace",
    description: "Invite users to workspace",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-8",
    action: "modify_component_settings",
    resource_type: "component",
    description: "Modify component configuration",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "perm-9",
    action: "manage_tokens",
    resource_type: "project",
    description: "Create and manage API tokens",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

const CRUD_ACTIONS: CRUDAction[] = ["create", "read", "update", "delete"];
const EXTENDED_ACTIONS: ExtendedAction[] = [
  "export_flow",
  "deploy_environment",
  "invite_users",
  "modify_component_settings",
  "manage_tokens",
];

interface PermissionCatalogProps {
  permissions?: Permission[];
  onPermissionSelect?: (permission: Permission) => void;
}

function PermissionCatalog({
  permissions = MOCK_PERMISSIONS,
  onPermissionSelect,
}: PermissionCatalogProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterAction, setFilterAction] = useState<PermissionAction | "all">(
    "all",
  );
  const [filterResourceType, setFilterResourceType] = useState<string>("all");

  const filteredPermissions = useMemo(() => {
    return permissions.filter((permission) => {
      const matchesSearch =
        permission.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        permission.resource_type
          .toLowerCase()
          .includes(searchTerm.toLowerCase()) ||
        permission.description.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesAction =
        filterAction === "all" || permission.action === filterAction;

      const matchesResourceType =
        filterResourceType === "all" ||
        permission.resource_type === filterResourceType;

      return matchesSearch && matchesAction && matchesResourceType;
    });
  }, [permissions, searchTerm, filterAction, filterResourceType]);

  const resourceTypes = useMemo(() => {
    const types = new Set(permissions.map((p) => p.resource_type));
    return Array.from(types);
  }, [permissions]);

  const getActionBadgeVariant = (action: PermissionAction) => {
    if (CRUD_ACTIONS.includes(action as CRUDAction)) {
      return "default";
    }
    return "secondary";
  };

  const getActionIcon = (action: PermissionAction) => {
    switch (action) {
      case "create":
        return "Plus";
      case "read":
        return "Eye";
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Permission Catalog</h3>
          <p className="text-sm text-muted-foreground">
            CRUD and extended actions available for role building
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          {filteredPermissions.length} permissions
        </Badge>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search permissions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>
        <Select
          value={filterAction}
          onValueChange={(value) =>
            setFilterAction(value as PermissionAction | "all")
          }
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by action" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Actions</SelectItem>
            <SelectItem value="create">Create</SelectItem>
            <SelectItem value="read">Read</SelectItem>
            <SelectItem value="update">Update</SelectItem>
            <SelectItem value="delete">Delete</SelectItem>
            <SelectItem value="export_flow">Export Flow</SelectItem>
            <SelectItem value="deploy_environment">
              Deploy Environment
            </SelectItem>
            <SelectItem value="invite_users">Invite Users</SelectItem>
            <SelectItem value="modify_component_settings">
              Modify Component
            </SelectItem>
            <SelectItem value="manage_tokens">Manage Tokens</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={filterResourceType}
          onValueChange={setFilterResourceType}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by resource" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Resources</SelectItem>
            {resourceTypes.map((type) => (
              <SelectItem key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Permission Table */}
      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Action</TableHead>
                <TableHead>Resource Type</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="w-12"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredPermissions.map((permission) => (
                <TableRow
                  key={permission.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => onPermissionSelect?.(permission)}
                >
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <IconComponent
                        name={getActionIcon(permission.action)}
                        className="h-4 w-4"
                      />
                      <code className="text-sm bg-muted px-2 py-1 rounded">
                        {permission.action}
                      </code>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{permission.resource_type}</Badge>
                  </TableCell>
                  <TableCell>{permission.description}</TableCell>
                  <TableCell>
                    <Badge variant={getActionBadgeVariant(permission.action)}>
                      {CRUD_ACTIONS.includes(permission.action as CRUDAction)
                        ? "CRUD"
                        : "Extended"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <IconComponent
                      name="ChevronRight"
                      className="h-4 w-4 text-muted-foreground"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">CRUD Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {
                permissions.filter((p) =>
                  CRUD_ACTIONS.includes(p.action as CRUDAction),
                ).length
              }
            </div>
            <p className="text-xs text-muted-foreground">Basic operations</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Extended Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {
                permissions.filter((p) =>
                  EXTENDED_ACTIONS.includes(p.action as ExtendedAction),
                ).length
              }
            </div>
            <p className="text-xs text-muted-foreground">
              Specialized operations
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Resource Types
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{resourceTypes.length}</div>
            <p className="text-xs text-muted-foreground">Different resources</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Total Permissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{permissions.length}</div>
            <p className="text-xs text-muted-foreground">
              Available permissions
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function PermissionManagement() {
  const [selectedPermission, setSelectedPermission] =
    useState<Permission | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [pendingAction, setPendingAction] = useState<string | null>(null);

  // Modal states
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editModalMode, setEditModalMode] = useState<"edit" | "create">("edit");

  // API integration for fetching permissions
  const getPermissions = useGetPermissions();
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);

  // Authentication state management with multiple sources for reliability
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const userData = useAuthStore((state) => state.userData);

  // More robust authentication check
  const isFullyAuthenticated = Boolean(isAuthenticated && accessToken);

  // Helper function to handle authentication-protected actions
  const requireAuth = (action: string, callback: () => void) => {
    console.log("🔐 Authentication check:", {
      action,
      isAuthenticated,
      accessToken: !!accessToken,
      isFullyAuthenticated,
      userData: !!userData
    });

    if (!isFullyAuthenticated) {
      console.log("❌ Not authenticated, showing modal");
      setPendingAction(action);
      setShowAuthModal(true);
    } else {
      console.log("✅ Authenticated, executing action:", action);
      callback();
    }
  };

  // Handle authentication success
  const handleAuthSuccess = () => {
    console.log("🎉 Authentication successful, executing pending action:", pendingAction);

    // Force a small delay to ensure state updates
    setTimeout(() => {
      if (pendingAction === "add-permission") {
        handleAddPermission();
      } else if (pendingAction === "edit-permission") {
        handleEditPermission();
      } else if (pendingAction === "delete-permission") {
        handleDeletePermission();
      } else if (pendingAction === "refresh") {
        handleRefreshPermissions();
      }
      setPendingAction(null);
    }, 100);
  };

  // Action handlers
  const handleAddPermission = () => {
    console.log("🔧 Add Permission clicked - opening modal");
    setEditModalMode("create");
    setSelectedPermission(null);
    setShowEditModal(true);
  };

  const handleEditPermission = () => {
    console.log("🔧 Edit Permission clicked for:", selectedPermission);
    if (selectedPermission) {
      setEditModalMode("edit");
      setShowEditModal(true);
    }
  };

  const handleDeletePermission = () => {
    console.log("🔧 Delete Permission clicked for:", selectedPermission);
    if (selectedPermission) {
      setShowDeleteModal(true);
    }
  };

  // Modal handlers
  const handleSavePermission = (permission: Permission) => {
    console.log("💾 Saving permission:", permission);

    if (editModalMode === "create") {
      // Add new permission
      setPermissions(prev => [permission, ...prev]);
      console.log("✅ New permission added:", permission);
    } else {
      // Update existing permission
      setPermissions(prev =>
        prev.map(p => p.id === permission.id ? permission : p)
      );
      setSelectedPermission(permission);
      console.log("✅ Permission updated:", permission);
    }
  };

  const handleConfirmDelete = () => {
    console.log("🗑️ Confirming delete for:", selectedPermission);
    if (selectedPermission) {
      setPermissions(prev => prev.filter(p => p.id !== selectedPermission.id));
      setSelectedPermission(null);
      console.log("✅ Permission deleted:", selectedPermission.id);
    }
  };

  const handleRefreshPermissions = () => {
    setLoading(true);
    getPermissions.mutate(
      { limit: 100 },
      {
        onSuccess: (data) => {
          setPermissions(data || []);
          setLoading(false);
        },
        onError: (error) => {
          console.error("Failed to refresh permissions:", error);
          setLoading(false);
        },
      },
    );
  };

  // Fetch permissions on component mount
  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        setLoading(true);
        getPermissions.mutate(
          { limit: 100 },
          {
            onSuccess: (data) => {
              setPermissions(data || []);
              setLoading(false);
            },
            onError: (error) => {
              console.error("Failed to fetch permissions:", error);
              // Fallback to mock data if API fails
              setPermissions(MOCK_PERMISSIONS);
              setLoading(false);
            },
          },
        );
      } catch (error) {
        console.error("Permission fetch error:", error);
        setPermissions(MOCK_PERMISSIONS);
        setLoading(false);
      }
    };

    fetchPermissions();
  }, []);

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Permission Management</h2>
          <p className="text-muted-foreground">
            Manage the permission catalog with CRUD and extended actions
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {/* Authentication Status Indicator */}
          <Badge variant={isFullyAuthenticated ? "default" : "destructive"} className="text-xs">
            <IconComponent
              name={isFullyAuthenticated ? "CheckCircle" : "XCircle"}
              className="h-3 w-3 mr-1"
            />
            {isFullyAuthenticated ? "Authenticated" : "Not Authenticated"}
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={() => requireAuth("refresh", handleRefreshPermissions)}
            disabled={loading}
          >
            <IconComponent
              name={loading ? "Loader2" : "RefreshCw"}
              className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => requireAuth("add-permission", handleAddPermission)}
          >
            <IconComponent name="Plus" className="h-4 w-4 mr-2" />
            Add Permission
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <IconComponent
              name="Loader2"
              className="h-6 w-6 animate-spin mr-2"
            />
            Loading permissions...
          </div>
        ) : (
          <PermissionCatalog
            permissions={permissions}
            onPermissionSelect={setSelectedPermission}
          />
        )}
      </div>

      {/* Permission Details Panel */}
      {selectedPermission && (
        <Card className="border-t">
          <CardHeader>
            <CardTitle className="text-lg flex items-center space-x-2">
              <IconComponent
                name={getActionIcon(selectedPermission.action)}
                className="h-5 w-5"
              />
              <span>Permission Details</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Action</label>
                <div className="mt-1">
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    {selectedPermission.action}
                  </code>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Resource Type</label>
                <div className="mt-1">
                  <Badge variant="outline">
                    {selectedPermission.resource_type}
                  </Badge>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <p className="mt-1 text-sm text-muted-foreground">
                  {selectedPermission.description}
                </p>
              </div>
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    requireAuth("edit-permission", handleEditPermission)
                  }
                >
                  <IconComponent name="Edit" className="h-4 w-4 mr-2" />
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() =>
                    requireAuth("delete-permission", handleDeletePermission)
                  }
                >
                  <IconComponent name="Trash2" className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Authentication Modal */}
      <AuthenticationModal
        open={showAuthModal}
        onOpenChange={setShowAuthModal}
        onSuccess={handleAuthSuccess}
      />

      {/* Permission Edit/Create Modal */}
      <PermissionEditModal
        open={showEditModal}
        onOpenChange={setShowEditModal}
        permission={selectedPermission}
        onSave={handleSavePermission}
        mode={editModalMode}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmDeleteModal
        open={showDeleteModal}
        onOpenChange={setShowDeleteModal}
        permission={selectedPermission}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}

function getActionIcon(action: PermissionAction) {
  switch (action) {
    case "create":
      return "Plus";
    case "read":
      return "Eye";
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
}

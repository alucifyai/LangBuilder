import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import IconComponent from "@/components/common/genericIconComponent";
import ShadTooltip from "@/components/common/shadTooltipComponent";
import PaginatorComponent from "@/components/common/paginatorComponent";
import LoadingComponent from "@/components/common/loadingComponent";
import useAlertStore from "@/stores/alertStore";
import {
  useGetWorkspaces,
  useGetRoles,
  useCreateRole,
  useUpdateRole,
  useDeleteRole,
  type Workspace,
  type Role,
} from "@/controllers/API/queries/rbac";
import RoleForm from "./RoleForm";
import RoleDetails from "./RoleDetails";

export default function RoleManagement() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: getWorkspaces } = useGetWorkspaces();
  const { mutate: getRoles, isPending: isLoadingRoles } = useGetRoles();
  const { mutate: createRole, isPending: isCreating } = useCreateRole();
  const { mutate: updateRole, isPending: isUpdating } = useUpdateRole();
  const { mutate: deleteRole, isPending: isDeleting } = useDeleteRole();

  useEffect(() => {
    loadWorkspaces();
  }, []);

  useEffect(() => {
    fetchRoles();
  }, [pageIndex, pageSize, searchTerm, selectedWorkspace]);

  const loadWorkspaces = () => {
    getWorkspaces(
      { limit: 100 },
      {
        onSuccess: (data) => {
          setWorkspaces(data.workspaces);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load workspaces",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const fetchRoles = () => {
    getRoles(
      {
        skip: pageSize * (pageIndex - 1),
        limit: pageSize,
        search: searchTerm || undefined,
        workspace_id: selectedWorkspace || undefined,
        include_system_roles: true,
      },
      {
        onSuccess: (data) => {
          setRoles(data.roles);
          setTotalCount(data.total_count);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load roles",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const handleCreateRole = (data: {
    name: string;
    description?: string;
    permissions: string[];
    workspace_id: string;
  }) => {
    createRole(data, {
      onSuccess: () => {
        setSuccessData({ title: "Role created successfully" });
        setIsFormOpen(false);
        fetchRoles();
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to create role",
          list: [error?.message || "Unknown error occurred"],
        });
      },
    });
  };

  const handleUpdateRole = (
    id: string,
    data: {
      name?: string;
      description?: string;
      permissions?: string[];
      is_active?: boolean;
    }
  ) => {
    updateRole(
      { role_id: id, ...data },
      {
        onSuccess: () => {
          setSuccessData({ title: "Role updated successfully" });
          setIsFormOpen(false);
          setIsEditing(false);
          setSelectedRole(null);
          fetchRoles();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update role",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const handleDeleteRole = (id: string) => {
    deleteRole(
      { role_id: id },
      {
        onSuccess: () => {
          setSuccessData({ title: "Role deleted successfully" });
          fetchRoles();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete role",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const openCreateForm = () => {
    setSelectedRole(null);
    setIsEditing(false);
    setIsFormOpen(true);
  };

  const openEditForm = (role: Role) => {
    if (role.is_system_role) {
      setErrorData({
        title: "Cannot edit system role",
        list: ["System roles cannot be modified"],
      });
      return;
    }
    setSelectedRole(role);
    setIsEditing(true);
    setIsFormOpen(true);
  };

  const openDetails = (role: Role) => {
    setSelectedRole(role);
    setIsDetailsOpen(true);
  };

  const handlePaginationChange = (pageIndex: number, pageSize: number) => {
    setPageIndex(pageIndex);
    setPageSize(pageSize);
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header and Controls */}
      <div className="flex items-center justify-between p-6 border-b">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Input
              placeholder="Search roles..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64"
            />
            <ShadTooltip content="Search by role name or description">
              <IconComponent name="Search" className="h-4 w-4 text-muted-foreground" />
            </ShadTooltip>
          </div>

          <Select value={selectedWorkspace} onValueChange={setSelectedWorkspace}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All Workspaces" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Workspaces</SelectItem>
              {workspaces.map((workspace) => (
                <SelectItem key={workspace.id} value={workspace.id}>
                  {workspace.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
          <DialogTrigger asChild>
            <Button onClick={openCreateForm} className="flex items-center space-x-2">
              <IconComponent name="Plus" className="h-4 w-4" />
              <span>Create Role</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>
                {isEditing ? "Edit Role" : "Create New Role"}
              </DialogTitle>
            </DialogHeader>
            <RoleForm
              role={selectedRole}
              workspaces={workspaces}
              onSubmit={
                isEditing
                  ? (data) => handleUpdateRole(selectedRole!.id, data)
                  : handleCreateRole
              }
              onCancel={() => {
                setIsFormOpen(false);
                setSelectedRole(null);
                setIsEditing(false);
              }}
              isLoading={isCreating || isUpdating}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Role Table */}
      <div className="flex-1 overflow-hidden">
        {isLoadingRoles ? (
          <div className="flex h-full items-center justify-center">
            <LoadingComponent />
          </div>
        ) : (
          <>
            <div className="h-full overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Role</TableHead>
                    <TableHead>Workspace</TableHead>
                    <TableHead>Permissions</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Assignments</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {roles.map((role) => (
                    <TableRow key={role.id}>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <IconComponent
                              name={role.is_system_role ? "Shield" : "Users"}
                              className="h-4 w-4 text-muted-foreground"
                            />
                            <span className="font-medium">{role.name}</span>
                          </div>
                          {role.description && (
                            <p className="text-xs text-muted-foreground max-w-xs truncate">
                              {role.description}
                            </p>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        {role.workspace_id ? (
                          <div className="flex items-center space-x-1">
                            <IconComponent name="Building2" className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">
                              {workspaces.find((w) => w.id === role.workspace_id)?.name || "Unknown"}
                            </span>
                          </div>
                        ) : (
                          <Badge variant="outline">System</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <IconComponent name="Key" className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{role.permissions.length}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={role.is_system_role ? "default" : "secondary"}>
                          {role.is_system_role ? "System" : "Custom"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={role.is_active ? "default" : "secondary"}>
                          {role.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <IconComponent name="UserCheck" className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm">{role.assignment_count || 0}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <ShadTooltip content="View Details">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openDetails(role)}
                            >
                              <IconComponent name="Eye" className="h-4 w-4" />
                            </Button>
                          </ShadTooltip>
                          {!role.is_system_role && (
                            <>
                              <ShadTooltip content="Edit Role">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => openEditForm(role)}
                                >
                                  <IconComponent name="Pencil" className="h-4 w-4" />
                                </Button>
                              </ShadTooltip>
                              <ShadTooltip content="Delete Role">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDeleteRole(role.id)}
                                  disabled={isDeleting}
                                >
                                  <IconComponent name="Trash2" className="h-4 w-4 text-destructive" />
                                </Button>
                              </ShadTooltip>
                            </>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="border-t p-4">
              <PaginatorComponent
                pageIndex={pageIndex}
                pageSize={pageSize}
                totalRowsCount={totalCount}
                paginate={handlePaginationChange}
                rowsCount={[5, 10, 25, 50]}
              />
            </div>
          </>
        )}
      </div>

      {/* Role Details Dialog */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Role Details</DialogTitle>
          </DialogHeader>
          {selectedRole && (
            <RoleDetails
              role={selectedRole}
              workspace={workspaces.find((w) => w.id === selectedRole.workspace_id)}
              onClose={() => {
                setIsDetailsOpen(false);
                setSelectedRole(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
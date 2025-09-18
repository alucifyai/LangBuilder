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
  useGetRoleAssignments,
  useCreateRoleAssignment,
  useUpdateRoleAssignment,
  useDeleteRoleAssignment,
  useGetRoles,
  type Workspace,
  type RoleAssignment,
  type Role,
} from "@/controllers/API/queries/rbac";
import { useGetUsers } from "@/controllers/API/queries/auth";
import RoleAssignmentForm from "./RoleAssignmentForm";
import RoleAssignmentDetails from "./RoleAssignmentDetails";

export default function UserAssignment() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [assignments, setAssignments] = useState<RoleAssignment[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");
  const [selectedAssignment, setSelectedAssignment] = useState<RoleAssignment | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: getWorkspaces } = useGetWorkspaces();
  const { mutate: getRoles } = useGetRoles();
  const { mutate: getRoleAssignments, isPending: isLoading } = useGetRoleAssignments();
  const { mutate: createRoleAssignment, isPending: isCreating } = useCreateRoleAssignment();
  const { mutate: updateRoleAssignment, isPending: isUpdating } = useUpdateRoleAssignment();
  const { mutate: deleteRoleAssignment, isPending: isDeleting } = useDeleteRoleAssignment();

  useEffect(() => {
    loadWorkspaces();
    loadRoles();
  }, []);

  useEffect(() => {
    fetchAssignments();
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

  const loadRoles = () => {
    getRoles(
      { limit: 100, include_system_roles: true },
      {
        onSuccess: (data) => {
          setRoles(data.roles);
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

  const fetchAssignments = () => {
    getRoleAssignments(
      {
        skip: pageSize * (pageIndex - 1),
        limit: pageSize,
        workspace_id: selectedWorkspace || undefined,
        // Note: Search would need backend support for searching by principal_name
      },
      {
        onSuccess: (data) => {
          setAssignments(data.assignments);
          setTotalCount(data.total_count);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load role assignments",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const handleCreateAssignment = (data: {
    role_id: string;
    principal_type: "user" | "service_account";
    principal_id: string;
    scope_type: "global" | "workspace" | "project" | "environment";
    scope_id?: string;
    expires_at?: string;
  }) => {
    createRoleAssignment(data, {
      onSuccess: () => {
        setSuccessData({ title: "Role assignment created successfully" });
        setIsFormOpen(false);
        fetchAssignments();
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to create role assignment",
          list: [error?.message || "Unknown error occurred"],
        });
      },
    });
  };

  const handleUpdateAssignment = (
    assignmentId: string,
    data: { expires_at?: string; is_active?: boolean }
  ) => {
    updateRoleAssignment(
      { assignment_id: assignmentId, ...data },
      {
        onSuccess: () => {
          setSuccessData({ title: "Role assignment updated successfully" });
          setIsFormOpen(false);
          setIsEditing(false);
          setSelectedAssignment(null);
          fetchAssignments();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update role assignment",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const handleDeleteAssignment = (assignmentId: string) => {
    deleteRoleAssignment(
      { assignment_id: assignmentId },
      {
        onSuccess: () => {
          setSuccessData({ title: "Role assignment deleted successfully" });
          fetchAssignments();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete role assignment",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      }
    );
  };

  const openCreateForm = () => {
    setSelectedAssignment(null);
    setIsEditing(false);
    setIsFormOpen(true);
  };

  const openEditForm = (assignment: RoleAssignment) => {
    setSelectedAssignment(assignment);
    setIsEditing(true);
    setIsFormOpen(true);
  };

  const openDetails = (assignment: RoleAssignment) => {
    setSelectedAssignment(assignment);
    setIsDetailsOpen(true);
  };

  const handlePaginationChange = (pageIndex: number, pageSize: number) => {
    setPageIndex(pageIndex);
    setPageSize(pageSize);
  };

  const getRoleName = (roleId: string) => {
    return roles.find((role) => role.id === roleId)?.name || "Unknown Role";
  };

  const getWorkspaceName = (workspaceId: string) => {
    return workspaces.find((workspace) => workspace.id === workspaceId)?.name || "Unknown Workspace";
  };

  const filteredAssignments = assignments.filter((assignment) => {
    if (!searchTerm) return true;
    return (
      assignment.principal_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      assignment.role_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <div className="flex h-full flex-col">
      {/* Header and Controls */}
      <div className="flex items-center justify-between p-6 border-b">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Input
              placeholder="Search users or roles..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64"
            />
            <ShadTooltip content="Search by user name or role name">
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
              <IconComponent name="UserPlus" className="h-4 w-4" />
              <span>Assign Role</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {isEditing ? "Edit Role Assignment" : "Create Role Assignment"}
              </DialogTitle>
            </DialogHeader>
            <RoleAssignmentForm
              assignment={selectedAssignment}
              workspaces={workspaces}
              roles={roles}
              onSubmit={
                isEditing
                  ? (data) => handleUpdateAssignment(selectedAssignment!.id, data)
                  : handleCreateAssignment
              }
              onCancel={() => {
                setIsFormOpen(false);
                setSelectedAssignment(null);
                setIsEditing(false);
              }}
              isLoading={isCreating || isUpdating}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Assignments Table */}
      <div className="flex-1 overflow-hidden">
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <LoadingComponent />
          </div>
        ) : (
          <>
            <div className="h-full overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Principal</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Scope</TableHead>
                    <TableHead>Granted By</TableHead>
                    <TableHead>Granted At</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAssignments.map((assignment) => (
                    <TableRow key={assignment.id}>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <IconComponent
                            name={assignment.principal_type === "user" ? "User" : "Bot"}
                            className="h-4 w-4 text-muted-foreground"
                          />
                          <div>
                            <span className="font-medium">{assignment.principal_name}</span>
                            <div className="text-xs text-muted-foreground">
                              {assignment.principal_type}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <IconComponent name="Shield" className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">{assignment.role_name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Badge variant="outline" className="text-xs">
                            {assignment.scope_type}
                          </Badge>
                          {assignment.scope_name && (
                            <div className="text-xs text-muted-foreground">
                              {assignment.scope_name}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">
                        {assignment.granted_by_name}
                      </TableCell>
                      <TableCell className="text-sm">
                        {new Date(assignment.granted_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Badge variant={assignment.is_active ? "default" : "secondary"}>
                            {assignment.is_active ? "Active" : "Inactive"}
                          </Badge>
                          {assignment.expires_at && (
                            <div className="text-xs text-muted-foreground">
                              Expires: {new Date(assignment.expires_at).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <ShadTooltip content="View Details">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openDetails(assignment)}
                            >
                              <IconComponent name="Eye" className="h-4 w-4" />
                            </Button>
                          </ShadTooltip>
                          <ShadTooltip content="Edit Assignment">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditForm(assignment)}
                            >
                              <IconComponent name="Pencil" className="h-4 w-4" />
                            </Button>
                          </ShadTooltip>
                          <ShadTooltip content="Delete Assignment">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteAssignment(assignment.id)}
                              disabled={isDeleting}
                            >
                              <IconComponent name="Trash2" className="h-4 w-4 text-destructive" />
                            </Button>
                          </ShadTooltip>
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

      {/* Assignment Details Dialog */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Role Assignment Details</DialogTitle>
          </DialogHeader>
          {selectedAssignment && (
            <RoleAssignmentDetails
              assignment={selectedAssignment}
              workspace={workspaces.find((w) => w.id === selectedAssignment.scope_id)}
              role={roles.find((r) => r.id === selectedAssignment.role_id)}
              onClose={() => {
                setIsDetailsOpen(false);
                setSelectedAssignment(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
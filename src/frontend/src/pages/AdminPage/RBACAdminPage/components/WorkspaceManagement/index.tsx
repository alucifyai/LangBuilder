import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import LoadingComponent from "@/components/common/loadingComponent";
import PaginatorComponent from "@/components/common/paginatorComponent";
import ShadTooltip from "@/components/common/shadTooltipComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useCreateWorkspace,
  useDeleteWorkspace,
  useGetWorkspaces,
  useUpdateWorkspace,
  type Workspace,
} from "@/controllers/API/queries/rbac";
import useAlertStore from "@/stores/alertStore";
import WorkspaceDetails from "./WorkspaceDetails";
import WorkspaceForm from "./WorkspaceForm";

export default function WorkspaceManagement() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(
    null,
  );
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: getWorkspaces, isPending: isLoading } = useGetWorkspaces();
  const { mutate: createWorkspace, isPending: isCreating } =
    useCreateWorkspace();
  const { mutate: updateWorkspace, isPending: isUpdating } =
    useUpdateWorkspace();
  const { mutate: deleteWorkspace, isPending: isDeleting } =
    useDeleteWorkspace();

  useEffect(() => {
    fetchWorkspaces();
  }, [pageIndex, pageSize, searchTerm]);

  const fetchWorkspaces = () => {
    getWorkspaces(
      {
        skip: pageSize * (pageIndex - 1),
        limit: pageSize,
        search: searchTerm || undefined,
      },
      {
        onSuccess: (data) => {
          setWorkspaces(data.workspaces);
          setTotalCount(data.total_count);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load workspaces",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      },
    );
  };

  const handleCreateWorkspace = (data: {
    name: string;
    description?: string;
  }) => {
    createWorkspace(data, {
      onSuccess: () => {
        setSuccessData({ title: "Workspace created successfully" });
        setIsFormOpen(false);
        fetchWorkspaces();
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to create workspace",
          list: [error?.message || "Unknown error occurred"],
        });
      },
    });
  };

  const handleUpdateWorkspace = (
    id: string,
    data: { name?: string; description?: string; is_active?: boolean },
  ) => {
    updateWorkspace(
      { workspace_id: id, ...data },
      {
        onSuccess: () => {
          setSuccessData({ title: "Workspace updated successfully" });
          setIsFormOpen(false);
          setIsEditing(false);
          setSelectedWorkspace(null);
          fetchWorkspaces();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update workspace",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      },
    );
  };

  const handleDeleteWorkspace = (id: string) => {
    deleteWorkspace(
      { workspace_id: id },
      {
        onSuccess: () => {
          setSuccessData({ title: "Workspace deleted successfully" });
          fetchWorkspaces();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete workspace",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      },
    );
  };

  const openCreateForm = () => {
    setSelectedWorkspace(null);
    setIsEditing(false);
    setIsFormOpen(true);
  };

  const openEditForm = (workspace: Workspace) => {
    setSelectedWorkspace(workspace);
    setIsEditing(true);
    setIsFormOpen(true);
  };

  const openDetails = (workspace: Workspace) => {
    setSelectedWorkspace(workspace);
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
              placeholder="Search workspaces..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64"
            />
            <ShadTooltip content="Search by workspace name or description">
              <IconComponent
                name="Search"
                className="h-4 w-4 text-muted-foreground"
              />
            </ShadTooltip>
          </div>
        </div>

        <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
          <DialogTrigger asChild>
            <Button
              onClick={openCreateForm}
              className="flex items-center space-x-2"
            >
              <IconComponent name="Plus" className="h-4 w-4" />
              <span>Create Workspace</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {isEditing ? "Edit Workspace" : "Create New Workspace"}
              </DialogTitle>
            </DialogHeader>
            <WorkspaceForm
              workspace={selectedWorkspace}
              onSubmit={
                isEditing
                  ? (data) => handleUpdateWorkspace(selectedWorkspace!.id, data)
                  : handleCreateWorkspace
              }
              onCancel={() => {
                setIsFormOpen(false);
                setSelectedWorkspace(null);
                setIsEditing(false);
              }}
              isLoading={isCreating || isUpdating}
            />
          </DialogContent>
        </Dialog>
      </div>

      {/* Workspace Table */}
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
                    <TableHead>Name</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Members</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {workspaces.map((workspace) => (
                    <TableRow key={workspace.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center space-x-2">
                          <IconComponent
                            name="Building2"
                            className="h-4 w-4 text-muted-foreground"
                          />
                          <span>{workspace.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {workspace.description || "No description"}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            workspace.is_active ? "default" : "secondary"
                          }
                        >
                          {workspace.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {new Date(workspace.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-1">
                          <IconComponent
                            name="Users"
                            className="h-4 w-4 text-muted-foreground"
                          />
                          <span>{workspace.member_count || 0}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center space-x-2">
                          <ShadTooltip content="View Details">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openDetails(workspace)}
                            >
                              <IconComponent name="Eye" className="h-4 w-4" />
                            </Button>
                          </ShadTooltip>
                          <ShadTooltip content="Edit Workspace">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditForm(workspace)}
                            >
                              <IconComponent
                                name="Pencil"
                                className="h-4 w-4"
                              />
                            </Button>
                          </ShadTooltip>
                          <ShadTooltip content="Delete Workspace">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() =>
                                handleDeleteWorkspace(workspace.id)
                              }
                              disabled={isDeleting}
                            >
                              <IconComponent
                                name="Trash2"
                                className="h-4 w-4 text-destructive"
                              />
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

      {/* Workspace Details Dialog */}
      <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Workspace Details</DialogTitle>
          </DialogHeader>
          {selectedWorkspace && (
            <WorkspaceDetails
              workspace={selectedWorkspace}
              onClose={() => {
                setIsDetailsOpen(false);
                setSelectedWorkspace(null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

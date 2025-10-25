import { useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Button } from "../../../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../../../components/ui/card";
import { Label } from "../../../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../components/ui/select";
import {
  useDeleteAssignment,
  useGetRoles,
  usePatchAssignment,
  usePostAssignment,
} from "../../../controllers/API/queries/rbac";
import type { UserRoleAssignment } from "../../../controllers/API/queries/rbac/use-get-assignments";
import BaseModal from "../../../modals/baseModal";
import useAlertStore from "../../../stores/alertStore";
import AssignmentListView from "./AssignmentListView";
import CreateAssignmentModal from "./CreateAssignmentModal";

/**
 * RBACManagementPage - Main RBAC management interface
 *
 * PRD Story 3.1: RBAC Management Section in the Admin Page
 *
 * This component is rendered as a tab within the AdminPage
 */
export default function RBACManagementPage() {
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] =
    useState<UserRoleAssignment | null>(null);
  const [newRoleId, setNewRoleId] = useState("");

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: createAssignment } = usePostAssignment();
  const { mutate: deleteAssignment } = useDeleteAssignment();
  const { mutate: updateAssignment } = usePatchAssignment();
  const { data: rolesData } = useGetRoles();

  const roles = rolesData?.roles ?? [];

  const handleCreateAssignment = (
    assignment: Parameters<typeof createAssignment>[0],
  ) => {
    createAssignment(assignment, {
      onSuccess: () => {
        setSuccessData({
          title: "Assignment created successfully",
        });
      },
      onError: (error: any) => {
        setErrorData({
          title: "Failed to create assignment",
          list: [error?.response?.data?.detail || "Unknown error occurred"],
        });
      },
    });
  };

  const handleDeleteAssignment = (assignmentId: string) => {
    deleteAssignment(assignmentId, {
      onSuccess: () => {
        setSuccessData({
          title: "Assignment deleted successfully",
        });
      },
      onError: (error: any) => {
        const detail = error?.response?.data?.detail;
        setErrorData({
          title: "Failed to delete assignment",
          list: [
            typeof detail === "string"
              ? detail
              : detail?.message || "Unknown error occurred",
          ],
        });
      },
    });
  };

  const handleEditAssignment = (assignment: UserRoleAssignment) => {
    setSelectedAssignment(assignment);
    setNewRoleId(assignment.role_id);
    setEditModalOpen(true);
  };

  const handleConfirmEdit = () => {
    if (!selectedAssignment || !newRoleId) return;

    updateAssignment(
      {
        assignmentId: selectedAssignment.id,
        data: { role_id: newRoleId },
      },
      {
        onSuccess: () => {
          setSuccessData({
            title: "Assignment updated successfully",
          });
          setEditModalOpen(false);
          setSelectedAssignment(null);
          setNewRoleId("");
        },
        onError: (error: any) => {
          const detail = error?.response?.data?.detail;
          setErrorData({
            title: "Failed to update assignment",
            list: [
              typeof detail === "string"
                ? detail
                : detail?.message || "Unknown error occurred",
            ],
          });
        },
      },
    );
  };

  return (
    <div className="flex h-full flex-col space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">RBAC Management</h2>
          <p className="text-muted-foreground">
            Manage role-based access control assignments for users
          </p>
        </div>
        <CreateAssignmentModal onConfirm={handleCreateAssignment} asChild>
          <Button>
            <IconComponent name="Plus" className="h-4 w-4 mr-2" />
            New Assignment
          </Button>
        </CreateAssignmentModal>
      </div>

      {/* Roles Reference Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Available Roles</CardTitle>
          <CardDescription>
            Default roles with their permission levels
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {roles.map((role) => (
              <div key={role.id} className="rounded-lg border p-3 space-y-1">
                <div className="flex items-center gap-2">
                  <div className="font-medium">{role.name}</div>
                  {role.is_global && (
                    <div className="rounded bg-blue-100 dark:bg-blue-900/30 px-1.5 py-0.5 text-xs text-blue-700 dark:text-blue-300">
                      Global
                    </div>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  {role.description}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Assignments List */}
      <div className="flex-1 min-h-0">
        <AssignmentListView
          onDelete={handleDeleteAssignment}
          onEdit={handleEditAssignment}
        />
      </div>

      {/* Edit Assignment Modal */}
      <BaseModal size="small" open={editModalOpen} setOpen={setEditModalOpen}>
        <BaseModal.Header description="Change the role for this assignment">
          <span className="pr-2">Edit Assignment</span>
          <IconComponent
            name="Pencil"
            className="h-6 w-6 pl-1 text-foreground"
            aria-hidden="true"
          />
        </BaseModal.Header>
        <BaseModal.Content>
          {selectedAssignment && (
            <div className="space-y-4">
              <div className="rounded-md bg-muted p-3 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">User:</span>
                  <span className="font-medium">
                    {selectedAssignment.user_username ||
                      selectedAssignment.user_id}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Scope:</span>
                  <span className="font-medium capitalize">
                    {selectedAssignment.scope}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Entity:</span>
                  <span className="font-medium">
                    {selectedAssignment.scope_name ||
                      selectedAssignment.scope_id}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="new-role-select">New Role</Label>
                <Select value={newRoleId} onValueChange={setNewRoleId}>
                  <SelectTrigger id="new-role-select">
                    <SelectValue placeholder="Select new role..." />
                  </SelectTrigger>
                  <SelectContent>
                    {roles.map((role) => (
                      <SelectItem key={role.id} value={role.id}>
                        <div className="flex flex-col">
                          <span>{role.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {role.description}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button
                  variant="ghost"
                  onClick={() => {
                    setEditModalOpen(false);
                    setSelectedAssignment(null);
                    setNewRoleId("");
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmEdit}
                  disabled={
                    !newRoleId || newRoleId === selectedAssignment.role_id
                  }
                >
                  Update Assignment
                </Button>
              </div>
            </div>
          )}
        </BaseModal.Content>
      </BaseModal>
    </div>
  );
}

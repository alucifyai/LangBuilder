/**
 * AssignmentListView Component
 *
 * Task 4.2: Main list view for role assignments with filtering
 *
 * Displays all User:Role:Scope assignments with:
 * - Filtering by User, Role, and Scope
 * - Inline delete actions for non-immutable assignments
 * - Clear messaging about role inheritance
 * - Real-time updates on assignment changes
 */

import { useState } from "react";
import {
  useGetAssignments,
  useDeleteAssignment,
  useGetRoles,
  type Assignment,
} from "../../../controllers/API/queries/rbac";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../../components/ui/table";
import { Input } from "../../../components/ui/input";
import { Button } from "../../../components/ui/button";
import { Badge } from "../../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../components/ui/select";
import useAlertStore from "../../../stores/alertStore";
import CreateAssignmentModal from "./CreateAssignmentModal";

export default function AssignmentListView() {
  const [userFilter, setUserFilter] = useState<string>("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [scopeFilter, setScopeFilter] = useState<string>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingAssignment, setEditingAssignment] = useState<Assignment | null>(null);

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  // Build query params
  const queryParams = {
    ...(userFilter && { user_id: userFilter }),
    ...(roleFilter && roleFilter !== "all" && { role_id: roleFilter }),
    ...(scopeFilter && scopeFilter !== "all" && { scope_type: scopeFilter }),
  };

  const {
    data: assignments,
    isLoading,
    error,
  } = useGetAssignments(Object.keys(queryParams).length > 0 ? queryParams : undefined);

  const { data: roles } = useGetRoles();

  const deleteMutation = useDeleteAssignment();

  const handleDelete = async (assignment: Assignment) => {
    setDeletingId(assignment.id);
    try {
      await deleteMutation.mutateAsync(assignment.id);
      setSuccessData({
        title: "Assignment Deleted",
        description: "Role assignment has been successfully deleted.",
      });
    } catch (error: any) {
      // Enhanced error messages for immutable assignments and last Admin
      const errorMessage =
        error?.response?.data?.detail ||
        error?.detail ||
        "Failed to delete assignment";

      if (errorMessage.includes("immutable")) {
        setErrorData({
          title: "Cannot Delete Assignment",
          description:
            "Cannot modify Starter Project Owner assignment. This assignment is protected to ensure users always have access to their default project.",
        });
      } else if (errorMessage.toLowerCase().includes("last admin")) {
        setErrorData({
          title: "Cannot Delete Last Admin",
          description:
            "Cannot delete the last Admin role assignment. At least one Admin must exist to manage the system. Please assign the Admin role to another user first.",
        });
      } else {
        setErrorData({
          title: "Delete Failed",
          description: errorMessage,
        });
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearFilters = () => {
    setUserFilter("");
    setRoleFilter("all");
    setScopeFilter("all");
  };

  const hasActiveFilters = userFilter || (roleFilter !== "all") || (scopeFilter !== "all");

  const handleOpenCreateModal = () => {
    setEditingAssignment(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (assignment: Assignment) => {
    setEditingAssignment(assignment);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingAssignment(null);
  };

  return (
    <div className="flex h-full w-full flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Role Assignments</h3>
          <p className="text-sm text-muted-foreground">
            Manage user role assignments for projects and flows
          </p>
        </div>
        <Button onClick={handleOpenCreateModal}>
          Create Assignment
        </Button>
      </div>

      {/* Inheritance Message */}
      <div className="rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-950">
        <p className="text-sm text-blue-900 dark:text-blue-100">
          <strong>Note:</strong> Project-level assignments are inherited by
          contained Flows and can be overridden by explicit Flow-specific roles.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[200px]">
          <label className="mb-1 block text-sm font-medium">Filter by User ID</label>
          <Input
            placeholder="Enter user ID..."
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
            className="w-full"
          />
        </div>

        <div className="flex-1 min-w-[200px]">
          <label className="mb-1 block text-sm font-medium">Filter by Role</label>
          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All Roles" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Roles</SelectItem>
              {roles?.map((role) => (
                <SelectItem key={role.id} value={role.id}>
                  {role.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex-1 min-w-[200px]">
          <label className="mb-1 block text-sm font-medium">Filter by Scope</label>
          <Select value={scopeFilter} onValueChange={setScopeFilter}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="All Scopes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Scopes</SelectItem>
              <SelectItem value="Global">Global</SelectItem>
              <SelectItem value="Project">Project</SelectItem>
              <SelectItem value="Flow">Flow</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {hasActiveFilters && (
          <Button
            variant="outline"
            onClick={handleClearFilters}
            className="min-w-[100px]"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto rounded-md border">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <p className="text-muted-foreground">Loading assignments...</p>
          </div>
        ) : error ? (
          <div className="flex h-64 items-center justify-center">
            <p className="text-destructive">
              Failed to load assignments: {(error as Error).message}
            </p>
          </div>
        ) : !assignments || assignments.length === 0 ? (
          <div className="flex h-64 items-center justify-center">
            <div className="text-center">
              <p className="text-muted-foreground">
                {hasActiveFilters
                  ? "No assignments match the current filters"
                  : "No role assignments found"}
              </p>
              {hasActiveFilters && (
                <Button
                  variant="link"
                  onClick={handleClearFilters}
                  className="mt-2"
                >
                  Clear filters to see all assignments
                </Button>
              )}
            </div>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Scope Type</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assignments.map((assignment) => (
                <TableRow key={assignment.id}>
                  <TableCell>
                    <span className="font-medium">{assignment.user_name || "Unknown"}</span>
                  </TableCell>
                  <TableCell>
                    <Badge variant="default">{assignment.role_name || "Unknown Role"}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{assignment.scope_type}</Badge>
                  </TableCell>
                  <TableCell>
                    {assignment.scope_name ? (
                      <span className="font-medium">{assignment.scope_name}</span>
                    ) : assignment.scope_type === "Global" ? (
                      <span className="text-muted-foreground italic">Global</span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    {new Date(assignment.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      {assignment.is_immutable ? (
                        <Badge variant="secondary">Immutable</Badge>
                      ) : (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenEditModal(assignment)}
                          >
                            Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleDelete(assignment)}
                            disabled={deletingId === assignment.id}
                          >
                            {deletingId === assignment.id
                              ? "Deleting..."
                              : "Delete"}
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Summary */}
      {assignments && assignments.length > 0 && (
        <div className="text-sm text-muted-foreground">
          Showing {assignments.length} assignment
          {assignments.length !== 1 ? "s" : ""}
          {hasActiveFilters && " (filtered)"}
        </div>
      )}

      {/* Create/Edit Assignment Modal */}
      <CreateAssignmentModal
        open={isModalOpen}
        onClose={handleCloseModal}
        editAssignment={editingAssignment}
      />
    </div>
  );
}

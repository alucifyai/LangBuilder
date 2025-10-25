import { useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import CustomLoader from "@/customization/components/custom-loader";
import ShadTooltip from "../../../components/common/shadTooltipComponent";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../../components/ui/table";
import { useGetAssignments, useGetRoles } from "../../../controllers/API/queries/rbac";
import type { UserRoleAssignment } from "../../../controllers/API/queries/rbac/use-get-assignments";
import ConfirmationModal from "../../../modals/confirmationModal";

export interface AssignmentListViewProps {
  onDelete: (assignmentId: string) => void;
  onEdit: (assignment: UserRoleAssignment) => void;
}

/**
 * AssignmentListView - Displays and filters role assignments
 *
 * PRD Story 3.3: Assignment List View and Filtering
 * PRD Story 3.5: Flow Role Inheritance Display Rule
 */
export default function AssignmentListView({
  onDelete,
  onEdit,
}: AssignmentListViewProps) {
  // Filter state
  const [userFilter, setUserFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [scopeFilter, setScope Filter] = useState<"" | "flow" | "project">("");

  // Fetch assignments with filters
  const { data: assignmentsData, isLoading } = useGetAssignments({
    role_id: roleFilter || undefined,
    scope: scopeFilter || undefined,
  });

  const { data: rolesData } = useGetRoles();

  const assignments = assignmentsData?.assignments ?? [];
  const roles = rolesData?.roles ?? [];

  // Client-side filtering for username (since API doesn't support it directly)
  const filteredAssignments = assignments.filter((assignment) => {
    if (userFilter && assignment.user_username) {
      return assignment.user_username
        .toLowerCase()
        .includes(userFilter.toLowerCase());
    }
    return true;
  });

  const handleClearFilters = () => {
    setUserFilter("");
    setRoleFilter("");
    setScopeFilter("");
  };

  const hasActiveFilters = userFilter || roleFilter || scopeFilter;

  return (
    <div className="flex h-full flex-col space-y-4">
      {/* Inheritance info banner */}
      <div className="rounded-md bg-blue-50 dark:bg-blue-950/20 p-3 text-sm text-blue-900 dark:text-blue-100">
        <div className="flex items-start gap-2">
          <IconComponent name="Info" className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <p>
            Project-level assignments are inherited by contained Flows and can be
            overridden by explicit Flow-specific roles.
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex-1 min-w-[200px]">
          <Input
            placeholder="Filter by username..."
            value={userFilter}
            onChange={(e) => setUserFilter(e.target.value)}
          />
        </div>

        <div className="w-[180px]">
          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by role..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Roles</SelectItem>
              {roles.map((role) => (
                <SelectItem key={role.id} value={role.id}>
                  {role.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="w-[180px]">
          <Select value={scopeFilter} onValueChange={(value) => setScopeFilter(value as typeof scopeFilter)}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by scope..." />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Scopes</SelectItem>
              <SelectItem value="project">Project</SelectItem>
              <SelectItem value="flow">Flow</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            <IconComponent name="X" className="h-4 w-4 mr-1" />
            Clear Filters
          </Button>
        )}
      </div>

      {/* Assignments table */}
      <div className="flex-1 overflow-auto rounded-md border-2 bg-background">
        {isLoading ? (
          <div className="flex h-full items-center justify-center p-8">
            <CustomLoader remSize={8} />
          </div>
        ) : filteredAssignments.length === 0 ? (
          <div className="flex h-full items-center justify-center p-8 text-muted-foreground">
            {hasActiveFilters ? "No assignments match the current filters." : "No role assignments yet."}
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-muted">
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="w-[100px] text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAssignments.map((assignment) => (
                <TableRow key={assignment.id}>
                  <TableCell className="font-medium">
                    {assignment.user_username || assignment.user_id}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {assignment.role_name || assignment.role_id}
                      {assignment.is_immutable && (
                        <ShadTooltip content="This assignment is immutable and cannot be modified or deleted">
                          <IconComponent
                            name="Lock"
                            className="h-3 w-3 text-muted-foreground"
                          />
                        </ShadTooltip>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="capitalize">{assignment.scope}</TableCell>
                  <TableCell className="truncate max-w-[200px]">
                    <ShadTooltip content={assignment.scope_name || assignment.scope_id}>
                      <span className="cursor-default">
                        {assignment.scope_name || assignment.scope_id}
                      </span>
                    </ShadTooltip>
                  </TableCell>
                  <TableCell>
                    {new Date(assignment.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {!assignment.is_immutable && (
                        <>
                          <ShadTooltip content="Edit assignment" side="top">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => onEdit(assignment)}
                              className="h-8 w-8 p-0"
                            >
                              <IconComponent name="Pencil" className="h-4 w-4" />
                            </Button>
                          </ShadTooltip>

                          <ConfirmationModal
                            size="x-small"
                            title="Delete Assignment"
                            titleHeader="Delete Role Assignment"
                            modalContentTitle="Attention!"
                            cancelText="Cancel"
                            confirmationText="Delete"
                            icon="Trash2"
                            data={assignment}
                            index={0}
                            onConfirm={(_, data) => onDelete(data.id)}
                          >
                            <ConfirmationModal.Content>
                              <span>
                                Are you sure you want to delete this role assignment? This
                                action cannot be undone.
                              </span>
                            </ConfirmationModal.Content>
                            <ConfirmationModal.Trigger>
                              <ShadTooltip content="Delete assignment" side="top">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                                >
                                  <IconComponent name="Trash2" className="h-4 w-4" />
                                </Button>
                              </ShadTooltip>
                            </ConfirmationModal.Trigger>
                          </ConfirmationModal>
                        </>
                      )}
                      {assignment.is_immutable && (
                        <ShadTooltip content="This assignment cannot be modified">
                          <div className="flex h-8 w-8 items-center justify-center">
                            <IconComponent
                              name="Lock"
                              className="h-4 w-4 text-muted-foreground"
                            />
                          </div>
                        </ShadTooltip>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}

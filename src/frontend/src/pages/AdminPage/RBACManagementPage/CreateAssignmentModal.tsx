import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import CustomLoader from "@/customization/components/custom-loader";
import { Button } from "../../../components/ui/button";
import { Label } from "../../../components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../components/ui/select";
import { useGetUsers } from "../../../controllers/API/queries/auth";
import { useGetFlows } from "../../../controllers/API/queries/flows";
import { useGetFolders } from "../../../controllers/API/queries/folders";
import { useGetRoles } from "../../../controllers/API/queries/rbac";
import type { CreateAssignmentRequest } from "../../../controllers/API/queries/rbac/use-post-assignment";
import BaseModal from "../../../modals/baseModal";

export interface CreateAssignmentModalProps {
  children: React.ReactNode;
  onConfirm: (assignment: CreateAssignmentRequest) => void;
  asChild?: boolean;
}

/**
 * CreateAssignmentModal - Multi-step workflow for creating role assignments
 *
 * Workflow: Select User → Select Scope → Select Role → Confirm
 *
 * PRD Story 3.2: Assignment Creation Workflow
 */
export default function CreateAssignmentModal({
  children,
  onConfirm,
  asChild,
}: CreateAssignmentModalProps) {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Form state
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedScope, setSelectedScope] = useState<"flow" | "project" | "">(
    "",
  );
  const [selectedScopeId, setSelectedScopeId] = useState<string>("");
  const [selectedRoleId, setSelectedRoleId] = useState<string>("");

  // API queries
  const { data: usersData, isLoading: usersLoading } = useGetUsers({});
  const { data: rolesData, isLoading: rolesLoading } = useGetRoles();
  const { data: flowsData, isLoading: flowsLoading } = useGetFlows({});
  const { data: foldersData, isLoading: foldersLoading } = useGetFolders({});

  const users = usersData?.users ?? [];
  const roles = rolesData?.roles ?? [];
  const flows = flowsData?.flows ?? [];
  const folders = foldersData?.folders ?? [];

  // Reset form when modal closes
  useEffect(() => {
    if (!open) {
      setStep(1);
      setSelectedUserId("");
      setSelectedScope("");
      setSelectedScopeId("");
      setSelectedRoleId("");
    }
  }, [open]);

  const handleNext = () => {
    if (step < 4) {
      setStep((prev) => (prev + 1) as typeof step);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((prev) => (prev - 1) as typeof step);
    }
  };

  const handleConfirm = () => {
    if (
      !selectedUserId ||
      !selectedScope ||
      !selectedScopeId ||
      !selectedRoleId
    ) {
      return;
    }

    onConfirm({
      user_id: selectedUserId,
      role_id: selectedRoleId,
      scope: selectedScope as "flow" | "project",
      scope_id: selectedScopeId,
    });

    setOpen(false);
  };

  const canProceedFromStep1 = !!selectedUserId;
  const canProceedFromStep2 = !!selectedScope && !!selectedScopeId;
  const canProceedFromStep3 = !!selectedRoleId;

  return (
    <BaseModal size="medium" open={open} setOpen={setOpen}>
      <BaseModal.Trigger asChild={asChild}>{children}</BaseModal.Trigger>
      <BaseModal.Header description="Create a new role assignment">
        <span className="pr-2">New Assignment</span>
        <IconComponent
          name="ShieldPlus"
          className="h-6 w-6 pl-1 text-foreground"
          aria-hidden="true"
        />
      </BaseModal.Header>
      <BaseModal.Content>
        <div className="flex flex-col gap-6">
          {/* Step indicator */}
          <div className="flex items-center justify-between">
            {[1, 2, 3, 4].map((s) => (
              <div
                key={s}
                className={`flex h-8 w-8 items-center justify-center rounded-full ${
                  s === step
                    ? "bg-primary text-primary-foreground"
                    : s < step
                      ? "bg-primary/50 text-primary-foreground"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {s}
              </div>
            ))}
          </div>

          {/* Step labels */}
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Select User</span>
            <span>Select Scope</span>
            <span>Select Role</span>
            <span>Confirm</span>
          </div>

          <div className="min-h-[200px]">
            {/* Step 1: Select User */}
            {step === 1 && (
              <div className="space-y-4">
                <Label htmlFor="user-select">Select User</Label>
                {usersLoading ? (
                  <div className="flex justify-center p-4">
                    <CustomLoader remSize={4} />
                  </div>
                ) : (
                  <Select
                    value={selectedUserId}
                    onValueChange={setSelectedUserId}
                  >
                    <SelectTrigger id="user-select">
                      <SelectValue placeholder="Choose a user..." />
                    </SelectTrigger>
                    <SelectContent>
                      {users.map((user) => (
                        <SelectItem key={user.id} value={user.id}>
                          {user.username}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                {selectedUserId && (
                  <div className="text-sm text-muted-foreground">
                    Selected:{" "}
                    {users.find((u) => u.id === selectedUserId)?.username}
                  </div>
                )}
              </div>
            )}

            {/* Step 2: Select Scope */}
            {step === 2 && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="scope-type-select">Scope Type</Label>
                  <Select
                    value={selectedScope}
                    onValueChange={(value) => {
                      setSelectedScope(value as "flow" | "project");
                      setSelectedScopeId(""); // Reset scope ID when type changes
                    }}
                  >
                    <SelectTrigger id="scope-type-select">
                      <SelectValue placeholder="Choose scope type..." />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="project">Project</SelectItem>
                      <SelectItem value="flow">Flow</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {selectedScope && (
                  <div className="space-y-2">
                    <Label htmlFor="scope-entity-select">
                      Select {selectedScope === "project" ? "Project" : "Flow"}
                    </Label>
                    {(selectedScope === "flow" && flowsLoading) ||
                    (selectedScope === "project" && foldersLoading) ? (
                      <div className="flex justify-center p-4">
                        <CustomLoader remSize={4} />
                      </div>
                    ) : (
                      <Select
                        value={selectedScopeId}
                        onValueChange={setSelectedScopeId}
                      >
                        <SelectTrigger id="scope-entity-select">
                          <SelectValue
                            placeholder={`Choose ${selectedScope === "project" ? "project" : "flow"}...`}
                          />
                        </SelectTrigger>
                        <SelectContent>
                          {selectedScope === "project"
                            ? folders.map((folder) => (
                                <SelectItem key={folder.id} value={folder.id}>
                                  {folder.name}
                                </SelectItem>
                              ))
                            : flows.map((flow) => (
                                <SelectItem key={flow.id} value={flow.id}>
                                  {flow.name}
                                </SelectItem>
                              ))}
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                )}

                {selectedScopeId && (
                  <div className="text-sm text-muted-foreground">
                    Selected:{" "}
                    {selectedScope === "project"
                      ? folders.find((f) => f.id === selectedScopeId)?.name
                      : flows.find((f) => f.id === selectedScopeId)?.name}
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Select Role */}
            {step === 3 && (
              <div className="space-y-4">
                <Label htmlFor="role-select">Select Role</Label>
                {rolesLoading ? (
                  <div className="flex justify-center p-4">
                    <CustomLoader remSize={4} />
                  </div>
                ) : (
                  <Select
                    value={selectedRoleId}
                    onValueChange={setSelectedRoleId}
                  >
                    <SelectTrigger id="role-select">
                      <SelectValue placeholder="Choose a role..." />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.map((role) => (
                        <SelectItem key={role.id} value={role.id}>
                          <div className="flex flex-col">
                            <span>{role.name}</span>
                            {role.description && (
                              <span className="text-xs text-muted-foreground">
                                {role.description}
                              </span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                {selectedRoleId && (
                  <div className="rounded-md border p-3">
                    <div className="text-sm font-medium">
                      {roles.find((r) => r.id === selectedRoleId)?.name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {roles.find((r) => r.id === selectedRoleId)?.description}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 4: Confirm */}
            {step === 4 && (
              <div className="space-y-4">
                <h3 className="font-medium">Review Assignment</h3>
                <div className="rounded-md border p-4 space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">User:</span>
                    <span className="text-sm font-medium">
                      {users.find((u) => u.id === selectedUserId)?.username}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">
                      Scope:
                    </span>
                    <span className="text-sm font-medium capitalize">
                      {selectedScope}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">
                      {selectedScope === "project" ? "Project" : "Flow"}:
                    </span>
                    <span className="text-sm font-medium">
                      {selectedScope === "project"
                        ? folders.find((f) => f.id === selectedScopeId)?.name
                        : flows.find((f) => f.id === selectedScopeId)?.name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Role:</span>
                    <span className="text-sm font-medium">
                      {roles.find((r) => r.id === selectedRoleId)?.name}
                    </span>
                  </div>
                </div>
                <div className="rounded-md bg-muted p-3 text-xs text-muted-foreground">
                  {selectedScope === "project" && (
                    <p>
                      Note: Project-level assignments are inherited by contained
                      Flows and can be overridden by explicit Flow-specific
                      roles.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex justify-between pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleBack}
              disabled={step === 1}
            >
              Back
            </Button>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              {step < 4 ? (
                <Button
                  type="button"
                  onClick={handleNext}
                  disabled={
                    (step === 1 && !canProceedFromStep1) ||
                    (step === 2 && !canProceedFromStep2) ||
                    (step === 3 && !canProceedFromStep3)
                  }
                >
                  Next
                </Button>
              ) : (
                <Button type="button" onClick={handleConfirm}>
                  Create Assignment
                </Button>
              )}
            </div>
          </div>
        </div>
      </BaseModal.Content>
    </BaseModal>
  );
}

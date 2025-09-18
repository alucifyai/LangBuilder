import { useEffect, useState } from "react";
import IconComponent from "../../../../../components/common/genericIconComponent";
import { Button } from "../../../../../components/ui/button";
import { Input } from "../../../../../components/ui/input";
import { Label } from "../../../../../components/ui/label";
import { CheckBoxDiv } from "../../../../../components/ui/checkbox";
import { Textarea } from "../../../../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../../../components/ui/select";
import BaseModal from "../../../../../modals/baseModal";
import type { Role } from "@/controllers/API/queries/rbac/use-get-roles";
import type { Workspace } from "@/controllers/API/queries/rbac/use-get-workspaces";

// Common RBAC permissions
const AVAILABLE_PERMISSIONS = [
  "workspaces:read",
  "workspaces:write",
  "workspaces:delete",
  "flows:read",
  "flows:write",
  "flows:execute",
  "flows:delete",
  "users:read",
  "users:write",
  "users:invite",
  "users:delete",
  "roles:read",
  "roles:write",
  "roles:assign",
  "roles:delete",
  "projects:read",
  "projects:write",
  "projects:delete",
  "environments:read",
  "environments:write",
  "environments:deploy",
  "audit:read",
  "audit:export",
  "compliance:read",
  "compliance:generate",
  "system:admin",
] as const;

export interface RoleFormData {
  name: string;
  description?: string;
  permissions: string[];
  workspace_id: string;
  is_active?: boolean;
}

interface RoleManagementModalProps {
  children: React.ReactNode;
  title: string;
  titleHeader: string;
  cancelText: string;
  confirmationText: string;
  icon: string;
  data?: Role;
  workspaces: Workspace[];
  index?: number;
  onConfirm: (roleData: RoleFormData) => void;
  asChild?: boolean;
}

export default function RoleManagementModal({
  children,
  title,
  titleHeader,
  cancelText,
  confirmationText,
  icon,
  data,
  workspaces,
  index,
  onConfirm,
  asChild = false,
}: RoleManagementModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [isActive, setIsActive] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (data) {
      setName(data.name);
      setDescription(data.description || "");
      setWorkspaceId(data.workspace_id);
      setSelectedPermissions(data.permissions);
      setIsActive(data.is_active);
    } else {
      setName("");
      setDescription("");
      setWorkspaceId(workspaces[0]?.id || "");
      setSelectedPermissions([]);
      setIsActive(true);
    }
  }, [data, workspaces, open]);

  const handleSubmit = () => {
    if (!name.trim() || !workspaceId || selectedPermissions.length === 0) {
      return;
    }

    const roleData: RoleFormData = {
      name: name.trim(),
      description: description.trim() || undefined,
      permissions: selectedPermissions,
      workspace_id: workspaceId,
      is_active: isActive,
    };

    onConfirm(roleData);
    setOpen(false);
  };

  const handlePermissionToggle = (permission: string) => {
    setSelectedPermissions(prev => 
      prev.includes(permission)
        ? prev.filter(p => p !== permission)
        : [...prev, permission]
    );
  };

  const isValid = name.trim().length > 0 && workspaceId && selectedPermissions.length > 0;

  return (
    <BaseModal size="large" open={open} setOpen={setOpen}>
      <BaseModal.Trigger asChild={asChild}>{children}</BaseModal.Trigger>
      <BaseModal.Header description={titleHeader}>
        <span className="pr-2">{title}</span>
        <IconComponent
          name={icon}
          className="h-6 w-6 pl-1 text-foreground"
          aria-hidden="true"
        />
      </BaseModal.Header>
      <BaseModal.Content>
        <div className="flex flex-col space-y-4 max-h-96 overflow-y-auto">
          <div className="space-y-2">
            <Label htmlFor="role-name">Name *</Label>
            <Input
              id="role-name"
              placeholder="Enter role name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role-workspace">Workspace *</Label>
            <Select value={workspaceId} onValueChange={setWorkspaceId}>
              <SelectTrigger>
                <SelectValue placeholder="Select workspace" />
              </SelectTrigger>
              <SelectContent>
                {workspaces.map((workspace) => (
                  <SelectItem key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="role-description">Description</Label>
            <Textarea
              id="role-description"
              placeholder="Enter role description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full"
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Permissions *</Label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto border rounded-md p-3">
              {AVAILABLE_PERMISSIONS.map((permission) => (
                <div key={permission} className="flex items-center space-x-2">
                  <CheckBoxDiv
                    checked={selectedPermissions.includes(permission)}
                    onChange={() => handlePermissionToggle(permission)}
                  />
                  <Label className="text-xs font-normal cursor-pointer">
                    {permission}
                  </Label>
                </div>
              ))}
            </div>
            <div className="text-xs text-muted-foreground">
              Selected {selectedPermissions.length} permission{selectedPermissions.length !== 1 ? "s" : ""}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <CheckBoxDiv
              checked={isActive}
              onChange={setIsActive}
            />
            <Label className="text-sm font-medium">
              Active role
            </Label>
          </div>

          <div className="text-xs text-muted-foreground">
            * Required fields
          </div>
        </div>
      </BaseModal.Content>
      <BaseModal.Footer>
        <Button
          variant="outline"
          onClick={() => setOpen(false)}
          type="button"
        >
          {cancelText}
        </Button>
        <Button
          type="button"
          variant="primary"
          onClick={handleSubmit}
          disabled={!isValid}
        >
          {confirmationText}
        </Button>
      </BaseModal.Footer>
    </BaseModal>
  );
}
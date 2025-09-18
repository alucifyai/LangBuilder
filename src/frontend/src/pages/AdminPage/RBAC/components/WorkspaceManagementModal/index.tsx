import { useEffect, useState } from "react";
import IconComponent from "../../../../../components/common/genericIconComponent";
import { Button } from "../../../../../components/ui/button";
import { Input } from "../../../../../components/ui/input";
import { Label } from "../../../../../components/ui/label";
import { CheckBoxDiv } from "../../../../../components/ui/checkbox";
import { Textarea } from "../../../../../components/ui/textarea";
import BaseModal from "../../../../../modals/baseModal";
import type { Workspace } from "@/controllers/API/queries/rbac/use-get-workspaces";

export interface WorkspaceFormData {
  name: string;
  description?: string;
  is_active?: boolean;
}

interface WorkspaceManagementModalProps {
  children: React.ReactNode;
  title: string;
  titleHeader: string;
  cancelText: string;
  confirmationText: string;
  icon: string;
  data?: Workspace;
  index?: number;
  onConfirm: (workspaceData: WorkspaceFormData) => void;
  asChild?: boolean;
}

export default function WorkspaceManagementModal({
  children,
  title,
  titleHeader,
  cancelText,
  confirmationText,
  icon,
  data,
  index,
  onConfirm,
  asChild = false,
}: WorkspaceManagementModalProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (data) {
      setName(data.name);
      setDescription(data.description || "");
      setIsActive(data.is_active);
    } else {
      setName("");
      setDescription("");
      setIsActive(true);
    }
  }, [data, open]);

  const handleSubmit = () => {
    if (!name.trim()) {
      return;
    }

    const workspaceData: WorkspaceFormData = {
      name: name.trim(),
      description: description.trim() || undefined,
      is_active: isActive,
    };

    onConfirm(workspaceData);
    setOpen(false);
  };

  const isValid = name.trim().length > 0;

  return (
    <BaseModal size="medium" open={open} setOpen={setOpen}>
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
        <div className="flex flex-col space-y-4">
          <div className="space-y-2">
            <Label htmlFor="workspace-name">Name *</Label>
            <Input
              id="workspace-name"
              placeholder="Enter workspace name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="workspace-description">Description</Label>
            <Textarea
              id="workspace-description"
              placeholder="Enter workspace description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full"
              rows={3}
            />
          </div>

          <div className="flex items-center space-x-2">
            <CheckBoxDiv
              checked={isActive}
              onChange={setIsActive}
            />
            <Label htmlFor="workspace-active" className="text-sm font-medium">
              Active workspace
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
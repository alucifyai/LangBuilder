import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Workspace } from "@/controllers/API/queries/rbac";

interface WorkspaceFormProps {
  workspace?: Workspace | null;
  onSubmit: (data: {
    name: string;
    description?: string;
    is_active?: boolean;
  }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function WorkspaceForm({
  workspace,
  onSubmit,
  onCancel,
  isLoading = false,
}: WorkspaceFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    is_active: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (workspace) {
      setFormData({
        name: workspace.name,
        description: workspace.description || "",
        is_active: workspace.is_active,
      });
    } else {
      setFormData({
        name: "",
        description: "",
        is_active: true,
      });
    }
    setErrors({});
  }, [workspace]);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Workspace name is required";
    } else if (formData.name.length < 3) {
      newErrors.name = "Workspace name must be at least 3 characters";
    } else if (formData.name.length > 255) {
      newErrors.name = "Workspace name must be less than 255 characters";
    }

    if (formData.description.length > 1000) {
      newErrors.description = "Description must be less than 1000 characters";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const submitData: {
      name: string;
      description?: string;
      is_active?: boolean;
    } = {
      name: formData.name.trim(),
    };

    if (formData.description.trim()) {
      submitData.description = formData.description.trim();
    }

    if (workspace) {
      // Include is_active when editing
      submitData.is_active = formData.is_active;
    }

    onSubmit(submitData);
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: "",
      }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="workspace-name">
          Workspace Name <span className="text-destructive">*</span>
        </Label>
        <Input
          id="workspace-name"
          value={formData.name}
          onChange={(e) => handleInputChange("name", e.target.value)}
          placeholder="Enter workspace name"
          className={errors.name ? "border-destructive" : ""}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="workspace-description">Description</Label>
        <Textarea
          id="workspace-description"
          value={formData.description}
          onChange={(e) => handleInputChange("description", e.target.value)}
          placeholder="Enter workspace description (optional)"
          rows={3}
          className={errors.description ? "border-destructive" : ""}
        />
        {errors.description && (
          <p className="text-sm text-destructive">{errors.description}</p>
        )}
        <p className="text-xs text-muted-foreground">
          {formData.description.length}/1000 characters
        </p>
      </div>

      {workspace && (
        <div className="flex items-center space-x-2">
          <Checkbox
            id="workspace-active"
            checked={formData.is_active}
            onCheckedChange={(checked) =>
              handleInputChange("is_active", checked === true)
            }
          />
          <Label htmlFor="workspace-active">Active workspace</Label>
        </div>
      )}

      <div className="flex justify-end space-x-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
              {workspace ? "Updating..." : "Creating..."}
            </>
          ) : workspace ? (
            "Update Workspace"
          ) : (
            "Create Workspace"
          )}
        </Button>
      </div>
    </form>
  );
}

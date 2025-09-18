import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import IconComponent from "@/components/common/genericIconComponent";
import LoadingComponent from "@/components/common/loadingComponent";
import {
  useGetPermissions,
  type Role,
  type Workspace,
  type Permission,
} from "@/controllers/API/queries/rbac";

interface RoleFormProps {
  role?: Role | null;
  workspaces: Workspace[];
  onSubmit: (data: {
    name: string;
    description?: string;
    permissions: string[];
    workspace_id: string;
    is_active?: boolean;
  }) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function RoleForm({
  role,
  workspaces,
  onSubmit,
  onCancel,
  isLoading = false,
}: RoleFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    workspace_id: "",
    is_active: true,
  });
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [availablePermissions, setAvailablePermissions] = useState<Permission[]>([]);
  const [permissionFilter, setPermissionFilter] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { mutate: getPermissions, isPending: isLoadingPermissions } = useGetPermissions();

  useEffect(() => {
    loadPermissions();
  }, []);

  useEffect(() => {
    if (role) {
      setFormData({
        name: role.name,
        description: role.description || "",
        workspace_id: role.workspace_id,
        is_active: role.is_active,
      });
      setSelectedPermissions(role.permissions);
    } else {
      setFormData({
        name: "",
        description: "",
        workspace_id: workspaces[0]?.id || "",
        is_active: true,
      });
      setSelectedPermissions([]);
    }
    setErrors({});
  }, [role, workspaces]);

  const loadPermissions = () => {
    getPermissions(
      { limit: 1000 },
      {
        onSuccess: (data) => {
          setAvailablePermissions(data.permissions);
        },
        onError: () => {
          setAvailablePermissions([]);
        },
      }
    );
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "Role name is required";
    }

    if (!formData.workspace_id) {
      newErrors.workspace_id = "Workspace is required";
    }

    if (selectedPermissions.length === 0) {
      newErrors.permissions = "At least one permission is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const submitData: any = {
      name: formData.name.trim(),
      workspace_id: formData.workspace_id,
      permissions: selectedPermissions,
    };

    if (formData.description.trim()) {
      submitData.description = formData.description.trim();
    }

    if (role) {
      submitData.is_active = formData.is_active;
    }

    onSubmit(submitData);
  };

  const togglePermission = (permissionCode: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(permissionCode)
        ? prev.filter((p) => p !== permissionCode)
        : [...prev, permissionCode]
    );

    if (errors.permissions) {
      setErrors((prev) => ({ ...prev, permissions: "" }));
    }
  };

  const filteredPermissions = availablePermissions.filter(
    (permission) =>
      permission.name.toLowerCase().includes(permissionFilter.toLowerCase()) ||
      permission.code.toLowerCase().includes(permissionFilter.toLowerCase()) ||
      permission.resource_type.toLowerCase().includes(permissionFilter.toLowerCase())
  );

  const groupedPermissions = filteredPermissions.reduce((acc, permission) => {
    const resource = permission.resource_type;
    if (!acc[resource]) {
      acc[resource] = [];
    }
    acc[resource].push(permission);
    return acc;
  }, {} as Record<string, Permission[]>);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="role-name">
            Role Name <span className="text-destructive">*</span>
          </Label>
          <Input
            id="role-name"
            value={formData.name}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, name: e.target.value }))
            }
            placeholder="Enter role name"
            className={errors.name ? "border-destructive" : ""}
          />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="workspace">
            Workspace <span className="text-destructive">*</span>
          </Label>
          <Select
            value={formData.workspace_id}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, workspace_id: value }))
            }
          >
            <SelectTrigger className={errors.workspace_id ? "border-destructive" : ""}>
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
          {errors.workspace_id && (
            <p className="text-sm text-destructive">{errors.workspace_id}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="role-description">Description</Label>
        <Textarea
          id="role-description"
          value={formData.description}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, description: e.target.value }))
          }
          placeholder="Enter role description (optional)"
          rows={3}
        />
      </div>

      {role && (
        <div className="flex items-center space-x-2">
          <Checkbox
            id="role-active"
            checked={formData.is_active}
            onCheckedChange={(checked) =>
              setFormData((prev) => ({ ...prev, is_active: checked === true }))
            }
          />
          <Label htmlFor="role-active">Active role</Label>
        </div>
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Label>
            Permissions <span className="text-destructive">*</span>
          </Label>
          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
            <span>{selectedPermissions.length} selected</span>
          </div>
        </div>

        <Input
          placeholder="Filter permissions..."
          value={permissionFilter}
          onChange={(e) => setPermissionFilter(e.target.value)}
          className="w-full"
        />

        {errors.permissions && (
          <p className="text-sm text-destructive">{errors.permissions}</p>
        )}

        <div className="border rounded-lg max-h-96 overflow-auto">
          {isLoadingPermissions ? (
            <div className="flex items-center justify-center p-8">
              <LoadingComponent />
            </div>
          ) : (
            <div className="p-4 space-y-4">
              {Object.entries(groupedPermissions).map(([resource, permissions]) => (
                <div key={resource} className="space-y-2">
                  <h4 className="font-medium text-sm uppercase tracking-wide text-muted-foreground">
                    {resource}
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    {permissions.map((permission) => (
                      <div
                        key={permission.code}
                        className="flex items-start space-x-2 p-2 rounded-md hover:bg-muted/50"
                      >
                        <Checkbox
                          checked={selectedPermissions.includes(permission.code)}
                          onCheckedChange={() => togglePermission(permission.code)}
                          className="mt-0.5"
                        />
                        <div className="flex-1 space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-medium">{permission.name}</span>
                            {permission.is_dangerous && (
                              <Badge variant="destructive" className="text-xs">
                                Dangerous
                              </Badge>
                            )}
                            {permission.requires_mfa && (
                              <Badge variant="outline" className="text-xs">
                                MFA
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {permission.description || permission.code}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
              {role ? "Updating..." : "Creating..."}
            </>
          ) : (
            role ? "Update Role" : "Create Role"
          )}
        </Button>
      </div>
    </form>
  );
}
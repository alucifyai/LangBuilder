import { format } from "date-fns";
import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useGetUsers } from "@/controllers/API/queries/auth";
import {
  type Role,
  type RoleAssignment,
  useGetEnvironments,
  useGetProjects,
  type Workspace,
} from "@/controllers/API/queries/rbac";
import { cn } from "@/lib/utils";

interface RoleAssignmentFormProps {
  assignment?: RoleAssignment | null;
  workspaces: Workspace[];
  roles: Role[];
  onSubmit: (data: any) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export default function RoleAssignmentForm({
  assignment,
  workspaces,
  roles,
  onSubmit,
  onCancel,
  isLoading,
}: RoleAssignmentFormProps) {
  const [formData, setFormData] = useState({
    role_id: assignment?.role_id || "",
    principal_type:
      assignment?.principal_type || ("user" as "user" | "service_account"),
    principal_id: assignment?.principal_id || "",
    scope_type:
      assignment?.scope_type ||
      ("global" as "global" | "workspace" | "project" | "environment"),
    scope_id: assignment?.scope_id || "",
    expires_at: assignment?.expires_at
      ? new Date(assignment.expires_at)
      : (undefined as Date | undefined),
    is_active: assignment?.is_active ?? true,
  });

  const [users, setUsers] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [environments, setEnvironments] = useState<any[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { mutate: getUsers } = useGetUsers();
  const { mutate: getProjects } = useGetProjects();
  const { mutate: getEnvironments } = useGetEnvironments();

  useEffect(() => {
    loadUsers();
  }, []);

  useEffect(() => {
    if (formData.scope_type === "project" && formData.scope_id) {
      loadProjects();
    }
  }, [formData.scope_type]);

  useEffect(() => {
    if (formData.scope_type === "environment" && projects.length > 0) {
      loadEnvironments();
    }
  }, [formData.scope_type, projects]);

  const loadUsers = () => {
    getUsers(
      { limit: 100 },
      {
        onSuccess: (data) => {
          setUsers(data.users || []);
        },
        onError: () => {
          setUsers([]);
        },
      },
    );
  };

  const loadProjects = () => {
    if (formData.scope_id) {
      getProjects(
        { workspace_id: formData.scope_id, limit: 100 },
        {
          onSuccess: (data) => {
            setProjects(data.projects || []);
          },
          onError: () => {
            setProjects([]);
          },
        },
      );
    }
  };

  const loadEnvironments = () => {
    getEnvironments(
      { limit: 100 },
      {
        onSuccess: (data) => {
          setEnvironments(data.environments || []);
        },
        onError: () => {
          setEnvironments([]);
        },
      },
    );
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.role_id) {
      newErrors.role_id = "Role is required";
    }

    if (!formData.principal_id) {
      newErrors.principal_id = "Principal is required";
    }

    if (formData.scope_type !== "global" && !formData.scope_id) {
      newErrors.scope_id = "Scope is required for non-global assignments";
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
      role_id: formData.role_id,
      principal_type: formData.principal_type,
      principal_id: formData.principal_id,
      scope_type: formData.scope_type,
    };

    if (formData.scope_type !== "global") {
      submitData.scope_id = formData.scope_id;
    }

    if (formData.expires_at) {
      submitData.expires_at = formData.expires_at.toISOString();
    }

    if (assignment) {
      submitData.is_active = formData.is_active;
    }

    onSubmit(submitData);
  };

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: value };

      if (field === "scope_type") {
        updated.scope_id = "";
      }

      return updated;
    });

    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  const getScopeOptions = () => {
    switch (formData.scope_type) {
      case "workspace":
        return workspaces.map((w) => ({ id: w.id, name: w.name }));
      case "project":
        return projects.map((p) => ({ id: p.id, name: p.name }));
      case "environment":
        return environments.map((e) => ({ id: e.id, name: e.name }));
      default:
        return [];
    }
  };

  const getPrincipalOptions = () => {
    if (formData.principal_type === "user") {
      return users.map((u) => ({ id: u.id, name: u.username || u.email }));
    }
    return [];
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="principal_type">Principal Type</Label>
          <Select
            value={formData.principal_type}
            onValueChange={(value) => updateFormData("principal_type", value)}
            disabled={!!assignment}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user">User</SelectItem>
              <SelectItem value="service_account">Service Account</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="principal_id">Principal</Label>
          <Select
            value={formData.principal_id}
            onValueChange={(value) => updateFormData("principal_id", value)}
            disabled={!!assignment}
          >
            <SelectTrigger
              className={errors.principal_id ? "border-destructive" : ""}
            >
              <SelectValue placeholder="Select principal" />
            </SelectTrigger>
            <SelectContent>
              {getPrincipalOptions().map((option) => (
                <SelectItem key={option.id} value={option.id}>
                  {option.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.principal_id && (
            <p className="text-sm text-destructive">{errors.principal_id}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="role_id">Role</Label>
        <Select
          value={formData.role_id}
          onValueChange={(value) => updateFormData("role_id", value)}
          disabled={!!assignment}
        >
          <SelectTrigger className={errors.role_id ? "border-destructive" : ""}>
            <SelectValue placeholder="Select role" />
          </SelectTrigger>
          <SelectContent>
            {roles.map((role) => (
              <SelectItem key={role.id} value={role.id}>
                <div className="flex items-center space-x-2">
                  <span>{role.name}</span>
                  {role.description && (
                    <span className="text-xs text-muted-foreground">
                      - {role.description}
                    </span>
                  )}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.role_id && (
          <p className="text-sm text-destructive">{errors.role_id}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="scope_type">Scope Type</Label>
          <Select
            value={formData.scope_type}
            onValueChange={(value) => updateFormData("scope_type", value)}
            disabled={!!assignment}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="global">Global</SelectItem>
              <SelectItem value="workspace">Workspace</SelectItem>
              <SelectItem value="project">Project</SelectItem>
              <SelectItem value="environment">Environment</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {formData.scope_type !== "global" && (
          <div className="space-y-2">
            <Label htmlFor="scope_id">Scope</Label>
            <Select
              value={formData.scope_id}
              onValueChange={(value) => updateFormData("scope_id", value)}
              disabled={!!assignment}
            >
              <SelectTrigger
                className={errors.scope_id ? "border-destructive" : ""}
              >
                <SelectValue placeholder={`Select ${formData.scope_type}`} />
              </SelectTrigger>
              <SelectContent>
                {getScopeOptions().map((option) => (
                  <SelectItem key={option.id} value={option.id}>
                    {option.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.scope_id && (
              <p className="text-sm text-destructive">{errors.scope_id}</p>
            )}
          </div>
        )}
      </div>

      <div className="space-y-2">
        <Label>Expiration Date (Optional)</Label>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                "justify-start text-left font-normal",
                !formData.expires_at && "text-muted-foreground",
              )}
            >
              <IconComponent name="Calendar" className="mr-2 h-4 w-4" />
              {formData.expires_at ? (
                format(formData.expires_at, "PPP")
              ) : (
                <span>No expiration</span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              mode="single"
              selected={formData.expires_at}
              onSelect={(date) => updateFormData("expires_at", date)}
              disabled={(date) => date < new Date()}
              initialFocus
            />
            <div className="p-3 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => updateFormData("expires_at", undefined)}
              >
                Clear expiration
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      </div>

      {assignment && (
        <div className="flex items-center space-x-2">
          <Checkbox
            id="is_active"
            checked={formData.is_active}
            onCheckedChange={(checked) => updateFormData("is_active", checked)}
          />
          <Label htmlFor="is_active">Active assignment</Label>
        </div>
      )}

      <div className="flex justify-end space-x-2 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isLoading}>
          {isLoading ? (
            <>
              <IconComponent
                name="Loader2"
                className="mr-2 h-4 w-4 animate-spin"
              />
              {assignment ? "Updating..." : "Creating..."}
            </>
          ) : assignment ? (
            "Update Assignment"
          ) : (
            "Create Assignment"
          )}
        </Button>
      </div>
    </form>
  );
}

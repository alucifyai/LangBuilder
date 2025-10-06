/**
 * AssignRoleModal Component
 *
 * Modal for assigning a role to a principal within a scope.
 * Features:
 * - Principal type and ID input
 * - Role selector
 * - Scope type and ID input
 * - Optional expiration date
 * - Validation and error handling
 */

import { useState } from "react";
import { X } from "lucide-react";
import { createGrant } from "../../controllers/API/grants";
import { listRoles } from "../../controllers/API/roles";
import { useGetUsers } from "../../controllers/API/queries/auth";
import type { GrantFormData, PrincipalType, ScopeType } from "../../types/grant";
import { useEffect } from "react";

interface AssignRoleModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

const PRINCIPAL_TYPES = [
  { value: "user", label: "User" },
  { value: "group", label: "Group" },
  { value: "service_account", label: "Service Account" },
];

const SCOPE_TYPES = [
  { value: "workspace", label: "Workspace" },
  { value: "project", label: "Project" },
  { value: "environment", label: "Environment" },
  { value: "flow", label: "Flow" },
  { value: "component", label: "Component" },
];

export function AssignRoleModal({ onClose, onSuccess }: AssignRoleModalProps) {
  const [formData, setFormData] = useState<GrantFormData>({
    principal_type: "user" as PrincipalType,
    principal_id: "",
    role_id: "",
    scope_type: "workspace" as ScopeType,
    scope_id: "",
    expires_at: null,
  });
  const [roles, setRoles] = useState<Array<{ id: string; name: string }>>([]);
  const [users, setUsers] = useState<Array<{ id: string; username: string }>>([]);
  const [errors, setErrors] = useState<{
    principal_id?: string;
    role_id?: string;
    scope_id?: string;
  }>({});
  const [submitting, setSubmitting] = useState(false);

  // Fetch roles
  useEffect(() => {
    const fetchRoles = async () => {
      try {
        const response = await listRoles();
        setRoles(response.roles);
      } catch (err) {
        console.error("Failed to fetch roles:", err);
      }
    };
    fetchRoles();
  }, []);

  // Fetch users using existing hook
  const { mutate: mutateGetUsers } = useGetUsers({});

  useEffect(() => {
    if (formData.principal_type === "user") {
      mutateGetUsers(
        { skip: 0, limit: 100 },
        {
          onSuccess: (data) => {
            setUsers(data.users);
          },
          onError: (err) => {
            console.error("Failed to fetch users:", err);
          },
        }
      );
    }
  }, [formData.principal_type]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: typeof errors = {};
    if (!formData.principal_id.trim()) {
      newErrors.principal_id = "Principal ID is required";
    }
    if (!formData.role_id) {
      newErrors.role_id = "Role is required";
    }
    if (!formData.scope_id.trim()) {
      newErrors.scope_id = "Scope ID is required";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setSubmitting(true);
      setErrors({});

      await createGrant({
        principal_type: formData.principal_type,
        principal_id: formData.principal_id.trim(),
        role_id: formData.role_id,
        scope_type: formData.scope_type,
        scope_id: formData.scope_id.trim(),
        expires_at: formData.expires_at,
      });

      onSuccess();
    } catch (err: any) {
      if (err.message.includes("role")) {
        setErrors({ role_id: err.message });
      } else if (err.message.includes("user")) {
        setErrors({ principal_id: err.message });
      } else {
        setErrors({ principal_id: err.message || "Failed to assign role" });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-background border rounded-lg shadow-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold">Assign Role</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-accent rounded-md"
            disabled={submitting}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Principal section */}
          <div className="space-y-3">
            <h4 className="font-medium">Principal (Who)</h4>

            <div className="grid grid-cols-2 gap-3">
              {/* Principal Type */}
              <div>
                <label htmlFor="principal-type" className="block text-sm font-medium mb-2">
                  Principal Type *
                </label>
                <select
                  id="principal-type"
                  value={formData.principal_type}
                  onChange={(e) =>
                    setFormData({ ...formData, principal_type: e.target.value as PrincipalType, principal_id: "" })
                  }
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={submitting}
                >
                  {PRINCIPAL_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Principal ID */}
              <div>
                <label htmlFor="principal-id" className="block text-sm font-medium mb-2">
                  {formData.principal_type === "user" ? "User *" : "Principal ID *"}
                </label>
                {formData.principal_type === "user" ? (
                  <select
                    id="principal-id"
                    value={formData.principal_id}
                    onChange={(e) => setFormData({ ...formData, principal_id: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    disabled={submitting}
                  >
                    <option value="">Select user</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.username}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    id="principal-id"
                    type="text"
                    value={formData.principal_id}
                    onChange={(e) => setFormData({ ...formData, principal_id: e.target.value })}
                    placeholder="Enter principal ID"
                    className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    disabled={submitting}
                  />
                )}
                {errors.principal_id && (
                  <p className="mt-1 text-sm text-destructive">{errors.principal_id}</p>
                )}
              </div>
            </div>
          </div>

          {/* Role section */}
          <div>
            <h4 className="font-medium mb-3">Role (What)</h4>
            <label htmlFor="role" className="block text-sm font-medium mb-2">
              Role *
            </label>
            <select
              id="role"
              value={formData.role_id}
              onChange={(e) => setFormData({ ...formData, role_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={submitting}
            >
              <option value="">Select role</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
            {errors.role_id && <p className="mt-1 text-sm text-destructive">{errors.role_id}</p>}
          </div>

          {/* Scope section */}
          <div className="space-y-3">
            <h4 className="font-medium">Scope (Where)</h4>

            <div className="grid grid-cols-2 gap-3">
              {/* Scope Type */}
              <div>
                <label htmlFor="scope-type" className="block text-sm font-medium mb-2">
                  Scope Type *
                </label>
                <select
                  id="scope-type"
                  value={formData.scope_type}
                  onChange={(e) =>
                    setFormData({ ...formData, scope_type: e.target.value as ScopeType })
                  }
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={submitting}
                >
                  {SCOPE_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Scope ID */}
              <div>
                <label htmlFor="scope-id" className="block text-sm font-medium mb-2">
                  Scope ID *
                </label>
                <input
                  id="scope-id"
                  type="text"
                  value={formData.scope_id}
                  onChange={(e) => setFormData({ ...formData, scope_id: e.target.value })}
                  placeholder="e.g., workspace-123"
                  className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  disabled={submitting}
                />
                {errors.scope_id && (
                  <p className="mt-1 text-sm text-destructive">{errors.scope_id}</p>
                )}
              </div>
            </div>
          </div>

          {/* Expiration */}
          <div>
            <h4 className="font-medium mb-3">Expiration (Optional)</h4>
            <label htmlFor="expires-at" className="block text-sm font-medium mb-2">
              Expires At
            </label>
            <input
              id="expires-at"
              type="datetime-local"
              value={formData.expires_at || ""}
              onChange={(e) => setFormData({ ...formData, expires_at: e.target.value || null })}
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={submitting}
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Leave empty for permanent grant
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 border rounded-md hover:bg-accent disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? "Assigning..." : "Assign Role"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

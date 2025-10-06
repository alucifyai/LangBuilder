/**
 * CreateRoleModal Component
 *
 * Modal for creating a new role.
 * Features:
 * - Form with role name input and permission multi-select
 * - Validation (required name, at least one permission recommended)
 * - Error handling for duplicate names
 */

import { useState } from "react";
import { X } from "lucide-react";
import { createRole } from "../../controllers/API/roles";
import type { RoleFormData } from "../../types/role";
import { PermissionMultiSelect } from "./PermissionMultiSelect";

interface CreateRoleModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export function CreateRoleModal({ onClose, onSuccess }: CreateRoleModalProps) {
  const [formData, setFormData] = useState<RoleFormData>({
    name: "",
    permissions: [],
  });
  const [errors, setErrors] = useState<{ name?: string; permissions?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: typeof errors = {};
    if (!formData.name.trim()) {
      newErrors.name = "Role name is required";
    }
    if (formData.permissions.length === 0) {
      newErrors.permissions = "Select at least one permission";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      setSubmitting(true);
      setErrors({});
      await createRole({
        name: formData.name.trim(),
        permissions: formData.permissions,
      });
      onSuccess();
    } catch (err: any) {
      if (err.message.includes("unique")) {
        setErrors({ name: "Role name must be unique" });
      } else if (err.message.includes("permission")) {
        setErrors({ permissions: err.message });
      } else {
        setErrors({ name: err.message || "Failed to create role" });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-background border rounded-lg shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h3 className="text-lg font-semibold">Create New Role</h3>
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
          {/* Role name */}
          <div>
            <label htmlFor="role-name" className="block text-sm font-medium mb-2">
              Role Name *
            </label>
            <input
              id="role-name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Deployer, Editor"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              disabled={submitting}
            />
            {errors.name && <p className="mt-1 text-sm text-destructive">{errors.name}</p>}
          </div>

          {/* Permissions */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Permissions *
            </label>
            <PermissionMultiSelect
              value={formData.permissions}
              onChange={(permissions) => setFormData({ ...formData, permissions })}
              error={errors.permissions}
            />
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
              {submitting ? "Creating..." : "Create Role"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

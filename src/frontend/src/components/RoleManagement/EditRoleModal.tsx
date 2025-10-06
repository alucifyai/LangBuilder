/**
 * EditRoleModal Component
 *
 * Modal for editing an existing role.
 * Features:
 * - Pre-populated form with current role data
 * - Shows current version number
 * - Updates version on successful save
 * - Error handling for duplicate names
 */

import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { updateRole } from "../../controllers/API/roles";
import type { Role, RoleFormData } from "../../types/role";
import { PermissionMultiSelect } from "./PermissionMultiSelect";

interface EditRoleModalProps {
  role: Role;
  onClose: () => void;
  onSuccess: () => void;
}

export function EditRoleModal({ role, onClose, onSuccess }: EditRoleModalProps) {
  const [formData, setFormData] = useState<RoleFormData>({
    name: role.name,
    permissions: role.permissions,
  });
  const [errors, setErrors] = useState<{ name?: string; permissions?: string }>({});
  const [submitting, setSubmitting] = useState(false);

  const hasChanges =
    formData.name !== role.name ||
    JSON.stringify([...formData.permissions].sort()) !==
      JSON.stringify([...role.permissions].sort());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!hasChanges) {
      onClose();
      return;
    }

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

      const updateData: { name?: string; permissions?: string[] } = {};
      if (formData.name !== role.name) {
        updateData.name = formData.name.trim();
      }
      if (JSON.stringify([...formData.permissions].sort()) !== JSON.stringify([...role.permissions].sort())) {
        updateData.permissions = formData.permissions;
      }

      await updateRole(role.id, updateData);
      onSuccess();
    } catch (err: any) {
      if (err.message.includes("unique")) {
        setErrors({ name: "Role name must be unique" });
      } else if (err.message.includes("permission")) {
        setErrors({ permissions: err.message });
      } else {
        setErrors({ name: err.message || "Failed to update role" });
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
          <div>
            <h3 className="text-lg font-semibold">Edit Role</h3>
            <p className="text-sm text-muted-foreground">Version {role.version}</p>
          </div>
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
            <label htmlFor="role-name-edit" className="block text-sm font-medium mb-2">
              Role Name *
            </label>
            <input
              id="role-name-edit"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
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

          {hasChanges && (
            <p className="text-sm text-muted-foreground">
              Version will increment to <strong>v{role.version + 1}</strong> when saved
            </p>
          )}

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
              disabled={submitting || !hasChanges}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

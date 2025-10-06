/**
 * RoleListView Component
 *
 * Displays list of roles in a table with CRUD actions.
 * Features:
 * - Table view with name, permissions count, version, created date
 * - Edit and Delete actions per role
 * - Create Role button
 * - Loading and error states
 */

import { useState, useEffect } from "react";
import { Edit, Trash2, Plus } from "lucide-react";
import type { Role } from "../../types/role";
import { listRoles, deleteRole } from "../../controllers/API/roles";
import { CreateRoleModal } from "./CreateRoleModal";
import { EditRoleModal } from "./EditRoleModal";
import { DeleteRoleDialog } from "./DeleteRoleDialog";

export function RoleListView() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [deletingRole, setDeletingRole] = useState<Role | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch roles on mount
  const fetchRoles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await listRoles();
      setRoles(response.roles);
    } catch (err: any) {
      setError(err.message || "Failed to load roles");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  // Handle role deletion
  const handleDeleteConfirm = async () => {
    if (!deletingRole) return;

    try {
      setIsDeleting(true);
      await deleteRole(deletingRole.id);
      setDeletingRole(null);
      await fetchRoles(); // Refresh list
    } catch (err: any) {
      alert(err.message || "Failed to delete role");
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading roles...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-destructive">{error}</p>
        <button
          onClick={fetchRoles}
          className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Role Management</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" />
          Create Role
        </button>
      </div>

      {/* Roles table */}
      <div className="border rounded-md">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Permissions
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Version
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium">
                Created
              </th>
              <th className="px-4 py-3 text-right text-sm font-medium">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {roles.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                  No roles found. Create your first role to get started.
                </td>
              </tr>
            ) : (
              roles.map((role) => (
                <tr key={role.id} className="border-t hover:bg-muted/50">
                  <td className="px-4 py-3 font-medium">{role.name}</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {role.permissions.length} permission
                    {role.permissions.length !== 1 ? "s" : ""}
                  </td>
                  <td className="px-4 py-3 text-sm">v{role.version}</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {new Date(role.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditingRole(role)}
                        className="p-2 hover:bg-accent rounded-md"
                        title="Edit role"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => setDeletingRole(role)}
                        disabled={isDeleting}
                        className="p-2 hover:bg-destructive/10 hover:text-destructive rounded-md disabled:opacity-50"
                        title="Delete role"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateRoleModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchRoles();
          }}
        />
      )}

      {editingRole && (
        <EditRoleModal
          role={editingRole}
          onClose={() => setEditingRole(null)}
          onSuccess={() => {
            setEditingRole(null);
            fetchRoles();
          }}
        />
      )}

      {deletingRole && (
        <DeleteRoleDialog
          roleName={deletingRole.name}
          activeGrantsCount={0} // TODO: Fetch from API when grant count endpoint is available
          onConfirm={handleDeleteConfirm}
          onCancel={() => {
            setDeletingRole(null);
            setIsDeleting(false);
          }}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}

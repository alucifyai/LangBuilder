import { useEffect, useState } from "react";
import {
  type Permission,
  useGetPermissions,
} from "../../../../../controllers/API/queries/rbac/use-get-permissions";
import { useGetRolePermissions } from "../../../../../controllers/API/queries/rbac/use-get-role-permissions";
import { useUpdateRolePermissions } from "../../../../../controllers/API/queries/rbac/use-update-role-permissions";

interface PermissionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  role: {
    id: string;
    name: string;
    permissions?: string[];
  } | null;
  onSave: (roleId: string, permissions: string[]) => void;
}

export default function PermissionsModal({
  isOpen,
  onClose,
  role,
  onSave,
}: PermissionsModalProps) {
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState("");

  // Get all available permissions
  const {
    mutate: fetchPermissions,
    data: permissionsData,
    isPending: isLoadingPermissions,
  } = useGetPermissions({
    onSuccess: (data) => {
      console.log("Permissions fetched successfully:", data);
    },
    onError: (error) => {
      console.error("Failed to fetch permissions:", error);
    },
  });

  // Get role's current permissions
  const {
    mutate: fetchRolePermissions,
    data: rolePermissionsData,
    isPending: isLoadingRolePermissions,
  } = useGetRolePermissions({
    onSuccess: (data) => {
      console.log("Role permissions fetched successfully:", data);
      const permissionIds = data.map((permission) => permission.id);
      setSelectedPermissions(permissionIds);
    },
    onError: (error) => {
      console.error("Failed to fetch role permissions:", error);
    },
  });

  // Update role permissions
  const { mutate: updatePermissions, isPending: isUpdatingPermissions } =
    useUpdateRolePermissions({
      onSuccess: () => {
        console.log("Role permissions updated successfully");
        onSave(role!.id, selectedPermissions);
        onClose();
      },
      onError: (error) => {
        console.error("Failed to update role permissions:", error);
      },
    });

  console.log("PermissionsModal render - isOpen:", isOpen, "role:", role);

  // Handle escape key to close modal
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden"; // Prevent background scroll
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  // Fetch permissions when modal opens
  useEffect(() => {
    if (isOpen && role) {
      console.log(
        "Fetching permissions and role permissions for role:",
        role.id,
      );
      fetchPermissions({ limit: 1000 });
      fetchRolePermissions({ role_id: role.id });
    } else if (!isOpen) {
      setSelectedPermissions([]);
      setSearchTerm("");
    }
  }, [isOpen, role, fetchPermissions, fetchRolePermissions]);

  const handlePermissionToggle = (permissionId: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(permissionId)
        ? prev.filter((id) => id !== permissionId)
        : [...prev, permissionId],
    );
  };

  const handleSave = () => {
    if (role) {
      console.log(
        "Saving permissions for role:",
        role.id,
        "permissions:",
        selectedPermissions,
      );
      updatePermissions({
        role_id: role.id,
        permission_ids: selectedPermissions,
      });
    }
  };

  // Get permissions from backend data
  const allPermissions = permissionsData || [];

  const filteredPermissions = allPermissions.filter(
    (permission) =>
      permission.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (permission.description &&
        permission.description
          .toLowerCase()
          .includes(searchTerm.toLowerCase())) ||
      (permission.category &&
        permission.category.toLowerCase().includes(searchTerm.toLowerCase())),
  );

  const groupedPermissions = filteredPermissions.reduce(
    (groups, permission) => {
      const category =
        permission.category || permission.resource_type || "Other";
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(permission);
      return groups;
    },
    {} as Record<string, Permission[]>,
  );

  if (!isOpen || !role) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-4xl h-full max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex-shrink-0 p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Manage Permissions
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Role: <span className="font-medium">{role.name}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-3xl leading-none p-2 hover:bg-gray-100 rounded-full transition-colors"
              title="Close modal"
            >
              ×
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="flex-shrink-0 p-6 border-b border-gray-200">
          <input
            type="text"
            placeholder="Search permissions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Permissions List */}
        <div className="flex-1 overflow-y-auto p-6 min-h-0">
          {isLoadingPermissions || isLoadingRolePermissions ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">Loading permissions...</div>
            </div>
          ) : filteredPermissions.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-gray-500">No permissions available</div>
            </div>
          ) : (
            <div className="space-y-6">
              {Object.entries(groupedPermissions).map(
                ([category, permissions]) => (
                  <div key={category}>
                    <h3 className="text-lg font-medium text-gray-900 mb-3">
                      {category}
                    </h3>
                    <div className="space-y-2">
                      {permissions.map((permission) => (
                        <div
                          key={permission.id}
                          className="flex items-start space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                          onClick={() => handlePermissionToggle(permission.id)}
                        >
                          <input
                            type="checkbox"
                            id={permission.id}
                            checked={selectedPermissions.includes(
                              permission.id,
                            )}
                            onChange={(e) => e.stopPropagation()}
                            className="mt-1 h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                          />
                          <div className="flex-1">
                            <label
                              htmlFor={permission.id}
                              className="block text-sm font-medium text-gray-900 cursor-pointer"
                            >
                              {permission.name}
                            </label>
                            {permission.description && (
                              <p className="text-sm text-gray-600 mt-1">
                                {permission.description}
                              </p>
                            )}
                            <div className="flex items-center gap-2 mt-1">
                              <span className="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                                {permission.code || permission.id}
                              </span>
                              {permission.is_system && (
                                <span className="inline-block px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded">
                                  System
                                </span>
                              )}
                              {permission.is_dangerous && (
                                <span className="inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                                  Dangerous
                                </span>
                              )}
                              {permission.requires_mfa && (
                                <span className="inline-block px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded">
                                  MFA Required
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex-shrink-0 p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {selectedPermissions.length} permission
              {selectedPermissions.length !== 1 ? "s" : ""} selected
            </div>
            <div className="flex space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isUpdatingPermissions}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50"
              >
                {isUpdatingPermissions ? "Saving..." : "Save Permissions"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

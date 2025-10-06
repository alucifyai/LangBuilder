/**
 * PermissionMultiSelect Component
 *
 * Multi-select component for selecting permissions from the catalog.
 * Features:
 * - Fetches permissions from /api/v1/permissions/ endpoint
 * - Search/filter functionality
 * - Accessible multi-select with keyboard navigation
 * - Displays permission ID and description
 */

import { useEffect, useState } from "react";
import { Check, ChevronsUpDown, Search, X } from "lucide-react";
import { cn } from "@/utils/utils";
import type { Permission } from "../../types/role";
import { api } from "../../controllers/API/api";
import { BASE_URL_API } from "../../constants/constants";

interface PermissionMultiSelectProps {
  value: string[]; // Selected permission IDs
  onChange: (value: string[]) => void;
  className?: string;
  error?: string;
}

export function PermissionMultiSelect({
  value,
  onChange,
  className,
  error,
}: PermissionMultiSelectProps) {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  // Fetch permissions from catalog
  useEffect(() => {
    const fetchPermissions = async () => {
      try {
        setLoading(true);
        const response = await api.get(`${BASE_URL_API}permissions/`);
        setPermissions(response.data.permissions || []);
      } catch (err) {
        console.error("Failed to fetch permissions:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPermissions();
  }, []);

  // Filter permissions based on search query
  const filteredPermissions = permissions.filter(
    (perm) =>
      perm.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      perm.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Toggle permission selection
  const togglePermission = (permissionId: string) => {
    if (value.includes(permissionId)) {
      onChange(value.filter((id) => id !== permissionId));
    } else {
      onChange([...value, permissionId]);
    }
  };

  // Remove permission from selection
  const removePermission = (permissionId: string) => {
    onChange(value.filter((id) => id !== permissionId));
  };

  // Get permission details for selected IDs
  const selectedPermissions = permissions.filter((perm) =>
    value.includes(perm.id)
  );

  return (
    <div className={cn("space-y-2", className)}>
      {/* Selected permissions badges */}
      {selectedPermissions.length > 0 && (
        <div className="flex flex-wrap gap-2 p-2 border rounded-md bg-muted/50">
          {selectedPermissions.map((perm) => (
            <span
              key={perm.id}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-primary/10 text-primary rounded-md"
            >
              {perm.id}
              <button
                type="button"
                onClick={() => removePermission(perm.id)}
                className="hover:text-destructive"
                aria-label={`Remove ${perm.id}`}
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Dropdown trigger */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          className={cn(
            "w-full flex items-center justify-between px-3 py-2 text-sm border rounded-md bg-background",
            "hover:bg-accent hover:text-accent-foreground",
            "focus:outline-none focus:ring-2 focus:ring-ring",
            error && "border-destructive"
          )}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
        >
          <span className="text-muted-foreground">
            {value.length > 0
              ? `${value.length} permission${value.length !== 1 ? "s" : ""} selected`
              : "Select permissions..."}
          </span>
          <ChevronsUpDown className="h-4 w-4 opacity-50" />
        </button>

        {/* Dropdown content */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-md">
            {/* Search input */}
            <div className="p-2 border-b">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search permissions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-2 py-2 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>

            {/* Permission list */}
            <div className="max-h-64 overflow-y-auto p-1">
              {loading ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  Loading permissions...
                </div>
              ) : filteredPermissions.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  No permissions found
                </div>
              ) : (
                filteredPermissions.map((perm) => {
                  const isSelected = value.includes(perm.id);
                  return (
                    <button
                      key={perm.id}
                      type="button"
                      onClick={() => togglePermission(perm.id)}
                      className={cn(
                        "w-full flex items-start gap-2 px-3 py-2 text-sm rounded-md",
                        "hover:bg-accent hover:text-accent-foreground",
                        "text-left",
                        isSelected && "bg-accent"
                      )}
                      role="option"
                      aria-selected={isSelected}
                    >
                      <div
                        className={cn(
                          "flex h-5 w-5 items-center justify-center rounded-sm border",
                          isSelected
                            ? "bg-primary text-primary-foreground border-primary"
                            : "border-muted-foreground"
                        )}
                      >
                        {isSelected && <Check className="h-4 w-4" />}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium">{perm.id}</div>
                        <div className="text-xs text-muted-foreground">
                          {perm.description}
                        </div>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Click outside to close */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  );
}

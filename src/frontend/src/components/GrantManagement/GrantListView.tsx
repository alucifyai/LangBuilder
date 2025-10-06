/**
 * GrantListView Component
 *
 * Displays list of grants (role assignments) with filtering.
 * Features:
 * - Table view with principal, role, scope, expiration
 * - Filter by principal, role, scope
 * - Assign and revoke actions
 * - Loading and error states
 */

import { useState, useEffect } from "react";
import { Plus, X, Filter } from "lucide-react";
import type { Grant, GrantFilters, PrincipalType, ScopeType } from "../../types/grant";
import { listGrants, revokeGrant } from "../../controllers/API/grants";
import { listRoles } from "../../controllers/API/roles";
import type { Role } from "../../types/role";
import { AssignRoleModal } from "./AssignRoleModal";
import { RevokeGrantDialog } from "./RevokeGrantDialog";

const PRINCIPAL_TYPE_LABELS = {
  user: "User",
  group: "Group",
  service_account: "Service Account",
};

const SCOPE_TYPE_LABELS = {
  workspace: "Workspace",
  project: "Project",
  environment: "Environment",
  flow: "Flow",
  component: "Component",
};

export function GrantListView() {
  const [grants, setGrants] = useState<Grant[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [revokingGrant, setRevokingGrant] = useState<Grant | null>(null);
  const [isRevoking, setIsRevoking] = useState(false);

  // Filter state
  const [filters, setFilters] = useState<GrantFilters>({});
  const [showFilters, setShowFilters] = useState(false);

  // Fetch grants and roles
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [grantsResponse, rolesResponse] = await Promise.all([
        listGrants(filters),
        listRoles(),
      ]);
      setGrants(grantsResponse.grants);
      setRoles(rolesResponse.roles);
    } catch (err: any) {
      setError(err.message || "Failed to load grants");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filters]);

  // Get role name by ID
  const getRoleName = (roleId: string) => {
    const role = roles.find((r) => r.id === roleId);
    return role?.name || roleId;
  };

  // Handle grant revocation
  const handleRevokeConfirm = async () => {
    if (!revokingGrant) return;

    try {
      setIsRevoking(true);
      await revokeGrant(revokingGrant.id);
      setRevokingGrant(null);
      await fetchData(); // Refresh list
    } catch (err: any) {
      alert(err.message || "Failed to revoke grant");
      setIsRevoking(false);
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString();
  };

  // Check if grant is expired
  const isExpired = (grant: Grant) => {
    if (!grant.expires_at) return false;
    return new Date(grant.expires_at) < new Date();
  };

  // Clear filters
  const clearFilters = () => {
    setFilters({});
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading grants...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <p className="text-destructive">{error}</p>
        <button
          onClick={fetchData}
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
        <h2 className="text-2xl font-bold">Grant Management</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-3 py-2 border rounded-md hover:bg-accent"
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button
            onClick={() => setShowAssignModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            Assign Role
          </button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <div className="p-4 border rounded-md bg-muted/50 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Principal Type filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Principal Type</label>
              <select
                value={filters.principal_type || ""}
                onChange={(e) =>
                  setFilters({ ...filters, principal_type: e.target.value as PrincipalType || undefined })
                }
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All types</option>
                <option value="user">User</option>
                <option value="group">Group</option>
                <option value="service_account">Service Account</option>
              </select>
            </div>

            {/* Scope Type filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Scope Type</label>
              <select
                value={filters.scope_type || ""}
                onChange={(e) =>
                  setFilters({ ...filters, scope_type: e.target.value as ScopeType || undefined })
                }
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All scopes</option>
                <option value="workspace">Workspace</option>
                <option value="project">Project</option>
                <option value="environment">Environment</option>
                <option value="flow">Flow</option>
                <option value="component">Component</option>
              </select>
            </div>

            {/* Role filter */}
            <div>
              <label className="block text-sm font-medium mb-1">Role</label>
              <select
                value={filters.role_id || ""}
                onChange={(e) =>
                  setFilters({ ...filters, role_id: e.target.value || undefined })
                }
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">All roles</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={clearFilters}
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            Clear all filters
          </button>
        </div>
      )}

      {/* Grants table */}
      <div className="border rounded-md">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium">Principal</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Role</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Scope</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Created</th>
              <th className="px-4 py-3 text-left text-sm font-medium">Expires</th>
              <th className="px-4 py-3 text-right text-sm font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {grants.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No grants found. Assign a role to get started.
                </td>
              </tr>
            ) : (
              grants.map((grant) => (
                <tr
                  key={grant.id}
                  className={`border-t hover:bg-muted/50 ${
                    isExpired(grant) ? "opacity-50" : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    <div>
                      <div className="font-medium text-sm">
                        {PRINCIPAL_TYPE_LABELS[grant.principal_type]}
                      </div>
                      <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                        {grant.principal_id}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-medium">{getRoleName(grant.role_id)}</td>
                  <td className="px-4 py-3">
                    <div>
                      <div className="font-medium text-sm">
                        {SCOPE_TYPE_LABELS[grant.scope_type]}
                      </div>
                      <div className="text-xs text-muted-foreground truncate max-w-[150px]">
                        {grant.scope_id}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {formatTimestamp(grant.created_at)}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {grant.expires_at ? (
                      <span className={isExpired(grant) ? "text-destructive" : ""}>
                        {formatTimestamp(grant.expires_at)}
                        {isExpired(grant) && " (Expired)"}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">Never</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setRevokingGrant(grant)}
                      disabled={isRevoking}
                      className="p-2 hover:bg-destructive/10 hover:text-destructive rounded-md disabled:opacity-50"
                      title="Revoke grant"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modals */}
      {showAssignModal && (
        <AssignRoleModal
          onClose={() => setShowAssignModal(false)}
          onSuccess={() => {
            setShowAssignModal(false);
            fetchData();
          }}
        />
      )}

      {revokingGrant && (
        <RevokeGrantDialog
          grant={revokingGrant}
          roleName={getRoleName(revokingGrant.role_id)}
          onConfirm={handleRevokeConfirm}
          onCancel={() => {
            setRevokingGrant(null);
            setIsRevoking(false);
          }}
          isRevoking={isRevoking}
        />
      )}
    </div>
  );
}

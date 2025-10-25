import { useQuery } from "@tanstack/react-query";
import { useContext } from "react";
import { AuthContext } from "../contexts/authContext";
import { api } from "../controllers/API/api";

export type PermissionAction = "create" | "read" | "update" | "delete";
export type PermissionScope = "flow" | "project";

export interface PermissionCheckParams {
  action: PermissionAction;
  scope: PermissionScope;
  scopeId?: string;
}

export interface PermissionCheckResponse {
  authorized: boolean;
  reason?: string;
}

/**
 * Custom hook for checking RBAC permissions
 *
 * @param action - The permission action to check (create, read, update, delete)
 * @param scope - The permission scope (flow, project)
 * @param scopeId - Optional ID of the specific resource
 * @returns Object with hasPermission boolean and isLoading state
 *
 * @example
 * const { hasPermission, isLoading } = usePermission("delete", "flow", flowId);
 *
 * if (!hasPermission) {
 *   return <div>Access Denied</div>;
 * }
 */
export function usePermission(
  action: PermissionAction,
  scope: PermissionScope,
  scopeId?: string,
) {
  const { userData } = useContext(AuthContext);

  const { data, isLoading, error } = useQuery<PermissionCheckResponse>({
    queryKey: ["permission", action, scope, scopeId, userData?.id],
    queryFn: async () => {
      const params = new URLSearchParams({
        action,
        scope,
      });

      if (scopeId) {
        params.append("scope_id", scopeId);
      }

      const response = await api.get<PermissionCheckResponse>(
        `/api/v1/rbac/check-permission?${params.toString()}`,
      );
      return response.data;
    },
    enabled: !!userData,
    // Cache permission checks for 30 seconds
    staleTime: 30000,
    // Keep in cache for 5 minutes
    gcTime: 300000,
  });

  return {
    hasPermission: data?.authorized ?? false,
    isLoading,
    error,
    reason: data?.reason,
  };
}

/**
 * Hook for checking multiple permissions at once
 * Useful for bulk permission checks on page load
 */
export function usePermissions(checks: PermissionCheckParams[]) {
  const { userData } = useContext(AuthContext);

  const queries = checks.map((check) => ({
    queryKey: [
      "permission",
      check.action,
      check.scope,
      check.scopeId,
      userData?.id,
    ],
    queryFn: async () => {
      const params = new URLSearchParams({
        action: check.action,
        scope: check.scope,
      });

      if (check.scopeId) {
        params.append("scope_id", check.scopeId);
      }

      const response = await api.get<PermissionCheckResponse>(
        `/api/v1/rbac/check-permission?${params.toString()}`,
      );
      return response.data;
    },
    enabled: !!userData,
    staleTime: 30000,
    gcTime: 300000,
  }));

  // This would use useQueries from react-query for batch requests
  // For now, simplified implementation
  return {
    permissions: checks.map(() => ({ hasPermission: false, isLoading: true })),
    isLoading: true,
  };
}

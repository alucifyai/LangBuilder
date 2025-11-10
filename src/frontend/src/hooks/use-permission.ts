import { useCheckPermission } from "@/controllers/API/queries/rbac/use-check-permission";
import { useContext } from "react";
import { AuthContext } from "@/contexts/authContext";

/**
 * Permission types available in the RBAC system.
 *
 * Note: Uses uppercase convention (CREATE, READ, UPDATE, DELETE) which is
 * standard for permission constants. The backend RBAC service is case-insensitive.
 */
export type Permission = "CREATE" | "READ" | "UPDATE" | "DELETE";

/**
 * Scope types for permission checks.
 */
export type ScopeType = "Project" | "Flow" | "Global";

/**
 * RBAC feature flag - Set to true to enable permission checks.
 * When disabled, all permission checks will return true (allow all).
 *
 * NOTE: Temporarily disabled to debug 500 errors
 */
export const RBAC_ENABLED = false;

/**
 * Hook to check permissions for UI components using TanStack Query.
 *
 * This hook integrates with the RBAC API endpoints:
 * - /api/v1/rbac/check-permission (single permission check)
 * - /api/v1/rbac/check-permissions-batch (batch permission check)
 *
 * Results are cached for 5 minutes (staleTime) to minimize API calls.
 * Cache is garbage collected after 10 minutes of non-use (gcTime).
 *
 * @returns Object with permission checking methods
 */
export const usePermission = () => {
  const { userData } = useContext(AuthContext);

  /**
   * Check if user can create resources in a project.
   * When RBAC is disabled, always returns true.
   *
   * @param projectId - The project ID to check CREATE permission for
   * @returns Object with canCreate boolean and loading state
   */
  const canCreateInProject = (projectId: string) => {
    const { data, isLoading } = useCheckPermission(
      {
        permission: "CREATE",
        scope_type: "Project",
        scope_id: projectId,
      },
      {
        enabled: RBAC_ENABLED && !!userData,
      }
    );

    return {
      canCreate: RBAC_ENABLED ? (data?.allowed ?? false) : true,
      isLoading: RBAC_ENABLED ? isLoading : false
    };
  };

  /**
   * Check if user can read a resource.
   * When RBAC is disabled, always returns true.
   *
   * @param scopeType - The scope type (Project or Flow)
   * @param resourceId - The resource ID
   * @returns Object with canRead boolean and loading state
   */
  const canRead = (scopeType: ScopeType, resourceId: string) => {
    const { data, isLoading } = useCheckPermission(
      {
        permission: "READ",
        scope_type: scopeType,
        scope_id: scopeType !== "Global" ? resourceId : undefined,
      },
      {
        enabled: RBAC_ENABLED && !!userData,
      }
    );

    return {
      canRead: RBAC_ENABLED ? (data?.allowed ?? false) : true,
      isLoading: RBAC_ENABLED ? isLoading : false
    };
  };

  /**
   * Check if user can update a resource.
   * When RBAC is disabled, always returns true.
   *
   * @param scopeType - The scope type (Project or Flow)
   * @param resourceId - The resource ID
   * @returns Object with canUpdate boolean and loading state
   */
  const canUpdate = (scopeType: ScopeType, resourceId: string) => {
    const { data, isLoading } = useCheckPermission(
      {
        permission: "UPDATE",
        scope_type: scopeType,
        scope_id: scopeType !== "Global" ? resourceId : undefined,
      },
      {
        enabled: RBAC_ENABLED && !!userData,
      }
    );

    return {
      canUpdate: RBAC_ENABLED ? (data?.allowed ?? false) : true,
      isLoading: RBAC_ENABLED ? isLoading : false
    };
  };

  /**
   * Check if user can delete a resource.
   * When RBAC is disabled, always returns true.
   *
   * @param scopeType - The scope type (Project or Flow)
   * @param resourceId - The resource ID
   * @returns Object with canDelete boolean and loading state
   */
  const canDelete = (scopeType: ScopeType, resourceId: string) => {
    const { data, isLoading } = useCheckPermission(
      {
        permission: "DELETE",
        scope_type: scopeType,
        scope_id: scopeType !== "Global" ? resourceId : undefined,
      },
      {
        enabled: RBAC_ENABLED && !!userData,
      }
    );

    return {
      canDelete: RBAC_ENABLED ? (data?.allowed ?? false) : true,
      isLoading: RBAC_ENABLED ? isLoading : false
    };
  };

  return {
    canCreateInProject,
    canRead,
    canUpdate,
    canDelete,
  };
};

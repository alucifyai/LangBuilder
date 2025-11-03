import { useEffect, useState } from "react";
import { useCheckPermission } from "@/controllers/API/queries/rbac";
import type { PermissionEnum, ScopeTypeEnum } from "@/types/api/rbac";

/**
 * Options for usePermission hook
 */
interface UsePermissionOptions {
  /** Permission to check (CREATE, READ, UPDATE, DELETE) */
  permission: PermissionEnum;
  /** Scope type (GLOBAL, PROJECT, FLOW) */
  scopeType: ScopeTypeEnum;
  /** UUID of the scope (project or flow), optional for GLOBAL scope */
  scopeId?: string;
  /** Whether the permission check should be enabled (default: true) */
  enabled?: boolean;
}

/**
 * Return type for usePermission hook
 */
interface UsePermissionResult {
  /** Whether the user has the requested permission */
  hasPermission: boolean;
  /** Whether the permission check is loading */
  isLoading: boolean;
  /** Error from permission check, if any */
  error: Error | null;
  /** Function to manually re-check permission */
  refetch: () => void;
}

/**
 * Hook to check if current user has a specific permission.
 * Automatically checks permission on mount and when dependencies change.
 * Caches results via TanStack Query for performance.
 *
 * @param options - Permission check options
 * @returns Permission check result with hasPermission boolean, loading state, and error
 *
 * @example
 * ```tsx
 * // Check if user can update a specific flow
 * const { hasPermission, isLoading } = usePermission({
 *   permission: 'UPDATE',
 *   scopeType: 'FLOW',
 *   scopeId: flowId
 * });
 *
 * if (hasPermission && !isLoading) {
 *   // Show edit button
 * }
 * ```
 *
 * @example
 * ```tsx
 * // Conditionally enable permission check
 * const { hasPermission } = usePermission({
 *   permission: 'DELETE',
 *   scopeType: 'PROJECT',
 *   scopeId: projectId,
 *   enabled: Boolean(projectId) // Only check when projectId is available
 * });
 * ```
 */
export const usePermission = ({
  permission,
  scopeType,
  scopeId,
  enabled = true,
}: UsePermissionOptions): UsePermissionResult => {
  const { mutate, data, isPending, error } = useCheckPermission();
  const [hasChecked, setHasChecked] = useState(false);

  // Function to trigger permission check
  const checkPermission = () => {
    if (!enabled) {
      setHasChecked(false);
      return;
    }

    mutate({
      permission,
      scope_type: scopeType,
      scope_id: scopeId || null,
    });
    setHasChecked(true);
  };

  // Check permission when dependencies change
  useEffect(() => {
    checkPermission();
  }, [permission, scopeType, scopeId, enabled]);

  return {
    hasPermission: data?.has_permission ?? false,
    isLoading: isPending || (enabled && !hasChecked),
    error: error as Error | null,
    refetch: checkPermission,
  };
};

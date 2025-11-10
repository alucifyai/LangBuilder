import { ReactNode, useContext } from "react";
import { AuthContext } from "@/contexts/authContext";
import { useCheckPermission } from "@/controllers/API/queries/rbac/use-check-permission";
import { RBAC_ENABLED, Permission, ScopeType } from "@/hooks/use-permission";

/**
 * Props for the RBACGuard component.
 */
export interface RBACGuardProps {
  /**
   * The permission to check (CREATE, READ, UPDATE, DELETE).
   */
  permission: Permission;

  /**
   * The scope type (Project, Flow, Global).
   */
  scopeType: ScopeType;

  /**
   * The scope ID (required for Project and Flow, optional for Global).
   */
  scopeId?: string;

  /**
   * Content to render if permission is granted.
   */
  children: ReactNode;

  /**
   * Optional content to render if permission is denied or loading.
   * Defaults to null (renders nothing).
   */
  fallback?: ReactNode;
}

/**
 * RBACGuard component conditionally renders children based on permission check.
 *
 * This component uses TanStack Query for caching with the following strategy:
 * - staleTime: 5 minutes (results are considered fresh for 5 minutes)
 * - gcTime: 10 minutes (cached data is kept for 10 minutes after last use)
 *
 * When RBAC is disabled (RBAC_ENABLED = false), all guards pass through.
 *
 * Loading state shows fallback content to prevent UI flicker.
 * Permission denied shows fallback content (default: null/nothing).
 *
 * @example
 * ```tsx
 * <RBACGuard
 *   permission="UPDATE"
 *   scopeType="Flow"
 *   scopeId={flowId}
 *   fallback={<div>You don't have permission to edit this flow</div>}
 * >
 *   <EditFlowButton />
 * </RBACGuard>
 * ```
 */
export function RBACGuard({
  permission,
  scopeType,
  scopeId,
  children,
  fallback = null,
}: RBACGuardProps) {
  const { userData } = useContext(AuthContext);

  // If RBAC is disabled, always render children
  if (!RBAC_ENABLED) {
    return <>{children}</>;
  }

  // Query for permission check
  const { data, isLoading } = useCheckPermission(
    {
      permission,
      scope_type: scopeType,
      scope_id: scopeType !== "Global" ? scopeId : undefined,
    },
    {
      enabled: RBAC_ENABLED && !!userData,
    }
  );

  // Show fallback while loading
  if (isLoading) {
    return <>{fallback}</>;
  }

  // Show fallback if permission denied
  if (!data?.allowed) {
    return <>{fallback}</>;
  }

  // Permission granted - render children
  return <>{children}</>;
}

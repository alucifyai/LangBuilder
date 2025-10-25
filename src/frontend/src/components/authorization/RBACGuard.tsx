import { ReactNode } from "react";
import CustomLoader from "@/customization/components/custom-loader";
import {
  type PermissionAction,
  type PermissionScope,
  usePermission,
} from "../../hooks/usePermission";

export interface RBACGuardProps {
  /** The permission action required (create, read, update, delete) */
  action: PermissionAction;
  /** The permission scope (flow, project) */
  scope: PermissionScope;
  /** Optional ID of the specific resource */
  scopeId?: string;
  /** Content to show when user has permission */
  children: ReactNode;
  /** Content to show when user lacks permission (default: null - hide completely) */
  fallback?: ReactNode;
  /** Content to show while permission is being checked (default: loader) */
  loadingFallback?: ReactNode;
  /** If true, shows children in disabled/read-only state instead of hiding */
  showDisabled?: boolean;
}

/**
 * RBAC Guard Component
 *
 * Conditionally renders children based on user permissions.
 * Used to hide/disable UI elements based on RBAC permissions.
 *
 * @example
 * // Hide delete button if no delete permission
 * <RBACGuard action="delete" scope="flow" scopeId={flowId}>
 *   <Button onClick={handleDelete}>Delete Flow</Button>
 * </RBACGuard>
 *
 * @example
 * // Show disabled state if no update permission
 * <RBACGuard
 *   action="update"
 *   scope="flow"
 *   scopeId={flowId}
 *   showDisabled
 *   fallback={<Button disabled>Edit Flow (No Permission)</Button>}
 * >
 *   <Button onClick={handleEdit}>Edit Flow</Button>
 * </RBACGuard>
 */
export function RBACGuard({
  action,
  scope,
  scopeId,
  children,
  fallback = null,
  loadingFallback,
  showDisabled = false,
}: RBACGuardProps) {
  const { hasPermission, isLoading } = usePermission(action, scope, scopeId);

  // Show loading state
  if (isLoading) {
    return (
      <>
        {loadingFallback ?? (
          <div className="flex items-center justify-center p-2">
            <CustomLoader remSize={2} />
          </div>
        )}
      </>
    );
  }

  // No permission - show fallback or nothing
  if (!hasPermission) {
    return <>{fallback}</>;
  }

  // Has permission - show children
  return <>{children}</>;
}

/**
 * Higher-order component version of RBACGuard
 *
 * @example
 * const ProtectedDeleteButton = withRBACGuard(
 *   DeleteButton,
 *   { action: "delete", scope: "flow" }
 * );
 */
export function withRBACGuard<P extends object>(
  Component: React.ComponentType<P>,
  guardProps: Omit<RBACGuardProps, "children">,
) {
  return function GuardedComponent(props: P) {
    return (
      <RBACGuard {...guardProps}>
        <Component {...props} />
      </RBACGuard>
    );
  };
}

/**
 * Permission Guard Components
 *
 * Components to conditionally render or disable UI based on permissions.
 */

import React, { useEffect, useState } from "react";
import { usePermissions } from "../../contexts/permissionContext";
import type { ScopeType } from "../../types/grant";

interface PermissionGuardProps {
  permission: string;
  scopeType: ScopeType;
  scopeId: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * PermissionGuard - Only renders children if user has permission
 *
 * Usage:
 *   <PermissionGuard permission="flows:delete" scopeType="flow" scopeId={flowId}>
 *     <DeleteButton />
 *   </PermissionGuard>
 */
export function PermissionGuard({
  permission,
  scopeType,
  scopeId,
  children,
  fallback = null,
}: PermissionGuardProps) {
  const { hasPermission } = usePermissions();
  const allowed = hasPermission(permission, scopeType, scopeId);

  return <>{allowed ? children : fallback}</>;
}

interface PermissionButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  permission: string;
  scopeType: ScopeType;
  scopeId: string;
  children: React.ReactNode;
}

/**
 * PermissionButton - Button that's disabled if user lacks permission
 *
 * Usage:
 *   <PermissionButton
 *     permission="flows:update"
 *     scopeType="flow"
 *     scopeId={flowId}
 *     onClick={handleUpdate}
 *   >
 *     Update Flow
 *   </PermissionButton>
 */
export function PermissionButton({
  permission,
  scopeType,
  scopeId,
  children,
  disabled,
  title,
  ...props
}: PermissionButtonProps) {
  const { hasPermission } = usePermissions();
  const allowed = hasPermission(permission, scopeType, scopeId);

  const effectiveTitle = !allowed
    ? title || `Requires permission: ${permission}`
    : title;

  return (
    <button disabled={disabled || !allowed} title={effectiveTitle} {...props}>
      {children}
    </button>
  );
}

interface RequirePermissionProps {
  permission: string;
  scopeType: ScopeType;
  scopeId: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onDenied?: () => void;
}

/**
 * RequirePermission - Async permission check with loading state
 *
 * Usage:
 *   <RequirePermission
 *     permission="flows:read"
 *     scopeType="flow"
 *     scopeId={flowId}
 *     fallback={<AccessDenied />}
 *   >
 *     <FlowDetails />
 *   </RequirePermission>
 */
export function RequirePermission({
  permission,
  scopeType,
  scopeId,
  children,
  fallback = <div>Access denied</div>,
  onDenied,
}: RequirePermissionProps) {
  const { checkPermission } = usePermissions();
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    checkPermission(permission, scopeType, scopeId).then((result) => {
      setAllowed(result);
      if (!result && onDenied) {
        onDenied();
      }
    });
  }, [permission, scopeType, scopeId, checkPermission, onDenied]);

  if (allowed === null) {
    return <div>Checking permissions...</div>;
  }

  return <>{allowed ? children : fallback}</>;
}

interface PermissionLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  permission: string;
  scopeType: ScopeType;
  scopeId: string;
  children: React.ReactNode;
}

/**
 * PermissionLink - Link that's disabled if user lacks permission
 */
export function PermissionLink({
  permission,
  scopeType,
  scopeId,
  children,
  className,
  title,
  ...props
}: PermissionLinkProps) {
  const { hasPermission } = usePermissions();
  const allowed = hasPermission(permission, scopeType, scopeId);

  const effectiveClassName = allowed
    ? className
    : `${className} opacity-50 cursor-not-allowed pointer-events-none`;

  const effectiveTitle = !allowed
    ? title || `Requires permission: ${permission}`
    : title;

  return (
    <a className={effectiveClassName} title={effectiveTitle} {...props}>
      {children}
    </a>
  );
}

/**
 * withPermission HOC - Wraps component with permission check
 *
 * Usage:
 *   const ProtectedComponent = withPermission(MyComponent, {
 *     permission: "flows:update",
 *     getScope: (props) => ({ type: "flow", id: props.flowId }),
 *   });
 */
export function withPermission<P extends object>(
  Component: React.ComponentType<P>,
  config: {
    permission: string;
    getScope: (props: P) => { type: ScopeType; id: string };
    fallback?: React.ReactNode;
  }
) {
  return function PermissionWrappedComponent(props: P) {
    const scope = config.getScope(props);

    return (
      <PermissionGuard
        permission={config.permission}
        scopeType={scope.type}
        scopeId={scope.id}
        fallback={config.fallback}
      >
        <Component {...props} />
      </PermissionGuard>
    );
  };
}

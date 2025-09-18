import { useEffect, useState } from "react";
import { useRBAC } from "../../../contexts/rbacContext";

interface PermissionGuardProps {
  permission: string;
  scope_type?: string;
  scope_id?: string;
  resource_type?: string;
  resource_id?: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export default function PermissionGuard({
  permission,
  scope_type,
  scope_id,
  resource_type,
  resource_id,
  fallback = null,
  children,
}: PermissionGuardProps) {
  const { checkPermission } = useRBAC();
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const verifyPermission = async () => {
      setIsLoading(true);
      try {
        const result = await checkPermission(permission, {
          scope_type,
          scope_id,
          resource_type,
          resource_id,
        });

        if (mounted) {
          setHasPermission(result);
          setIsLoading(false);
        }
      } catch (error) {
        if (mounted) {
          setHasPermission(false);
          setIsLoading(false);
        }
      }
    };

    verifyPermission();

    return () => {
      mounted = false;
    };
  }, [
    permission,
    scope_type,
    scope_id,
    resource_type,
    resource_id,
    checkPermission,
  ]);

  if (isLoading) {
    return <div className="opacity-50">{children}</div>;
  }

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

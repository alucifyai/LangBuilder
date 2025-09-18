import React, {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useState,
} from "react";
import { useCheckPermission } from "@/controllers/API/queries/rbac";

interface RBACContextType {
  hasPermission: (
    resource: string,
    action: string,
    resourceId?: string,
  ) => boolean;
  isLoading: boolean;
  currentWorkspace: string | null;
  setCurrentWorkspace: (workspaceId: string | null) => void;
  currentProject: string | null;
  setCurrentProject: (projectId: string | null) => void;
}

const RBACContext = createContext<RBACContextType | undefined>(undefined);

interface RBACProviderProps {
  children: ReactNode;
}

export function RBACProvider({ children }: RBACProviderProps) {
  const [currentWorkspace, setCurrentWorkspace] = useState<string | null>(null);
  const [currentProject, setCurrentProject] = useState<string | null>(null);
  const [permissionCache, setPermissionCache] = useState<Map<string, boolean>>(
    new Map(),
  );

  // @ts-ignore - Type definition issue with mutation hook
  const { mutate: checkPermission, isPending: isLoading } =
    useCheckPermission();

  const hasPermission = (
    resource: string,
    action: string,
    resourceId?: string,
  ): boolean => {
    // Create cache key
    const cacheKey = `${resource}:${action}:${resourceId || "any"}`;

    // Check cache first
    if (permissionCache.has(cacheKey)) {
      return permissionCache.get(cacheKey)!;
    }

    // For now, return true as fallback (in production, this should be more restrictive)
    // This will be replaced with actual permission checks once the backend is fully integrated
    return true;
  };

  const checkAndCachePermission = (
    resource: string,
    action: string,
    resourceId?: string,
  ) => {
    const cacheKey = `${resource}:${action}:${resourceId || "any"}`;

    checkPermission(
      {
        resource_type: resource,
        action: action,
        resource_id: resourceId,
      },
      {
        onSuccess: (result) => {
          setPermissionCache(
            (prev) => new Map(prev.set(cacheKey, result.granted)),
          );
        },
        onError: () => {
          // Default to false on error
          setPermissionCache((prev) => new Map(prev.set(cacheKey, false)));
        },
      },
    );
  };

  // Clear cache when workspace or project changes
  useEffect(() => {
    setPermissionCache(new Map());
  }, [currentWorkspace, currentProject]);

  const value: RBACContextType = {
    hasPermission,
    isLoading,
    currentWorkspace,
    setCurrentWorkspace,
    currentProject,
    setCurrentProject,
  };

  return <RBACContext.Provider value={value}>{children}</RBACContext.Provider>;
}

export function useRBAC(): RBACContextType {
  const context = useContext(RBACContext);
  if (context === undefined) {
    throw new Error("useRBAC must be used within an RBACProvider");
  }
  return context;
}

// Helper hook for conditional rendering based on permissions
export function usePermissionGuard(
  resource: string,
  action: string,
  resourceId?: string,
) {
  const { hasPermission, isLoading } = useRBAC();
  return {
    canAccess: hasPermission(resource, action, resourceId),
    isLoading,
  };
}

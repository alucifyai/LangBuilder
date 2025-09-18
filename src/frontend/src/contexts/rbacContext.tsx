import React, { createContext, useContext, useEffect, useState } from "react";
import { useCheckPermission } from "@/controllers/API/queries/rbac";
import type { PermissionResult } from "@/controllers/API/queries/rbac/use-check-permission";

interface RBACContextType {
  checkPermission: (
    permission: string,
    options?: {
      scope_type?: string;
      scope_id?: string;
      resource_type?: string;
      resource_id?: string;
    }
  ) => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
  permissions: Set<string>;
  isLoading: boolean;
  refreshPermissions: () => void;
}

const RBACContext = createContext<RBACContextType | undefined>(undefined);

interface RBACProviderProps {
  children: React.ReactNode;
}

export function RBACProvider({ children }: RBACProviderProps) {
  const [permissions, setPermissions] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [permissionCache, setPermissionCache] = useState<Map<string, { result: boolean; timestamp: number }>>(new Map());
  
  const { mutate: mutateCheckPermission } = useCheckPermission();

  // Cache timeout: 5 minutes
  const CACHE_TIMEOUT = 5 * 60 * 1000;

  const checkPermission = async (
    permission: string,
    options?: {
      scope_type?: string;
      scope_id?: string;
      resource_type?: string;
      resource_id?: string;
    }
  ): Promise<boolean> => {
    const cacheKey = `${permission}-${JSON.stringify(options)}`;
    const cached = permissionCache.get(cacheKey);
    
    // Return cached result if valid
    if (cached && Date.now() - cached.timestamp < CACHE_TIMEOUT) {
      return cached.result;
    }

    return new Promise((resolve) => {
      mutateCheckPermission(
        {
          permission,
          ...options,
        },
        {
          onSuccess: (result: PermissionResult) => {
            const hasPermission = result.allowed;
            
            // Update cache
            setPermissionCache(prev => new Map(prev).set(cacheKey, {
              result: hasPermission,
              timestamp: Date.now()
            }));
            
            // Update permissions set for simple checks
            if (hasPermission && !options) {
              setPermissions(prev => new Set(prev).add(permission));
            }
            
            resolve(hasPermission);
          },
          onError: () => {
            resolve(false);
          },
        }
      );
    });
  };

  const hasPermission = (permission: string): boolean => {
    return permissions.has(permission);
  };

  const refreshPermissions = () => {
    setPermissionCache(new Map());
    setPermissions(new Set());
  };

  // Clean up old cache entries periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      setPermissionCache(prev => {
        const newCache = new Map();
        for (const [key, value] of prev.entries()) {
          if (now - value.timestamp < CACHE_TIMEOUT) {
            newCache.set(key, value);
          }
        }
        return newCache;
      });
    }, CACHE_TIMEOUT);

    return () => clearInterval(interval);
  }, []);

  const value: RBACContextType = {
    checkPermission,
    hasPermission,
    permissions,
    isLoading,
    refreshPermissions,
  };

  return (
    <RBACContext.Provider value={value}>
      {children}
    </RBACContext.Provider>
  );
}

export function useRBAC(): RBACContextType {
  const context = useContext(RBACContext);
  if (context === undefined) {
    throw new Error("useRBAC must be used within an RBACProvider");
  }
  return context;
}
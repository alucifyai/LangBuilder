/**
 * Permission Context
 *
 * Provides permission checking functionality throughout the app.
 * Uses grants and roles to determine what users can do.
 */

import React, { createContext, useContext, useState, useCallback } from "react";
import { listGrantsForPrincipal } from "../controllers/API/grants";
import { getRole } from "../controllers/API/roles";
import type { Grant, PrincipalType, ScopeType } from "../types/grant";
import { AuthContext } from "./authContext";

interface PermissionContextType {
  checkPermission: (
    permission: string,
    scopeType: ScopeType,
    scopeId: string
  ) => Promise<boolean>;
  hasPermission: (permission: string, scopeType: ScopeType, scopeId: string) => boolean;
  loadPermissions: () => Promise<void>;
  permissions: Map<string, Set<string>>;
  loading: boolean;
}

const PermissionContext = createContext<PermissionContextType | undefined>(undefined);

// Scope hierarchy (highest to lowest)
const SCOPE_HIERARCHY: ScopeType[] = [
  "workspace",
  "project",
  "environment",
  "flow",
  "component",
];

function getScopeRank(scopeType: ScopeType): number {
  const index = SCOPE_HIERARCHY.indexOf(scopeType);
  return index === -1 ? SCOPE_HIERARCHY.length : index;
}

export function PermissionProvider({ children }: { children: React.ReactNode }) {
  const { userData } = useContext(AuthContext);
  const [permissions, setPermissions] = useState<Map<string, Set<string>>>(new Map());
  const [loading, setLoading] = useState(false);

  /**
   * Load all grants and build permission map for current user
   */
  const loadPermissions = useCallback(async () => {
    if (!userData?.id) return;

    try {
      setLoading(true);

      // Superusers have all permissions
      if (userData.is_superuser) {
        // Create a special marker for superuser
        const permMap = new Map<string, Set<string>>();
        permMap.set("*", new Set(["*"]));
        setPermissions(permMap);
        return;
      }

      // Fetch user's grants
      const { grants } = await listGrantsForPrincipal("user" as PrincipalType, userData.id);

      // Build permission map: "scopeType:scopeId" -> Set<permission>
      const permMap = new Map<string, Set<string>>();

      for (const grant of grants) {
        // Skip expired grants
        if (grant.expires_at && new Date(grant.expires_at) < new Date()) {
          continue;
        }

        // Fetch role to get permissions
        try {
          const role = await getRole(grant.role_id);
          const scopeKey = `${grant.scope_type}:${grant.scope_id}`;

          if (!permMap.has(scopeKey)) {
            permMap.set(scopeKey, new Set());
          }

          // Add all role permissions to this scope
          role.permissions.forEach((perm) => {
            permMap.get(scopeKey)!.add(perm);
          });
        } catch (err) {
          console.error(`Failed to load role ${grant.role_id}:`, err);
        }
      }

      setPermissions(permMap);
    } catch (error) {
      console.error("Failed to load permissions:", error);
    } finally {
      setLoading(false);
    }
  }, [userData]);

  /**
   * Check if user has a permission at a specific scope
   * Implements scope hierarchy (higher scopes cascade down)
   */
  const checkPermission = useCallback(
    async (permission: string, scopeType: ScopeType, scopeId: string): Promise<boolean> => {
      if (!userData) return false;

      // Superusers have all permissions
      if (userData.is_superuser || permissions.has("*")) {
        return true;
      }

      const requiredRank = getScopeRank(scopeType);

      // Check exact scope first
      const exactKey = `${scopeType}:${scopeId}`;
      if (permissions.get(exactKey)?.has(permission)) {
        return true;
      }

      // Check higher scopes (cascading)
      for (const [scopeKey, perms] of permissions.entries()) {
        const [grantScopeType] = scopeKey.split(":");
        const grantRank = getScopeRank(grantScopeType as ScopeType);

        // Only consider grants at higher scopes (lower rank number)
        if (grantRank < requiredRank && perms.has(permission)) {
          return true;
        }
      }

      return false;
    },
    [userData, permissions]
  );

  /**
   * Synchronous permission check (uses cached permissions)
   * Call loadPermissions() first to populate cache
   */
  const hasPermission = useCallback(
    (permission: string, scopeType: ScopeType, scopeId: string): boolean => {
      if (!userData) return false;

      // Superusers have all permissions
      if (userData.is_superuser || permissions.has("*")) {
        return true;
      }

      const requiredRank = getScopeRank(scopeType);

      // Check exact scope
      const exactKey = `${scopeType}:${scopeId}`;
      if (permissions.get(exactKey)?.has(permission)) {
        return true;
      }

      // Check higher scopes
      for (const [scopeKey, perms] of permissions.entries()) {
        const [grantScopeType] = scopeKey.split(":");
        const grantRank = getScopeRank(grantScopeType as ScopeType);

        if (grantRank < requiredRank && perms.has(permission)) {
          return true;
        }
      }

      return false;
    },
    [userData, permissions]
  );

  return (
    <PermissionContext.Provider
      value={{
        checkPermission,
        hasPermission,
        loadPermissions,
        permissions,
        loading,
      }}
    >
      {children}
    </PermissionContext.Provider>
  );
}

/**
 * Hook to use permission context
 */
export function usePermissions() {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error("usePermissions must be used within PermissionProvider");
  }
  return context;
}

/**
 * Hook to check a specific permission
 */
export function useHasPermission(
  permission: string,
  scopeType: ScopeType,
  scopeId: string
): boolean {
  const { hasPermission } = usePermissions();
  return hasPermission(permission, scopeType, scopeId);
}

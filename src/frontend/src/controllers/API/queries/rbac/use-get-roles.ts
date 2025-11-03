import type { UseQueryResult } from "@tanstack/react-query";
import type { RoleRead } from "@/types/api/rbac";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * Hook to fetch all available roles.
 * Admin-only endpoint per PRD Epic 3 Story 3.1.
 *
 * @returns Query result with roles array
 *
 * @example
 * const { data: roles, isLoading, error } = useGetRoles();
 */
export const useGetRoles = () => {
  const { query } = UseRequestProcessor();

  async function getRoles(): Promise<RoleRead[]> {
    const res = await api.get(`${getURL("RBAC")}/roles`);
    if (res.status === 200) {
      return res.data;
    }
    return [];
  }

  const queryResult: UseQueryResult<RoleRead[], any> = query(
    ["useGetRoles"],
    getRoles,
    {
      // Roles are static, cache for 1 hour
      staleTime: 1000 * 60 * 60,
      // Keep in cache for 2 hours
      gcTime: 1000 * 60 * 60 * 2,
    },
  );

  return queryResult;
};

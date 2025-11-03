import type { UseQueryResult } from "@tanstack/react-query";
import type { AssignmentFilters, AssignmentResponse } from "@/types/api/rbac";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * Hook to fetch role assignments with optional filtering.
 * Admin-only endpoint per PRD Epic 3 Story 3.3.
 *
 * @param filters - Optional filters (user_id, role_name, scope_type, scope_id)
 * @returns Query result with assignments array
 *
 * @example
 * const { data: assignments, isLoading } = useGetAssignments({
 *   user_id: "123",
 *   scope_type: "PROJECT"
 * });
 */
export const useGetAssignments = (filters?: AssignmentFilters) => {
  const { query } = UseRequestProcessor();

  async function getAssignments(): Promise<AssignmentResponse[]> {
    // Build query params
    const params = new URLSearchParams();
    if (filters?.user_id) {
      params.append("user_id", filters.user_id);
    }
    if (filters?.role_name) {
      params.append("role_name", filters.role_name);
    }
    if (filters?.scope_type) {
      params.append("scope_type", filters.scope_type);
    }
    if (filters?.scope_id) {
      params.append("scope_id", filters.scope_id);
    }

    const queryString = params.toString();
    const url = `${getURL("RBAC")}/assignments${queryString ? `?${queryString}` : ""}`;

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return [];
  }

  const queryResult: UseQueryResult<AssignmentResponse[], any> = query(
    ["useGetAssignments", filters],
    getAssignments,
    {
      // Refetch on window focus to keep assignments fresh
      refetchOnWindowFocus: true,
      // Assignments can change, moderate cache time
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  );

  return queryResult;
};

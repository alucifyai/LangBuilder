import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";

export interface Assignment {
  id: string;
  user_id: string;
  user_name?: string;  // Enriched field from backend
  role_id: string;
  role_name?: string;  // Enriched field from backend
  scope_type: string;
  scope_id: string | null;
  scope_name?: string;  // Enriched field from backend
  is_immutable: boolean;
  created_at: string;
  created_by: string | null;
}

export interface GetAssignmentsParams {
  user_id?: string;
  role_id?: string;
  scope_type?: string;
}

/**
 * Hook to fetch role assignments with optional filtering.
 *
 * @param params - Optional filter parameters
 * @param options - Additional query options
 * @returns Query result with assignments array
 */
export const useGetAssignments = (
  params?: GetAssignmentsParams,
  options?: {
    enabled?: boolean;
  }
): UseQueryResult<Assignment[], Error> => {
  return useQuery<Assignment[], Error>({
    queryKey: ["rbac-assignments", params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();
      if (params?.user_id) queryParams.append("user_id", params.user_id);
      if (params?.role_id) queryParams.append("role_id", params.role_id);
      if (params?.scope_type) queryParams.append("scope_type", params.scope_type);

      const url = `${getURL("RBAC")}/assignments${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
      const response = await api.get<Assignment[]>(url);
      return response.data;
    },
    enabled: options?.enabled !== false,
    staleTime: 30 * 1000, // 30 seconds - assignments change less frequently than other data
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
};

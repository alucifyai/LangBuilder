import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";

interface BatchResource {
  id: string;
  scope_type: string;
  scope_id?: string;
}

interface CheckPermissionsBatchRequest {
  permission: string;
  resources: BatchResource[];
}

interface CheckPermissionsBatchResponse {
  results: Record<string, boolean>;
}

/**
 * Hook to check permissions for multiple resources in a single request.
 * This optimizes list view queries by reducing N individual permission checks
 * to a single API call.
 *
 * @param request - The batch permission check request
 * @param options - Additional query options
 * @returns Query result with results object mapping resource ID to allowed boolean
 */
export const useCheckPermissionsBatch = (
  request: CheckPermissionsBatchRequest,
  options?: {
    enabled?: boolean;
  }
): UseQueryResult<CheckPermissionsBatchResponse, Error> => {
  return useQuery<CheckPermissionsBatchResponse, Error>({
    queryKey: ["check-permissions-batch", request],
    queryFn: async () => {
      const response = await api.post<CheckPermissionsBatchResponse>(
        `${getURL("RBAC")}/check-permissions-batch`,
        request
      );
      return response.data;
    },
    enabled: options?.enabled !== false && request.resources.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes - permissions don't change frequently
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
};

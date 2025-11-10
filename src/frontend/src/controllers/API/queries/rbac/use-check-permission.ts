import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";

interface CheckPermissionRequest {
  permission: string;
  scope_type: string;
  scope_id?: string;
}

interface CheckPermissionResponse {
  allowed: boolean;
}

/**
 * Hook to check if the current user has a specific permission.
 *
 * @param request - The permission check request
 * @param options - Additional query options
 * @returns Query result with allowed boolean
 */
export const useCheckPermission = (
  request: CheckPermissionRequest,
  options?: {
    enabled?: boolean;
  }
): UseQueryResult<CheckPermissionResponse, Error> => {
  return useQuery<CheckPermissionResponse, Error>({
    queryKey: ["check-permission", request],
    queryFn: async () => {
      const response = await api.get<CheckPermissionResponse>(
        `${getURL("RBAC")}/check-permission`,
        {
          params: {
            permission: request.permission,
            scope_type: request.scope_type,
            scope_id: request.scope_id,
          },
        }
      );
      return response.data;
    },
    enabled: options?.enabled !== false,
    staleTime: 5 * 60 * 1000, // 5 minutes - permissions don't change frequently
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
};

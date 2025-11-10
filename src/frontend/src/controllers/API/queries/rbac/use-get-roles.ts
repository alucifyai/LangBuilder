import { useQuery, UseQueryResult } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";

export interface Role {
  id: string;
  name: string;
  description: string | null;
  is_system: boolean;
}

/**
 * Hook to fetch all available roles.
 *
 * @param options - Additional query options
 * @returns Query result with roles array
 */
export const useGetRoles = (options?: {
  enabled?: boolean;
}): UseQueryResult<Role[], Error> => {
  return useQuery<Role[], Error>({
    queryKey: ["rbac-roles"],
    queryFn: async () => {
      const response = await api.get<Role[]>(`${getURL("RBAC")}/roles`);
      return response.data;
    },
    enabled: options?.enabled !== false,
    staleTime: 5 * 60 * 1000, // 5 minutes - roles rarely change
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
};

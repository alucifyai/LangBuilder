import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";

export interface Role {
  id: string;
  name: string;
  description: string | null;
  is_global: boolean;
  is_system: boolean;
}

export interface RolesResponse {
  roles: Role[];
}

export const useGetRoles = () => {
  return useQuery<RolesResponse>({
    queryKey: ["roles"],
    queryFn: async () => {
      const response = await api.get<RolesResponse>("/api/v1/rbac/roles");
      return response.data;
    },
    staleTime: 300000, // 5 minutes - roles don't change often
  });
};

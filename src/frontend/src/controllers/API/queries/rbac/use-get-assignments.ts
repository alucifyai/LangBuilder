import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";

export interface UserRoleAssignment {
  id: string;
  user_id: string;
  role_id: string;
  scope: "flow" | "project";
  scope_id: string;
  is_immutable: boolean;
  created_at: string;
  // Populated fields
  user_username?: string;
  role_name?: string;
  scope_name?: string;
}

export interface AssignmentsResponse {
  assignments: UserRoleAssignment[];
  total_count: number;
}

export interface GetAssignmentsParams {
  user_id?: string;
  role_id?: string;
  scope?: "flow" | "project";
  scope_id?: string;
  skip?: number;
  limit?: number;
}

export const useGetAssignments = (params: GetAssignmentsParams = {}) => {
  return useQuery<AssignmentsResponse>({
    queryKey: ["assignments", params],
    queryFn: async () => {
      const queryParams = new URLSearchParams();

      if (params.user_id) queryParams.append("user_id", params.user_id);
      if (params.role_id) queryParams.append("role_id", params.role_id);
      if (params.scope) queryParams.append("scope", params.scope);
      if (params.scope_id) queryParams.append("scope_id", params.scope_id);
      if (params.skip !== undefined)
        queryParams.append("skip", params.skip.toString());
      if (params.limit !== undefined)
        queryParams.append("limit", params.limit.toString());

      const response = await api.get<AssignmentsResponse>(
        `/api/v1/rbac/assignments?${queryParams.toString()}`,
      );
      return response.data;
    },
    staleTime: 10000, // 10 seconds
  });
};

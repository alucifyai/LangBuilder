import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";
import type { UserRoleAssignment } from "./use-get-assignments";

export interface CreateAssignmentRequest {
  user_id: string;
  role_id: string;
  scope: "flow" | "project";
  scope_id: string;
}

export const usePostAssignment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAssignmentRequest) => {
      const response = await api.post<UserRoleAssignment>(
        "/api/v1/rbac/assignments",
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate assignments query to refetch
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      // Also invalidate permission checks
      queryClient.invalidateQueries({ queryKey: ["permission"] });
    },
  });
};

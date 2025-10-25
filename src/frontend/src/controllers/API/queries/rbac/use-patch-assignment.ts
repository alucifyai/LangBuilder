import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";
import type { UserRoleAssignment } from "./use-get-assignments";

export interface UpdateAssignmentRequest {
  role_id: string;
}

export const usePatchAssignment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      assignmentId,
      data,
    }: {
      assignmentId: string;
      data: UpdateAssignmentRequest;
    }) => {
      const response = await api.patch<UserRoleAssignment>(
        `/api/v1/rbac/assignments/${assignmentId}`,
        data,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["permission"] });
    },
  });
};

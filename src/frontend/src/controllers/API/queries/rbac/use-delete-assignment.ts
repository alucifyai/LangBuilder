import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";

export const useDeleteAssignment = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (assignmentId: string) => {
      const response = await api.delete(
        `/api/v1/rbac/assignments/${assignmentId}`,
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      queryClient.invalidateQueries({ queryKey: ["permission"] });
    },
  });
};

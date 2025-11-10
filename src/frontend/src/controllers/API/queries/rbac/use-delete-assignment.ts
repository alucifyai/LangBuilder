import { useMutation, UseMutationResult, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";

interface DeleteAssignmentError {
  status?: number;
  detail?: string;
}

/**
 * Hook to delete a role assignment.
 *
 * @returns Mutation result for delete operation
 */
export const useDeleteAssignment = (): UseMutationResult<
  void,
  DeleteAssignmentError,
  string
> => {
  const queryClient = useQueryClient();

  return useMutation<void, DeleteAssignmentError, string>({
    mutationFn: async (assignmentId: string) => {
      await api.delete(`${getURL("RBAC")}/assignments/${assignmentId}`);
    },
    onSuccess: () => {
      // Invalidate all assignment queries to trigger a refetch
      queryClient.invalidateQueries({ queryKey: ["rbac-assignments"] });
    },
  });
};

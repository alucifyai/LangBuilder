import { useMutation, UseMutationResult, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import type { Assignment } from "./use-get-assignments";

export interface UpdateAssignmentRequest {
  assignment_id: string;
  role_id: string;
}

interface UpdateAssignmentError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  detail?: string;
}

/**
 * Hook to update an existing role assignment.
 * Only the role_id can be updated - user, scope_type, and scope_id are immutable.
 *
 * @returns Mutation result for update operation
 */
export const useUpdateAssignment = (): UseMutationResult<
  Assignment,
  UpdateAssignmentError,
  UpdateAssignmentRequest
> => {
  const queryClient = useQueryClient();

  return useMutation<Assignment, UpdateAssignmentError, UpdateAssignmentRequest>({
    mutationFn: async ({ assignment_id, role_id }: UpdateAssignmentRequest) => {
      const response = await api.put<Assignment>(
        `${getURL("RBAC")}/assignments/${assignment_id}`,
        { role_id }
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate all assignment queries to trigger a refetch
      queryClient.invalidateQueries({ queryKey: ["rbac-assignments"] });
    },
  });
};

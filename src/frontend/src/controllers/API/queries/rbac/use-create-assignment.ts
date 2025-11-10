import { useMutation, UseMutationResult, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import type { Assignment } from "./use-get-assignments";

export interface CreateAssignmentRequest {
  user_id: string;
  role_id: string;
  scope_type: "Global" | "Project" | "Flow";
  scope_id: string | null;
}

interface CreateAssignmentError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  detail?: string;
}

/**
 * Hook to create a new role assignment.
 *
 * @returns Mutation result for create operation
 */
export const useCreateAssignment = (): UseMutationResult<
  Assignment,
  CreateAssignmentError,
  CreateAssignmentRequest
> => {
  const queryClient = useQueryClient();

  return useMutation<Assignment, CreateAssignmentError, CreateAssignmentRequest>({
    mutationFn: async (request: CreateAssignmentRequest) => {
      const response = await api.post<Assignment>(
        `${getURL("RBAC")}/assignments`,
        request
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate all assignment queries to trigger a refetch
      queryClient.invalidateQueries({ queryKey: ["rbac-assignments"] });
    },
  });
};

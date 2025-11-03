import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "@/types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * Delete request parameters
 */
interface DeleteAssignmentParams {
  assignment_id: string;
}

/**
 * Hook to delete a role assignment.
 * Admin-only endpoint per PRD Epic 3 Story 3.3.
 * Cannot delete immutable assignments per PRD Story 1.4.
 *
 * @param options - TanStack Query mutation options
 * @returns Mutation result
 *
 * @example
 * const { mutate: deleteAssignment } = useDeleteAssignment({
 *   onSuccess: () => console.log('Assignment deleted')
 * });
 *
 * deleteAssignment({ assignment_id: "789" });
 */
export const useDeleteAssignment: useMutationFunctionType<
  undefined,
  DeleteAssignmentParams
> = (options?) => {
  const { mutate, queryClient } = UseRequestProcessor();

  async function deleteAssignment({
    assignment_id,
  }: DeleteAssignmentParams): Promise<void> {
    await api.delete(`${getURL("RBAC")}/assignments/${assignment_id}`);
  }

  const mutation: UseMutationResult<void, any, DeleteAssignmentParams> = mutate(
    ["useDeleteAssignment"],
    deleteAssignment,
    {
      ...options,
      onSuccess: (data, variables, context) => {
        // Invalidate assignments query to refetch
        queryClient.invalidateQueries({ queryKey: ["useGetAssignments"] });
        // Call user-provided onSuccess
        options?.onSuccess?.(data, variables, context);
      },
    },
  );

  return mutation;
};

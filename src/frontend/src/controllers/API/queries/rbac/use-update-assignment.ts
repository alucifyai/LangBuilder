import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "@/types/api";
import type { AssignmentResponse, AssignmentUpdate } from "@/types/api/rbac";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * Update request parameters
 */
interface UpdateAssignmentParams {
  assignment_id: string;
  update: AssignmentUpdate;
}

/**
 * Hook to update an existing role assignment.
 * Admin-only endpoint per PRD Epic 3 Story 3.2.
 * Cannot modify immutable assignments per PRD Story 1.4.
 *
 * @param options - TanStack Query mutation options
 * @returns Mutation result
 *
 * @example
 * const { mutate: updateAssignment } = useUpdateAssignment({
 *   onSuccess: () => console.log('Assignment updated')
 * });
 *
 * updateAssignment({
 *   assignment_id: "789",
 *   update: { new_role_name: "Viewer" }
 * });
 */
export const useUpdateAssignment: useMutationFunctionType<
  undefined,
  UpdateAssignmentParams
> = (options?) => {
  const { mutate, queryClient } = UseRequestProcessor();

  async function updateAssignment({
    assignment_id,
    update,
  }: UpdateAssignmentParams): Promise<AssignmentResponse> {
    const res = await api.put(
      `${getURL("RBAC")}/assignments/${assignment_id}`,
      update,
    );
    return res.data;
  }

  const mutation: UseMutationResult<
    AssignmentResponse,
    any,
    UpdateAssignmentParams
  > = mutate(["useUpdateAssignment"], updateAssignment, {
    ...options,
    onSuccess: (data, variables, context) => {
      // Invalidate assignments query to refetch
      queryClient.invalidateQueries({ queryKey: ["useGetAssignments"] });
      // Call user-provided onSuccess
      options?.onSuccess?.(data, variables, context);
    },
  });

  return mutation;
};

import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "@/types/api";
import type { AssignmentCreate, AssignmentResponse } from "@/types/api/rbac";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * Hook to create a new role assignment.
 * Admin-only endpoint per PRD Epic 3 Story 3.2.
 *
 * @param options - TanStack Query mutation options
 * @returns Mutation result
 *
 * @example
 * const { mutate: createAssignment, isPending } = useCreateAssignment({
 *   onSuccess: () => console.log('Assignment created'),
 *   onError: (error) => console.error(error)
 * });
 *
 * createAssignment({
 *   user_id: "123",
 *   role_name: "Editor",
 *   scope_type: "PROJECT",
 *   scope_id: "456"
 * });
 */
export const useCreateAssignment: useMutationFunctionType<
  undefined,
  AssignmentCreate
> = (options?) => {
  const { mutate, queryClient } = UseRequestProcessor();

  async function createAssignment(
    assignment: AssignmentCreate,
  ): Promise<AssignmentResponse> {
    const res = await api.post(`${getURL("RBAC")}/assignments`, assignment);
    return res.data;
  }

  const mutation: UseMutationResult<AssignmentResponse, any, AssignmentCreate> =
    mutate(["useCreateAssignment"], createAssignment, {
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

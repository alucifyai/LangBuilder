import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "@/types/api";
import type {
  PermissionCheckRequest,
  PermissionCheckResponse,
} from "@/types/api/rbac";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

/**
 * Hook options for permission checking
 */
interface UseCheckPermissionOptions {
  enabled?: boolean;
}

/**
 * Hook to check if current user has a specific permission.
 * Available to all authenticated users (not admin-only).
 * Used by frontend to determine UI visibility and capabilities.
 *
 * @param options - TanStack Query mutation options
 * @returns Mutation result
 *
 * @example
 * const { mutate: checkPermission, data } = useCheckPermission();
 *
 * checkPermission({
 *   permission: "UPDATE",
 *   scope_type: "FLOW",
 *   scope_id: "123"
 * });
 *
 * // Access result
 * if (data?.has_permission) {
 *   // User has UPDATE permission on flow 123
 * }
 */
export const useCheckPermission: useMutationFunctionType<
  UseCheckPermissionOptions,
  PermissionCheckRequest
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function checkPermission(
    request: PermissionCheckRequest,
  ): Promise<PermissionCheckResponse> {
    const res = await api.post(`${getURL("RBAC")}/check-permission`, request);
    return res.data;
  }

  const mutation: UseMutationResult<
    PermissionCheckResponse,
    any,
    PermissionCheckRequest
  > = mutate(["useCheckPermission"], checkPermission, {
    ...options,
    // Don't retry permission checks as frequently
    retry: 1,
  });

  return mutation;
};

import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface DeleteRoleData {
  role_id: string;
}

export const useDeleteRole: useMutationFunctionType<{ success: boolean }, DeleteRoleData> = (
  options?
) => {
  const { mutate } = UseRequestProcessor();

  async function deleteRole({ role_id }: DeleteRoleData): Promise<{ success: boolean }> {
    const res = await api.delete(`${getURL("RBAC")}/roles/${role_id}`);
    if (res.status === 204) {
      return { success: true };
    }
    throw new Error(`Failed to delete role: ${res.status}`);
  }

  const mutation: UseMutationResult<{ success: boolean }, any, DeleteRoleData> = mutate(
    ["useDeleteRole"],
    deleteRole,
    options
  );

  return mutation;
};
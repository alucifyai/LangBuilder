import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { Role } from "./use-get-roles";

export interface UpdateRoleData {
  role_id: string;
  role: {
    name?: string;
    description?: string;
    permissions?: string[];
    is_active?: boolean;
  };
}

export const useUpdateRole: useMutationFunctionType<Role, UpdateRoleData> = (
  options?,
) => {
  const { mutate } = UseRequestProcessor();

  async function updateRole({ role_id, role }: UpdateRoleData): Promise<Role> {
    const res = await api.patch(`${getURL("RBAC")}/roles/${role_id}`, role);
    if (res.status === 200) {
      return res.data;
    }
    throw new Error(`Failed to update role: ${res.status}`);
  }

  const mutation: UseMutationResult<Role, any, UpdateRoleData> = mutate(
    ["useUpdateRole"],
    updateRole,
    options,
  );

  return mutation;
};

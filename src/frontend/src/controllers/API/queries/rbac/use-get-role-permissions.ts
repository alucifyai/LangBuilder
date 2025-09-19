import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

import type { Permission } from "./use-get-permissions";

interface GetRolePermissionsQueryParams {
  role_id: string;
}

export const useGetRolePermissions: useMutationFunctionType<
  Permission[],
  GetRolePermissionsQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getRolePermissions({
    role_id,
  }: GetRolePermissionsQueryParams): Promise<Permission[]> {
    const url = `${getURL("RBAC")}/roles/${role_id}/permissions`;

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return [];
  }

  const mutation: UseMutationResult<
    Permission[],
    any,
    GetRolePermissionsQueryParams
  > = mutate(["useGetRolePermissions"], getRolePermissions, options);

  return mutation;
};

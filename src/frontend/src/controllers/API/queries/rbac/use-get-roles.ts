import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface Role {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system_role: boolean;
  is_active: boolean;
  workspace_id: string;
  created_at: string;
  updated_at: string;
  created_by_id: string;
  assignment_count?: number;
}

interface GetRolesQueryParams {
  workspace_id?: string;
  skip?: number;
  limit?: number;
  search?: string;
  include_system_roles?: boolean;
  is_active?: boolean;
}

export const useGetRoles: useMutationFunctionType<
  { roles: Role[]; total_count: number },
  GetRolesQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getRoles({
    workspace_id,
    skip = 0,
    limit = 50,
    search,
    include_system_roles = false,
    is_active,
  }: GetRolesQueryParams): Promise<{ roles: Role[]; total_count: number }> {
    let url = `${getURL("RBAC")}/roles/?skip=${skip}&limit=${limit}`;

    if (workspace_id) {
      url += `&workspace_id=${workspace_id}`;
    }
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    if (include_system_roles) {
      url += `&include_system_roles=true`;
    }
    if (is_active !== undefined) {
      url += `&is_active=${is_active}`;
    }

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return { roles: [], total_count: 0 };
  }

  const mutation: UseMutationResult<
    { roles: Role[]; total_count: number },
    any,
    GetRolesQueryParams
  > = mutate(["useGetRoles"], getRoles, options);

  return mutation;
};

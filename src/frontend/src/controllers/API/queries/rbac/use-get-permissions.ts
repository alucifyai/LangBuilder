import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface Permission {
  id: string;
  name: string;
  code: string;
  description: string | null;
  resource_type: string;
  action: string;
  scope?: string;
  category?: string;
  is_system: boolean;
  is_dangerous: boolean;
  requires_mfa: boolean;
  created_at: string;
  updated_at: string;
}

interface GetPermissionsQueryParams {
  skip?: number;
  limit?: number;
  search?: string;
  resource_type?: string;
  category?: string;
  is_system?: boolean;
}

export const useGetPermissions: useMutationFunctionType<
  { permissions: Permission[]; total_count: number },
  GetPermissionsQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getPermissions({
    skip = 0,
    limit = 100,
    search,
    resource_type,
    category,
    is_system,
  }: GetPermissionsQueryParams): Promise<{ permissions: Permission[]; total_count: number }> {
    let url = `${getURL("RBAC")}/permissions/?skip=${skip}&limit=${limit}`;

    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    if (resource_type) {
      url += `&resource_type=${resource_type}`;
    }
    if (category) {
      url += `&category=${category}`;
    }
    if (is_system !== undefined) {
      url += `&is_system=${is_system}`;
    }

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return { permissions: [], total_count: 0 };
  }

  const mutation: UseMutationResult<
    { permissions: Permission[]; total_count: number },
    any,
    GetPermissionsQueryParams
  > = mutate(["useGetPermissions"], getPermissions, options);

  return mutation;
};
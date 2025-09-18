import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface ServiceAccount {
  id: string;
  name: string;
  description: string | null;
  workspace_id: string;
  created_by_id: string;
  scope_type: "global" | "workspace" | "project" | "environment";
  scope_id: string | null;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  token_count?: number;
}

interface GetServiceAccountsQueryParams {
  workspace_id?: string;
  scope_type?: string;
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
}

export const useGetServiceAccounts: useMutationFunctionType<
  { service_accounts: ServiceAccount[]; total_count: number },
  GetServiceAccountsQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getServiceAccounts({
    workspace_id,
    scope_type,
    skip = 0,
    limit = 50,
    search,
    is_active,
  }: GetServiceAccountsQueryParams): Promise<{ service_accounts: ServiceAccount[]; total_count: number }> {
    let url = `${getURL("RBAC")}/service-accounts/?skip=${skip}&limit=${limit}`;

    if (workspace_id) url += `&workspace_id=${workspace_id}`;
    if (scope_type) url += `&scope_type=${scope_type}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (is_active !== undefined) url += `&is_active=${is_active}`;

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return { service_accounts: [], total_count: 0 };
  }

  const mutation: UseMutationResult<
    { service_accounts: ServiceAccount[]; total_count: number },
    any,
    GetServiceAccountsQueryParams
  > = mutate(["useGetServiceAccounts"], getServiceAccounts, options);

  return mutation;
};
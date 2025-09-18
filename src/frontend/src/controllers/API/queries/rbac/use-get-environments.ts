import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface Environment {
  id: string;
  name: string;
  description: string | null;
  project_id: string;
  type: "development" | "staging" | "production" | "testing";
  is_active: boolean;
  is_default: boolean;
  variables: Record<string, any>;
  created_at: string;
  updated_at: string;
  deployment_count?: number;
  last_deployed_at?: string;
}

interface GetEnvironmentsQueryParams {
  project_id?: string;
  type?: string;
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
}

export const useGetEnvironments: useMutationFunctionType<
  { environments: Environment[]; total_count: number },
  GetEnvironmentsQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getEnvironments({
    project_id,
    type,
    skip = 0,
    limit = 50,
    search,
    is_active,
  }: GetEnvironmentsQueryParams): Promise<{ environments: Environment[]; total_count: number }> {
    let url = `${getURL("RBAC")}/environments/?skip=${skip}&limit=${limit}`;

    if (project_id) url += `&project_id=${project_id}`;
    if (type) url += `&type=${type}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (is_active !== undefined) url += `&is_active=${is_active}`;

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return { environments: [], total_count: 0 };
  }

  const mutation: UseMutationResult<
    { environments: Environment[]; total_count: number },
    any,
    GetEnvironmentsQueryParams
  > = mutate(["useGetEnvironments"], getEnvironments, options);

  return mutation;
};
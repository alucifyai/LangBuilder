import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  workspace_id: string;
  owner_id: string;
  is_active: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  environment_count?: number;
  flow_count?: number;
  last_deployed_at?: string;
}

interface GetProjectsQueryParams {
  workspace_id?: string;
  skip?: number;
  limit?: number;
  search?: string;
  is_active?: boolean;
}

export const useGetProjects: useMutationFunctionType<
  { projects: Project[]; total_count: number },
  GetProjectsQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getProjects({
    workspace_id,
    skip = 0,
    limit = 50,
    search,
    is_active,
  }: GetProjectsQueryParams): Promise<{
    projects: Project[];
    total_count: number;
  }> {
    let url = `${getURL("RBAC")}/projects/?skip=${skip}&limit=${limit}`;

    if (workspace_id) {
      url += `&workspace_id=${workspace_id}`;
    }
    if (search) {
      url += `&search=${encodeURIComponent(search)}`;
    }
    if (is_active !== undefined) {
      url += `&is_active=${is_active}`;
    }

    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return { projects: [], total_count: 0 };
  }

  const mutation: UseMutationResult<
    { projects: Project[]; total_count: number },
    any,
    GetProjectsQueryParams
  > = mutate(["useGetProjects"], getProjects, options);

  return mutation;
};

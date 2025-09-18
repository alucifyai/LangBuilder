import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by_id: string;
  member_count?: number;
  role_count?: number;
}

interface GetWorkspacesQueryParams {
  skip?: number;
  limit?: number;
  search?: string;
}

export const useGetWorkspaces: useMutationFunctionType<
  { workspaces: Workspace[]; total_count: number },
  GetWorkspacesQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getWorkspaces({
    skip = 0,
    limit = 50,
    search,
  }: GetWorkspacesQueryParams): Promise<{ workspaces: Workspace[]; total_count: number }> {
    try {
      let url = `${getURL("RBAC")}/workspaces/?skip=${skip}&limit=${limit}`;
      if (search) {
        url += `&search=${encodeURIComponent(search)}`;
      }
      
      const res = await api.get(url);
      if (res.status === 200) {
        return res.data;
      }
      return { workspaces: [], total_count: 0 };
    } catch (error) {
      console.error('Failed to fetch workspaces:', error);
      throw error;
    }
  }

  const mutation: UseMutationResult<
    { workspaces: Workspace[]; total_count: number },
    any,
    GetWorkspacesQueryParams
  > = mutate(["useGetWorkspaces"], getWorkspaces, options);

  return mutation;
};
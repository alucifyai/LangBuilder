import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import { handleRBACError, normalizeListResponse } from "./error-handler";

export interface Workspace {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Support both naming conventions for compatibility
  created_by_id?: string;
  owner_id?: string;
  member_count?: number;
  user_count?: number;
  role_count?: number;
  project_count?: number;
}

interface GetWorkspacesQueryParams {
  page?: number;
  page_size?: number;
  search?: string;
  organization?: string;
  is_active?: boolean;
}

interface WorkspaceListResponse {
  workspaces: Workspace[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

export const useGetWorkspaces: useMutationFunctionType<
  undefined,
  GetWorkspacesQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getWorkspaces({
    page = 1,
    page_size = 50,
    search,
    organization,
    is_active,
  }: GetWorkspacesQueryParams): Promise<WorkspaceListResponse> {
    try {
      const params = new URLSearchParams();
      params.append("page", page.toString());
      params.append("page_size", page_size.toString());

      if (search) {
        params.append("search", search);
      }
      if (organization) {
        params.append("organization", organization);
      }
      if (is_active !== undefined) {
        params.append("is_active", is_active.toString());
      }

      const url = `${getURL("RBAC")}/workspaces/?${params.toString()}`;

      const res = await api.get(url);

      if (res.status === 200) {
        // Use normalized response handler
        const normalized = normalizeListResponse<Workspace>(
          res.data,
          "workspaces",
          page,
          page_size,
        );

        return {
          workspaces: normalized.items,
          total_count: normalized.total_count,
          page: normalized.page,
          page_size: normalized.page_size,
          has_next: normalized.has_next,
          has_previous: normalized.has_previous,
        };
      }

      return {
        workspaces: [],
        total_count: 0,
        page: page,
        page_size: page_size,
        has_next: false,
        has_previous: false,
      };
    } catch (error) {
      handleRBACError(error, "workspace list");
    }
  }

  const mutation: UseMutationResult<
    WorkspaceListResponse,
    any,
    GetWorkspacesQueryParams
  > = mutate(["useGetWorkspaces"], getWorkspaces, options || {});

  return mutation;
};

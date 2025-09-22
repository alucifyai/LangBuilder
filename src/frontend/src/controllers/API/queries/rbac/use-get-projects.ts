import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import { handleRBACError, normalizeListResponse } from "./error-handler";

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
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  is_archived?: boolean;
}

interface ProjectListResponse {
  projects: Project[];
  total_count: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

export const useGetProjects: useMutationFunctionType<
  undefined,
  GetProjectsQueryParams,
  ProjectListResponse
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getProjects({
    workspace_id,
    page = 1,
    page_size = 50,
    search,
    is_active,
    is_archived,
  }: GetProjectsQueryParams): Promise<ProjectListResponse> {
    const params = new URLSearchParams();
    params.append("page", page.toString());
    params.append("page_size", page_size.toString());

    if (workspace_id) {
      params.append("workspace_id", workspace_id);
    }
    if (search) {
      params.append("search", search);
    }
    if (is_active !== undefined) {
      params.append("is_active", is_active.toString());
    }
    if (is_archived !== undefined) {
      params.append("is_archived", is_archived.toString());
    }

    const url = `${getURL("RBAC")}/projects/?${params.toString()}`;

    try {
      const res = await api.get(url);

      if (res.status === 200) {
        // Use normalized response handler
        const normalized = normalizeListResponse<Project>(
          res.data,
          "projects",
          page,
          page_size,
        );

        return {
          projects: normalized.items,
          total_count: normalized.total_count,
          page: normalized.page,
          page_size: normalized.page_size,
          has_next: normalized.has_next,
          has_previous: normalized.has_previous,
        };
      }

      return {
        projects: [],
        total_count: 0,
        page: page,
        page_size: page_size,
        has_next: false,
        has_previous: false,
      };
    } catch (error) {
      handleRBACError(error, "project list");
    }
  }

  const mutation: UseMutationResult<
    ProjectListResponse,
    any,
    GetProjectsQueryParams
  > = mutate(["useGetProjects"], getProjects, options || {});

  return mutation;
};

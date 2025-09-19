import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { Workspace } from "./use-get-workspaces";

export interface CreateWorkspaceData {
  name: string;
  description?: string;
  is_active?: boolean;
}

export const useCreateWorkspace: useMutationFunctionType<
  undefined,
  CreateWorkspaceData
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function createWorkspace(
    workspaceData: CreateWorkspaceData,
  ): Promise<Workspace> {
    try {
      console.log("Creating workspace with data:", workspaceData);
      const res = await api.post(
        `${getURL("RBAC")}/workspaces/`,
        workspaceData,
      );
      console.log("Create workspace response:", res.status, res.data);

      if (res.status === 201) {
        return res.data;
      }
      throw new Error(`Failed to create workspace: ${res.status}`);
    } catch (error: any) {
      console.error("Create workspace error:", error);

      // Extract meaningful error message from response
      let errorMessage = "Unknown error";
      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error?.message) {
        errorMessage = error.message;
      }

      throw new Error(errorMessage);
    }
  }

  const mutation: UseMutationResult<Workspace, any, CreateWorkspaceData> =
    mutate(["useCreateWorkspace"], createWorkspace, options);

  return mutation;
};

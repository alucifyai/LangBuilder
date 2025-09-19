import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { Workspace } from "./use-get-workspaces";

export interface UpdateWorkspaceData {
  workspace_id: string;
  workspace: {
    name?: string;
    description?: string;
    is_active?: boolean;
  };
}

export const useUpdateWorkspace: useMutationFunctionType<
  undefined,
  UpdateWorkspaceData
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function updateWorkspace({
    workspace_id,
    workspace,
  }: UpdateWorkspaceData): Promise<Workspace> {
    try {
      console.log("Updating workspace:", workspace_id, "with data:", workspace);
      const res = await api.put(
        `${getURL("RBAC")}/workspaces/${workspace_id}`,
        workspace,
      );
      console.log("Update workspace response:", res.status, res.data);

      if (res.status === 200 || res.status === 201 || res.status === 204) {
        return res.data;
      }
      throw new Error(`Failed to update workspace: ${res.status}`);
    } catch (error: any) {
      console.error("Update workspace error:", error);

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

  const mutation: UseMutationResult<Workspace, any, UpdateWorkspaceData> =
    mutate(["useUpdateWorkspace"], updateWorkspace, options);

  return mutation;
};

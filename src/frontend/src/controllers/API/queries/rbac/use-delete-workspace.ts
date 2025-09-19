import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface DeleteWorkspaceData {
  workspace_id: string;
}

export const useDeleteWorkspace: useMutationFunctionType<
  undefined,
  DeleteWorkspaceData
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function deleteWorkspace({
    workspace_id,
  }: DeleteWorkspaceData): Promise<{ success: boolean }> {
    try {
      console.log("Deleting workspace:", workspace_id);
      const res = await api.delete(
        `${getURL("RBAC")}/workspaces/${workspace_id}`,
      );
      console.log("Delete workspace response:", res.status);

      if (res.status === 204 || res.status === 200) {
        return { success: true };
      }
      throw new Error(`Failed to delete workspace: ${res.status}`);
    } catch (error: any) {
      console.error("Delete workspace error:", error);

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

  const mutation: UseMutationResult<
    { success: boolean },
    any,
    DeleteWorkspaceData
  > = mutate(["useDeleteWorkspace"], deleteWorkspace, options);

  return mutation;
};

import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface DeleteWorkspaceData {
  workspace_id: string;
}

export const useDeleteSimpleWorkspace: useMutationFunctionType<
  undefined,
  DeleteWorkspaceData,
  { success: boolean; message: string }
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function deleteWorkspace({
    workspace_id,
  }: DeleteWorkspaceData): Promise<{ success: boolean; message: string }> {
    const res = await api.delete(
      `${getURL("RBAC")}/simple-workspaces/${workspace_id}`,
    );
    if (res.status === 200) {
      return res.data;
    }
    throw new Error(`Failed to delete workspace: ${res.status}`);
  }

  const mutation: UseMutationResult<
    { success: boolean; message: string },
    any,
    DeleteWorkspaceData
  > = mutate(["useDeleteSimpleWorkspace"], deleteWorkspace, options);

  return mutation;
};

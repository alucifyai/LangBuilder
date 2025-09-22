import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { Workspace } from "./use-get-simple-workspaces";

export interface UpdateWorkspaceData {
  workspace_id: string;
  workspace: {
    name?: string;
    description?: string;
    is_active?: boolean;
  };
}

export const useUpdateSimpleWorkspace: useMutationFunctionType<
  undefined,
  UpdateWorkspaceData,
  Workspace
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function updateWorkspace({
    workspace_id,
    workspace,
  }: UpdateWorkspaceData): Promise<Workspace> {
    const res = await api.put(
      `${getURL("RBAC")}/simple-workspaces/${workspace_id}`,
      workspace,
    );
    if (res.status === 200) {
      // Simple endpoint returns {success: true, workspace: {...}}
      if (res.data.success && res.data.workspace) {
        return res.data.workspace;
      }
      return res.data; // Fallback if structure is different
    }
    throw new Error(`Failed to update workspace: ${res.status}`);
  }

  const mutation: UseMutationResult<Workspace, any, UpdateWorkspaceData> =
    mutate(["useUpdateSimpleWorkspace"], updateWorkspace, options);

  return mutation;
};

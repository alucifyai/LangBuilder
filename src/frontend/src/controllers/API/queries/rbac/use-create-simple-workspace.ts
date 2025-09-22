import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { Workspace } from "./use-get-simple-workspaces";

export interface CreateWorkspaceData {
  name: string;
  description?: string;
  is_active?: boolean;
}

export const useCreateSimpleWorkspace: useMutationFunctionType<
  undefined,
  CreateWorkspaceData,
  Workspace
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function createWorkspace(
    workspaceData: CreateWorkspaceData,
  ): Promise<Workspace> {
    const res = await api.post(
      `${getURL("RBAC")}/simple-workspaces/`,
      workspaceData,
    );
    if (res.status === 200) {
      // Simple endpoint returns {success: true, workspace: {...}}
      if (res.data.success && res.data.workspace) {
        return res.data.workspace;
      }
      return res.data; // Fallback if structure is different
    }
    throw new Error(`Failed to create workspace: ${res.status}`);
  }

  const mutation: UseMutationResult<Workspace, any, CreateWorkspaceData> =
    mutate(["useCreateSimpleWorkspace"], createWorkspace, options);

  return mutation;
};

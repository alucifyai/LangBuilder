import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface RoleAssignment {
  id: string;
  role_id: string;
  role_name: string;
  principal_type: "user" | "service_account";
  principal_id: string;
  principal_name: string;
  scope_type: "global" | "workspace" | "project" | "environment";
  scope_id: string | null;
  scope_name?: string;
  granted_by_id: string;
  granted_by_name: string;
  granted_at: string;
  expires_at: string | null;
  is_active: boolean;
}

interface GetRoleAssignmentsQueryParams {
  workspace_id?: string;
  principal_id?: string;
  principal_type?: "user" | "service_account";
  role_id?: string;
  scope_type?: string;
  skip?: number;
  limit?: number;
}

export const useGetRoleAssignments: useMutationFunctionType<
  { assignments: RoleAssignment[]; total_count: number },
  GetRoleAssignmentsQueryParams
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getRoleAssignments({
    workspace_id,
    principal_id,
    principal_type,
    role_id,
    scope_type,
    skip = 0,
    limit = 50,
  }: GetRoleAssignmentsQueryParams): Promise<{ assignments: RoleAssignment[]; total_count: number }> {
    let url = `${getURL("RBAC")}/role-assignments/?skip=${skip}&limit=${limit}`;
    
    if (workspace_id) url += `&workspace_id=${workspace_id}`;
    if (principal_id) url += `&principal_id=${principal_id}`;
    if (principal_type) url += `&principal_type=${principal_type}`;
    if (role_id) url += `&role_id=${role_id}`;
    if (scope_type) url += `&scope_type=${scope_type}`;
    
    const res = await api.get(url);
    if (res.status === 200) {
      return res.data;
    }
    return { assignments: [], total_count: 0 };
  }

  const mutation: UseMutationResult<
    { assignments: RoleAssignment[]; total_count: number },
    any,
    GetRoleAssignmentsQueryParams
  > = mutate(["useGetRoleAssignments"], getRoleAssignments, options);

  return mutation;
};
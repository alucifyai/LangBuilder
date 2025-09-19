import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface RoleAssignment {
  id: string;
  role_id: string;
  role_name?: string;
  assignment_type: "user" | "group" | "service_account";
  scope_type: "workspace" | "project" | "environment" | "flow" | "component";

  // Assignee
  user_id?: string;
  user_name?: string;
  group_id?: string;
  group_name?: string;
  service_account_id?: string;
  service_account_name?: string;

  // Scope
  workspace_id?: string;
  workspace_name?: string;
  project_id?: string;
  project_name?: string;
  environment_id?: string;
  environment_name?: string;
  flow_id?: string;
  flow_name?: string;
  component_id?: string;

  // Assignment info
  assigned_by_id: string;
  assigned_by_name?: string;
  approved_by_id?: string;
  approved_by_name?: string;
  assigned_at: string;
  approved_at?: string;
  valid_from?: string;
  valid_until?: string;
  is_active: boolean;
  conditions?: Record<string, any>;
  ip_restrictions?: string[];
  time_restrictions?: Record<string, any>;
  reason?: string;
  approval_reason?: string;
}

interface GetRoleAssignmentsQueryParams {
  workspace_id: string; // Required in backend
  user_id?: string;
  role_id?: string;
  assignment_type?: "user" | "group" | "service_account";
  scope?: "workspace" | "project" | "environment" | "flow" | "component";
  is_active?: boolean;
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
    user_id,
    assignment_type,
    role_id,
    scope,
    is_active,
    skip = 0,
    limit = 50,
  }: GetRoleAssignmentsQueryParams): Promise<{
    assignments: RoleAssignment[];
    total_count: number;
  }> {
    let url = `${getURL("RBAC")}/role-assignments/?workspace_id=${workspace_id}&skip=${skip}&limit=${limit}`;

    if (user_id) url += `&user_id=${user_id}`;
    if (assignment_type) url += `&assignment_type=${assignment_type}`;
    if (role_id) url += `&role_id=${role_id}`;
    if (scope) url += `&scope=${scope}`;
    if (is_active !== undefined) url += `&is_active=${is_active}`;

    const res = await api.get(url);
    if (res.status === 200) {
      // Backend returns array directly, not wrapped in object
      return { assignments: res.data, total_count: res.data.length };
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

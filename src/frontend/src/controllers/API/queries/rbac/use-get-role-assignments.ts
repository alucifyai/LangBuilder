import type { UseMutationResult } from "@tanstack/react-query";
import { customGetAccessToken } from "@/customization/utils/custom-get-access-token";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import { handleRBACError } from "./error-handler";

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
  undefined,
  Partial<GetRoleAssignmentsQueryParams>,
  { assignments: RoleAssignment[]; total_count: number }
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function getRoleAssignments({
    workspace_id = "00000000-0000-0000-0000-000000000000", // Use default UUID for development
    user_id,
    assignment_type,
    role_id,
    scope,
    is_active,
    skip = 0,
    limit = 50,
  }: Partial<GetRoleAssignmentsQueryParams>): Promise<{
    assignments: RoleAssignment[];
    total_count: number;
  }> {
    try {
      // Build URL with required workspace_id as query parameter
      const params = new URLSearchParams();
      params.append("workspace_id", workspace_id);

      // Add optional parameters
      if (user_id) params.append("user_id", user_id);
      if (assignment_type) params.append("assignment_type", assignment_type);
      if (role_id) params.append("role_id", role_id);
      if (scope) params.append("scope", scope);
      if (is_active !== undefined)
        params.append("is_active", is_active.toString());

      const url = `${getURL("RBAC")}/role-assignments/?${params.toString()}`;

      // Debug authentication token
      const accessToken = customGetAccessToken ? customGetAccessToken() : null;
      console.log("🔍 RBAC Role Assignments API call:", {
        url,
        workspace_id,
        params: {
          user_id,
          assignment_type,
          role_id,
          scope,
          is_active,
          skip,
          limit,
        },
        hasAccessToken: !!accessToken,
        accessTokenLength: accessToken ? accessToken.length : 0,
      });

      // Use automatic authentication via interceptors (same as working roles/workspaces APIs)
      const res = await api.get(url);
      if (res.status === 200) {
        console.log("✅ Role assignments API response:", res.data);
        // Backend returns list of RoleAssignmentRead objects
        return { assignments: res.data, total_count: res.data.length };
      }
      return { assignments: [], total_count: 0 };
    } catch (error) {
      console.error("❌ Role assignments API error:", {
        error,
        status: error?.response?.status,
        data: error?.response?.data,
        message: error?.message,
        config: {
          url: error?.config?.url,
          headers: error?.config?.headers,
        },
      });

      // Handle "no data" cases gracefully instead of showing errors
      if (error?.response?.status === 404) {
        console.log("📝 No role assignments found, returning empty result");
        return { assignments: [], total_count: 0 };
      }

      handleRBACError(error, "role assignments list");
    }
  }

  const mutation: UseMutationResult<
    { assignments: RoleAssignment[]; total_count: number },
    any,
    Partial<GetRoleAssignmentsQueryParams>
  > = mutate(["useGetRoleAssignments"], getRoleAssignments, options);

  return mutation;
};

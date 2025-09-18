import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { RoleAssignment } from "./use-get-role-assignments";

export interface CreateRoleAssignmentData {
  role_id: string;
  principal_type: "user" | "service_account";
  principal_id: string;
  scope_type: "global" | "workspace" | "project" | "environment";
  scope_id?: string;
  expires_at?: string;
}

export const useCreateRoleAssignment: useMutationFunctionType<
  RoleAssignment,
  CreateRoleAssignmentData
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function createRoleAssignment(data: CreateRoleAssignmentData): Promise<RoleAssignment> {
    const res = await api.post(`${getURL("RBAC")}/role-assignments/`, data);
    if (res.status === 201) {
      return res.data;
    }
    throw new Error(`Failed to create role assignment: ${res.status}`);
  }

  const mutation: UseMutationResult<RoleAssignment, any, CreateRoleAssignmentData> = mutate(
    ["useCreateRoleAssignment"],
    createRoleAssignment,
    options
  );

  return mutation;
};
import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";

export interface CheckPermissionData {
  permission: string;
  scope_type?: string;
  scope_id?: string;
  resource_type?: string;
  resource_id?: string;
}

export interface PermissionResult {
  allowed: boolean;
  reason?: string;
  conditions_met?: string[];
  conditions_failed?: string[];
}

export const useCheckPermission: useMutationFunctionType<
  PermissionResult,
  CheckPermissionData
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function checkPermission(data: CheckPermissionData): Promise<PermissionResult> {
    const res = await api.post(`${getURL("RBAC")}/check-permission`, data);
    if (res.status === 200) {
      return res.data;
    }
    throw new Error(`Failed to check permission: ${res.status}`);
  }

  const mutation: UseMutationResult<PermissionResult, any, CheckPermissionData> = mutate(
    ["useCheckPermission"],
    checkPermission,
    options
  );

  return mutation;
};
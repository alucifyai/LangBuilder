import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { ServiceAccount } from "./use-get-service-accounts";

export interface CreateServiceAccountData {
  name: string;
  description?: string;
  workspace_id: string;
  scope_type: "global" | "workspace" | "project" | "environment";
  scope_id?: string;
  permissions: string[];
}

export const useCreateServiceAccount: useMutationFunctionType<
  undefined,
  CreateServiceAccountData,
  ServiceAccount
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function createServiceAccount(
    data: CreateServiceAccountData,
  ): Promise<ServiceAccount> {
    const res = await api.post(
      `${getURL("RBAC")}/simple-service-accounts/`,
      data,
    );
    if (res.status === 200) {
      // Simple endpoint returns {success: true, service_account: {...}}
      if (res.data.success && res.data.service_account) {
        return res.data.service_account;
      }
      return res.data; // Fallback if structure is different
    }
    throw new Error(`Failed to create service account: ${res.status}`);
  }

  const mutation: UseMutationResult<
    ServiceAccount,
    any,
    CreateServiceAccountData
  > = mutate(["useCreateServiceAccount"], createServiceAccount, options);

  return mutation;
};

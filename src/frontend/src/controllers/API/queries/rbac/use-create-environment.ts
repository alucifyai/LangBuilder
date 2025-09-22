import type { UseMutationResult } from "@tanstack/react-query";
import type { useMutationFunctionType } from "../../../../types/api";
import { api } from "../../api";
import { getURL } from "../../helpers/constants";
import { UseRequestProcessor } from "../../services/request-processor";
import type { Environment } from "./use-get-environments";

export interface CreateEnvironmentData {
  name: string;
  description?: string;
  project_id: string;
  type: "development" | "staging" | "production" | "testing";
  is_default?: boolean;
  variables?: Record<string, any>;
}

export const useCreateEnvironment: useMutationFunctionType<
  undefined,
  CreateEnvironmentData,
  Environment
> = (options?) => {
  const { mutate } = UseRequestProcessor();

  async function createEnvironment(
    data: CreateEnvironmentData,
  ): Promise<Environment> {
    const res = await api.post(`${getURL("RBAC")}/simple-environments/`, data);
    if (res.status === 200) {
      // Simple endpoint returns {success: true, environment: {...}}
      if (res.data.success && res.data.environment) {
        return res.data.environment;
      }
      return res.data; // Fallback if structure is different
    }
    throw new Error(`Failed to create environment: ${res.status}`);
  }

  const mutation: UseMutationResult<Environment, any, CreateEnvironmentData> =
    mutate(["useCreateEnvironment"], createEnvironment, options);

  return mutation;
};

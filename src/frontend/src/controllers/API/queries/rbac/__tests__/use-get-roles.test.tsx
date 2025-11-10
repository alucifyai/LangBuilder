/**
 * useGetRoles Hook Tests
 *
 * Task 4.2: Test roles fetching query hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useGetRoles } from "../use-get-roles";
import { api } from "../../../api";

// Mock stores that use import.meta
jest.mock("../../../../../stores/darkStore", () => ({
  useDarkStore: jest.fn(() => ({
    dark: false,
    setDark: jest.fn(),
  })),
}));

jest.mock("../../../../../stores/flowStore", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    nodes: [],
    edges: [],
  })),
}));

jest.mock("../../../../../stores/alertStore", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    setSuccessData: jest.fn(),
    setErrorData: jest.fn(),
  })),
}));

jest.mock("../../../api");

describe("useGetRoles", () => {
  let queryClient: QueryClient;

  const mockRoles = [
    {
      id: "role-admin",
      name: "Admin",
      description: "Administrator role",
      is_system: true,
    },
    {
      id: "role-owner",
      name: "Owner",
      description: "Owner role",
      is_system: true,
    },
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    (api.get as jest.Mock).mockResolvedValue({
      data: mockRoles,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should fetch roles successfully", async () => {
    const { result } = renderHook(() => useGetRoles(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockRoles);
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining("/rbac/roles"));
  });

  it("should handle API errors", async () => {
    const error = new Error("Failed to fetch roles");
    (api.get as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useGetRoles(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it("should respect enabled option", async () => {
    const { result } = renderHook(() => useGetRoles({ enabled: false }), {
      wrapper,
    });

    await waitFor(() => {
      expect(result.current.isFetching).toBe(false);
    });

    expect(api.get).not.toHaveBeenCalled();
  });

  it("should cache roles with correct key", async () => {
    const { result } = renderHook(() => useGetRoles(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const cachedData = queryClient.getQueryData(["rbac-roles"]);
    expect(cachedData).toEqual(mockRoles);
  });
});

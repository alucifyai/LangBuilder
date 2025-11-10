/**
 * useGetAssignments Hook Tests
 *
 * Task 4.2: Test assignment fetching query hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useGetAssignments } from "../use-get-assignments";
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

describe("useGetAssignments", () => {
  let queryClient: QueryClient;

  const mockAssignments = [
    {
      id: "assignment-1",
      user_id: "user-123",
      role_id: "role-admin",
      scope_type: "Global",
      scope_id: null,
      is_immutable: false,
      created_at: "2024-01-01T00:00:00Z",
      created_by: "admin-user",
    },
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    (api.get as jest.Mock).mockResolvedValue({
      data: mockAssignments,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should fetch assignments successfully", async () => {
    const { result } = renderHook(() => useGetAssignments(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAssignments);
    expect(api.get).toHaveBeenCalledWith(expect.stringContaining("/rbac/assignments"));
  });

  it("should fetch assignments with user_id filter", async () => {
    const { result } = renderHook(
      () => useGetAssignments({ user_id: "user-123" }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("user_id=user-123")
    );
  });

  it("should fetch assignments with role_id filter", async () => {
    const { result } = renderHook(
      () => useGetAssignments({ role_id: "role-admin" }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("role_id=role-admin")
    );
  });

  it("should fetch assignments with scope_type filter", async () => {
    const { result } = renderHook(
      () => useGetAssignments({ scope_type: "Global" }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("scope_type=Global")
    );
  });

  it("should fetch assignments with multiple filters", async () => {
    const { result } = renderHook(
      () =>
        useGetAssignments({
          user_id: "user-123",
          role_id: "role-admin",
          scope_type: "Global",
        }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    const calledUrl = (api.get as jest.Mock).mock.calls[0][0];
    expect(calledUrl).toContain("user_id=user-123");
    expect(calledUrl).toContain("role_id=role-admin");
    expect(calledUrl).toContain("scope_type=Global");
  });

  it("should handle API errors", async () => {
    const error = new Error("Failed to fetch");
    (api.get as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useGetAssignments(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it("should respect enabled option", async () => {
    const { result } = renderHook(
      () => useGetAssignments(undefined, { enabled: false }),
      { wrapper }
    );

    await waitFor(() => {
      expect(result.current.isFetching).toBe(false);
    });

    expect(api.get).not.toHaveBeenCalled();
  });

  it("should use correct cache key with filters", async () => {
    const params = { user_id: "user-123" };
    const { result } = renderHook(() => useGetAssignments(params), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Check that the query is cached with the correct key
    const cachedData = queryClient.getQueryData(["rbac-assignments", params]);
    expect(cachedData).toEqual(mockAssignments);
  });
});

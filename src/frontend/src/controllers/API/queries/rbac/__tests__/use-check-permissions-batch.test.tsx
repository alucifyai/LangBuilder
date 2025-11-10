import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { useCheckPermissionsBatch } from "../use-check-permissions-batch";
import { api } from "../../../api";

// Mock the API
jest.mock("../../../api", () => ({
  api: {
    post: jest.fn(),
  },
}));

// Mock the getURL helper
jest.mock("../../../helpers/constants", () => ({
  getURL: jest.fn((key: string) => `/api/v1/${key.toLowerCase()}`),
}));

describe("useCheckPermissionsBatch", () => {
  let queryClient: QueryClient;

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    jest.clearAllMocks();
  });

  afterEach(() => {
    queryClient.clear();
  });

  it("should check permissions for multiple resources successfully", async () => {
    const mockResponse = {
      results: {
        "flow-1": true,
        "flow-2": false,
        "flow-3": true,
      },
    };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "DELETE",
          resources: [
            { id: "flow-1", scope_type: "Flow", scope_id: "flow-1" },
            { id: "flow-2", scope_type: "Flow", scope_id: "flow-2" },
            { id: "flow-3", scope_type: "Flow", scope_id: "flow-3" },
          ],
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockResponse);
    expect(result.current.data?.results["flow-1"]).toBe(true);
    expect(result.current.data?.results["flow-2"]).toBe(false);
    expect(result.current.data?.results["flow-3"]).toBe(true);
    expect(api.post).toHaveBeenCalledWith("/api/v1/rbac/check-permissions-batch", {
      permission: "DELETE",
      resources: [
        { id: "flow-1", scope_type: "Flow", scope_id: "flow-1" },
        { id: "flow-2", scope_type: "Flow", scope_id: "flow-2" },
        { id: "flow-3", scope_type: "Flow", scope_id: "flow-3" },
      ],
    });
  });

  it("should handle empty resources array", async () => {
    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "READ",
          resources: [],
        }),
      { wrapper }
    );

    // Query should be disabled when resources array is empty
    expect(result.current.status).toBe("pending");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("should handle single resource", async () => {
    const mockResponse = {
      results: {
        "project-1": true,
      },
    };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "UPDATE",
          resources: [{ id: "project-1", scope_type: "Project", scope_id: "project-1" }],
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.results["project-1"]).toBe(true);
  });

  it("should handle API errors", async () => {
    const mockError = new Error("Batch API Error");
    (api.post as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "CREATE",
          resources: [{ id: "project-1", scope_type: "Project", scope_id: "project-1" }],
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });

  it("should be disabled when enabled option is false", async () => {
    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch(
          {
            permission: "DELETE",
            resources: [{ id: "flow-1", scope_type: "Flow", scope_id: "flow-1" }],
          },
          { enabled: false }
        ),
      { wrapper }
    );

    expect(result.current.status).toBe("pending");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("should handle resources without scope_id (Global scope)", async () => {
    const mockResponse = {
      results: {
        "global-1": true,
        "global-2": true,
      },
    };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "READ",
          resources: [
            { id: "global-1", scope_type: "Global" },
            { id: "global-2", scope_type: "Global" },
          ],
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.results["global-1"]).toBe(true);
    expect(result.current.data?.results["global-2"]).toBe(true);
  });

  it("should cache results with same query key", async () => {
    const mockResponse = {
      results: {
        "flow-1": true,
        "flow-2": false,
      },
    };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const request = {
      permission: "DELETE" as const,
      resources: [
        { id: "flow-1", scope_type: "Flow" as const, scope_id: "flow-1" },
        { id: "flow-2", scope_type: "Flow" as const, scope_id: "flow-2" },
      ],
    };

    // First hook instance
    const { result: result1 } = renderHook(() => useCheckPermissionsBatch(request), {
      wrapper,
    });

    await waitFor(() => expect(result1.current.isSuccess).toBe(true));

    // Second hook instance with same request
    const { result: result2 } = renderHook(() => useCheckPermissionsBatch(request), {
      wrapper,
    });

    await waitFor(() => expect(result2.current.isSuccess).toBe(true));

    // Should only call API once due to caching
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(result2.current.data).toEqual(mockResponse);
  });

  it("should handle mixed permission results", async () => {
    const mockResponse = {
      results: {
        "resource-1": true,
        "resource-2": true,
        "resource-3": false,
        "resource-4": false,
        "resource-5": true,
      },
    };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "UPDATE",
          resources: [
            { id: "resource-1", scope_type: "Project", scope_id: "resource-1" },
            { id: "resource-2", scope_type: "Flow", scope_id: "resource-2" },
            { id: "resource-3", scope_type: "Project", scope_id: "resource-3" },
            { id: "resource-4", scope_type: "Flow", scope_id: "resource-4" },
            { id: "resource-5", scope_type: "Project", scope_id: "resource-5" },
          ],
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const results = result.current.data?.results;
    expect(results?.["resource-1"]).toBe(true);
    expect(results?.["resource-2"]).toBe(true);
    expect(results?.["resource-3"]).toBe(false);
    expect(results?.["resource-4"]).toBe(false);
    expect(results?.["resource-5"]).toBe(true);
  });

  it("should handle large batch of resources", async () => {
    const mockResults: Record<string, boolean> = {};
    const resources = [];

    // Create 100 resources
    for (let i = 1; i <= 100; i++) {
      const id = `flow-${i}`;
      resources.push({ id, scope_type: "Flow" as const, scope_id: id });
      mockResults[id] = i % 2 === 0; // Even numbers allowed, odd numbers denied
    }

    const mockResponse = { results: mockResults };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermissionsBatch({
          permission: "DELETE",
          resources,
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(Object.keys(result.current.data?.results ?? {}).length).toBe(100);
    expect(result.current.data?.results["flow-2"]).toBe(true);
    expect(result.current.data?.results["flow-3"]).toBe(false);
  });
});

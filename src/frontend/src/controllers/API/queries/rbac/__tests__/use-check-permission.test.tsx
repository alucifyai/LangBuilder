import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode } from "react";
import { useCheckPermission } from "../use-check-permission";
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

describe("useCheckPermission", () => {
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

  it("should check permission successfully", async () => {
    const mockResponse = { allowed: true };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermission({
          permission: "CREATE",
          scope_type: "Project",
          scope_id: "project-123",
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockResponse);
    expect(result.current.data?.allowed).toBe(true);
    expect(api.post).toHaveBeenCalledWith("/api/v1/rbac/check-permission", {
      permission: "CREATE",
      scope_type: "Project",
      scope_id: "project-123",
    });
  });

  it("should handle permission denied", async () => {
    const mockResponse = { allowed: false };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermission({
          permission: "DELETE",
          scope_type: "Flow",
          scope_id: "flow-123",
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.allowed).toBe(false);
  });

  it("should work without scope_id for Global permissions", async () => {
    const mockResponse = { allowed: true };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const { result } = renderHook(
      () =>
        useCheckPermission({
          permission: "CREATE",
          scope_type: "Global",
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.allowed).toBe(true);
    expect(api.post).toHaveBeenCalledWith("/api/v1/rbac/check-permission", {
      permission: "CREATE",
      scope_type: "Global",
    });
  });

  it("should handle API errors", async () => {
    const mockError = new Error("API Error");
    (api.post as jest.Mock).mockRejectedValue(mockError);

    const { result } = renderHook(
      () =>
        useCheckPermission({
          permission: "READ",
          scope_type: "Project",
          scope_id: "project-123",
        }),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });

  it("should be disabled when enabled option is false", async () => {
    const { result } = renderHook(
      () =>
        useCheckPermission(
          {
            permission: "CREATE",
            scope_type: "Project",
            scope_id: "project-123",
          },
          { enabled: false }
        ),
      { wrapper }
    );

    // Should not make API call when disabled
    expect(result.current.status).toBe("pending");
    expect(api.post).not.toHaveBeenCalled();
  });

  it("should cache results with same query key", async () => {
    const mockResponse = { allowed: true };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const request = {
      permission: "UPDATE" as const,
      scope_type: "Flow" as const,
      scope_id: "flow-123",
    };

    // First hook instance
    const { result: result1 } = renderHook(() => useCheckPermission(request), {
      wrapper,
    });

    await waitFor(() => expect(result1.current.isSuccess).toBe(true));

    // Second hook instance with same request
    const { result: result2 } = renderHook(() => useCheckPermission(request), {
      wrapper,
    });

    await waitFor(() => expect(result2.current.isSuccess).toBe(true));

    // Should only call API once due to caching
    expect(api.post).toHaveBeenCalledTimes(1);
    expect(result2.current.data).toEqual(mockResponse);
  });

  it("should handle different permission types", async () => {
    const mockResponse = { allowed: true };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const permissions = ["CREATE", "READ", "UPDATE", "DELETE"] as const;

    for (const permission of permissions) {
      jest.clearAllMocks();

      const { result } = renderHook(
        () =>
          useCheckPermission({
            permission,
            scope_type: "Project",
            scope_id: "project-123",
          }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(api.post).toHaveBeenCalledWith("/api/v1/rbac/check-permission", {
        permission,
        scope_type: "Project",
        scope_id: "project-123",
      });
    }
  });

  it("should handle different scope types", async () => {
    const mockResponse = { allowed: true };
    (api.post as jest.Mock).mockResolvedValue({ data: mockResponse });

    const scopeTypes = ["Project", "Flow", "Global"] as const;

    for (const scope_type of scopeTypes) {
      jest.clearAllMocks();

      const { result } = renderHook(
        () =>
          useCheckPermission({
            permission: "READ",
            scope_type,
            scope_id: scope_type !== "Global" ? "resource-123" : undefined,
          }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.allowed).toBe(true);
    }
  });
});

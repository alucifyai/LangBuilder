/**
 * useDeleteAssignment Hook Tests
 *
 * Task 4.2: Test assignment deletion mutation hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useDeleteAssignment } from "../use-delete-assignment";
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

describe("useDeleteAssignment", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        mutations: { retry: false },
      },
    });

    (api.delete as jest.Mock).mockResolvedValue({});
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should delete assignment successfully", async () => {
    const { result } = renderHook(() => useDeleteAssignment(), { wrapper });

    result.current.mutate("assignment-123");

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.delete).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments/assignment-123")
    );
  });

  it("should handle deletion errors", async () => {
    const error = {
      response: {
        data: {
          detail: "Cannot delete immutable assignment",
        },
      },
    };
    (api.delete as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useDeleteAssignment(), { wrapper });

    result.current.mutate("assignment-123");

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it("should invalidate assignments query on success", async () => {
    const invalidateQueriesSpy = jest.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useDeleteAssignment(), { wrapper });

    result.current.mutate("assignment-123");

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: ["rbac-assignments"],
    });
  });

  it("should support mutateAsync", async () => {
    const { result } = renderHook(() => useDeleteAssignment(), { wrapper });

    await result.current.mutateAsync("assignment-123");

    expect(api.delete).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments/assignment-123")
    );
  });
});

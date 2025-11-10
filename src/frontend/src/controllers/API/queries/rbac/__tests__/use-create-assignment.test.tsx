/**
 * useCreateAssignment Hook Tests
 *
 * Task 4.3: Test assignment creation mutation hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useCreateAssignment } from "../use-create-assignment";
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

describe("useCreateAssignment", () => {
  let queryClient: QueryClient;

  const mockAssignment = {
    id: "assignment-123",
    user_id: "user-456",
    role_id: "role-owner",
    scope_type: "Project",
    scope_id: "project-789",
    is_immutable: false,
    created_at: "2024-01-01T00:00:00Z",
    created_by: "admin-user",
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        mutations: { retry: false },
      },
    });

    (api.post as jest.Mock).mockResolvedValue({
      data: mockAssignment,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should create assignment successfully with Project scope", async () => {
    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-owner",
      scope_type: "Project" as const,
      scope_id: "project-789",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.post).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments"),
      request
    );
    expect(result.current.data).toEqual(mockAssignment);
  });

  it("should create assignment successfully with Global scope", async () => {
    const globalAssignment = { ...mockAssignment, scope_type: "Global", scope_id: null };
    (api.post as jest.Mock).mockResolvedValue({ data: globalAssignment });

    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-admin",
      scope_type: "Global" as const,
      scope_id: null,
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.post).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments"),
      request
    );
    expect(result.current.data).toEqual(globalAssignment);
  });

  it("should create assignment successfully with Flow scope", async () => {
    const flowAssignment = { ...mockAssignment, scope_type: "Flow", scope_id: "flow-123" };
    (api.post as jest.Mock).mockResolvedValue({ data: flowAssignment });

    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-editor",
      scope_type: "Flow" as const,
      scope_id: "flow-123",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.post).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments"),
      request
    );
    expect(result.current.data).toEqual(flowAssignment);
  });

  it("should handle creation errors", async () => {
    const error = {
      response: {
        data: {
          detail: "Assignment already exists",
        },
      },
    };
    (api.post as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-owner",
      scope_type: "Project" as const,
      scope_id: "project-789",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it("should handle validation errors", async () => {
    const error = {
      response: {
        data: {
          detail: "Invalid user_id",
        },
      },
    };
    (api.post as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "invalid-user",
      role_id: "role-owner",
      scope_type: "Project" as const,
      scope_id: "project-789",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error?.response?.data?.detail).toBe("Invalid user_id");
  });

  it("should invalidate assignments query on success", async () => {
    const invalidateQueriesSpy = jest.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-owner",
      scope_type: "Project" as const,
      scope_id: "project-789",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(invalidateQueriesSpy).toHaveBeenCalledWith({
      queryKey: ["rbac-assignments"],
    });
  });

  it("should support mutateAsync", async () => {
    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-owner",
      scope_type: "Project" as const,
      scope_id: "project-789",
    };

    const response = await result.current.mutateAsync(request);

    expect(api.post).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments"),
      request
    );
    expect(response).toEqual(mockAssignment);
  });

  it("should handle network errors", async () => {
    const error = new Error("Network error");
    (api.post as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useCreateAssignment(), { wrapper });

    const request = {
      user_id: "user-456",
      role_id: "role-owner",
      scope_type: "Project" as const,
      scope_id: "project-789",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });
});

/**
 * useUpdateAssignment Hook Tests
 *
 * Task 4.3: Test assignment update mutation hook
 */

import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useUpdateAssignment } from "../use-update-assignment";
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

describe("useUpdateAssignment", () => {
  let queryClient: QueryClient;

  const mockUpdatedAssignment = {
    id: "assignment-123",
    user_id: "user-456",
    role_id: "role-editor",
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

    (api.put as jest.Mock).mockResolvedValue({
      data: mockUpdatedAssignment,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should update assignment role successfully", async () => {
    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "role-editor",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments/assignment-123"),
      { role_id: "role-editor" }
    );
    expect(result.current.data).toEqual(mockUpdatedAssignment);
  });

  it("should handle update to different role", async () => {
    const ownerAssignment = { ...mockUpdatedAssignment, role_id: "role-owner" };
    (api.put as jest.Mock).mockResolvedValue({ data: ownerAssignment });

    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "role-owner",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments/assignment-123"),
      { role_id: "role-owner" }
    );
    expect(result.current.data?.role_id).toBe("role-owner");
  });

  it("should handle immutable assignment update errors", async () => {
    const error = {
      response: {
        data: {
          detail: "Cannot modify immutable assignment",
        },
      },
    };
    (api.put as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "role-editor",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it("should handle invalid role_id errors", async () => {
    const error = {
      response: {
        data: {
          detail: "Role not found",
        },
      },
    };
    (api.put as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "invalid-role",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error?.response?.data?.detail).toBe("Role not found");
  });

  it("should handle assignment not found errors", async () => {
    const error = {
      response: {
        data: {
          detail: "Assignment not found",
        },
      },
    };
    (api.put as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "nonexistent-assignment",
      role_id: "role-editor",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error?.response?.data?.detail).toBe("Assignment not found");
  });

  it("should invalidate assignments query on success", async () => {
    const invalidateQueriesSpy = jest.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "role-editor",
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
    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "role-editor",
    };

    const response = await result.current.mutateAsync(request);

    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments/assignment-123"),
      { role_id: "role-editor" }
    );
    expect(response).toEqual(mockUpdatedAssignment);
  });

  it("should handle network errors", async () => {
    const error = new Error("Network error");
    (api.put as jest.Mock).mockRejectedValue(error);

    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "assignment-123",
      role_id: "role-editor",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(error);
  });

  it("should call correct API endpoint with assignment_id", async () => {
    const { result } = renderHook(() => useUpdateAssignment(), { wrapper });

    const request = {
      assignment_id: "test-assignment-456",
      role_id: "role-viewer",
    };

    result.current.mutate(request);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(api.put).toHaveBeenCalledWith(
      expect.stringContaining("/rbac/assignments/test-assignment-456"),
      { role_id: "role-viewer" }
    );
  });
});

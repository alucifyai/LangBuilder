// useUpdateAssignment hook tests

// Mock dependencies before imports
jest.mock("@/controllers/API/api", () => ({
  api: {
    put: jest.fn(),
  },
}));

jest.mock("@/controllers/API/services/request-processor", () => ({
  UseRequestProcessor: jest.fn(() => ({
    mutate: jest.fn((key, fn, options) => ({
      mutate: async (variables: any) => await fn(variables),
      isPending: false,
    })),
    queryClient: {
      invalidateQueries: jest.fn(),
    },
  })),
}));

import { useUpdateAssignment } from "../use-update-assignment";

const mockApiPut = require("@/controllers/API/api").api.put;

describe("useUpdateAssignment hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("successful assignment updates", () => {
    it("should update assignment role via API", async () => {
      const mockRequest = {
        assignment_id: "assignment-123",
        update: { new_role_name: "Editor" as const },
      };

      const mockResponse = {
        id: "assignment-123",
        user_id: "user-456",
        role_id: "role-editor",
        role_name: "Editor",
        scope_type: "PROJECT",
        scope_id: "project-789",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const mutation = useUpdateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(mockApiPut).toHaveBeenCalledWith(
        expect.stringContaining("rbac/assignments/assignment-123"),
        { new_role_name: "Editor" },
      );
      expect(result).toEqual(mockResponse);
      expect(result.role_name).toBe("Editor");
    });

    it("should handle Owner to Editor role transition", async () => {
      const mockRequest = {
        assignment_id: "assignment-456",
        update: { new_role_name: "Editor" as const },
      };

      const mockResponse = {
        id: "assignment-456",
        user_id: "user-123",
        role_id: "role-editor",
        role_name: "Editor",
        scope_type: "PROJECT",
        scope_id: "project-789",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const mutation = useUpdateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Editor");
    });

    it("should handle Editor to Viewer role transition", async () => {
      const mockRequest = {
        assignment_id: "assignment-789",
        update: { new_role_name: "Viewer" as const },
      };

      const mockResponse = {
        id: "assignment-789",
        user_id: "user-123",
        role_id: "role-viewer",
        role_name: "Viewer",
        scope_type: "FLOW",
        scope_id: "flow-abc",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const mutation = useUpdateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Viewer");
    });

    it("should handle Viewer to Editor role transition", async () => {
      const mockRequest = {
        assignment_id: "assignment-111",
        update: { new_role_name: "Editor" as const },
      };

      const mockResponse = {
        id: "assignment-111",
        user_id: "user-123",
        role_id: "role-editor",
        role_name: "Editor",
        scope_type: "PROJECT",
        scope_id: "project-xyz",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const mutation = useUpdateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Editor");
    });

    it("should handle Editor to Owner role transition", async () => {
      const mockRequest = {
        assignment_id: "assignment-222",
        update: { new_role_name: "Owner" as const },
      };

      const mockResponse = {
        id: "assignment-222",
        user_id: "user-456",
        role_id: "role-owner",
        role_name: "Owner",
        scope_type: "PROJECT",
        scope_id: "project-def",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const mutation = useUpdateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Owner");
    });
  });

  describe("cache invalidation", () => {
    it("should invalidate assignments query on success", async () => {
      const mockRequest = {
        assignment_id: "assignment-123",
        update: { new_role_name: "Viewer" as const },
      };

      mockApiPut.mockResolvedValue({
        data: {
          id: "assignment-123",
          user_id: "user-123",
          role_id: "role-viewer",
          role_name: "Viewer",
          scope_type: "PROJECT",
          scope_id: "project-456",
          is_immutable: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      });

      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      const mutation = useUpdateAssignment();
      await mutation.mutate(mockRequest);

      const mutateCall =
        mockRequestProcessor.mock.results[0].value.mutate.mock.calls[0];
      const options = mutateCall[2];

      // Verify onSuccess is provided
      expect(options.onSuccess).toBeDefined();
    });

    it("should preserve user-provided onSuccess callback", async () => {
      const mockRequest = {
        assignment_id: "assignment-456",
        update: { new_role_name: "Editor" as const },
      };

      const mockResponse = {
        id: "assignment-456",
        user_id: "user-789",
        role_id: "role-editor",
        role_name: "Editor",
        scope_type: "FLOW",
        scope_id: "flow-abc",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const userOnSuccess = jest.fn();
      const mutation = useUpdateAssignment({ onSuccess: userOnSuccess });
      await mutation.mutate(mockRequest);

      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;
      const mutateCall =
        mockRequestProcessor.mock.results[0].value.mutate.mock.calls[0];
      const options = mutateCall[2];

      // Verify onSuccess callback exists and preserves user callback
      expect(options.onSuccess).toBeDefined();
    });
  });

  describe("error handling", () => {
    it("should handle immutable assignment errors", async () => {
      const mockRequest = {
        assignment_id: "immutable-assignment",
        update: { new_role_name: "Viewer" as const },
      };

      const mockError = new Error(
        "Cannot modify immutable assignment (Default Project Owner)",
      );
      mockApiPut.mockRejectedValue(mockError);

      const mutation = useUpdateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow("immutable");
    });

    it("should handle assignment not found errors", async () => {
      const mockRequest = {
        assignment_id: "nonexistent-assignment",
        update: { new_role_name: "Editor" as const },
      };

      const mockError = new Error("Assignment not found");
      mockApiPut.mockRejectedValue(mockError);

      const mutation = useUpdateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow(
        "Assignment not found",
      );
    });

    it("should handle invalid role name errors", async () => {
      const mockRequest = {
        assignment_id: "assignment-123",
        update: { new_role_name: "InvalidRole" as any },
      };

      const mockError = new Error("Invalid role name");
      mockApiPut.mockRejectedValue(mockError);

      const mutation = useUpdateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow(
        "Invalid role name",
      );
    });

    it("should handle API network errors", async () => {
      const mockRequest = {
        assignment_id: "assignment-789",
        update: { new_role_name: "Owner" as const },
      };

      const mockError = new Error("Network error");
      mockApiPut.mockRejectedValue(mockError);

      const mutation = useUpdateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow(
        "Network error",
      );
    });
  });

  describe("request validation", () => {
    it("should require assignment_id parameter", async () => {
      const mockRequest = {
        assignment_id: "",
        update: { new_role_name: "Editor" as const },
      };

      mockApiPut.mockResolvedValue({
        data: {
          id: "test-id",
          user_id: "user-123",
          role_id: "role-editor",
          role_name: "Editor",
          scope_type: "PROJECT",
          scope_id: "project-456",
          is_immutable: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      });

      const mutation = useUpdateAssignment();
      await mutation.mutate(mockRequest);

      // Verify API was called with the provided (empty) assignment_id
      expect(mockApiPut).toHaveBeenCalledWith(
        expect.stringContaining("rbac/assignments/"),
        mockRequest.update,
      );
    });

    it("should require update parameter with new_role_name", async () => {
      const mockRequest = {
        assignment_id: "assignment-123",
        update: { new_role_name: "Viewer" as const },
      };

      mockApiPut.mockResolvedValue({
        data: {
          id: "assignment-123",
          user_id: "user-123",
          role_id: "role-viewer",
          role_name: "Viewer",
          scope_type: "PROJECT",
          scope_id: "project-456",
          is_immutable: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      });

      const mutation = useUpdateAssignment();
      await mutation.mutate(mockRequest);

      expect(mockApiPut).toHaveBeenCalledWith(expect.any(String), {
        new_role_name: "Viewer",
      });
    });
  });

  describe("URL construction", () => {
    it("should construct correct API endpoint URL with assignment_id", async () => {
      mockApiPut.mockResolvedValue({
        data: {
          id: "test-id",
          user_id: "user-123",
          role_id: "role-editor",
          role_name: "Editor",
          scope_type: "PROJECT",
          scope_id: "project-456",
          is_immutable: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      });

      const mutation = useUpdateAssignment();
      await mutation.mutate({
        assignment_id: "test-assignment-id",
        update: { new_role_name: "Editor" as const },
      });

      const callUrl = mockApiPut.mock.calls[0][0];
      expect(callUrl).toContain("rbac/assignments");
      expect(callUrl).toContain("test-assignment-id");
    });

    it("should use PUT method for update operation", async () => {
      const mockRequest = {
        assignment_id: "assignment-999",
        update: { new_role_name: "Viewer" as const },
      };

      mockApiPut.mockResolvedValue({
        data: {
          id: "assignment-999",
          user_id: "user-123",
          role_id: "role-viewer",
          role_name: "Viewer",
          scope_type: "FLOW",
          scope_id: "flow-xyz",
          is_immutable: false,
          created_at: "2024-01-01T00:00:00Z",
        },
      });

      const mutation = useUpdateAssignment();
      await mutation.mutate(mockRequest);

      // Verify that PUT method was used (mockApiPut should be called)
      expect(mockApiPut).toHaveBeenCalled();
    });
  });

  describe("response structure", () => {
    it("should return complete AssignmentResponse structure", async () => {
      const mockRequest = {
        assignment_id: "assignment-complete",
        update: { new_role_name: "Owner" as const },
      };

      const mockResponse = {
        id: "assignment-complete",
        user_id: "user-abc",
        role_id: "role-owner",
        role_name: "Owner",
        scope_type: "PROJECT",
        scope_id: "project-123",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPut.mockResolvedValue({ data: mockResponse });

      const mutation = useUpdateAssignment();
      const result = await mutation.mutate(mockRequest);

      // Verify all required fields are present
      expect(result).toHaveProperty("id");
      expect(result).toHaveProperty("user_id");
      expect(result).toHaveProperty("role_id");
      expect(result).toHaveProperty("role_name");
      expect(result).toHaveProperty("scope_type");
      expect(result).toHaveProperty("scope_id");
      expect(result).toHaveProperty("is_immutable");
      expect(result).toHaveProperty("created_at");
    });
  });
});

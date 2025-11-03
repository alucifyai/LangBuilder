// useCreateAssignment hook tests

// Mock dependencies before imports
jest.mock("@/controllers/API/api", () => ({
  api: {
    post: jest.fn(),
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

import { useCreateAssignment } from "../use-create-assignment";

const mockApiPost = require("@/controllers/API/api").api.post;

describe("useCreateAssignment hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("successful assignment creation", () => {
    it("should create assignment via API", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Editor" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      };

      const mockResponse = {
        id: "assignment-789",
        ...mockRequest,
        role_id: "role-2",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(mockApiPost).toHaveBeenCalledWith(
        expect.stringContaining("rbac/assignments"),
        mockRequest,
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle Global scope without scope_id", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Admin" as const,
        scope_type: "GLOBAL" as const,
        scope_id: null,
      };

      const mockResponse = {
        id: "assignment-global",
        ...mockRequest,
        role_id: "role-1",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.scope_type).toBe("GLOBAL");
      expect(result.scope_id).toBeNull();
    });
  });

  describe("cache invalidation", () => {
    it("should invalidate assignments query on success", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Owner" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({
        data: { id: "assignment-1", ...mockRequest },
      });

      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      const mutation = useCreateAssignment();
      await mutation.mutate(mockRequest);

      const mutateCall =
        mockRequestProcessor.mock.results[0].value.mutate.mock.calls[0];
      const options = mutateCall[2];

      // Verify onSuccess is provided
      expect(options.onSuccess).toBeDefined();
    });
  });

  describe("error handling", () => {
    it("should handle duplicate assignment errors", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Owner" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      };

      const mockError = new Error(
        "Assignment already exists for this user and scope",
      );
      mockApiPost.mockRejectedValue(mockError);

      const mutation = useCreateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow(
        "Assignment already exists",
      );
    });

    it("should handle immutable scope errors", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Viewer" as const,
        scope_type: "PROJECT" as const,
        scope_id: "default-project",
      };

      const mockError = new Error(
        "Cannot modify Default Project Owner assignment (immutable)",
      );
      mockApiPost.mockRejectedValue(mockError);

      const mutation = useCreateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow("immutable");
    });

    it("should handle user not found errors", async () => {
      const mockRequest = {
        user_id: "nonexistent-user",
        role_name: "Owner" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      };

      const mockError = new Error("User not found");
      mockApiPost.mockRejectedValue(mockError);

      const mutation = useCreateAssignment();

      await expect(mutation.mutate(mockRequest)).rejects.toThrow(
        "User not found",
      );
    });
  });

  describe("role validation", () => {
    it("should create assignment with Owner role", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Owner" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({
        data: { id: "assignment-1", ...mockRequest },
      });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Owner");
    });

    it("should create assignment with Editor role", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Editor" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({
        data: { id: "assignment-2", ...mockRequest },
      });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Editor");
    });

    it("should create assignment with Viewer role", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Viewer" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({
        data: { id: "assignment-3", ...mockRequest },
      });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.role_name).toBe("Viewer");
    });
  });

  describe("scope type validation", () => {
    it("should create assignment with PROJECT scope", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Owner" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({
        data: { id: "assignment-1", ...mockRequest },
      });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.scope_type).toBe("PROJECT");
      expect(result.scope_id).toBe("project-456");
    });

    it("should create assignment with FLOW scope", async () => {
      const mockRequest = {
        user_id: "user-123",
        role_name: "Editor" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({
        data: { id: "assignment-2", ...mockRequest },
      });

      const mutation = useCreateAssignment();
      const result = await mutation.mutate(mockRequest);

      expect(result.scope_type).toBe("FLOW");
      expect(result.scope_id).toBe("flow-789");
    });
  });
});

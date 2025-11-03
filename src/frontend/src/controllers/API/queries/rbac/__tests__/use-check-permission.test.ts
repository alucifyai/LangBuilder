// useCheckPermission hook tests

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
      data: undefined,
    })),
  })),
}));

import { useCheckPermission } from "../use-check-permission";

const mockApiPost = require("@/controllers/API/api").api.post;

describe("useCheckPermission hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("successful permission checks", () => {
    it("should check permission via API", async () => {
      const mockRequest = {
        permission: "UPDATE" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-123",
      };

      const mockResponse = {
        has_permission: true,
        user_id: "user-456",
        permission: "UPDATE",
        scope_type: "FLOW",
        scope_id: "flow-123",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate(mockRequest);

      expect(mockApiPost).toHaveBeenCalledWith(
        expect.stringContaining("rbac/check-permission"),
        mockRequest,
      );
      expect(result).toEqual(mockResponse);
      expect(result.has_permission).toBe(true);
    });

    it("should return permission granted response", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "READ",
        scope_type: "PROJECT",
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "READ" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      });

      expect(result.has_permission).toBe(true);
    });

    it("should return permission denied response", async () => {
      const mockResponse = {
        has_permission: false,
        user_id: "user-123",
        permission: "DELETE",
        scope_type: "FLOW",
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "DELETE" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      });

      expect(result.has_permission).toBe(false);
    });
  });

  describe("permission types", () => {
    it("should check CREATE permission", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "CREATE",
        scope_type: "PROJECT",
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "CREATE" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      });

      expect(result.permission).toBe("CREATE");
    });

    it("should check READ permission", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "READ",
        scope_type: "FLOW",
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "READ" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      });

      expect(result.permission).toBe("READ");
    });

    it("should check UPDATE permission", async () => {
      const mockResponse = {
        has_permission: false,
        user_id: "user-123",
        permission: "UPDATE",
        scope_type: "FLOW",
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "UPDATE" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      });

      expect(result.permission).toBe("UPDATE");
    });

    it("should check DELETE permission", async () => {
      const mockResponse = {
        has_permission: false,
        user_id: "user-123",
        permission: "DELETE",
        scope_type: "PROJECT",
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "DELETE" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      });

      expect(result.permission).toBe("DELETE");
    });
  });

  describe("scope types", () => {
    it("should check permission on GLOBAL scope", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "CREATE",
        scope_type: "GLOBAL",
        scope_id: null,
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "CREATE" as const,
        scope_type: "GLOBAL" as const,
      });

      expect(result.scope_type).toBe("GLOBAL");
      expect(result.scope_id).toBeNull();
    });

    it("should check permission on PROJECT scope", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "UPDATE",
        scope_type: "PROJECT",
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "UPDATE" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      });

      expect(result.scope_type).toBe("PROJECT");
      expect(result.scope_id).toBe("project-456");
    });

    it("should check permission on FLOW scope", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "READ",
        scope_type: "FLOW",
        scope_id: "flow-789",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "READ" as const,
        scope_type: "FLOW" as const,
        scope_id: "flow-789",
      });

      expect(result.scope_type).toBe("FLOW");
      expect(result.scope_id).toBe("flow-789");
    });
  });

  describe("error handling", () => {
    it("should handle API errors", async () => {
      const mockError = new Error("Permission check failed");
      mockApiPost.mockRejectedValue(mockError);

      const mutation = useCheckPermission();

      await expect(
        mutation.mutate({
          permission: "READ" as const,
          scope_type: "FLOW" as const,
          scope_id: "flow-123",
        }),
      ).rejects.toThrow("Permission check failed");
    });

    it("should handle unauthorized errors", async () => {
      const mockError = new Error("Unauthorized");
      mockApiPost.mockRejectedValue(mockError);

      const mutation = useCheckPermission();

      await expect(
        mutation.mutate({
          permission: "UPDATE" as const,
          scope_type: "PROJECT" as const,
          scope_id: "project-456",
        }),
      ).rejects.toThrow("Unauthorized");
    });
  });

  describe("retry behavior", () => {
    it("should use reduced retry count for permission checks", () => {
      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      useCheckPermission();

      const mutateCall =
        mockRequestProcessor.mock.results[0].value.mutate.mock.calls[0];
      const options = mutateCall[2];

      // Should have reduced retry count
      expect(options.retry).toBeLessThan(3);
    });
  });

  describe("response structure", () => {
    it("should return all response fields", async () => {
      const mockResponse = {
        has_permission: true,
        user_id: "user-123",
        permission: "READ",
        scope_type: "PROJECT",
        scope_id: "project-456",
      };

      mockApiPost.mockResolvedValue({ data: mockResponse });

      const mutation = useCheckPermission();
      const result = await mutation.mutate({
        permission: "READ" as const,
        scope_type: "PROJECT" as const,
        scope_id: "project-456",
      });

      expect(result).toHaveProperty("has_permission");
      expect(result).toHaveProperty("user_id");
      expect(result).toHaveProperty("permission");
      expect(result).toHaveProperty("scope_type");
      expect(result).toHaveProperty("scope_id");
    });
  });
});

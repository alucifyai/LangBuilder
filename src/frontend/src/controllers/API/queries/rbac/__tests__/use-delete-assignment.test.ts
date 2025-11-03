// useDeleteAssignment hook tests

// Mock dependencies before imports
jest.mock("@/controllers/API/api", () => ({
  api: {
    delete: jest.fn(),
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

import { useDeleteAssignment } from "../use-delete-assignment";

const mockApiDelete = require("@/controllers/API/api").api.delete;

describe("useDeleteAssignment hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("successful assignment deletion", () => {
    it("should delete assignment via API", async () => {
      mockApiDelete.mockResolvedValue({ status: 204 });

      const mutation = useDeleteAssignment();
      await mutation.mutate({ assignment_id: "assignment-123" });

      expect(mockApiDelete).toHaveBeenCalledWith(
        expect.stringContaining("rbac/assignments/assignment-123"),
      );
    });

    it("should handle deletion without returning data", async () => {
      mockApiDelete.mockResolvedValue({ status: 204, data: undefined });

      const mutation = useDeleteAssignment();
      const result = await mutation.mutate({ assignment_id: "assignment-456" });

      expect(result).toBeUndefined();
    });
  });

  describe("cache invalidation", () => {
    it("should invalidate assignments query on success", async () => {
      mockApiDelete.mockResolvedValue({ status: 204 });

      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      const mutation = useDeleteAssignment();
      await mutation.mutate({ assignment_id: "assignment-123" });

      const mutateCall =
        mockRequestProcessor.mock.results[0].value.mutate.mock.calls[0];
      const options = mutateCall[2];

      // Verify onSuccess is provided
      expect(options.onSuccess).toBeDefined();
    });
  });

  describe("error handling", () => {
    it("should handle immutable assignment errors", async () => {
      const mockError = new Error(
        "Cannot delete immutable assignment (Default Project Owner)",
      );
      mockApiDelete.mockRejectedValue(mockError);

      const mutation = useDeleteAssignment();

      await expect(
        mutation.mutate({ assignment_id: "immutable-assignment" }),
      ).rejects.toThrow("immutable");
    });

    it("should handle assignment not found errors", async () => {
      const mockError = new Error("Assignment not found");
      mockApiDelete.mockRejectedValue(mockError);

      const mutation = useDeleteAssignment();

      await expect(
        mutation.mutate({ assignment_id: "nonexistent-assignment" }),
      ).rejects.toThrow("Assignment not found");
    });

    it("should handle permission denied errors", async () => {
      const mockError = new Error("Forbidden");
      mockApiDelete.mockRejectedValue(mockError);

      const mutation = useDeleteAssignment();

      await expect(
        mutation.mutate({ assignment_id: "assignment-123" }),
      ).rejects.toThrow("Forbidden");
    });
  });

  describe("request validation", () => {
    it("should require assignment_id parameter", async () => {
      const mutation = useDeleteAssignment();

      // TypeScript would prevent this, but testing runtime behavior
      await expect(mutation.mutate({ assignment_id: "" })).rejects.toThrow();
    });
  });

  describe("URL construction", () => {
    it("should construct correct API endpoint URL", async () => {
      mockApiDelete.mockResolvedValue({ status: 204 });

      const mutation = useDeleteAssignment();
      await mutation.mutate({ assignment_id: "test-assignment-id" });

      const callUrl = mockApiDelete.mock.calls[0][0];
      expect(callUrl).toContain("rbac/assignments");
      expect(callUrl).toContain("test-assignment-id");
    });
  });
});

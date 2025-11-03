// useGetAssignments hook tests

// Mock dependencies before imports
jest.mock("@/controllers/API/api", () => ({
  api: {
    get: jest.fn(),
  },
}));

jest.mock("@/controllers/API/services/request-processor", () => ({
  UseRequestProcessor: jest.fn(() => ({
    query: jest.fn((key, fn, options) => ({
      data: undefined,
      isLoading: false,
      error: null,
      refetch: async () => await fn(),
    })),
  })),
}));

import { useGetAssignments } from "../use-get-assignments";

const mockApiGet = require("@/controllers/API/api").api.get;

describe("useGetAssignments hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("successful assignment fetching", () => {
    it("should fetch assignments from API", async () => {
      const mockAssignments = [
        {
          id: "1",
          user_id: "user-1",
          role_id: "role-1",
          role_name: "Owner",
          scope_type: "PROJECT",
          scope_id: "project-1",
          is_immutable: true,
          created_at: "2024-01-01T00:00:00Z",
        },
      ];

      mockApiGet.mockResolvedValue({ status: 200, data: mockAssignments });

      const queryResult = useGetAssignments();
      const assignments = await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("rbac/assignments"),
      );
      expect(assignments).toEqual(mockAssignments);
    });

    it("should fetch assignments without filters", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments();
      await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("rbac/assignments"),
      );
      expect(mockApiGet).toHaveBeenCalledWith(expect.not.stringContaining("?"));
    });
  });

  describe("filter parameters", () => {
    it("should include user_id filter in query string", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments({ user_id: "user-123" });
      await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("user_id=user-123"),
      );
    });

    it("should include role_name filter in query string", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments({ role_name: "Editor" });
      await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("role_name=Editor"),
      );
    });

    it("should include scope_type filter in query string", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments({ scope_type: "PROJECT" });
      await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("scope_type=PROJECT"),
      );
    });

    it("should include scope_id filter in query string", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments({ scope_id: "scope-456" });
      await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("scope_id=scope-456"),
      );
    });

    it("should include multiple filters in query string", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments({
        user_id: "user-123",
        role_name: "Owner",
        scope_type: "PROJECT",
      });
      await queryResult.refetch();

      const callArg = mockApiGet.mock.calls[0][0];
      expect(callArg).toContain("user_id=user-123");
      expect(callArg).toContain("role_name=Owner");
      expect(callArg).toContain("scope_type=PROJECT");
    });

    it("should omit undefined filter values", async () => {
      mockApiGet.mockResolvedValue({ status: 200, data: [] });

      const queryResult = useGetAssignments({
        user_id: "user-123",
        role_name: undefined,
      });
      await queryResult.refetch();

      const callArg = mockApiGet.mock.calls[0][0];
      expect(callArg).toContain("user_id=user-123");
      expect(callArg).not.toContain("role_name");
    });
  });

  describe("error handling", () => {
    it("should return empty array when status is not 200", async () => {
      mockApiGet.mockResolvedValue({ status: 404, data: null });

      const queryResult = useGetAssignments();
      const assignments = await queryResult.refetch();

      expect(assignments).toEqual([]);
    });

    it("should handle API errors", async () => {
      const mockError = new Error("API Error");
      mockApiGet.mockRejectedValue(mockError);

      const queryResult = useGetAssignments();

      await expect(queryResult.refetch()).rejects.toThrow("API Error");
    });
  });

  describe("caching behavior", () => {
    it("should use moderate cache time for dynamic data", () => {
      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      useGetAssignments();

      const queryCall =
        mockRequestProcessor.mock.results[0].value.query.mock.calls[0];
      const options = queryCall[2];

      // Assignments are dynamic, should have moderate staleTime
      expect(options.staleTime).toBeLessThan(1000 * 60 * 60); // < 1 hour
      expect(options.refetchOnWindowFocus).toBe(true);
    });
  });

  describe("query key", () => {
    it("should include filters in query key", () => {
      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      const filters = { user_id: "user-123", role_name: "Owner" };
      useGetAssignments(filters);

      const queryCall =
        mockRequestProcessor.mock.results[0].value.query.mock.calls[0];
      const queryKey = queryCall[0];

      expect(queryKey).toEqual(["useGetAssignments", filters]);
    });
  });

  describe("data structure validation", () => {
    it("should return assignments with all required fields", async () => {
      const mockAssignment = {
        id: "assignment-1",
        user_id: "user-1",
        role_id: "role-1",
        role_name: "Owner",
        scope_type: "PROJECT",
        scope_id: "project-1",
        is_immutable: false,
        created_at: "2024-01-01T00:00:00Z",
      };

      mockApiGet.mockResolvedValue({ status: 200, data: [mockAssignment] });

      const queryResult = useGetAssignments();
      const assignments = await queryResult.refetch();

      expect(assignments[0]).toHaveProperty("id");
      expect(assignments[0]).toHaveProperty("user_id");
      expect(assignments[0]).toHaveProperty("role_id");
      expect(assignments[0]).toHaveProperty("role_name");
      expect(assignments[0]).toHaveProperty("scope_type");
      expect(assignments[0]).toHaveProperty("is_immutable");
      expect(assignments[0]).toHaveProperty("created_at");
    });
  });
});

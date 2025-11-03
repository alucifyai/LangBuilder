// useGetRoles hook tests

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

import { useGetRoles } from "../use-get-roles";

const mockApiGet = require("@/controllers/API/api").api.get;

describe("useGetRoles hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("successful role fetching", () => {
    it("should fetch roles from API", async () => {
      const mockRoles = [
        {
          id: "1",
          name: "Admin",
          description: "Full system access",
        },
        {
          id: "2",
          name: "Owner",
          description: "Full access to owned resources",
        },
        {
          id: "3",
          name: "Editor",
          description: "Can create, read, and update",
        },
        {
          id: "4",
          name: "Viewer",
          description: "Read-only access",
        },
      ];

      mockApiGet.mockResolvedValue({ status: 200, data: mockRoles });

      const queryResult = useGetRoles();
      const roles = await queryResult.refetch();

      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("rbac/roles"),
      );
      expect(roles).toEqual(mockRoles);
    });

    it("should return all four predefined roles", async () => {
      const mockRoles = [
        { id: "1", name: "Admin", description: "Admin role" },
        { id: "2", name: "Owner", description: "Owner role" },
        { id: "3", name: "Editor", description: "Editor role" },
        { id: "4", name: "Viewer", description: "Viewer role" },
      ];

      mockApiGet.mockResolvedValue({ status: 200, data: mockRoles });

      const queryResult = useGetRoles();
      const roles = await queryResult.refetch();

      expect(roles).toHaveLength(4);
      expect(roles.map((r: any) => r.name)).toEqual([
        "Admin",
        "Owner",
        "Editor",
        "Viewer",
      ]);
    });
  });

  describe("error handling", () => {
    it("should return empty array when status is not 200", async () => {
      mockApiGet.mockResolvedValue({ status: 404, data: null });

      const queryResult = useGetRoles();
      const roles = await queryResult.refetch();

      expect(roles).toEqual([]);
    });

    it("should handle API errors", async () => {
      const mockError = new Error("API Error");
      mockApiGet.mockRejectedValue(mockError);

      const queryResult = useGetRoles();

      await expect(queryResult.refetch()).rejects.toThrow("API Error");
    });
  });

  describe("caching behavior", () => {
    it("should use long cache times for static role data", () => {
      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      useGetRoles();

      // Verify query was called with cache options
      const queryCall =
        mockRequestProcessor.mock.results[0].value.query.mock.calls[0];
      const options = queryCall[2];

      // Roles are static, should have long staleTime and gcTime
      expect(options.staleTime).toBeGreaterThan(1000 * 60 * 30); // > 30 minutes
      expect(options.gcTime).toBeGreaterThan(1000 * 60 * 30); // > 30 minutes
    });
  });

  describe("query key", () => {
    it("should use correct query key for cache invalidation", () => {
      const mockRequestProcessor =
        require("@/controllers/API/services/request-processor").UseRequestProcessor;

      useGetRoles();

      const queryCall =
        mockRequestProcessor.mock.results[0].value.query.mock.calls[0];
      const queryKey = queryCall[0];

      expect(queryKey).toEqual(["useGetRoles"]);
    });
  });
});

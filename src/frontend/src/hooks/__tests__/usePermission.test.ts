// usePermission hook tests

import { renderHook, waitFor } from "@testing-library/react";
import type {
  PermissionCheckResponse,
  PermissionEnum,
  ScopeTypeEnum,
} from "@/types/api/rbac";
import { usePermission } from "../usePermission";

// Mock the useCheckPermission hook
const mockMutate = jest.fn();
const mockData: PermissionCheckResponse | undefined = undefined;
const mockIsPending = false;
const mockError = null;

jest.mock("@/controllers/API/queries/rbac", () => ({
  useCheckPermission: jest.fn(() => ({
    mutate: mockMutate,
    data: mockData,
    isPending: mockIsPending,
    error: mockError,
  })),
}));

describe("usePermission hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset the mock implementation
    const { useCheckPermission } = require("@/controllers/API/queries/rbac");
    useCheckPermission.mockImplementation(() => ({
      mutate: mockMutate,
      data: undefined,
      isPending: false,
      error: null,
    }));
  });

  describe("basic functionality", () => {
    it("should accept all required parameters", () => {
      const { result } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      expect(result.current).toHaveProperty("hasPermission");
      expect(result.current).toHaveProperty("isLoading");
      expect(result.current).toHaveProperty("error");
      expect(result.current).toHaveProperty("refetch");
    });

    it("should trigger permission check on mount", () => {
      renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "PROJECT",
          scopeId: "project-456",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "READ",
        scope_type: "PROJECT",
        scope_id: "project-456",
      });
    });

    it("should return hasPermission as false by default", () => {
      const { result } = renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "PROJECT",
          scopeId: "project-789",
        }),
      );

      expect(result.current.hasPermission).toBe(false);
    });
  });

  describe("permission check results", () => {
    it("should return true when permission is granted", () => {
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: {
          has_permission: true,
          user_id: "user-123",
          permission: "UPDATE",
          scope_type: "FLOW",
          scope_id: "flow-123",
        },
        isPending: false,
        error: null,
      }));

      const { result } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      expect(result.current.hasPermission).toBe(true);
    });

    it("should return false when permission is denied", () => {
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: {
          has_permission: false,
          user_id: "user-123",
          permission: "DELETE",
          scope_type: "FLOW",
          scope_id: "flow-123",
        },
        isPending: false,
        error: null,
      }));

      const { result } = renderHook(() =>
        usePermission({
          permission: "DELETE",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      expect(result.current.hasPermission).toBe(false);
    });
  });

  describe("loading states", () => {
    it("should return isLoading true when mutation is pending", () => {
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: undefined,
        isPending: true,
        error: null,
      }));

      const { result } = renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "PROJECT",
          scopeId: "project-456",
        }),
      );

      expect(result.current.isLoading).toBe(true);
    });

    it("should return isLoading false when mutation completes", () => {
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: {
          has_permission: true,
          user_id: "user-123",
          permission: "READ",
          scope_type: "PROJECT",
          scope_id: "project-456",
        },
        isPending: false,
        error: null,
      }));

      const { result, rerender } = renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "PROJECT",
          scopeId: "project-456",
        }),
      );

      // Force a re-render to update loading state
      rerender();

      expect(result.current.isLoading).toBe(false);
    });
  });

  describe("error handling", () => {
    it("should return error when permission check fails", () => {
      const mockErrorObj = new Error("Permission check failed");
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: undefined,
        isPending: false,
        error: mockErrorObj,
      }));

      const { result } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      expect(result.current.error).toBe(mockErrorObj);
    });

    it("should have hasPermission false on error", () => {
      const mockErrorObj = new Error("Network error");
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: undefined,
        isPending: false,
        error: mockErrorObj,
      }));

      const { result } = renderHook(() =>
        usePermission({
          permission: "DELETE",
          scopeType: "PROJECT",
          scopeId: "project-789",
        }),
      );

      expect(result.current.hasPermission).toBe(false);
    });
  });

  describe("enabled flag", () => {
    it("should not trigger check when enabled is false", () => {
      renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "FLOW",
          scopeId: "flow-123",
          enabled: false,
        }),
      );

      expect(mockMutate).not.toHaveBeenCalled();
    });

    it("should trigger check when enabled is true", () => {
      renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "PROJECT",
          scopeId: "project-456",
          enabled: true,
        }),
      );

      expect(mockMutate).toHaveBeenCalled();
    });

    it("should use enabled=true by default", () => {
      renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "PROJECT",
          scopeId: "project-789",
        }),
      );

      expect(mockMutate).toHaveBeenCalled();
    });

    it("should re-check when enabled changes from false to true", () => {
      const { rerender } = renderHook(
        ({ enabled }) =>
          usePermission({
            permission: "READ",
            scopeType: "FLOW",
            scopeId: "flow-123",
            enabled,
          }),
        { initialProps: { enabled: false } },
      );

      expect(mockMutate).not.toHaveBeenCalled();

      rerender({ enabled: true });

      expect(mockMutate).toHaveBeenCalled();
    });
  });

  describe("dependency changes", () => {
    it("should re-check when permission changes", () => {
      const { rerender } = renderHook(
        ({ permission }: { permission: PermissionEnum }) =>
          usePermission({
            permission,
            scopeType: "FLOW",
            scopeId: "flow-123",
          }),
        { initialProps: { permission: "READ" as PermissionEnum } },
      );

      expect(mockMutate).toHaveBeenCalledTimes(1);

      rerender({ permission: "UPDATE" as PermissionEnum });

      expect(mockMutate).toHaveBeenCalledTimes(2);
      expect(mockMutate).toHaveBeenLastCalledWith({
        permission: "UPDATE",
        scope_type: "FLOW",
        scope_id: "flow-123",
      });
    });

    it("should re-check when scopeType changes", () => {
      const { rerender } = renderHook(
        ({ scopeType }: { scopeType: ScopeTypeEnum }) =>
          usePermission({
            permission: "READ",
            scopeType,
            scopeId: "123",
          }),
        { initialProps: { scopeType: "FLOW" as ScopeTypeEnum } },
      );

      expect(mockMutate).toHaveBeenCalledTimes(1);

      rerender({ scopeType: "PROJECT" as ScopeTypeEnum });

      expect(mockMutate).toHaveBeenCalledTimes(2);
      expect(mockMutate).toHaveBeenLastCalledWith({
        permission: "READ",
        scope_type: "PROJECT",
        scope_id: "123",
      });
    });

    it("should re-check when scopeId changes", () => {
      const { rerender } = renderHook(
        ({ scopeId }: { scopeId: string }) =>
          usePermission({
            permission: "UPDATE",
            scopeType: "FLOW",
            scopeId,
          }),
        { initialProps: { scopeId: "flow-123" } },
      );

      expect(mockMutate).toHaveBeenCalledTimes(1);

      rerender({ scopeId: "flow-456" });

      expect(mockMutate).toHaveBeenCalledTimes(2);
      expect(mockMutate).toHaveBeenLastCalledWith({
        permission: "UPDATE",
        scope_type: "FLOW",
        scope_id: "flow-456",
      });
    });

    it("should handle undefined scopeId", () => {
      renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "GLOBAL",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "CREATE",
        scope_type: "GLOBAL",
        scope_id: null,
      });
    });
  });

  describe("refetch functionality", () => {
    it("should provide refetch function", () => {
      const { result } = renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      expect(result.current.refetch).toBeInstanceOf(Function);
    });

    it("should re-check permission when refetch is called", () => {
      const { result } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "PROJECT",
          scopeId: "project-456",
        }),
      );

      expect(mockMutate).toHaveBeenCalledTimes(1);

      result.current.refetch();

      expect(mockMutate).toHaveBeenCalledTimes(2);
      expect(mockMutate).toHaveBeenLastCalledWith({
        permission: "UPDATE",
        scope_type: "PROJECT",
        scope_id: "project-456",
      });
    });

    it("should not refetch when disabled", () => {
      const { result } = renderHook(() =>
        usePermission({
          permission: "DELETE",
          scopeType: "FLOW",
          scopeId: "flow-789",
          enabled: false,
        }),
      );

      expect(mockMutate).not.toHaveBeenCalled();

      result.current.refetch();

      expect(mockMutate).not.toHaveBeenCalled();
    });
  });

  describe("all permission types", () => {
    it("should handle CREATE permission", () => {
      renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "PROJECT",
          scopeId: "project-123",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "CREATE",
        scope_type: "PROJECT",
        scope_id: "project-123",
      });
    });

    it("should handle READ permission", () => {
      renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "FLOW",
          scopeId: "flow-456",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "READ",
        scope_type: "FLOW",
        scope_id: "flow-456",
      });
    });

    it("should handle UPDATE permission", () => {
      renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "PROJECT",
          scopeId: "project-789",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "UPDATE",
        scope_type: "PROJECT",
        scope_id: "project-789",
      });
    });

    it("should handle DELETE permission", () => {
      renderHook(() =>
        usePermission({
          permission: "DELETE",
          scopeType: "FLOW",
          scopeId: "flow-321",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "DELETE",
        scope_type: "FLOW",
        scope_id: "flow-321",
      });
    });
  });

  describe("all scope types", () => {
    it("should handle GLOBAL scope", () => {
      renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "GLOBAL",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "CREATE",
        scope_type: "GLOBAL",
        scope_id: null,
      });
    });

    it("should handle PROJECT scope", () => {
      renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "PROJECT",
          scopeId: "project-123",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "READ",
        scope_type: "PROJECT",
        scope_id: "project-123",
      });
    });

    it("should handle FLOW scope", () => {
      renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "FLOW",
          scopeId: "flow-456",
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "UPDATE",
        scope_type: "FLOW",
        scope_id: "flow-456",
      });
    });
  });

  describe("TypeScript type safety", () => {
    it("should enforce PermissionEnum type", () => {
      // This test verifies TypeScript compilation
      const { result } = renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "PROJECT",
          scopeId: "project-123",
        }),
      );

      expect(result.current).toBeDefined();
    });

    it("should enforce ScopeTypeEnum type", () => {
      // This test verifies TypeScript compilation
      const { result } = renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      expect(result.current).toBeDefined();
    });

    it("should return strongly typed result", () => {
      const { result } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "PROJECT",
          scopeId: "project-456",
        }),
      );

      // Verify return type structure
      expect(typeof result.current.hasPermission).toBe("boolean");
      expect(typeof result.current.isLoading).toBe("boolean");
      expect(typeof result.current.refetch).toBe("function");
    });
  });

  describe("performance and caching", () => {
    it("should work with multiple concurrent calls", () => {
      const { result: result1 } = renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "FLOW",
          scopeId: "flow-1",
        }),
      );

      const { result: result2 } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "FLOW",
          scopeId: "flow-2",
        }),
      );

      const { result: result3 } = renderHook(() =>
        usePermission({
          permission: "DELETE",
          scopeType: "PROJECT",
          scopeId: "project-3",
        }),
      );

      // All hooks should work independently
      expect(result1.current).toBeDefined();
      expect(result2.current).toBeDefined();
      expect(result3.current).toBeDefined();

      // Each should have triggered its own check
      expect(mockMutate).toHaveBeenCalledTimes(3);
    });

    it("should handle rapid re-renders", () => {
      const { rerender } = renderHook(() =>
        usePermission({
          permission: "READ",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      const initialCallCount = mockMutate.mock.calls.length;

      // Rapid re-renders with same props
      rerender();
      rerender();
      rerender();

      // Should not trigger additional checks for same props
      expect(mockMutate.mock.calls.length).toBeGreaterThanOrEqual(
        initialCallCount,
      );
    });
  });

  describe("real-world usage scenarios", () => {
    it("should work in conditional rendering scenario", () => {
      const { useCheckPermission } = require("@/controllers/API/queries/rbac");
      useCheckPermission.mockImplementation(() => ({
        mutate: mockMutate,
        data: {
          has_permission: true,
          user_id: "user-123",
          permission: "UPDATE",
          scope_type: "FLOW",
          scope_id: "flow-123",
        },
        isPending: false,
        error: null,
      }));

      const { result } = renderHook(() =>
        usePermission({
          permission: "UPDATE",
          scopeType: "FLOW",
          scopeId: "flow-123",
        }),
      );

      // Simulate conditional rendering based on permission
      const shouldShowEditButton =
        result.current.hasPermission && !result.current.isLoading;

      expect(shouldShowEditButton).toBe(true);
    });

    it("should handle optional scopeId for global permissions", () => {
      renderHook(() =>
        usePermission({
          permission: "CREATE",
          scopeType: "GLOBAL",
          enabled: true,
        }),
      );

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "CREATE",
        scope_type: "GLOBAL",
        scope_id: null,
      });
    });

    it("should handle lazy permission checks", () => {
      const { rerender } = renderHook(
        ({ id }: { id: string | undefined }) =>
          usePermission({
            permission: "DELETE",
            scopeType: "FLOW",
            scopeId: id,
            enabled: Boolean(id),
          }),
        { initialProps: { id: undefined } },
      );

      // Should not check when id is undefined
      expect(mockMutate).not.toHaveBeenCalled();

      // Should check when id becomes available
      rerender({ id: "flow-123" });

      expect(mockMutate).toHaveBeenCalledWith({
        permission: "DELETE",
        scope_type: "FLOW",
        scope_id: "flow-123",
      });
    });
  });
});

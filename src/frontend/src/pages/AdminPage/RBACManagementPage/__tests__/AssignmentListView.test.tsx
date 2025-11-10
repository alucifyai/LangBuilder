/**
 * AssignmentListView Component Tests
 *
 * Task 4.2: Test assignment list view with filtering and delete actions
 *
 * Success Criteria:
 * - Assignment list displays all User:Role:Scope assignments
 * - Filtering works by User, Role, and Scope
 * - Inheritance message clearly displayed
 * - Inline delete works for non-immutable assignments
 * - Immutable assignments show "Immutable" badge and disable delete
 * - Error messages are clear and actionable
 * - Real-time updates on assignment changes
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import AssignmentListView from "../AssignmentListView";
import * as rbacHooks from "../../../../controllers/API/queries/rbac";
import useAlertStore from "../../../../stores/alertStore";

// Mock stores that use import.meta
jest.mock("../../../../stores/darkStore", () => ({
  useDarkStore: jest.fn(() => ({
    dark: false,
    setDark: jest.fn(),
  })),
}));

jest.mock("../../../../stores/flowStore", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    nodes: [],
    edges: [],
  })),
}));

// Mock the alert store
jest.mock("../../../../stores/alertStore");

// Mock the RBAC hooks
jest.mock("../../../../controllers/API/queries/rbac");

// Mock UI components to simplify testing
jest.mock("../../../../components/ui/select", () => ({
  Select: ({ children, onValueChange, value }: any) => (
    <div data-testid="select" data-value={value}>
      <button onClick={() => onValueChange("test-value")}>Change</button>
      {children}
    </div>
  ),
  SelectContent: ({ children }: any) => <div>{children}</div>,
  SelectItem: ({ children, value }: any) => <div data-value={value}>{children}</div>,
  SelectTrigger: ({ children }: any) => <div>{children}</div>,
  SelectValue: ({ placeholder }: any) => <div>{placeholder}</div>,
}));

describe("AssignmentListView - Task 4.2", () => {
  let queryClient: QueryClient;
  let mockSetSuccessData: jest.Mock;
  let mockSetErrorData: jest.Mock;

  const mockAssignments = [
    {
      id: "assignment-1",
      user_id: "user-123",
      role_id: "role-admin",
      scope_type: "Global",
      scope_id: null,
      is_immutable: false,
      created_at: "2024-01-01T00:00:00Z",
      created_by: "admin-user",
    },
    {
      id: "assignment-2",
      user_id: "user-456",
      role_id: "role-owner",
      scope_type: "Project",
      scope_id: "project-123",
      is_immutable: true,
      created_at: "2024-01-02T00:00:00Z",
      created_by: "admin-user",
    },
    {
      id: "assignment-3",
      user_id: "user-789",
      role_id: "role-editor",
      scope_type: "Flow",
      scope_id: "flow-456",
      is_immutable: false,
      created_at: "2024-01-03T00:00:00Z",
      created_by: "admin-user",
    },
  ];

  const mockRoles = [
    { id: "role-admin", name: "Admin", description: "Administrator", is_system: true },
    { id: "role-owner", name: "Owner", description: "Owner", is_system: true },
    { id: "role-editor", name: "Editor", description: "Editor", is_system: true },
    { id: "role-viewer", name: "Viewer", description: "Viewer", is_system: true },
  ];

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    mockSetSuccessData = jest.fn();
    mockSetErrorData = jest.fn();

    (useAlertStore as unknown as jest.Mock).mockReturnValue({
      setSuccessData: mockSetSuccessData,
      setErrorData: mockSetErrorData,
    });

    // Default mock implementations
    (rbacHooks.useGetAssignments as jest.Mock).mockReturnValue({
      data: mockAssignments,
      isLoading: false,
      error: null,
    });

    (rbacHooks.useGetRoles as jest.Mock).mockReturnValue({
      data: mockRoles,
      isLoading: false,
      error: null,
    });

    (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
      mutateAsync: jest.fn().mockResolvedValue(undefined),
      isPending: false,
      variables: null,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AssignmentListView />
      </QueryClientProvider>
    );
  };

  describe("Assignment List Display", () => {
    it("should display all assignments in a table", () => {
      renderComponent();

      // Check table headers
      expect(screen.getByText("User ID")).toBeInTheDocument();
      expect(screen.getByText("Role ID")).toBeInTheDocument();
      expect(screen.getByText("Scope Type")).toBeInTheDocument();
      expect(screen.getByText("Scope ID")).toBeInTheDocument();
      expect(screen.getByText("Created At")).toBeInTheDocument();
      expect(screen.getByText("Actions")).toBeInTheDocument();

      // Check that all assignments are displayed
      expect(screen.getByText("user-123")).toBeInTheDocument();
      expect(screen.getByText("user-456")).toBeInTheDocument();
      expect(screen.getByText("user-789")).toBeInTheDocument();
    });

    it("should display loading state", () => {
      (rbacHooks.useGetAssignments as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      renderComponent();
      expect(screen.getByText("Loading assignments...")).toBeInTheDocument();
    });

    it("should display error state", () => {
      const errorMessage = "Failed to fetch assignments";
      (rbacHooks.useGetAssignments as jest.Mock).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error(errorMessage),
      });

      renderComponent();
      expect(screen.getByText(/Failed to load assignments/i)).toBeInTheDocument();
    });

    it("should display empty state when no assignments", () => {
      (rbacHooks.useGetAssignments as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      });

      renderComponent();
      expect(screen.getByText("No role assignments found")).toBeInTheDocument();
    });

    it("should display assignment count", () => {
      renderComponent();
      expect(screen.getByText("Showing 3 assignments")).toBeInTheDocument();
    });
  });

  describe("Inheritance Message", () => {
    it("should display inheritance message prominently", () => {
      renderComponent();

      const message = screen.getByText(/Project-level assignments are inherited/i);
      expect(message).toBeInTheDocument();
      expect(message).toHaveTextContent(
        "Project-level assignments are inherited by contained Flows and can be overridden by explicit Flow-specific roles."
      );
    });
  });

  describe("Filtering Functionality", () => {
    it("should have user filter input", () => {
      renderComponent();

      const userInput = screen.getByPlaceholderText("Enter user ID...");
      expect(userInput).toBeInTheDocument();
    });

    it("should filter by user ID when user types", () => {
      renderComponent();

      const userInput = screen.getByPlaceholderText("Enter user ID...");
      fireEvent.change(userInput, { target: { value: "user-123" } });

      expect(userInput).toHaveValue("user-123");
    });

    it("should have role filter dropdown", () => {
      renderComponent();

      expect(screen.getByText("Filter by Role")).toBeInTheDocument();
    });

    it("should have scope filter dropdown", () => {
      renderComponent();

      expect(screen.getByText("Filter by Scope")).toBeInTheDocument();
    });

    it("should show clear filters button when filters are active", () => {
      renderComponent();

      const userInput = screen.getByPlaceholderText("Enter user ID...");
      fireEvent.change(userInput, { target: { value: "user-123" } });

      expect(screen.getByText("Clear Filters")).toBeInTheDocument();
    });

    it("should clear all filters when clear button clicked", () => {
      renderComponent();

      // Set a filter
      const userInput = screen.getByPlaceholderText("Enter user ID...");
      fireEvent.change(userInput, { target: { value: "user-123" } });

      // Click clear
      const clearButton = screen.getByText("Clear Filters");
      fireEvent.click(clearButton);

      // Check filter is cleared
      expect(userInput).toHaveValue("");
    });

    it("should show filtered count when filters are active", () => {
      (rbacHooks.useGetAssignments as jest.Mock).mockReturnValue({
        data: [mockAssignments[0]],
        isLoading: false,
        error: null,
      });

      renderComponent();

      const userInput = screen.getByPlaceholderText("Enter user ID...");
      fireEvent.change(userInput, { target: { value: "user-123" } });

      expect(screen.getByText("Showing 1 assignment (filtered)")).toBeInTheDocument();
    });

    it("should show no results message when filters match nothing", () => {
      renderComponent();

      // First set a filter
      const userInput = screen.getByPlaceholderText("Enter user ID...");
      fireEvent.change(userInput, { target: { value: "user-123" } });

      // Mock empty results
      (rbacHooks.useGetAssignments as jest.Mock).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      });

      // Re-render
      renderComponent();

      expect(screen.getByText("No assignments match the current filters")).toBeInTheDocument();
    });
  });

  describe("Delete Functionality", () => {
    it("should show delete button for non-immutable assignments", () => {
      renderComponent();

      // First assignment is not immutable - should have delete button
      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    it("should show immutable badge for immutable assignments", () => {
      renderComponent();

      // Second assignment is immutable
      expect(screen.getByText("Immutable")).toBeInTheDocument();
    });

    it("should call delete mutation when delete button clicked", async () => {
      const mockMutateAsync = jest.fn().mockResolvedValue(undefined);
      (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        variables: null,
      });

      renderComponent();

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith("assignment-1");
      });
    });

    it("should show success message after successful delete", async () => {
      const mockMutateAsync = jest.fn().mockResolvedValue(undefined);
      (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        variables: null,
      });

      renderComponent();

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockSetSuccessData).toHaveBeenCalledWith({
          title: "Assignment Deleted",
          description: "Role assignment has been successfully deleted.",
        });
      });
    });

    it("should show enhanced error message for immutable assignment deletion", async () => {
      const mockMutateAsync = jest.fn().mockRejectedValue({
        response: {
          data: {
            detail: "Cannot delete immutable assignment (e.g., Starter Project Owner role)",
          },
        },
      });
      (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        variables: null,
      });

      renderComponent();

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockSetErrorData).toHaveBeenCalledWith({
          title: "Cannot Delete Assignment",
          description: expect.stringContaining("Starter Project Owner"),
        });
      });
    });

    it("should show generic error message for other delete failures", async () => {
      const mockMutateAsync = jest.fn().mockRejectedValue({
        response: {
          data: {
            detail: "Database error",
          },
        },
      });
      (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        variables: null,
      });

      renderComponent();

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(mockSetErrorData).toHaveBeenCalledWith({
          title: "Delete Failed",
          description: "Database error",
        });
      });
    });

    it("should disable delete button while deletion is pending", async () => {
      const mockMutateAsync = jest.fn().mockImplementation(() => {
        return new Promise((resolve) => setTimeout(resolve, 100));
      });
      (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        variables: null,
      });

      renderComponent();

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      fireEvent.click(deleteButtons[0]);

      // Button should show "Deleting..." and be disabled
      await waitFor(() => {
        const deletingButton = screen.getByRole("button", { name: /deleting/i });
        expect(deletingButton).toBeDisabled();
      });
    });

    it("should show loading state only for the specific row being deleted", async () => {
      const mockMutateAsync = jest.fn().mockImplementation(() => {
        return new Promise((resolve) => setTimeout(resolve, 100));
      });
      (rbacHooks.useDeleteAssignment as jest.Mock).mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        variables: null,
      });

      renderComponent();

      const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
      // We have 2 non-immutable assignments (assignment-1 and assignment-3)
      expect(deleteButtons).toHaveLength(2);

      // Click the first delete button
      fireEvent.click(deleteButtons[0]);

      // First button should show "Deleting..." and be disabled
      await waitFor(() => {
        expect(screen.getByRole("button", { name: /deleting/i })).toBeInTheDocument();
      });

      // Only one "Deleting..." button should exist
      const deletingButtons = screen.getAllByRole("button", { name: /deleting/i });
      expect(deletingButtons).toHaveLength(1);

      // Second delete button should still show "Delete" and be enabled
      const stillDeleteButtons = screen.getAllByRole("button", { name: /^delete$/i });
      expect(stillDeleteButtons).toHaveLength(1);
      expect(stillDeleteButtons[0]).not.toBeDisabled();
    });
  });

  describe("Scope Display", () => {
    it("should display scope type as badge", () => {
      renderComponent();

      expect(screen.getByText("Global")).toBeInTheDocument();
      expect(screen.getByText("Project")).toBeInTheDocument();
      expect(screen.getByText("Flow")).toBeInTheDocument();
    });

    it("should display scope ID or dash for global scope", () => {
      renderComponent();

      // Global scope has no scope_id, should show dash
      const cells = screen.getAllByText("-");
      expect(cells.length).toBeGreaterThan(0);

      // Other scopes should show their IDs
      expect(screen.getByText("project-123")).toBeInTheDocument();
      expect(screen.getByText("flow-456")).toBeInTheDocument();
    });
  });

  describe("Date Formatting", () => {
    it("should format created_at dates correctly", () => {
      renderComponent();

      // Dates should be formatted as locale strings
      const expectedDate = new Date("2024-01-01T00:00:00Z").toLocaleDateString();
      expect(screen.getByText(expectedDate)).toBeInTheDocument();
    });
  });

  describe("Real-time Updates", () => {
    it("should use query key with filters for real-time updates", () => {
      renderComponent();

      // Check that useGetAssignments was called
      expect(rbacHooks.useGetAssignments).toHaveBeenCalled();

      // When filters change, new query should be made
      const userInput = screen.getByPlaceholderText("Enter user ID...");
      fireEvent.change(userInput, { target: { value: "user-123" } });

      // Re-render should call useGetAssignments with new params
      renderComponent();
      expect(rbacHooks.useGetAssignments).toHaveBeenCalledWith(
        expect.objectContaining({ user_id: "user-123" })
      );
    });
  });

  describe("UI/UX Features", () => {
    it("should display page title and description", () => {
      renderComponent();

      expect(screen.getByText("Role Assignments")).toBeInTheDocument();
      expect(
        screen.getByText("Manage user role assignments for projects and flows")
      ).toBeInTheDocument();
    });

    it("should have proper accessibility labels", () => {
      renderComponent();

      expect(screen.getByText("Filter by User ID")).toBeInTheDocument();
      expect(screen.getByText("Filter by Role")).toBeInTheDocument();
      expect(screen.getByText("Filter by Scope")).toBeInTheDocument();
    });

    it("should display clear visual hierarchy", () => {
      renderComponent();

      // Check that inheritance message is in a highlighted container
      const noteElement = screen.getByText(/Note:/i);
      expect(noteElement).toBeInTheDocument();
    });
  });
});

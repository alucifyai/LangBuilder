import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuditLogView } from "../AuditLogView";
import * as auditAPI from "../../../controllers/API/audit";
import { AuditAction } from "../../../types/audit";

// Mock the API functions
jest.mock("../../../controllers/API/audit");
const mockListAuditLogs = auditAPI.listAuditLogs as jest.MockedFunction<typeof auditAPI.listAuditLogs>;

// Mock the diff modal
jest.mock("../AuditLogDiffModal", () => ({
  AuditLogDiffModal: ({ log, onClose }: any) => (
    <div data-testid="diff-modal">
      <span>{log.action}</span>
      <button onClick={onClose}>Close</button>
    </div>
  ),
}));

describe("AuditLogView", () => {
  const mockLogs = [
    {
      id: "log-1",
      timestamp: "2024-01-01T12:00:00Z",
      actor_id: "user-1",
      action: AuditAction.ROLE_CREATED,
      resource_type: "role",
      resource_id: "role-1",
      before_state: null,
      after_state: { name: "Admin", permissions: ["flows:create"], version: 1 },
      metadata: null,
    },
    {
      id: "log-2",
      timestamp: "2024-01-02T12:00:00Z",
      actor_id: "user-1",
      action: AuditAction.ROLE_UPDATED,
      resource_type: "role",
      resource_id: "role-1",
      before_state: { name: "Admin", permissions: ["flows:create"], version: 1 },
      after_state: { name: "Admin", permissions: ["flows:create", "flows:read"], version: 2 },
      metadata: null,
    },
    {
      id: "log-3",
      timestamp: "2024-01-03T12:00:00Z",
      actor_id: "user-2",
      action: AuditAction.ROLE_DELETED,
      resource_type: "role",
      resource_id: "role-2",
      before_state: { name: "Viewer", permissions: ["flows:read"], version: 1 },
      after_state: null,
      metadata: null,
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Loading and Error States", () => {
    it("should display loading state", () => {
      mockListAuditLogs.mockReturnValue(new Promise(() => {})); // Never resolves
      render(<AuditLogView />);

      expect(screen.getByText("Loading audit logs...")).toBeInTheDocument();
    });

    it("should display error state and retry button", async () => {
      mockListAuditLogs.mockRejectedValue(new Error("Admin privileges required"));
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Admin privileges required")).toBeInTheDocument();
      });

      expect(screen.getByText("Retry")).toBeInTheDocument();
    });

    it("should retry fetching on retry button click", async () => {
      const user = userEvent.setup();
      mockListAuditLogs
        .mockRejectedValueOnce(new Error("Failed"))
        .mockResolvedValueOnce({ logs: mockLogs });

      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Failed")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Retry"));

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });
    });
  });

  describe("Audit Log Display", () => {
    beforeEach(() => {
      mockListAuditLogs.mockResolvedValue({ logs: mockLogs });
    });

    it("should display list of audit logs", async () => {
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
        expect(screen.getByText("Role Updated")).toBeInTheDocument();
        expect(screen.getByText("Role Deleted")).toBeInTheDocument();
      });
    });

    it("should display formatted timestamps", async () => {
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText(/1\/1\/2024/)).toBeInTheDocument();
      });
    });

    it("should display resource type and ID", async () => {
      render(<AuditLogView />);

      await waitFor(() => {
        const resourceTypes = screen.getAllByText("role");
        expect(resourceTypes.length).toBeGreaterThan(0);
        expect(screen.getByText("role-1")).toBeInTheDocument();
      });
    });

    it("should display actor IDs", async () => {
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getAllByText("user-1")).toHaveLength(2);
        expect(screen.getByText("user-2")).toBeInTheDocument();
      });
    });

    it("should display empty state when no logs", async () => {
      mockListAuditLogs.mockResolvedValue({ logs: [] });
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("No audit logs found.")).toBeInTheDocument();
      });
    });

    it("should display view changes button for updates", async () => {
      render(<AuditLogView />);

      await waitFor(() => {
        const viewButtons = screen.getAllByTitle("View changes");
        expect(viewButtons).toHaveLength(1); // Only for ROLE_UPDATED
      });
    });
  });

  describe("Filtering", () => {
    beforeEach(() => {
      mockListAuditLogs.mockResolvedValue({ logs: mockLogs });
    });

    it("should toggle filters panel on button click", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      const filtersButton = screen.getByText("Filters");
      await user.click(filtersButton);

      expect(screen.getByText("All actions")).toBeInTheDocument();
    });

    it("should filter by action type", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const actionSelect = screen.getByDisplayValue("All actions");
      await user.selectOptions(actionSelect, AuditAction.ROLE_CREATED);

      await waitFor(() => {
        expect(mockListAuditLogs).toHaveBeenCalledWith(
          expect.objectContaining({ action: AuditAction.ROLE_CREATED })
        );
      });
    });

    it("should filter by resource type", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const resourceSelect = screen.getByDisplayValue("All types");
      await user.selectOptions(resourceSelect, "role");

      await waitFor(() => {
        expect(mockListAuditLogs).toHaveBeenCalledWith(
          expect.objectContaining({ resource_type: "role" })
        );
      });
    });

    it("should filter by date range", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const startDateInput = screen.getByLabelText("Start Date");
      await user.type(startDateInput, "2024-01-01T00:00");

      await waitFor(() => {
        expect(mockListAuditLogs).toHaveBeenCalledWith(
          expect.objectContaining({ start_date: expect.any(String) })
        );
      });
    });

    it("should clear all filters", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const actionSelect = screen.getByDisplayValue("All actions");
      await user.selectOptions(actionSelect, AuditAction.ROLE_CREATED);

      await user.click(screen.getByText("Clear all filters"));

      await waitFor(() => {
        expect(mockListAuditLogs).toHaveBeenCalledWith({ limit: 50 });
      });
    });

    it("should change result limit", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const limitSelect = screen.getByDisplayValue("50");
      await user.selectOptions(limitSelect, "100");

      await waitFor(() => {
        expect(mockListAuditLogs).toHaveBeenCalledWith({ limit: 100 });
      });
    });
  });

  describe("Diff Modal", () => {
    beforeEach(() => {
      mockListAuditLogs.mockResolvedValue({ logs: mockLogs });
    });

    it("should open diff modal on view changes button click", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Updated")).toBeInTheDocument();
      });

      const viewButton = screen.getByTitle("View changes");
      await user.click(viewButton);

      expect(screen.getByTestId("diff-modal")).toBeInTheDocument();
      expect(screen.getByText(AuditAction.ROLE_UPDATED)).toBeInTheDocument();
    });

    it("should close diff modal", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Updated")).toBeInTheDocument();
      });

      const viewButton = screen.getByTitle("View changes");
      await user.click(viewButton);

      await user.click(screen.getByText("Close"));

      expect(screen.queryByTestId("diff-modal")).not.toBeInTheDocument();
    });
  });

  describe("Refresh", () => {
    beforeEach(() => {
      mockListAuditLogs.mockResolvedValue({ logs: mockLogs });
    });

    it("should refresh logs on refresh button click", async () => {
      const user = userEvent.setup();
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Role Created")).toBeInTheDocument();
      });

      mockListAuditLogs.mockClear();
      await user.click(screen.getByText("Refresh"));

      await waitFor(() => {
        expect(mockListAuditLogs).toHaveBeenCalled();
      });
    });
  });

  describe("Result Count", () => {
    it("should display singular result count", async () => {
      mockListAuditLogs.mockResolvedValue({ logs: [mockLogs[0]] });
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Showing 1 log")).toBeInTheDocument();
      });
    });

    it("should display plural result count", async () => {
      mockListAuditLogs.mockResolvedValue({ logs: mockLogs });
      render(<AuditLogView />);

      await waitFor(() => {
        expect(screen.getByText("Showing 3 logs")).toBeInTheDocument();
      });
    });
  });
});

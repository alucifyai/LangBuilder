import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { GrantListView } from "../GrantListView";
import * as grantsAPI from "../../../controllers/API/grants";
import * as rolesAPI from "../../../controllers/API/roles";
import { PrincipalType, ScopeType } from "../../../types/grant";

// Mock the API functions
jest.mock("../../../controllers/API/grants");
jest.mock("../../../controllers/API/roles");

const mockListGrants = grantsAPI.listGrants as jest.MockedFunction<typeof grantsAPI.listGrants>;
const mockRevokeGrant = grantsAPI.revokeGrant as jest.MockedFunction<typeof grantsAPI.revokeGrant>;
const mockListRoles = rolesAPI.listRoles as jest.MockedFunction<typeof rolesAPI.listRoles>;

// Mock the modals
jest.mock("../AssignRoleModal", () => ({
  AssignRoleModal: ({ onClose, onSuccess }: any) => (
    <div data-testid="assign-modal">
      <button onClick={onSuccess}>Assign</button>
      <button onClick={onClose}>Cancel</button>
    </div>
  ),
}));

jest.mock("../RevokeGrantDialog", () => ({
  RevokeGrantDialog: ({ grant, onConfirm, onCancel }: any) => (
    <div data-testid="revoke-dialog">
      <span>{grant.id}</span>
      <button onClick={onConfirm}>Confirm</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}));

describe("GrantListView", () => {
  const mockGrants = [
    {
      id: "grant-1",
      principal_type: PrincipalType.USER,
      principal_id: "user-1",
      role_id: "role-1",
      scope_type: ScopeType.WORKSPACE,
      scope_id: "workspace-1",
      created_at: "2024-01-01T00:00:00Z",
      expires_at: null,
    },
    {
      id: "grant-2",
      principal_type: PrincipalType.GROUP,
      principal_id: "group-1",
      role_id: "role-2",
      scope_type: ScopeType.PROJECT,
      scope_id: "project-1",
      created_at: "2024-01-02T00:00:00Z",
      expires_at: "2025-01-01T00:00:00Z",
    },
  ];

  const mockRoles = [
    {
      id: "role-1",
      name: "Admin",
      permissions: ["flows:create"],
      version: 1,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
    {
      id: "role-2",
      name: "Viewer",
      permissions: ["flows:read"],
      version: 1,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    mockListRoles.mockResolvedValue({ roles: mockRoles });
  });

  describe("Loading and Error States", () => {
    it("should display loading state", () => {
      mockListGrants.mockReturnValue(new Promise(() => {})); // Never resolves
      render(<GrantListView />);

      expect(screen.getByText("Loading grants...")).toBeInTheDocument();
    });

    it("should display error state and retry button", async () => {
      mockListGrants.mockRejectedValue(new Error("Failed to fetch"));
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Failed to fetch")).toBeInTheDocument();
      });

      expect(screen.getByText("Retry")).toBeInTheDocument();
    });

    it("should retry fetching on retry button click", async () => {
      const user = userEvent.setup();
      mockListGrants
        .mockRejectedValueOnce(new Error("Failed"))
        .mockResolvedValueOnce({ grants: mockGrants });

      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Failed")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Retry"));

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });
    });
  });

  describe("Grant List Display", () => {
    beforeEach(() => {
      mockListGrants.mockResolvedValue({ grants: mockGrants });
    });

    it("should display list of grants", async () => {
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("User")).toBeInTheDocument();
        expect(screen.getByText("Group")).toBeInTheDocument();
      });
    });

    it("should display role names", async () => {
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
        expect(screen.getByText("Viewer")).toBeInTheDocument();
      });
    });

    it("should display scope information", async () => {
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Workspace")).toBeInTheDocument();
        expect(screen.getByText("Project")).toBeInTheDocument();
      });
    });

    it("should display expiration dates", async () => {
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Never")).toBeInTheDocument();
        expect(screen.getByText(/1\/1\/2025/)).toBeInTheDocument();
      });
    });

    it("should display empty state when no grants", async () => {
      mockListGrants.mockResolvedValue({ grants: [] });
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText(/No grants found/)).toBeInTheDocument();
      });
    });
  });

  describe("Filtering", () => {
    beforeEach(() => {
      mockListGrants.mockResolvedValue({ grants: mockGrants });
    });

    it("should toggle filters panel on button click", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const filtersButton = screen.getByText("Filters");
      await user.click(filtersButton);

      expect(screen.getByText("All types")).toBeInTheDocument();
    });

    it("should filter by principal type", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const principalSelect = screen.getByDisplayValue("All types");
      await user.selectOptions(principalSelect, "user");

      await waitFor(() => {
        expect(mockListGrants).toHaveBeenCalledWith(
          expect.objectContaining({ principal_type: "user" })
        );
      });
    });

    it("should filter by scope type", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const scopeSelect = screen.getByDisplayValue("All scopes");
      await user.selectOptions(scopeSelect, "workspace");

      await waitFor(() => {
        expect(mockListGrants).toHaveBeenCalledWith(
          expect.objectContaining({ scope_type: "workspace" })
        );
      });
    });

    it("should filter by role", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const roleSelect = screen.getByDisplayValue("All roles");
      await user.selectOptions(roleSelect, "role-1");

      await waitFor(() => {
        expect(mockListGrants).toHaveBeenCalledWith(
          expect.objectContaining({ role_id: "role-1" })
        );
      });
    });

    it("should clear all filters", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Filters"));

      const principalSelect = screen.getByDisplayValue("All types");
      await user.selectOptions(principalSelect, "user");

      await user.click(screen.getByText("Clear all filters"));

      await waitFor(() => {
        expect(mockListGrants).toHaveBeenCalledWith({});
      });
    });
  });

  describe("Assign Role Modal", () => {
    beforeEach(() => {
      mockListGrants.mockResolvedValue({ grants: mockGrants });
    });

    it("should open assign modal on button click", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Assign Role"));

      expect(screen.getByTestId("assign-modal")).toBeInTheDocument();
    });

    it("should close assign modal and refresh on success", async () => {
      const user = userEvent.setup();
      mockListGrants.mockResolvedValue({ grants: mockGrants });

      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Assign Role"));

      mockListGrants.mockResolvedValue({ grants: [...mockGrants] });
      await user.click(screen.getByText("Assign"));

      await waitFor(() => {
        expect(screen.queryByTestId("assign-modal")).not.toBeInTheDocument();
      });
    });
  });

  describe("Revoke Grant", () => {
    beforeEach(() => {
      mockListGrants.mockResolvedValue({ grants: mockGrants });
      mockRevokeGrant.mockResolvedValue();
    });

    it("should open revoke dialog on revoke button click", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const revokeButtons = screen.getAllByTitle("Revoke grant");
      await user.click(revokeButtons[0]);

      expect(screen.getByTestId("revoke-dialog")).toBeInTheDocument();
    });

    it("should revoke grant and refresh on confirm", async () => {
      const user = userEvent.setup();
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const revokeButtons = screen.getAllByTitle("Revoke grant");
      await user.click(revokeButtons[0]);

      mockListGrants.mockResolvedValue({ grants: [mockGrants[1]] });
      await user.click(screen.getByText("Confirm"));

      await waitFor(() => {
        expect(mockRevokeGrant).toHaveBeenCalledWith("grant-1");
      });
    });

    it("should show error alert on revoke failure", async () => {
      const user = userEvent.setup();
      const alertSpy = jest.spyOn(window, "alert").mockImplementation();

      mockRevokeGrant.mockRejectedValue(new Error("Cannot revoke grant"));
      render(<GrantListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const revokeButtons = screen.getAllByTitle("Revoke grant");
      await user.click(revokeButtons[0]);
      await user.click(screen.getByText("Confirm"));

      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith("Cannot revoke grant");
      });

      alertSpy.mockRestore();
    });
  });
});

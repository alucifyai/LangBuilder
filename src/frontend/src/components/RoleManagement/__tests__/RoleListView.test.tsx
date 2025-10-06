import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RoleListView } from "../RoleListView";
import * as rolesAPI from "../../../controllers/API/roles";

// Mock the API functions
jest.mock("../../../controllers/API/roles");
const mockListRoles = rolesAPI.listRoles as jest.MockedFunction<typeof rolesAPI.listRoles>;
const mockDeleteRole = rolesAPI.deleteRole as jest.MockedFunction<typeof rolesAPI.deleteRole>;

// Mock the modals
jest.mock("../CreateRoleModal", () => ({
  CreateRoleModal: ({ onClose, onSuccess }: any) => (
    <div data-testid="create-modal">
      <button onClick={onSuccess}>Create</button>
      <button onClick={onClose}>Cancel</button>
    </div>
  ),
}));

jest.mock("../EditRoleModal", () => ({
  EditRoleModal: ({ role, onClose, onSuccess }: any) => (
    <div data-testid="edit-modal">
      <span>{role.name}</span>
      <button onClick={onSuccess}>Save</button>
      <button onClick={onClose}>Cancel</button>
    </div>
  ),
}));

jest.mock("../DeleteRoleDialog", () => ({
  DeleteRoleDialog: ({ roleName, onConfirm, onCancel }: any) => (
    <div data-testid="delete-dialog">
      <span>{roleName}</span>
      <button onClick={onConfirm}>Confirm</button>
      <button onClick={onCancel}>Cancel</button>
    </div>
  ),
}));

describe("RoleListView", () => {
  const mockRoles = [
    {
      id: "role-1",
      name: "Admin",
      permissions: ["flows:create", "flows:read", "flows:update"],
      version: 1,
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
    },
    {
      id: "role-2",
      name: "Viewer",
      permissions: ["flows:read"],
      version: 1,
      created_at: "2024-01-02T00:00:00Z",
      updated_at: "2024-01-02T00:00:00Z",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Loading and Error States", () => {
    it("should display loading state", () => {
      mockListRoles.mockReturnValue(new Promise(() => {})); // Never resolves
      render(<RoleListView />);

      expect(screen.getByText("Loading roles...")).toBeInTheDocument();
    });

    it("should display error state and retry button", async () => {
      mockListRoles.mockRejectedValue(new Error("Failed to fetch"));
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Failed to fetch")).toBeInTheDocument();
      });

      expect(screen.getByText("Retry")).toBeInTheDocument();
    });

    it("should retry fetching on retry button click", async () => {
      const user = userEvent.setup();
      mockListRoles
        .mockRejectedValueOnce(new Error("Failed"))
        .mockResolvedValueOnce({ roles: mockRoles });

      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Failed")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Retry"));

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });
    });
  });

  describe("Role List Display", () => {
    beforeEach(() => {
      mockListRoles.mockResolvedValue({ roles: mockRoles });
    });

    it("should display list of roles", async () => {
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
        expect(screen.getByText("Viewer")).toBeInTheDocument();
      });
    });

    it("should display permission count for each role", async () => {
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("3 permissions")).toBeInTheDocument();
        expect(screen.getByText("1 permission")).toBeInTheDocument();
      });
    });

    it("should display version for each role", async () => {
      render(<RoleListView />);

      await waitFor(() => {
        const versionCells = screen.getAllByText(/^v1$/);
        expect(versionCells).toHaveLength(2);
      });
    });

    it("should display formatted created date", async () => {
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("1/1/2024")).toBeInTheDocument();
        expect(screen.getByText("1/2/2024")).toBeInTheDocument();
      });
    });

    it("should display empty state when no roles", async () => {
      mockListRoles.mockResolvedValue({ roles: [] });
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText(/No roles found/)).toBeInTheDocument();
      });
    });
  });

  describe("Create Role Modal", () => {
    beforeEach(() => {
      mockListRoles.mockResolvedValue({ roles: mockRoles });
    });

    it("should open create modal on button click", async () => {
      const user = userEvent.setup();
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Create Role"));

      expect(screen.getByTestId("create-modal")).toBeInTheDocument();
    });

    it("should close create modal and refresh on success", async () => {
      const user = userEvent.setup();
      mockListRoles.mockResolvedValue({ roles: mockRoles });

      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Create Role"));

      mockListRoles.mockResolvedValue({ roles: [...mockRoles] });
      await user.click(screen.getByText("Create"));

      await waitFor(() => {
        expect(screen.queryByTestId("create-modal")).not.toBeInTheDocument();
      });
    });

    it("should close create modal on cancel", async () => {
      const user = userEvent.setup();
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      await user.click(screen.getByText("Create Role"));
      await user.click(screen.getAllByText("Cancel")[0]);

      expect(screen.queryByTestId("create-modal")).not.toBeInTheDocument();
    });
  });

  describe("Edit Role Modal", () => {
    beforeEach(() => {
      mockListRoles.mockResolvedValue({ roles: mockRoles });
    });

    it("should open edit modal on edit button click", async () => {
      const user = userEvent.setup();
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTitle("Edit role");
      await user.click(editButtons[0]);

      expect(screen.getByTestId("edit-modal")).toBeInTheDocument();
      expect(screen.getByText("Admin")).toBeInTheDocument();
    });

    it("should close edit modal and refresh on success", async () => {
      const user = userEvent.setup();
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const editButtons = screen.getAllByTitle("Edit role");
      await user.click(editButtons[0]);

      mockListRoles.mockResolvedValue({ roles: mockRoles });
      await user.click(screen.getByText("Save"));

      await waitFor(() => {
        expect(screen.queryByTestId("edit-modal")).not.toBeInTheDocument();
      });
    });
  });

  describe("Delete Role", () => {
    beforeEach(() => {
      mockListRoles.mockResolvedValue({ roles: mockRoles });
      mockDeleteRole.mockResolvedValue();
    });

    it("should open delete dialog on delete button click", async () => {
      const user = userEvent.setup();
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTitle("Delete role");
      await user.click(deleteButtons[0]);

      expect(screen.getByTestId("delete-dialog")).toBeInTheDocument();
    });

    it("should delete role and refresh on confirm", async () => {
      const user = userEvent.setup();
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTitle("Delete role");
      await user.click(deleteButtons[0]);

      mockListRoles.mockResolvedValue({ roles: [mockRoles[1]] });
      await user.click(screen.getByText("Confirm"));

      await waitFor(() => {
        expect(mockDeleteRole).toHaveBeenCalledWith("role-1");
      });
    });

    it("should show error alert on delete failure", async () => {
      const user = userEvent.setup();
      const alertSpy = jest.spyOn(window, "alert").mockImplementation();

      mockDeleteRole.mockRejectedValue(new Error("Cannot delete role with active grants"));
      render(<RoleListView />);

      await waitFor(() => {
        expect(screen.getByText("Admin")).toBeInTheDocument();
      });

      const deleteButtons = screen.getAllByTitle("Delete role");
      await user.click(deleteButtons[0]);
      await user.click(screen.getByText("Confirm"));

      await waitFor(() => {
        expect(alertSpy).toHaveBeenCalledWith("Cannot delete role with active grants");
      });

      alertSpy.mockRestore();
    });
  });
});

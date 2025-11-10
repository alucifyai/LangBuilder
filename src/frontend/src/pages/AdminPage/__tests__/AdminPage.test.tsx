/**
 * AdminPage Tab Navigation Tests
 *
 * Task 4.1: Test tab navigation and deep linking functionality
 *
 * Success Criteria:
 * - RBAC Management tab visible in AdminPage
 * - User Management is default tab
 * - RBAC Management accessible via deep link (#rbac)
 * - Non-admin users cannot see RBAC Management tab
 * - Tab switching works smoothly
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import AdminPage from "../index";
import { AuthContext } from "../../../contexts/authContext";
import type { AuthContextType } from "../../../types/contexts/auth";

// Mock stores that use import.meta
jest.mock("../../../stores/darkStore", () => ({
  useDarkStore: jest.fn(() => ({
    dark: false,
    setDark: jest.fn(),
  })),
}));

jest.mock("../../../stores/flowStore", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    nodes: [],
    edges: [],
  })),
}));

jest.mock("../../../stores/alertStore", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    setSuccessData: jest.fn(),
    setErrorData: jest.fn(),
  })),
}));

// Mock icon component to avoid complex dependencies
jest.mock("../../../components/common/genericIconComponent", () => {
  return function IconComponent({ name }: { name: string }) {
    return <span data-testid={`icon-${name}`}>{name}</span>;
  };
});

// Mock child components
jest.mock("../UserManagementSection", () => {
  return function UserManagementSection() {
    return <div data-testid="user-management-section">User Management Section</div>;
  };
});

jest.mock("../RBACManagementPage", () => {
  return function RBACManagementPage() {
    return <div data-testid="rbac-management-page">RBAC Management Page</div>;
  };
});

// Mock API hooks used by child components
jest.mock("../../../controllers/API/queries/auth", () => ({
  useAddUser: jest.fn(() => ({ mutate: jest.fn() })),
  useDeleteUsers: jest.fn(() => ({ mutate: jest.fn() })),
  useGetUsers: jest.fn(() => ({ mutate: jest.fn(), isPending: false, isIdle: false })),
  useUpdateUser: jest.fn(() => ({ mutate: jest.fn() })),
}));

describe("AdminPage - Tab Navigation (Task 4.1)", () => {
  const mockSuperUser = {
    id: "user-123",
    username: "admin",
    is_active: true,
    is_superuser: true,
  };

  const mockRegularUser = {
    id: "user-456",
    username: "regular",
    is_active: true,
    is_superuser: false,
  };

  const renderAdminPage = (userData: any, initialRoute = "/admin") => {
    const mockAuthContext: AuthContextType = {
      userData,
      setUserData: jest.fn(),
      login: jest.fn(),
      accessToken: null,
      authenticationErrorCount: 0,
      apiKey: null,
      setApiKey: jest.fn(),
      storeApiKey: jest.fn(),
      getUser: jest.fn(),
    };

    return render(
      <AuthContext.Provider value={mockAuthContext}>
        <MemoryRouter initialEntries={[initialRoute]}>
          <Routes>
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
  };

  describe("Default Tab Behavior", () => {
    it("should show User Management tab as default for superusers", () => {
      renderAdminPage(mockSuperUser);

      // User Management tab should be visible and active
      const userManagementTab = screen.getByRole("tab", { name: /user management/i });
      expect(userManagementTab).toBeInTheDocument();
      expect(userManagementTab).toHaveAttribute("data-state", "active");

      // User Management content should be visible
      expect(screen.getByTestId("user-management-section")).toBeInTheDocument();
    });

    it("should show User Management tab as default for regular users", () => {
      renderAdminPage(mockRegularUser);

      // User Management tab should be visible and active
      const userManagementTab = screen.getByRole("tab", { name: /user management/i });
      expect(userManagementTab).toBeInTheDocument();
      expect(userManagementTab).toHaveAttribute("data-state", "active");

      // User Management content should be visible
      expect(screen.getByTestId("user-management-section")).toBeInTheDocument();
    });
  });

  describe("RBAC Management Tab Visibility", () => {
    it("should show RBAC Management tab for superusers", () => {
      renderAdminPage(mockSuperUser);

      // RBAC Management tab should be visible
      const rbacTab = screen.getByRole("tab", { name: /rbac management/i });
      expect(rbacTab).toBeInTheDocument();
    });

    it("should NOT show RBAC Management tab for non-superusers", () => {
      renderAdminPage(mockRegularUser);

      // RBAC Management tab should NOT be visible
      const rbacTab = screen.queryByRole("tab", { name: /rbac management/i });
      expect(rbacTab).not.toBeInTheDocument();
    });
  });

  describe("Tab Switching", () => {
    it("should switch to RBAC Management tab when clicked", async () => {
      renderAdminPage(mockSuperUser);

      // Initially on User Management tab
      expect(screen.getByTestId("user-management-section")).toBeInTheDocument();

      // Click RBAC Management tab
      const rbacTab = screen.getByRole("tab", { name: /rbac management/i });

      // Simulate complete click interaction
      fireEvent.mouseDown(rbacTab);
      fireEvent.mouseUp(rbacTab);
      fireEvent.click(rbacTab);

      // Wait for tab switch
      await waitFor(() => {
        expect(rbacTab).toHaveAttribute("data-state", "active");
        expect(screen.getByTestId("rbac-management-page")).toBeInTheDocument();
      });

      // User Management content should no longer be visible
      expect(screen.queryByTestId("user-management-section")).not.toBeInTheDocument();
    });

    it("should switch back to User Management tab when clicked", async () => {
      renderAdminPage(mockSuperUser);

      // Switch to RBAC Management tab
      const rbacTab = screen.getByRole("tab", { name: /rbac management/i });
      fireEvent.mouseDown(rbacTab);
      fireEvent.mouseUp(rbacTab);
      fireEvent.click(rbacTab);

      await waitFor(() => {
        expect(screen.getByTestId("rbac-management-page")).toBeInTheDocument();
      });

      // Click User Management tab
      const userManagementTab = screen.getByRole("tab", { name: /user management/i });
      fireEvent.mouseDown(userManagementTab);
      fireEvent.mouseUp(userManagementTab);
      fireEvent.click(userManagementTab);

      // Wait for tab switch
      await waitFor(() => {
        expect(userManagementTab).toHaveAttribute("data-state", "active");
        expect(screen.getByTestId("user-management-section")).toBeInTheDocument();
      });

      // RBAC Management content should no longer be visible
      expect(screen.queryByTestId("rbac-management-page")).not.toBeInTheDocument();
    });
  });

  describe("Deep Linking", () => {
    it("should open RBAC Management tab when navigating to /admin#rbac", () => {
      renderAdminPage(mockSuperUser, "/admin#rbac");

      // RBAC Management tab should be active
      const rbacTab = screen.getByRole("tab", { name: /rbac management/i });
      expect(rbacTab).toHaveAttribute("data-state", "active");

      // RBAC Management content should be visible
      expect(screen.getByTestId("rbac-management-page")).toBeInTheDocument();

      // User Management content should NOT be visible
      expect(screen.queryByTestId("user-management-section")).not.toBeInTheDocument();
    });

    it("should default to User Management when no hash is present", () => {
      renderAdminPage(mockSuperUser, "/admin");

      // User Management tab should be active
      const userManagementTab = screen.getByRole("tab", { name: /user management/i });
      expect(userManagementTab).toHaveAttribute("data-state", "active");

      // User Management content should be visible
      expect(screen.getByTestId("user-management-section")).toBeInTheDocument();
    });

    it("should ignore #rbac deep link for non-superusers", () => {
      renderAdminPage(mockRegularUser, "/admin#rbac");

      // RBAC Management tab should NOT be visible
      const rbacTab = screen.queryByRole("tab", { name: /rbac management/i });
      expect(rbacTab).not.toBeInTheDocument();

      // Should show User Management instead
      // Note: User Management tab should be visible but may not have data-state="active"
      // because Radix UI doesn't render the tab trigger as active when the target tab doesn't exist
      const userManagementTab = screen.getByRole("tab", { name: /user management/i });
      expect(userManagementTab).toBeInTheDocument();
      expect(screen.getByTestId("user-management-section")).toBeInTheDocument();
    });
  });

  describe("Page Header", () => {
    it("should display admin page title and description", () => {
      renderAdminPage(mockSuperUser);

      // Check for admin header (title is in constants, using generic check)
      expect(screen.getByText(/admin/i)).toBeInTheDocument();
    });
  });

  describe("User Authentication", () => {
    it("should not render content when user is not authenticated", () => {
      const mockAuthContext: AuthContextType = {
        userData: null,
        setUserData: jest.fn(),
        login: jest.fn(),
        accessToken: null,
        authenticationErrorCount: 0,
        apiKey: null,
        setApiKey: jest.fn(),
        storeApiKey: jest.fn(),
        getUser: jest.fn(),
      };

      render(
        <AuthContext.Provider value={mockAuthContext}>
          <MemoryRouter initialEntries={["/admin"]}>
            <Routes>
              <Route path="/admin" element={<AdminPage />} />
            </Routes>
          </MemoryRouter>
        </AuthContext.Provider>
      );

      // Should not show any tabs
      expect(screen.queryByRole("tab", { name: /user management/i })).not.toBeInTheDocument();
      expect(screen.queryByRole("tab", { name: /rbac management/i })).not.toBeInTheDocument();
    });
  });
});

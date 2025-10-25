import { expect, test } from "@playwright/test";
import { loginLangflow } from "../../utils/login-langflow";

test.describe("Workspace Management", () => {
  test.beforeEach(async ({ page }) => {
    await loginLangflow(page);

    // Navigate to Admin Page
    await page.getByTestId("user-profile-settings").click();
    await page.getByText("Admin Page", { exact: true }).click();

    // Navigate to RBAC Management (Access Control) - default tab
    await page.waitForSelector('text="RBAC Management"', { timeout: 30000 });

    // Click on Workspaces tab
    await page.getByRole("tab", { name: "Workspaces" }).click();

    // Wait for workspace management to load
    await page.waitForSelector('text="Workspace Management"', { timeout: 30000 });
  });

  test(
    "should display workspace management page correctly",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      // Verify page elements
      await expect(page.getByText("Workspace Management")).toBeVisible();
      await expect(page.getByRole("button", { name: "Create Workspace" })).toBeVisible();

      // Verify table and headers exist
      const table = page.locator("table").first();
      await expect(table).toBeVisible();
      await expect(table.locator("th", { hasText: "Name" })).toBeVisible();
      await expect(table.locator("th", { hasText: "Members" })).toBeVisible();
      await expect(table.locator("th", { hasText: "Projects" })).toBeVisible();
      await expect(table.locator("th", { hasText: "Status" })).toBeVisible();
      await expect(table.locator("th", { hasText: "Actions" })).toBeVisible();

      // Verify search and action buttons
      await expect(page.getByPlaceholder("Search workspaces...")).toBeVisible();
      await expect(page.getByRole("button", { name: "Search" })).toBeVisible();
      await expect(page.getByRole("button", { name: "Refresh" })).toBeVisible();
    }
  );

  test(
    "should create workspace with name and description",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "test_workspace_" + Math.random().toString(36).substring(7);
      const workspaceDescription = "Test workspace description";

      // Click Create Workspace button
      await page.getByRole("button", { name: "Create Workspace" }).click();

      // Wait for create form to appear
      await expect(page.getByText("Create New Workspace")).toBeVisible();

      // Fill in workspace details
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByPlaceholder("Enter workspace description").fill(workspaceDescription);

      // Submit creation
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Wait for workspace to be created and form to close
      await expect(page.getByText("Create New Workspace")).not.toBeVisible({ timeout: 10000 });

      // Verify workspace appears in the list
      await page.waitForTimeout(1000); // Wait for refresh
      await expect(page.getByText(workspaceName)).toBeVisible({ timeout: 10000 });

      // Verify workspace shows Active status
      const workspaceRow = page.locator(`tr:has-text("${workspaceName}")`);
      await expect(workspaceRow.getByText("Active")).toBeVisible();
    }
  );

  test(
    "should create workspace with name only (optional description)",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "test_workspace_" + Math.random().toString(36).substring(7);

      // Click Create Workspace button
      await page.getByRole("button", { name: "Create Workspace" }).click();

      // Fill in only workspace name
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);

      // Verify Create button is enabled
      await expect(page.getByRole("button", { name: "Create", exact: true })).toBeEnabled();

      // Submit creation
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Wait for workspace to be created
      await expect(page.getByText("Create New Workspace")).not.toBeVisible({ timeout: 10000 });

      // Verify workspace appears in the list
      await page.waitForTimeout(1000);
      await expect(page.getByText(workspaceName)).toBeVisible({ timeout: 10000 });
    }
  );

  test(
    "should not allow creating workspace with empty name",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      // Click Create Workspace button
      await page.getByRole("button", { name: "Create Workspace" }).click();

      // Verify Create button is disabled when name is empty
      await expect(page.getByRole("button", { name: "Create", exact: true })).toBeDisabled();

      // Type and then clear the name
      await page.getByPlaceholder("Enter workspace name").fill("test");
      await page.getByPlaceholder("Enter workspace name").clear();

      // Verify Create button is still disabled
      await expect(page.getByRole("button", { name: "Create", exact: true })).toBeDisabled();
    }
  );

  test(
    "should cancel workspace creation",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      // Click Create Workspace button
      await page.getByRole("button", { name: "Create Workspace" }).click();

      // Fill in some data
      await page.getByPlaceholder("Enter workspace name").fill("test workspace");
      await page.getByPlaceholder("Enter workspace description").fill("test description");

      // Click Cancel
      await page.getByRole("button", { name: "Cancel", exact: true }).click();

      // Verify form is closed
      await expect(page.getByText("Create New Workspace")).not.toBeVisible();

      // Open form again and verify it's cleared
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await expect(page.getByPlaceholder("Enter workspace name")).toHaveValue("");
      await expect(page.getByPlaceholder("Enter workspace description")).toHaveValue("");
    }
  );

  test(
    "should edit workspace name and description",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const originalName = "edit_test_" + Math.random().toString(36).substring(7);
      const updatedName = "edited_" + Math.random().toString(36).substring(7);

      // First create a workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(originalName);
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Wait for workspace to appear in the table
      await expect(page.getByText(originalName, { exact: true })).toBeVisible({ timeout: 10000 });

      // Click Edit button
      await page.locator(`tr:has-text("${originalName}")`).getByRole("button", { name: "Edit" }).click();

      // Wait for Save button to appear (indicates edit mode is active)
      await page.getByRole("button", { name: "Save" }).waitFor({ state: "visible", timeout: 10000 });

      // Find the row that contains the Save button (this is the row in edit mode)
      const editingRow = page.locator("tr").filter({ has: page.getByRole("button", { name: "Save" }) });

      // Get the input field from that row
      const nameInput = editingRow.locator("input[type='text']");
      await nameInput.clear();
      await nameInput.fill(updatedName);

      // Save changes
      await editingRow.getByRole("button", { name: "Save" }).click();

      // Wait for save to complete
      await page.waitForTimeout(1000);

      // Verify the updated name appears
      await expect(page.getByText(updatedName)).toBeVisible({ timeout: 10000 });
      await expect(page.getByText(originalName, { exact: true })).not.toBeVisible();
    }
  );

  test(
    "should cancel workspace edit",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "cancel_edit_" + Math.random().toString(36).substring(7);

      // Create a workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByRole("button", { name: "Create", exact: true }).click();
      await page.waitForTimeout(1000);

      // Click Edit
      await page.locator(`tr:has-text("${workspaceName}")`).getByRole("button", { name: "Edit" }).click();

      // Wait for Save button to appear
      await page.getByRole("button", { name: "Save" }).waitFor({ state: "visible", timeout: 10000 });

      // Find the row in edit mode
      const editingRow = page.locator("tr").filter({ has: page.getByRole("button", { name: "Save" }) });

      // Modify the name
      const nameInput = editingRow.locator("input[type='text']");
      await nameInput.fill("modified name");

      // Click Cancel
      await editingRow.getByRole("button", { name: "Cancel" }).click();

      // Verify original name is still shown
      await expect(page.getByText(workspaceName)).toBeVisible();
      await expect(page.getByText("modified name")).not.toBeVisible();
    }
  );

  test.skip(
    "should delete workspace with confirmation",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "delete_test_" + Math.random().toString(36).substring(7);

      // Create a workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByRole("button", { name: "Create", exact: true }).click();
      await page.waitForTimeout(1000);

      // Verify workspace exists
      await expect(page.getByText(workspaceName)).toBeVisible();

      // Find the Delete button
      const workspaceRow = page.locator(`tr:has-text("${workspaceName}")`);

      // Set up dialog promise FIRST (before clicking, to avoid missing the event)
      const dialogPromise = page.waitForEvent('dialog');

      // Start the click but don't await it (it will block until dialog is handled)
      const clickPromise = workspaceRow.getByRole("button", { name: "Delete" }).click();

      // Wait for the dialog to appear
      const dialog = await dialogPromise;

      // Verify dialog message and accept it
      expect(dialog.message()).toContain("Are you sure you want to delete this workspace?");
      await dialog.accept();

      // Now wait for the click to complete
      await clickPromise;

      // Wait for deletion and list refresh to complete
      await page.waitForTimeout(2000);

      // Verify workspace is removed
      await expect(page.getByText(workspaceName, { exact: true })).not.toBeVisible({ timeout: 10000 });
    }
  );

  test(
    "should search for workspaces",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "search_test_" + Math.random().toString(36).substring(7);

      // Create a workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByRole("button", { name: "Create", exact: true }).click();
      await page.waitForTimeout(1000);

      // Search for the workspace
      await page.getByPlaceholder("Search workspaces...").fill(workspaceName);
      await page.getByRole("button", { name: "Search", exact: true }).click();

      // Wait for search results
      await page.waitForTimeout(1000);

      // Verify workspace is shown in results
      await expect(page.getByText(workspaceName)).toBeVisible();

      // Search for non-existent workspace
      await page.getByPlaceholder("Search workspaces...").clear();
      await page.getByPlaceholder("Search workspaces...").fill("nonexistent_workspace_xyz");
      await page.getByRole("button", { name: "Search", exact: true }).click();

      await page.waitForTimeout(1000);

      // Verify "No workspaces found" message or workspace not visible
      await expect(page.getByText(workspaceName, { exact: true })).not.toBeVisible();
    }
  );

  test(
    "should search with Enter key",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "enter_search_" + Math.random().toString(36).substring(7);

      // Create a workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByRole("button", { name: "Create", exact: true }).click();
      await page.waitForTimeout(1000);

      // Search using Enter key
      await page.getByPlaceholder("Search workspaces...").fill(workspaceName);
      await page.getByPlaceholder("Search workspaces...").press("Enter");

      // Wait for search results
      await page.waitForTimeout(1000);

      // Verify workspace is shown
      await expect(page.getByText(workspaceName)).toBeVisible();
    }
  );

  test(
    "should clear search",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      // Enter search term
      await page.getByPlaceholder("Search workspaces...").fill("test search");

      // Verify Clear button appears
      await expect(page.getByRole("button", { name: "Clear" })).toBeVisible();

      // Click Clear
      await page.getByRole("button", { name: "Clear" }).click();

      // Verify search input is cleared
      await expect(page.getByPlaceholder("Search workspaces...")).toHaveValue("");

      // Verify Clear button is no longer visible
      await expect(page.getByRole("button", { name: "Clear" })).not.toBeVisible();
    }
  );

  test(
    "should refresh workspace list",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      // Click Refresh button
      await page.getByRole("button", { name: "Refresh", exact: true }).click();

      // Verify loading state appears briefly
      await page.waitForTimeout(500);

      // Verify table is still visible after refresh
      await expect(page.getByText("Name", { exact: true })).toBeVisible();
    }
  );

  test(
    "should display workspace with correct status and member count",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "status_test_" + Math.random().toString(36).substring(7);

      // Create a workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByPlaceholder("Enter workspace description").fill("Status test description");
      await page.getByRole("button", { name: "Create", exact: true }).click();
      await page.waitForTimeout(1000);

      // Find the workspace row
      const workspaceRow = page.locator(`tr:has-text("${workspaceName}")`);

      // Verify status is "Active"
      await expect(workspaceRow.getByText("Active")).toBeVisible();

      // Verify member count is displayed (at least 1 - the creator)
      const memberCountCell = workspaceRow.locator("td").nth(1); // Members column
      const memberCountText = await memberCountCell.textContent();
      expect(parseInt(memberCountText || "0")).toBeGreaterThanOrEqual(1);

      // Verify projects column shows "-" (no projects yet)
      const projectsCell = workspaceRow.locator("td").nth(2); // Projects column
      await expect(projectsCell).toContainText("-");
    }
  );

  test(
    "should show empty state when no workspaces exist",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      // Delete all workspaces first (if any exist)
      const deleteButtons = page.getByRole("button", { name: "Delete" });
      const count = await deleteButtons.count();

      if (count > 0) {
        // Set up dialog handler
        page.on('dialog', async dialog => {
          await dialog.accept();
        });

        // Delete all workspaces
        for (let i = 0; i < count; i++) {
          await deleteButtons.first().click();
          await page.waitForTimeout(500);
        }

        // Refresh to update the list
        await page.getByRole("button", { name: "Refresh", exact: true }).click();
        await page.waitForTimeout(1000);
      }

      // Search for something to ensure no results
      await page.getByPlaceholder("Search workspaces...").fill("nonexistent");
      await page.getByRole("button", { name: "Search", exact: true }).click();
      await page.waitForTimeout(1000);

      // Verify empty state message
      await expect(page.getByText("No workspaces found. Create your first workspace!")).toBeVisible();
    }
  );

  test.skip(
    "should handle duplicate workspace names",
    { tag: ["@release", "@rbac", "@workspace"] },
    async ({ page }) => {
      const workspaceName = "duplicate_test_" + Math.random().toString(36).substring(7);

      // Create first workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByRole("button", { name: "Create", exact: true }).click();
      await page.waitForTimeout(1000);

      // Try to create duplicate workspace
      await page.getByRole("button", { name: "Create Workspace" }).click();
      await page.getByPlaceholder("Enter workspace name").fill(workspaceName);
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // The component handles duplicates gracefully - it either shows error or refreshes
      // Wait for the form to close or error to appear
      await page.waitForTimeout(2000);

      // Form should eventually close (component clears form on duplicate error)
      await expect(page.getByText("Create New Workspace")).not.toBeVisible({ timeout: 5000 });
    }
  );
});

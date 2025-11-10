/**
 * RBACManagementPage Component
 *
 * Main RBAC management interface within AdminPage.
 * Provides interface for managing role assignments.
 *
 * Task 4.1: Initial page structure
 * Task 4.2: AssignmentListView integration
 */

import AssignmentListView from "./AssignmentListView";

export default function RBACManagementPage() {
  return (
    <div className="flex h-full w-full flex-col p-4">
      <div className="mb-4">
        <h2 className="text-2xl font-semibold">RBAC Management</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Manage role-based access control for users, projects, and flows.
        </p>
      </div>

      <div className="flex-1 overflow-hidden">
        <AssignmentListView />
      </div>
    </div>
  );
}

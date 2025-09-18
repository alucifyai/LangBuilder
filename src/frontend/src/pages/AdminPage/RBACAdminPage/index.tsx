import { useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ComplianceReporting from "./components/ComplianceReporting";
import RoleManagement from "./components/RoleManagement";
import SystemSettings from "./components/SystemSettings";
import UserAssignment from "./components/UserAssignment";
import WorkspaceManagement from "./components/WorkspaceManagement";

export default function RBACAdminPage() {
  const [activeTab, setActiveTab] = useState("workspaces");

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center px-6">
          <div className="flex items-center space-x-2">
            <IconComponent name="Shield" className="h-6 w-6" />
            <h1 className="text-lg font-semibold">RBAC Management</h1>
          </div>
          <div className="ml-auto flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">
              Role-Based Access Control Administration
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="flex-1 flex flex-col"
      >
        <div className="border-b bg-muted/50">
          <TabsList className="grid w-full grid-cols-5 bg-transparent h-12">
            <TabsTrigger
              value="workspaces"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Building2" className="h-4 w-4" />
              <span>Workspaces</span>
            </TabsTrigger>
            <TabsTrigger
              value="roles"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Users" className="h-4 w-4" />
              <span>Roles</span>
            </TabsTrigger>
            <TabsTrigger
              value="assignments"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="UserCheck" className="h-4 w-4" />
              <span>Assignments</span>
            </TabsTrigger>
            <TabsTrigger
              value="compliance"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="FileText" className="h-4 w-4" />
              <span>Compliance</span>
            </TabsTrigger>
            <TabsTrigger
              value="settings"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Settings" className="h-4 w-4" />
              <span>Settings</span>
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          <TabsContent value="workspaces" className="h-full m-0 p-0">
            <WorkspaceManagement />
          </TabsContent>

          <TabsContent value="roles" className="h-full m-0 p-0">
            <RoleManagement />
          </TabsContent>

          <TabsContent value="assignments" className="h-full m-0 p-0">
            <UserAssignment />
          </TabsContent>

          <TabsContent value="compliance" className="h-full m-0 p-0">
            <ComplianceReporting />
          </TabsContent>

          <TabsContent value="settings" className="h-full m-0 p-0">
            <SystemSettings />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

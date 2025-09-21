import { useState, useEffect } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import useAuthStore from "@/stores/authStore";
import AuditLogs from "./components/AuditLogs";
import EnvironmentManagement from "./components/EnvironmentManagement";
import PermissionManagement from "./components/PermissionManagement";
import ProjectManagement from "./components/ProjectManagement";
import RoleAssignments from "./components/RoleAssignments";
import RoleManagement from "./components/RoleManagement";
import ServiceAccounts from "./components/ServiceAccounts";
import UserGroups from "./components/UserGroups";
import WorkspaceManagement from "./components/WorkspaceManagement";

export default function RBACAdminPage() {
  const [activeTab, setActiveTab] = useState("permissions");

  // Centralized authentication state management
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const userData = useAuthStore((state) => state.userData);
  const isFullyAuthenticated = Boolean(isAuthenticated && accessToken);

  // Debug authentication state changes across all tabs
  useEffect(() => {
    console.log("🔄 RBACAdminPage: Global auth state changed:", {
      isAuthenticated,
      accessToken: !!accessToken,
      isFullyAuthenticated,
      userData: !!userData,
      activeTab
    });
  }, [isAuthenticated, accessToken, userData, activeTab]);

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-14 items-center px-6">
          <div className="flex items-center space-x-2">
            <IconComponent name="Shield" className="h-6 w-6" />
            <h1 className="text-lg font-semibold">RBAC Management</h1>
          </div>
          <div className="ml-auto flex items-center space-x-4">
            {/* Global Authentication Status Indicator */}
            <Badge variant={isFullyAuthenticated ? "default" : "destructive"} className="text-xs">
              <IconComponent
                name={isFullyAuthenticated ? "CheckCircle" : "XCircle"}
                className="h-3 w-3 mr-1"
              />
              {isFullyAuthenticated ? "Authenticated" : "Not Authenticated"}
            </Badge>
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
          <TabsList className="grid w-full grid-cols-9 bg-transparent h-12">
            <TabsTrigger
              value="permissions"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Key" className="h-4 w-4" />
              <span>Permissions</span>
            </TabsTrigger>
            <TabsTrigger
              value="roles"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Users" className="h-4 w-4" />
              <span>Roles</span>
            </TabsTrigger>
            <TabsTrigger
              value="projects"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Building2" className="h-4 w-4" />
              <span>Projects</span>
            </TabsTrigger>
            <TabsTrigger
              value="service-accounts"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Bot" className="h-4 w-4" />
              <span>Service Accounts</span>
            </TabsTrigger>
            <TabsTrigger
              value="environments"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Settings" className="h-4 w-4" />
              <span>Environments</span>
            </TabsTrigger>
            <TabsTrigger
              value="workspaces"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="Building" className="h-4 w-4" />
              <span>Workspaces</span>
            </TabsTrigger>
            <TabsTrigger
              value="user-groups"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="UserCheck" className="h-4 w-4" />
              <span>User Groups</span>
            </TabsTrigger>
            <TabsTrigger
              value="assignments"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="UserPlus" className="h-4 w-4" />
              <span>Assignments</span>
            </TabsTrigger>
            <TabsTrigger
              value="audit"
              className="flex items-center space-x-2 data-[state=active]:bg-background"
            >
              <IconComponent name="FileText" className="h-4 w-4" />
              <span>Audit Logs</span>
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          <TabsContent value="permissions" className="h-full m-0 p-0">
            <PermissionManagement />
          </TabsContent>

          <TabsContent value="roles" className="h-full m-0 p-0">
            <RoleManagement />
          </TabsContent>

          <TabsContent value="projects" className="h-full m-0 p-0">
            <ProjectManagement />
          </TabsContent>

          <TabsContent value="service-accounts" className="h-full m-0 p-0">
            <ServiceAccounts />
          </TabsContent>

          <TabsContent value="environments" className="h-full m-0 p-0">
            <EnvironmentManagement />
          </TabsContent>

          <TabsContent value="workspaces" className="h-full m-0 p-0">
            <WorkspaceManagement />
          </TabsContent>

          <TabsContent value="user-groups" className="h-full m-0 p-0">
            <UserGroups />
          </TabsContent>

          <TabsContent value="assignments" className="h-full m-0 p-0">
            <RoleAssignments />
          </TabsContent>

          <TabsContent value="audit" className="h-full m-0 p-0">
            <AuditLogs />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}

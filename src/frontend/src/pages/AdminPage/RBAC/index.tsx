import { useState } from "react";
import { useContext } from "react";
import IconComponent from "../../../components/common/genericIconComponent";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../../components/ui/tabs";
import { AuthContext } from "../../../contexts/authContext";
import PermissionGuard from "../../../components/rbac/PermissionGuard";
import useAlertStore from "../../../stores/alertStore";
import WorkspaceManagementPage from "./WorkspaceManagementPage";
import RoleManagementPage from "./RoleManagementPage";
import RoleAssignmentPage from "./RoleAssignmentPage";
import ServiceAccountPage from "./ServiceAccountPage";
import AuditLogsPage from "./AuditLogsPage";
import ComplianceReportsPage from "./ComplianceReportsPage";

export default function RBACAdminPage() {
  const { userData } = useContext(AuthContext);
  const [activeTab, setActiveTab] = useState("workspaces");
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  if (!userData) {
    return null;
  }

  return (
    <div className="admin-page-panel flex h-full flex-col pb-8">
      <div className="main-page-nav-arrangement">
        <span className="main-page-nav-title">
          <IconComponent name="Shield" className="w-6" />
          RBAC Administration
        </span>
      </div>
      <span className="admin-page-description-text">
        Role-Based Access Control management for LangBuilder
      </span>

      <div className="px-4">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-6">
            <PermissionGuard permission="workspaces:read">
              <TabsTrigger value="workspaces" className="flex items-center gap-2">
                <IconComponent name="Building" className="h-4 w-4" />
                Workspaces
              </TabsTrigger>
            </PermissionGuard>
            
            <PermissionGuard permission="roles:read">
              <TabsTrigger value="roles" className="flex items-center gap-2">
                <IconComponent name="Shield" className="h-4 w-4" />
                Roles
              </TabsTrigger>
            </PermissionGuard>
            
            <PermissionGuard permission="roles:assign">
              <TabsTrigger value="assignments" className="flex items-center gap-2">
                <IconComponent name="Users" className="h-4 w-4" />
                Assignments
              </TabsTrigger>
            </PermissionGuard>
            
            <PermissionGuard permission="system:admin">
              <TabsTrigger value="service-accounts" className="flex items-center gap-2">
                <IconComponent name="Bot" className="h-4 w-4" />
                Service Accounts
              </TabsTrigger>
            </PermissionGuard>
            
            <PermissionGuard permission="audit:read">
              <TabsTrigger value="audit" className="flex items-center gap-2">
                <IconComponent name="FileText" className="h-4 w-4" />
                Audit Logs
              </TabsTrigger>
            </PermissionGuard>
            
            <PermissionGuard permission="compliance:read">
              <TabsTrigger value="compliance" className="flex items-center gap-2">
                <IconComponent name="CheckCircle" className="h-4 w-4" />
                Compliance
              </TabsTrigger>
            </PermissionGuard>
          </TabsList>

          <PermissionGuard permission="workspaces:read">
            <TabsContent value="workspaces" className="mt-4">
              <WorkspaceManagementPage />
            </TabsContent>
          </PermissionGuard>

          <PermissionGuard permission="roles:read">
            <TabsContent value="roles" className="mt-4">
              <RoleManagementPage />
            </TabsContent>
          </PermissionGuard>

          <PermissionGuard permission="roles:assign">
            <TabsContent value="assignments" className="mt-4">
              <RoleAssignmentPage />
            </TabsContent>
          </PermissionGuard>

          <PermissionGuard permission="system:admin">
            <TabsContent value="service-accounts" className="mt-4">
              <ServiceAccountPage />
            </TabsContent>
          </PermissionGuard>

          <PermissionGuard permission="audit:read">
            <TabsContent value="audit" className="mt-4">
              <AuditLogsPage />
            </TabsContent>
          </PermissionGuard>

          <PermissionGuard permission="compliance:read">
            <TabsContent value="compliance" className="mt-4">
              <ComplianceReportsPage />
            </TabsContent>
          </PermissionGuard>

          {/* Fallback content when no permission */}
          {!["workspaces", "roles", "assignments", "service-accounts", "audit", "compliance"].some(tab => 
            activeTab === tab
          ) && (
            <TabsContent value={activeTab} className="mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <IconComponent name="AlertTriangle" className="h-5 w-5 text-yellow-500" />
                    Access Restricted
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p>You don't have permission to access this section.</p>
                </CardContent>
              </Card>
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
}
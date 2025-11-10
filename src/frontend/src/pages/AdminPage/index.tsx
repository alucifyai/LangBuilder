import { useContext, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import IconComponent from "../../components/common/genericIconComponent";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import {
  ADMIN_HEADER_DESCRIPTION,
  ADMIN_HEADER_TITLE,
} from "../../constants/constants";
import { AuthContext } from "../../contexts/authContext";
import UserManagementSection from "./UserManagementSection";
import RBACManagementPage from "./RBACManagementPage";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState("user-management");
  const location = useLocation();
  const { userData } = useContext(AuthContext);

  // Check for deep link to RBAC Management tab
  useEffect(() => {
    if (location.hash === "#rbac" && userData?.is_superuser) {
      setActiveTab("rbac-management");
    }
  }, [location, userData]);

  return (
    <>
      {userData && (
        <div className="admin-page-panel flex h-full flex-col pb-8">
          <div className="main-page-nav-arrangement">
            <span className="main-page-nav-title">
              <IconComponent name="Shield" className="w-6" />
              {ADMIN_HEADER_TITLE}
            </span>
          </div>
          <span className="admin-page-description-text">
            {ADMIN_HEADER_DESCRIPTION}
          </span>

          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="flex h-full flex-col"
          >
            <TabsList className="mx-4 w-fit">
              <TabsTrigger value="user-management">
                User Management
              </TabsTrigger>
              {userData.is_superuser && (
                <TabsTrigger value="rbac-management">
                  RBAC Management
                </TabsTrigger>
              )}
            </TabsList>

            <TabsContent value="user-management" className="flex-1">
              <UserManagementSection />
            </TabsContent>

            {userData.is_superuser && (
              <TabsContent value="rbac-management" className="flex-1">
                <RBACManagementPage />
              </TabsContent>
            )}
          </Tabs>
        </div>
      )}
    </>
  );
}

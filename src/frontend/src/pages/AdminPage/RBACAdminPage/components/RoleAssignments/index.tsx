// Role Assignments Component - Real API Implementation
import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useGetRoleAssignments } from "@/controllers/API/queries/rbac/use-get-role-assignments";
import useAuthStore from "@/stores/authStore";
import AuthenticationModal from "../../../RBAC/components/AuthenticationModal";

export default function RoleAssignments() {
  const [searchTerm, setSearchTerm] = useState("");
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Authentication state
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const isFullyAuthenticated = Boolean(isAuthenticated && accessToken);

  // API hooks
  const {
    mutate: fetchRoleAssignments,
    data: roleAssignmentsData,
    isPending: isLoading,
    error,
  } = useGetRoleAssignments({
    onSuccess: (data) => console.log("✅ Role assignments fetched:", data),
    onError: (error) => console.error("❌ Failed to fetch role assignments:", error),
  });

  // Fetch data when authenticated
  useEffect(() => {
    if (isFullyAuthenticated) {
      fetchRoleAssignments({ search: searchTerm });
    }
  }, [isFullyAuthenticated]);

  const requireAuth = (action: string, callback: () => void) => {
    if (!isFullyAuthenticated) {
      setShowAuthModal(true);
    } else {
      callback();
    }
  };

  const handleSearch = () => {
    requireAuth("search-role-assignments", () => {
      fetchRoleAssignments({ search: searchTerm });
    });
  };

  const roleAssignments = roleAssignmentsData?.role_assignments || [];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <IconComponent name="UserPlus" className="h-5 w-5" />
            <span>Role Assignments</span>
          </h2>
          <p className="text-sm text-gray-600 mt-1">Manage user role assignments</p>
        </div>
        <Badge variant={isFullyAuthenticated ? "default" : "destructive"} className="text-xs">
          <IconComponent name={isFullyAuthenticated ? "CheckCircle" : "XCircle"} className="h-3 w-3 mr-1" />
          {isFullyAuthenticated ? "Authenticated" : "Not Authenticated"}
        </Badge>
      </div>

      <div className="mb-4 flex space-x-2">
        <Input
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search role assignments..."
          className="w-64"
        />
        <Button onClick={handleSearch} disabled={isLoading || !isFullyAuthenticated}>
          {isLoading ? "Searching..." : "Search"}
        </Button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          Error: {error.message}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Role Assignments</CardTitle>
          <CardDescription>
            {isLoading ? "Loading..." : `Found ${roleAssignments.length} assignment${roleAssignments.length !== 1 ? 's' : ''}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Scope</TableHead>
                <TableHead>Assigned By</TableHead>
                <TableHead>Assigned</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    <IconComponent name="Loader2" className="h-4 w-4 animate-spin mr-2" />
                    Loading role assignments...
                  </TableCell>
                </TableRow>
              ) : !isFullyAuthenticated ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    Please authenticate to view role assignments
                    <Button variant="link" onClick={() => setShowAuthModal(true)} className="ml-2">Sign In</Button>
                  </TableCell>
                </TableRow>
              ) : roleAssignments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">No role assignments found</TableCell>
                </TableRow>
              ) : (
                roleAssignments.map((assignment) => (
                  <TableRow key={assignment.id}>
                    <TableCell className="font-medium">{assignment.user?.name || assignment.user_id}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{assignment.role?.name || assignment.role_id}</Badge>
                    </TableCell>
                    <TableCell>{assignment.scope_type}</TableCell>
                    <TableCell>{assignment.assigned_by?.name || "System"}</TableCell>
                    <TableCell>{new Date(assignment.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm">
                        <IconComponent name="MoreHorizontal" className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <AuthenticationModal
        open={showAuthModal}
        onOpenChange={setShowAuthModal}
        onSuccess={() => {
          fetchRoleAssignments({ search: searchTerm });
        }}
      />
    </div>
  );
}
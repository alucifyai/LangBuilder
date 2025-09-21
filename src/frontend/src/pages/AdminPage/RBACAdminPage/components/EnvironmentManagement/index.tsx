// Environment Management Component - Real API Implementation
import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useGetEnvironments, Environment } from "@/controllers/API/queries/rbac/use-get-environments";
import useAuthStore from "@/stores/authStore";
import AuthenticationModal from "../../../RBAC/components/AuthenticationModal";

export default function EnvironmentManagement() {
  const [searchTerm, setSearchTerm] = useState("");
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Authentication state
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const isFullyAuthenticated = Boolean(isAuthenticated && accessToken);

  // API hooks
  const {
    mutate: fetchEnvironments,
    data: environmentsData,
    isPending: isLoading,
    error,
  } = useGetEnvironments({
    onSuccess: (data) => console.log("✅ Environments fetched:", data),
    onError: (error) => console.error("❌ Failed to fetch environments:", error),
  });

  // Fetch data when authenticated
  useEffect(() => {
    if (isFullyAuthenticated) {
      fetchEnvironments({ search: searchTerm });
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
    requireAuth("search-environments", () => {
      fetchEnvironments({ search: searchTerm });
    });
  };

  const environments = environmentsData?.environments || [];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <IconComponent name="Settings" className="h-5 w-5" />
            <span>Environment Management</span>
          </h2>
          <p className="text-sm text-gray-600 mt-1">Manage deployment environments</p>
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
          placeholder="Search environments..."
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
          <CardTitle>Environments</CardTitle>
          <CardDescription>
            {isLoading ? "Loading..." : `Found ${environments.length} environment${environments.length !== 1 ? 's' : ''}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Project</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Deployed</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    <IconComponent name="Loader2" className="h-4 w-4 animate-spin mr-2" />
                    Loading environments...
                  </TableCell>
                </TableRow>
              ) : !isFullyAuthenticated ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">
                    Please authenticate to view environments
                    <Button variant="link" onClick={() => setShowAuthModal(true)} className="ml-2">Sign In</Button>
                  </TableCell>
                </TableRow>
              ) : environments.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8">No environments found</TableCell>
                </TableRow>
              ) : (
                environments.map((env) => (
                  <TableRow key={env.id}>
                    <TableCell className="font-medium">{env.name}</TableCell>
                    <TableCell><Badge variant="outline">{env.type}</Badge></TableCell>
                    <TableCell>{env.project_id}</TableCell>
                    <TableCell>
                      <Badge variant={env.is_active ? "default" : "destructive"}>
                        {env.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>{env.last_deployed_at ? new Date(env.last_deployed_at).toLocaleDateString() : "Never"}</TableCell>
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
          fetchEnvironments({ search: searchTerm });
        }}
      />
    </div>
  );
}
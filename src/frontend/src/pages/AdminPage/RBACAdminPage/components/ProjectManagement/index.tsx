// Project Management Component - Real API Implementation
// Implements project creation and management within workspaces

import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { useGetProjects, Project } from "@/controllers/API/queries/rbac/use-get-projects";
import { useCreateProject, CreateProjectData } from "@/controllers/API/queries/rbac/use-create-project";
import { useGetWorkspaces, Workspace } from "@/controllers/API/queries/rbac/use-get-workspaces";
import useAuthStore from "@/stores/authStore";
import AuthenticationModal from "../../../RBAC/components/AuthenticationModal";

interface ProjectBuilderProps {
  project?: Project;
  workspaces: Workspace[];
  onSave: (projectData: CreateProjectData) => void;
  onCancel: () => void;
}

function ProjectBuilder({
  project,
  workspaces,
  onSave,
  onCancel,
}: ProjectBuilderProps) {
  const [name, setName] = useState(project?.name || "");
  const [description, setDescription] = useState(project?.description || "");
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(
    project?.workspace_id || workspaces[0]?.id || "",
  );
  const [nameError, setNameError] = useState("");
  const [workspaceError, setWorkspaceError] = useState("");

  const handleSave = () => {
    let hasError = false;

    if (!name.trim()) {
      setNameError("Project name is required");
      hasError = true;
    } else {
      setNameError("");
    }

    if (!selectedWorkspaceId) {
      setWorkspaceError("Workspace selection is required");
      hasError = true;
    } else {
      setWorkspaceError("");
    }

    if (!hasError) {
      onSave({
        name: name.trim(),
        description: description.trim() || undefined,
        workspace_id: selectedWorkspaceId,
      });
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Project Name *</Label>
        <Input
          id="name"
          placeholder="Enter project name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {nameError && <p className="text-sm text-red-600">{nameError}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="workspace">Workspace *</Label>
        <Select value={selectedWorkspaceId} onValueChange={setSelectedWorkspaceId}>
          <SelectTrigger>
            <SelectValue placeholder="Select workspace" />
          </SelectTrigger>
          <SelectContent>
            {workspaces.map((workspace) => (
              <SelectItem key={workspace.id} value={workspace.id}>
                {workspace.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {workspaceError && <p className="text-sm text-red-600">{workspaceError}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          placeholder="Enter project description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
        />
      </div>

      <div className="flex space-x-2">
        <Button onClick={handleSave} className="flex-1">
          {project ? "Update Project" : "Create Project"}
        </Button>
        <Button variant="outline" onClick={onCancel} className="flex-1">
          Cancel
        </Button>
      </div>
    </div>
  );
}

export default function ProjectManagement() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Authentication state
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const accessToken = useAuthStore((state) => state.accessToken);
  const userData = useAuthStore((state) => state.userData);
  const isFullyAuthenticated = Boolean(isAuthenticated && accessToken);

  // API hooks
  const {
    mutate: fetchProjects,
    data: projectsData,
    isPending: isLoadingProjects,
    error: projectsError,
  } = useGetProjects({
    onSuccess: (data) => {
      console.log("✅ Projects fetched successfully:", data);
    },
    onError: (error) => {
      console.error("❌ Failed to fetch projects:", error);
    },
  });

  const {
    mutate: fetchWorkspaces,
    data: workspacesData,
    isPending: isLoadingWorkspaces,
  } = useGetWorkspaces({
    onSuccess: (data) => {
      console.log("✅ Workspaces fetched successfully:", data);
    },
    onError: (error) => {
      console.error("❌ Failed to fetch workspaces:", error);
    },
  });

  const { mutate: createProject, isPending: isCreatingProject } = useCreateProject({
    onSuccess: (newProject) => {
      console.log("✅ Project created successfully:", newProject);
      setIsCreateDialogOpen(false);
      // Refresh projects list
      fetchProjects({ search: searchTerm });
      alert(`✅ Project "${newProject.name}" created successfully!`);
    },
    onError: (error) => {
      console.error("❌ Failed to create project:", error);
      alert(`❌ Failed to create project: ${error.message || "Unknown error"}`);
    },
  });

  // Authentication helper
  const requireAuth = (action: string, callback: () => void) => {
    if (!isFullyAuthenticated) {
      console.log("❌ Not authenticated, showing modal for action:", action);
      setShowAuthModal(true);
    } else {
      console.log("✅ Authenticated, executing action:", action);
      callback();
    }
  };

  const handleAuthSuccess = () => {
    console.log("🎉 Authentication successful, fetching data");
    fetchProjects({ search: searchTerm });
    fetchWorkspaces({});
  };

  // Fetch data when authenticated
  useEffect(() => {
    if (isFullyAuthenticated) {
      fetchProjects({ search: searchTerm });
      fetchWorkspaces({});
    }
  }, [isFullyAuthenticated]);

  // Debug authentication state changes
  useEffect(() => {
    console.log("🔄 ProjectManagement: Auth state changed:", {
      isAuthenticated,
      accessToken: !!accessToken,
      isFullyAuthenticated,
      userData: !!userData
    });
  }, [isAuthenticated, accessToken, userData]);

  const handleCreateProject = (projectData: CreateProjectData) => {
    requireAuth("create-project", () => {
      createProject(projectData);
    });
  };

  const handleSearch = () => {
    requireAuth("search-projects", () => {
      fetchProjects({ search: searchTerm });
    });
  };

  // Get data from API responses
  const projects = projectsData?.projects || [];
  const workspaces = workspacesData?.workspaces || [];

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <IconComponent name="Building2" className="h-5 w-5" />
            <span>Project Management</span>
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Create and manage projects within workspaces
          </p>
        </div>
        <div className="flex items-center space-x-2">
          {/* Authentication Status Indicator */}
          <Badge variant={isFullyAuthenticated ? "default" : "destructive"} className="text-xs">
            <IconComponent
              name={isFullyAuthenticated ? "CheckCircle" : "XCircle"}
              className="h-3 w-3 mr-1"
            />
            {isFullyAuthenticated ? "Authenticated" : "Not Authenticated"}
          </Badge>

          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button disabled={!isFullyAuthenticated}>
                <IconComponent name="Plus" className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
                <DialogDescription>
                  Add a new project to organize your flows and environments.
                </DialogDescription>
              </DialogHeader>
              <ProjectBuilder
                workspaces={workspaces}
                onSave={handleCreateProject}
                onCancel={() => setIsCreateDialogOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4 flex space-x-2">
        <Input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search projects..."
          className="w-64"
        />
        <Button onClick={handleSearch} disabled={isLoadingProjects || !isFullyAuthenticated}>
          {isLoadingProjects ? "Searching..." : "Search"}
        </Button>
        {searchTerm && (
          <Button
            variant="outline"
            onClick={() => {
              setSearchTerm("");
              requireAuth("clear-search", () => {
                fetchProjects({ search: "" });
              });
            }}
          >
            Clear
          </Button>
        )}
      </div>

      {/* Error Display */}
      {projectsError && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          Error loading projects: {projectsError.message}
        </div>
      )}

      {/* Projects Table */}
      <Card>
        <CardHeader>
          <CardTitle>Projects</CardTitle>
          <CardDescription>
            {isLoadingProjects ? "Loading projects..." :
             projects.length === 0 ? "No projects found" :
             `Found ${projects.length} project${projects.length !== 1 ? 's' : ''}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Workspace</TableHead>
                  <TableHead>Environments</TableHead>
                  <TableHead>Flows</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoadingProjects ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="flex items-center justify-center">
                        <IconComponent name="Loader2" className="h-4 w-4 animate-spin mr-2" />
                        Loading projects...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : !isFullyAuthenticated ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="text-gray-500">
                        Please authenticate to view projects
                        <Button
                          variant="link"
                          onClick={() => setShowAuthModal(true)}
                          className="ml-2"
                        >
                          Sign In
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : projects.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="text-gray-500">
                        No projects found. Create your first project!
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  projects.map((project) => (
                    <TableRow key={project.id}>
                      <TableCell className="font-medium">{project.name}</TableCell>
                      <TableCell>{project.description || "No description"}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {workspaces.find(w => w.id === project.workspace_id)?.name || "Unknown"}
                        </Badge>
                      </TableCell>
                      <TableCell>{project.environment_count || 0}</TableCell>
                      <TableCell>{project.flow_count || 0}</TableCell>
                      <TableCell>
                        {new Date(project.created_at).toLocaleDateString()}
                      </TableCell>
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
          </div>
        </CardContent>
      </Card>

      {/* Authentication Modal */}
      <AuthenticationModal
        open={showAuthModal}
        onOpenChange={setShowAuthModal}
        onSuccess={handleAuthSuccess}
      />
    </div>
  );
}
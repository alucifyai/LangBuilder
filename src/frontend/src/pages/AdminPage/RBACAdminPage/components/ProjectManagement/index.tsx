// Project Management Component - Epic 2: Hierarchy level 2
// Implements project creation and management within workspaces

import { useMemo, useState } from "react";
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
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Project, User, Workspace } from "../../types/rbac";

// Mock data for projects and workspaces
const MOCK_WORKSPACES: Workspace[] = [
  {
    id: "ws-1",
    name: "Data Science Team",
    description: "Main workspace for data science projects",
    owner_id: "user-1",
    settings: {},
    member_count: 12,
    project_count: 8,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-15T00:00:00Z",
  },
  {
    id: "ws-2",
    name: "ML Engineering",
    description: "Machine learning engineering and deployment workflows",
    owner_id: "user-2",
    settings: {},
    member_count: 6,
    project_count: 4,
    created_at: "2024-01-05T00:00:00Z",
    updated_at: "2024-01-20T00:00:00Z",
  },
];

const MOCK_PROJECTS: Project[] = [
  {
    id: "proj-1",
    name: "Customer Analytics",
    description: "Customer behavior analysis and segmentation",
    workspace_id: "ws-1",
    workspace: MOCK_WORKSPACES[0],
    owner_id: "user-1",
    environment_count: 3,
    flow_count: 12,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-25T00:00:00Z",
  },
  {
    id: "proj-2",
    name: "Fraud Detection",
    description: "Real-time fraud detection system",
    workspace_id: "ws-1",
    workspace: MOCK_WORKSPACES[0],
    owner_id: "user-2",
    environment_count: 2,
    flow_count: 8,
    created_at: "2024-01-05T00:00:00Z",
    updated_at: "2024-01-24T00:00:00Z",
  },
  {
    id: "proj-3",
    name: "Recommendation Engine",
    description: "Product recommendation ML pipeline",
    workspace_id: "ws-2",
    workspace: MOCK_WORKSPACES[1],
    owner_id: "user-1",
    environment_count: 4,
    flow_count: 15,
    created_at: "2024-01-08T00:00:00Z",
    updated_at: "2024-01-26T00:00:00Z",
  },
];

const MOCK_USERS: User[] = [
  {
    id: "user-1",
    email: "alice@company.com",
    name: "Alice Johnson",
    is_active: true,
    last_login: "2024-01-25T10:30:00Z",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-25T10:30:00Z",
  },
  {
    id: "user-2",
    email: "bob@company.com",
    name: "Bob Smith",
    is_active: true,
    last_login: "2024-01-24T15:45:00Z",
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-24T15:45:00Z",
  },
];

interface CreateProjectRequest {
  name: string;
  description?: string;
  workspace_id: string;
}

interface UpdateProjectRequest {
  name?: string;
  description?: string;
  workspace_id?: string;
}

interface ProjectBuilderProps {
  project?: Project;
  workspaces: Workspace[];
  onSave: (projectData: CreateProjectRequest | UpdateProjectRequest) => void;
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
      setWorkspaceError("Please select a workspace");
      hasError = true;
    } else {
      setWorkspaceError("");
    }

    if (hasError) return;

    const projectData = {
      name: name.trim(),
      description: description.trim() || undefined,
      workspace_id: selectedWorkspaceId,
    };

    onSave(projectData);
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        <div>
          <Label htmlFor="project-name">Project Name *</Label>
          <Input
            id="project-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter project name"
            className={nameError ? "border-red-500" : ""}
          />
          {nameError && (
            <p className="text-sm text-red-500 mt-1">{nameError}</p>
          )}
        </div>
        <div>
          <Label htmlFor="project-description">Description</Label>
          <Textarea
            id="project-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter project description"
            rows={3}
          />
        </div>
        <div>
          <Label htmlFor="project-workspace">Workspace *</Label>
          <Select
            value={selectedWorkspaceId}
            onValueChange={setSelectedWorkspaceId}
          >
            <SelectTrigger className={workspaceError ? "border-red-500" : ""}>
              <SelectValue placeholder="Select workspace" />
            </SelectTrigger>
            <SelectContent>
              {workspaces.map((workspace) => (
                <SelectItem key={workspace.id} value={workspace.id}>
                  <div className="flex items-center justify-between w-full">
                    <span>{workspace.name}</span>
                    <Badge variant="outline" className="ml-2 text-xs">
                      {workspace.member_count} members
                    </Badge>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {workspaceError && (
            <p className="text-sm text-red-500 mt-1">{workspaceError}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          disabled={!name.trim() || !selectedWorkspaceId}
        >
          {project ? "Update Project" : "Create Project"}
        </Button>
      </div>
    </div>
  );
}

interface ProjectTableProps {
  projects: Project[];
  workspaces: Workspace[];
  onEdit: (project: Project) => void;
  onDelete: (projectId: string) => void;
  onViewEnvironments: (project: Project) => void;
  onViewFlows: (project: Project) => void;
}

function ProjectTable({
  projects,
  workspaces,
  onEdit,
  onDelete,
  onViewEnvironments,
  onViewFlows,
}: ProjectTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterWorkspace, setFilterWorkspace] = useState<string>("all");
  const [sortBy, setSortBy] = useState<
    "name" | "environments" | "flows" | "updated"
  >("updated");

  const filteredAndSortedProjects = useMemo(() => {
    let filtered = projects.filter((project) => {
      const matchesSearch =
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (project.description
          ?.toLowerCase()
          .includes(searchTerm.toLowerCase()) ??
          false);

      const matchesWorkspace =
        filterWorkspace === "all" || project.workspace_id === filterWorkspace;

      return matchesSearch && matchesWorkspace;
    });

    filtered.sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "environments":
          return b.environment_count - a.environment_count;
        case "flows":
          return b.flow_count - a.flow_count;
        case "updated":
          return (
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
          );
        default:
          return 0;
      }
    });

    return filtered;
  }, [projects, searchTerm, filterWorkspace, sortBy]);

  const getOwnerName = (ownerId: string) => {
    const owner = MOCK_USERS.find((u) => u.id === ownerId);
    return owner?.name || "Unknown User";
  };

  const getWorkspaceName = (workspaceId: string) => {
    const workspace = workspaces.find((w) => w.id === workspaceId);
    return workspace?.name || "Unknown Workspace";
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Input
          placeholder="Search projects..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filterWorkspace} onValueChange={setFilterWorkspace}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by workspace" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Workspaces</SelectItem>
            {workspaces.map((workspace) => (
              <SelectItem key={workspace.id} value={workspace.id}>
                {workspace.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select
          value={sortBy}
          onValueChange={(value) => setSortBy(value as any)}
        >
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="updated">Recently Updated</SelectItem>
            <SelectItem value="name">Name</SelectItem>
            <SelectItem value="environments">Most Environments</SelectItem>
            <SelectItem value="flows">Most Flows</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Project</TableHead>
                <TableHead>Workspace</TableHead>
                <TableHead>Owner</TableHead>
                <TableHead>Environments</TableHead>
                <TableHead>Flows</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSortedProjects.map((project) => (
                <TableRow key={project.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{project.name}</div>
                      {project.description && (
                        <div className="text-sm text-muted-foreground">
                          {project.description}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {getWorkspaceName(project.workspace_id)}
                    </Badge>
                  </TableCell>
                  <TableCell>{getOwnerName(project.owner_id)}</TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewEnvironments(project)}
                      className="p-0 h-auto font-normal"
                    >
                      {project.environment_count} environments
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewFlows(project)}
                      className="p-0 h-auto font-normal"
                    >
                      {project.flow_count} flows
                    </Button>
                  </TableCell>
                  <TableCell>
                    {new Date(project.updated_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(project)}
                        title="Edit Project"
                      >
                        <IconComponent name="Edit" className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(project.id)}
                        title="Delete Project"
                      >
                        <IconComponent name="Trash2" className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ProjectManagement() {
  const [projects, setProjects] = useState<Project[]>(MOCK_PROJECTS);
  const [workspaces] = useState<Workspace[]>(MOCK_WORKSPACES);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  const handleCreateProject = (projectData: CreateProjectRequest) => {
    const selectedWorkspace = workspaces.find(
      (w) => w.id === projectData.workspace_id,
    );

    const newProject: Project = {
      id: `proj-${Date.now()}`,
      name: projectData.name,
      description: projectData.description,
      workspace_id: projectData.workspace_id,
      workspace: selectedWorkspace!,
      owner_id: "current-user",
      environment_count: 0,
      flow_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setProjects([...projects, newProject]);
    setIsCreateDialogOpen(false);
  };

  const handleUpdateProject = (projectData: UpdateProjectRequest) => {
    if (!editingProject) return;

    const selectedWorkspace = workspaces.find(
      (w) => w.id === projectData.workspace_id,
    );

    const updatedProject: Project = {
      ...editingProject,
      name: projectData.name || editingProject.name,
      description:
        projectData.description !== undefined
          ? projectData.description
          : editingProject.description,
      workspace_id: projectData.workspace_id || editingProject.workspace_id,
      workspace: selectedWorkspace || editingProject.workspace,
      updated_at: new Date().toISOString(),
    };

    setProjects(
      projects.map((p) => (p.id === editingProject.id ? updatedProject : p)),
    );
    setEditingProject(null);
  };

  const handleDeleteProject = (projectId: string) => {
    if (
      confirm(
        "Are you sure you want to delete this project? This action cannot be undone.",
      )
    ) {
      setProjects(projects.filter((p) => p.id !== projectId));
    }
  };

  const handleViewEnvironments = (project: Project) => {
    alert(
      `View environments for ${project.name} - This would open the environment management view`,
    );
  };

  const handleViewFlows = (project: Project) => {
    alert(
      `View flows for ${project.name} - This would open the flow management view`,
    );
  };

  // Calculate summary statistics
  const totalEnvironments = projects.reduce(
    (sum, p) => sum + p.environment_count,
    0,
  );
  const totalFlows = projects.reduce((sum, p) => sum + p.flow_count, 0);
  const averageEnvironments =
    projects.length > 0 ? Math.round(totalEnvironments / projects.length) : 0;
  const averageFlows =
    projects.length > 0 ? Math.round(totalFlows / projects.length) : 0;

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Project Management</h2>
          <p className="text-muted-foreground">
            Manage projects within workspaces and organize your workflows
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <IconComponent name="RefreshCw" className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Dialog
            open={isCreateDialogOpen}
            onOpenChange={setIsCreateDialogOpen}
          >
            <DialogTrigger asChild>
              <Button size="sm">
                <IconComponent name="Plus" className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
                <DialogDescription>
                  Create a new project within a workspace to organize your flows
                  and environments.
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

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Total Projects
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{projects.length}</div>
            <p className="text-xs text-muted-foreground">
              Across {workspaces.length} workspaces
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Total Environments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalEnvironments}</div>
            <p className="text-xs text-muted-foreground">
              Avg {averageEnvironments} per project
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Flows</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFlows}</div>
            <p className="text-xs text-muted-foreground">
              Avg {averageFlows} per project
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Active Workspaces
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{workspaces.length}</div>
            <p className="text-xs text-muted-foreground">With projects</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 overflow-hidden">
        <ProjectTable
          projects={projects}
          workspaces={workspaces}
          onEdit={setEditingProject}
          onDelete={handleDeleteProject}
          onViewEnvironments={handleViewEnvironments}
          onViewFlows={handleViewFlows}
        />
      </div>

      {/* Edit Project Dialog */}
      <Dialog
        open={!!editingProject}
        onOpenChange={() => setEditingProject(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Project: {editingProject?.name}</DialogTitle>
            <DialogDescription>
              Modify project settings and workspace assignment.
            </DialogDescription>
          </DialogHeader>
          {editingProject && (
            <ProjectBuilder
              project={editingProject}
              workspaces={workspaces}
              onSave={handleUpdateProject}
              onCancel={() => setEditingProject(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

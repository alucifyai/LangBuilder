// Environment Management Component - Epic 2: Hierarchy level 3
// Implements environment management within projects (dev/staging/production)

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
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { Environment, Project, Workspace } from "../../types/rbac";

// Mock data
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
];

const MOCK_PROJECTS: Project[] = [
  {
    id: "proj-1",
    name: "Customer Analytics",
    description: "Customer behavior analysis",
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
    description: "Real-time fraud detection",
    workspace_id: "ws-1",
    workspace: MOCK_WORKSPACES[0],
    owner_id: "user-2",
    environment_count: 2,
    flow_count: 8,
    created_at: "2024-01-05T00:00:00Z",
    updated_at: "2024-01-24T00:00:00Z",
  },
];

const MOCK_ENVIRONMENTS: Environment[] = [
  {
    id: "env-1",
    name: "Development",
    description: "Development environment for testing",
    project_id: "proj-1",
    project: MOCK_PROJECTS[0],
    environment_type: "development",
    configuration: {
      auto_deploy: true,
      retention_days: 7,
      resource_limit: "small",
      api_rate_limit: 100,
    },
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-26T00:00:00Z",
  },
  {
    id: "env-2",
    name: "Staging",
    description: "Pre-production testing environment",
    project_id: "proj-1",
    project: MOCK_PROJECTS[0],
    environment_type: "staging",
    configuration: {
      auto_deploy: false,
      retention_days: 30,
      resource_limit: "medium",
      api_rate_limit: 500,
    },
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-25T00:00:00Z",
  },
  {
    id: "env-3",
    name: "Production",
    description: "Live production environment",
    project_id: "proj-1",
    project: MOCK_PROJECTS[0],
    environment_type: "production",
    configuration: {
      auto_deploy: false,
      retention_days: 90,
      resource_limit: "large",
      api_rate_limit: 10000,
    },
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-24T00:00:00Z",
  },
  {
    id: "env-4",
    name: "Development",
    description: "Dev environment for fraud detection",
    project_id: "proj-2",
    project: MOCK_PROJECTS[1],
    environment_type: "development",
    configuration: {
      auto_deploy: true,
      retention_days: 7,
      resource_limit: "small",
      api_rate_limit: 100,
    },
    created_at: "2024-01-06T00:00:00Z",
    updated_at: "2024-01-26T00:00:00Z",
  },
];

interface CreateEnvironmentRequest {
  name: string;
  description?: string;
  project_id: string;
  environment_type: "development" | "staging" | "production";
  configuration: Record<string, any>;
}

interface EnvironmentBuilderProps {
  environment?: Environment;
  projects: Project[];
  onSave: (envData: CreateEnvironmentRequest) => void;
  onCancel: () => void;
}

function EnvironmentBuilder({
  environment,
  projects,
  onSave,
  onCancel,
}: EnvironmentBuilderProps) {
  const [name, setName] = useState(environment?.name || "");
  const [description, setDescription] = useState(
    environment?.description || "",
  );
  const [selectedProjectId, setSelectedProjectId] = useState(
    environment?.project_id || projects[0]?.id || "",
  );
  const [environmentType, setEnvironmentType] = useState<
    "development" | "staging" | "production"
  >(environment?.environment_type || "development");
  const [autoDeploy, setAutoDeploy] = useState(
    environment?.configuration?.auto_deploy ?? true,
  );
  const [retentionDays, setRetentionDays] = useState(
    environment?.configuration?.retention_days ?? 30,
  );
  const [resourceLimit, setResourceLimit] = useState(
    environment?.configuration?.resource_limit ?? "medium",
  );
  const [apiRateLimit, setApiRateLimit] = useState(
    environment?.configuration?.api_rate_limit ?? 1000,
  );

  const [nameError, setNameError] = useState("");

  const handleSave = () => {
    if (!name.trim()) {
      setNameError("Environment name is required");
      return;
    }

    setNameError("");

    const envData: CreateEnvironmentRequest = {
      name: name.trim(),
      description: description.trim() || undefined,
      project_id: selectedProjectId,
      environment_type: environmentType,
      configuration: {
        auto_deploy: autoDeploy,
        retention_days: retentionDays,
        resource_limit: resourceLimit,
        api_rate_limit: apiRateLimit,
      },
    };

    onSave(envData);
  };

  const getEnvironmentIcon = (type: string) => {
    switch (type) {
      case "development":
        return "Code";
      case "staging":
        return "TestTube";
      case "production":
        return "Rocket";
      default:
        return "Server";
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        <div>
          <Label htmlFor="env-name">Environment Name *</Label>
          <Input
            id="env-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter environment name"
            className={nameError ? "border-red-500" : ""}
          />
          {nameError && (
            <p className="text-sm text-red-500 mt-1">{nameError}</p>
          )}
        </div>
        <div>
          <Label htmlFor="env-description">Description</Label>
          <Textarea
            id="env-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter environment description"
            rows={3}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="env-project">Project *</Label>
            <Select
              value={selectedProjectId}
              onValueChange={setSelectedProjectId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="env-type">Environment Type *</Label>
            <Select
              value={environmentType}
              onValueChange={(value) => setEnvironmentType(value as any)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="development">
                  <div className="flex items-center">
                    <IconComponent name="Code" className="h-4 w-4 mr-2" />
                    Development
                  </div>
                </SelectItem>
                <SelectItem value="staging">
                  <div className="flex items-center">
                    <IconComponent name="TestTube" className="h-4 w-4 mr-2" />
                    Staging
                  </div>
                </SelectItem>
                <SelectItem value="production">
                  <div className="flex items-center">
                    <IconComponent name="Rocket" className="h-4 w-4 mr-2" />
                    Production
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="text-lg font-medium">Environment Configuration</h4>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <Label className="text-sm font-medium">Auto-deploy</Label>
              <p className="text-sm text-muted-foreground">
                Automatically deploy changes to this environment
              </p>
            </div>
            <Switch checked={autoDeploy} onCheckedChange={setAutoDeploy} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="retention-days">Data Retention (days)</Label>
              <Select
                value={retentionDays.toString()}
                onValueChange={(value) => setRetentionDays(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">7 days</SelectItem>
                  <SelectItem value="14">14 days</SelectItem>
                  <SelectItem value="30">30 days</SelectItem>
                  <SelectItem value="60">60 days</SelectItem>
                  <SelectItem value="90">90 days</SelectItem>
                  <SelectItem value="180">180 days</SelectItem>
                  <SelectItem value="365">1 year</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="resource-limit">Resource Limit</Label>
              <Select value={resourceLimit} onValueChange={setResourceLimit}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="small">Small (1 CPU, 2GB RAM)</SelectItem>
                  <SelectItem value="medium">
                    Medium (2 CPU, 4GB RAM)
                  </SelectItem>
                  <SelectItem value="large">Large (4 CPU, 8GB RAM)</SelectItem>
                  <SelectItem value="xlarge">
                    X-Large (8 CPU, 16GB RAM)
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="api-rate-limit">
              API Rate Limit (requests/hour)
            </Label>
            <Input
              id="api-rate-limit"
              type="number"
              value={apiRateLimit}
              onChange={(e) => setApiRateLimit(parseInt(e.target.value) || 0)}
              min="0"
              step="100"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          disabled={!name.trim() || !selectedProjectId}
        >
          {environment ? "Update Environment" : "Create Environment"}
        </Button>
      </div>
    </div>
  );
}

interface EnvironmentTableProps {
  environments: Environment[];
  projects: Project[];
  onEdit: (environment: Environment) => void;
  onDelete: (environmentId: string) => void;
  onDeploy: (environment: Environment) => void;
}

function EnvironmentTable({
  environments,
  projects,
  onEdit,
  onDelete,
  onDeploy,
}: EnvironmentTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterProject, setFilterProject] = useState<string>("all");
  const [filterType, setFilterType] = useState<string>("all");

  const filteredEnvironments = useMemo(() => {
    return environments.filter((env) => {
      const matchesSearch =
        env.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (env.description?.toLowerCase().includes(searchTerm.toLowerCase()) ??
          false);

      const matchesProject =
        filterProject === "all" || env.project_id === filterProject;
      const matchesType =
        filterType === "all" || env.environment_type === filterType;

      return matchesSearch && matchesProject && matchesType;
    });
  }, [environments, searchTerm, filterProject, filterType]);

  const getEnvironmentColor = (type: string) => {
    switch (type) {
      case "development":
        return "bg-blue-100 text-blue-800";
      case "staging":
        return "bg-yellow-100 text-yellow-800";
      case "production":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getEnvironmentIcon = (type: string) => {
    switch (type) {
      case "development":
        return "Code";
      case "staging":
        return "TestTube";
      case "production":
        return "Rocket";
      default:
        return "Server";
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Input
          placeholder="Search environments..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filterProject} onValueChange={setFilterProject}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map((project) => (
              <SelectItem key={project.id} value={project.id}>
                {project.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="development">Development</SelectItem>
            <SelectItem value="staging">Staging</SelectItem>
            <SelectItem value="production">Production</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Environment</TableHead>
                <TableHead>Project</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Configuration</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEnvironments.map((env) => (
                <TableRow key={env.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{env.name}</div>
                      {env.description && (
                        <div className="text-sm text-muted-foreground">
                          {env.description}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{env.project.name}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={getEnvironmentColor(env.environment_type)}
                    >
                      <IconComponent
                        name={getEnvironmentIcon(env.environment_type)}
                        className="h-3 w-3 mr-1"
                      />
                      {env.environment_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {env.configuration.auto_deploy && (
                        <Badge variant="outline" className="text-xs">
                          Auto-deploy
                        </Badge>
                      )}
                      <Badge variant="outline" className="text-xs">
                        {env.configuration.resource_limit}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {env.configuration.api_rate_limit} req/h
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(env.updated_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDeploy(env)}
                        title="Deploy"
                        disabled={
                          env.environment_type === "production" &&
                          !confirm("Deploy to production?")
                        }
                      >
                        <IconComponent name="Rocket" className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(env)}
                        title="Edit"
                      >
                        <IconComponent name="Edit" className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(env.id)}
                        title="Delete"
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

export default function EnvironmentManagement() {
  const [environments, setEnvironments] =
    useState<Environment[]>(MOCK_ENVIRONMENTS);
  const [projects] = useState<Project[]>(MOCK_PROJECTS);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingEnvironment, setEditingEnvironment] =
    useState<Environment | null>(null);

  const handleCreateEnvironment = (envData: CreateEnvironmentRequest) => {
    const selectedProject = projects.find((p) => p.id === envData.project_id);

    const newEnvironment: Environment = {
      id: `env-${Date.now()}`,
      name: envData.name,
      description: envData.description,
      project_id: envData.project_id,
      project: selectedProject!,
      environment_type: envData.environment_type,
      configuration: envData.configuration,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setEnvironments([...environments, newEnvironment]);
    setIsCreateDialogOpen(false);
  };

  const handleUpdateEnvironment = (envData: CreateEnvironmentRequest) => {
    if (!editingEnvironment) return;

    const selectedProject = projects.find((p) => p.id === envData.project_id);

    const updatedEnvironment: Environment = {
      ...editingEnvironment,
      name: envData.name,
      description: envData.description,
      project_id: envData.project_id,
      project: selectedProject!,
      environment_type: envData.environment_type,
      configuration: envData.configuration,
      updated_at: new Date().toISOString(),
    };

    setEnvironments(
      environments.map((e) =>
        e.id === editingEnvironment.id ? updatedEnvironment : e,
      ),
    );
    setEditingEnvironment(null);
  };

  const handleDeleteEnvironment = (environmentId: string) => {
    if (confirm("Are you sure you want to delete this environment?")) {
      setEnvironments(environments.filter((e) => e.id !== environmentId));
    }
  };

  const handleDeploy = (environment: Environment) => {
    // PRD: deploy_environment permission required
    alert(`Deploying to ${environment.name} (${environment.environment_type})`);
  };

  // Calculate statistics
  const typeStats = environments.reduce(
    (acc, env) => {
      acc[env.environment_type] = (acc[env.environment_type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Environment Management</h2>
          <p className="text-muted-foreground">
            Manage deployment environments across your projects
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
                Create Environment
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Environment</DialogTitle>
                <DialogDescription>
                  Set up a new environment for deployment and testing.
                </DialogDescription>
              </DialogHeader>
              <EnvironmentBuilder
                projects={projects}
                onSave={handleCreateEnvironment}
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
              Total Environments
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{environments.length}</div>
            <p className="text-xs text-muted-foreground">
              Across {projects.length} projects
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center">
              <IconComponent name="Code" className="h-4 w-4 mr-1" />
              Development
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {typeStats.development || 0}
            </div>
            <p className="text-xs text-muted-foreground">Dev environments</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center">
              <IconComponent name="TestTube" className="h-4 w-4 mr-1" />
              Staging
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{typeStats.staging || 0}</div>
            <p className="text-xs text-muted-foreground">
              Staging environments
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center">
              <IconComponent name="Rocket" className="h-4 w-4 mr-1" />
              Production
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {typeStats.production || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Production environments
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 overflow-hidden">
        <EnvironmentTable
          environments={environments}
          projects={projects}
          onEdit={setEditingEnvironment}
          onDelete={handleDeleteEnvironment}
          onDeploy={handleDeploy}
        />
      </div>

      {/* Edit Environment Dialog */}
      <Dialog
        open={!!editingEnvironment}
        onOpenChange={() => setEditingEnvironment(null)}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Edit Environment: {editingEnvironment?.name}
            </DialogTitle>
            <DialogDescription>
              Modify environment configuration and settings.
            </DialogDescription>
          </DialogHeader>
          {editingEnvironment && (
            <EnvironmentBuilder
              environment={editingEnvironment}
              projects={projects}
              onSave={handleUpdateEnvironment}
              onCancel={() => setEditingEnvironment(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

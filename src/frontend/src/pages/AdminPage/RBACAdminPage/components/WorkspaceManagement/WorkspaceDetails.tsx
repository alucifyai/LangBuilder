import { useEffect, useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import LoadingComponent from "@/components/common/loadingComponent";
import ShadTooltip from "@/components/common/shadTooltipComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  type Project,
  useGetProjects,
  useGetWorkspaceUsers,
  useInviteUser,
  type Workspace,
  type WorkspaceUser,
} from "@/controllers/API/queries/rbac";
import useAlertStore from "@/stores/alertStore";

interface WorkspaceDetailsProps {
  workspace: Workspace;
  onClose: () => void;
}

export default function WorkspaceDetails({
  workspace,
  onClose,
}: WorkspaceDetailsProps) {
  const [users, setUsers] = useState<WorkspaceUser[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [activeTab, setActiveTab] = useState("overview");

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const { mutate: getWorkspaceUsers, isPending: isLoadingUsers } =
    useGetWorkspaceUsers();
  const { mutate: getProjects, isPending: isLoadingProjects } =
    useGetProjects();
  const { mutate: inviteUser, isPending: isInviting } = useInviteUser();

  useEffect(() => {
    loadWorkspaceUsers();
    loadProjects();
  }, [workspace.id]);

  const loadWorkspaceUsers = () => {
    getWorkspaceUsers(
      { workspace_id: workspace.id },
      {
        onSuccess: (data) => {
          setUsers(data.users);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load workspace users",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      },
    );
  };

  const loadProjects = () => {
    getProjects(
      { workspace_id: workspace.id },
      {
        onSuccess: (data) => {
          setProjects(data.projects);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load projects",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      },
    );
  };

  const handleInviteUser = (e: React.FormEvent) => {
    e.preventDefault();

    if (!inviteEmail.trim()) {
      return;
    }

    inviteUser(
      {
        workspace_id: workspace.id,
        email: inviteEmail.trim(),
      },
      {
        onSuccess: () => {
          setSuccessData({ title: "Invitation sent successfully" });
          setInviteEmail("");
          setIsInviteOpen(false);
          loadWorkspaceUsers();
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to send invitation",
            list: [error?.message || "Unknown error occurred"],
          });
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <IconComponent name="Building2" className="h-5 w-5" />
            <h2 className="text-xl font-semibold">{workspace.name}</h2>
            <Badge variant={workspace.is_active ? "default" : "secondary"}>
              {workspace.is_active ? "Active" : "Inactive"}
            </Badge>
          </div>
          {workspace.description && (
            <p className="text-sm text-muted-foreground">
              {workspace.description}
            </p>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <Dialog open={isInviteOpen} onOpenChange={setIsInviteOpen}>
            <DialogTrigger asChild>
              <Button size="sm" className="flex items-center space-x-2">
                <IconComponent name="UserPlus" className="h-4 w-4" />
                <span>Invite User</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle>Invite User to Workspace</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleInviteUser} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="invite-email" className="text-sm font-medium">
                    Email Address
                  </label>
                  <Input
                    id="invite-email"
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="user@example.com"
                    required
                  />
                </div>
                <div className="flex justify-end space-x-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setIsInviteOpen(false);
                      setInviteEmail("");
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isInviting}>
                    {isInviting ? (
                      <>
                        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-transparent" />
                        Inviting...
                      </>
                    ) : (
                      "Send Invitation"
                    )}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Workspace Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center space-x-2">
            <IconComponent
              name="Users"
              className="h-4 w-4 text-muted-foreground"
            />
            <span className="text-sm font-medium">Members</span>
          </div>
          <p className="text-2xl font-bold">{workspace.member_count || 0}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center space-x-2">
            <IconComponent
              name="FolderOpen"
              className="h-4 w-4 text-muted-foreground"
            />
            <span className="text-sm font-medium">Projects</span>
          </div>
          <p className="text-2xl font-bold">{projects.length}</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <div className="flex items-center space-x-2">
            <IconComponent
              name="Shield"
              className="h-4 w-4 text-muted-foreground"
            />
            <span className="text-sm font-medium">Roles</span>
          </div>
          <p className="text-2xl font-bold">{workspace.role_count || 0}</p>
        </div>
      </div>

      {/* Tabs for detailed information */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="rounded-lg border bg-card p-4 space-y-2">
            <h3 className="font-medium">Workspace Information</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Created:</span>
                <span className="ml-2">
                  {new Date(workspace.created_at).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="font-medium">Last Updated:</span>
                <span className="ml-2">
                  {new Date(workspace.updated_at).toLocaleString()}
                </span>
              </div>
              <div>
                <span className="font-medium">ID:</span>
                <span className="ml-2 font-mono text-xs">{workspace.id}</span>
              </div>
              <div>
                <span className="font-medium">Owner ID:</span>
                <span className="ml-2 font-mono text-xs">
                  {workspace.created_by_id}
                </span>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <div className="space-y-2">
            <h3 className="font-medium">Workspace Members</h3>
            {isLoadingUsers ? (
              <LoadingComponent />
            ) : (
              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Roles</TableHead>
                      <TableHead>Joined</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.user_id}>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <IconComponent
                              name="User"
                              className="h-4 w-4 text-muted-foreground"
                            />
                            <div>
                              <p className="font-medium">{user.username}</p>
                              {user.email && (
                                <p className="text-xs text-muted-foreground">
                                  {user.email}
                                </p>
                              )}
                            </div>
                            {user.is_owner && (
                              <Badge variant="outline" className="text-xs">
                                Owner
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {user.roles.map((role) => (
                              <Badge
                                key={role}
                                variant="secondary"
                                className="text-xs"
                              >
                                {role}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell>
                          {new Date(user.joined_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={user.is_active ? "default" : "secondary"}
                          >
                            {user.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="projects" className="space-y-4">
          <div className="space-y-2">
            <h3 className="font-medium">Projects</h3>
            {isLoadingProjects ? (
              <LoadingComponent />
            ) : (
              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Project</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {projects.map((project) => (
                      <TableRow key={project.id}>
                        <TableCell>
                          <div className="flex items-center space-x-2">
                            <IconComponent
                              name="FolderOpen"
                              className="h-4 w-4 text-muted-foreground"
                            />
                            <span className="font-medium">{project.name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {project.description || "No description"}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              project.is_active ? "default" : "secondary"
                            }
                          >
                            {project.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {new Date(project.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

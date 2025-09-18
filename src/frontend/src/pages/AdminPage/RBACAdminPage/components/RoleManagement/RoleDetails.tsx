import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Role, Workspace } from "@/controllers/API/queries/rbac";

interface RoleDetailsProps {
  role: Role;
  workspace?: Workspace;
  onClose: () => void;
}

export default function RoleDetails({ role, workspace }: RoleDetailsProps) {
  return (
    <div className="space-y-6">
      {/* Role Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <IconComponent
              name={role.is_system_role ? "Shield" : "Users"}
              className="h-6 w-6"
            />
            <h2 className="text-xl font-semibold">{role.name}</h2>
            <div className="flex items-center space-x-2">
              <Badge variant={role.is_system_role ? "default" : "secondary"}>
                {role.is_system_role ? "System" : "Custom"}
              </Badge>
              <Badge variant={role.is_active ? "default" : "secondary"}>
                {role.is_active ? "Active" : "Inactive"}
              </Badge>
            </div>
          </div>
          {role.description && (
            <p className="text-muted-foreground">{role.description}</p>
          )}
        </div>
      </div>

      {/* Role Info */}
      <div className="grid grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="font-medium text-sm uppercase tracking-wide">
            Role Information
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">ID:</span>
              <span className="text-sm font-mono">{role.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Workspace:</span>
              <span className="text-sm">
                {workspace ? (
                  <div className="flex items-center space-x-1">
                    <IconComponent name="Building2" className="h-3 w-3" />
                    <span>{workspace.name}</span>
                  </div>
                ) : (
                  <Badge variant="outline">System-wide</Badge>
                )}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">Created:</span>
              <span className="text-sm">
                {new Date(role.created_at).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">
                Last Updated:
              </span>
              <span className="text-sm">
                {new Date(role.updated_at).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">
                Assignments:
              </span>
              <span className="text-sm font-medium">
                {role.assignment_count || 0}
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-medium text-sm uppercase tracking-wide">
            Permissions ({role.permissions.length})
          </h3>
          <ScrollArea className="h-64">
            <div className="space-y-2">
              {role.permissions.map((permission) => (
                <div
                  key={permission}
                  className="flex items-center justify-between p-2 rounded-md bg-muted/50"
                >
                  <span className="text-sm font-medium">{permission}</span>
                  <div className="flex items-center space-x-1">
                    <IconComponent
                      name="Key"
                      className="h-3 w-3 text-muted-foreground"
                    />
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* System Role Warning */}
      {role.is_system_role && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20">
          <div className="flex items-center space-x-2">
            <IconComponent
              name="AlertTriangle"
              className="h-4 w-4 text-amber-600"
            />
            <p className="text-sm text-amber-800 dark:text-amber-200">
              <strong>System Role:</strong> This is a built-in system role that
              cannot be modified or deleted. System roles are automatically
              managed by LangBuilder.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

import IconComponent from "@/components/common/genericIconComponent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  type Role,
  type RoleAssignment,
  type Workspace,
} from "@/controllers/API/queries/rbac";

interface RoleAssignmentDetailsProps {
  assignment: RoleAssignment;
  workspace?: Workspace;
  role?: Role;
  onClose: () => void;
}

export default function RoleAssignmentDetails({
  assignment,
  workspace,
  role,
  onClose,
}: RoleAssignmentDetailsProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getScopeIcon = (scopeType: string) => {
    switch (scopeType) {
      case "global":
        return "Globe";
      case "workspace":
        return "Building";
      case "project":
        return "Folder";
      case "environment":
        return "Server";
      default:
        return "Circle";
    }
  };

  const getPrincipalIcon = (principalType: string) => {
    return principalType === "user" ? "User" : "Bot";
  };

  const getStatusColor = (isActive: boolean, expiresAt?: string) => {
    if (!isActive) return "secondary";
    if (expiresAt && new Date(expiresAt) < new Date()) return "destructive";
    return "default";
  };

  const getStatusText = (isActive: boolean, expiresAt?: string) => {
    if (!isActive) return "Inactive";
    if (expiresAt && new Date(expiresAt) < new Date()) return "Expired";
    return "Active";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <IconComponent
              name={getPrincipalIcon(assignment.principal_type)}
              className="h-5 w-5 text-muted-foreground"
            />
            <h3 className="text-lg font-semibold">
              {assignment.principal_name}
            </h3>
          </div>
          <IconComponent
            name="ArrowRight"
            className="h-4 w-4 text-muted-foreground"
          />
          <div className="flex items-center space-x-2">
            <IconComponent
              name="Shield"
              className="h-5 w-5 text-muted-foreground"
            />
            <span className="text-lg font-semibold">
              {assignment.role_name}
            </span>
          </div>
        </div>
        <Badge
          variant={getStatusColor(assignment.is_active, assignment.expires_at)}
          className="text-sm"
        >
          {getStatusText(assignment.is_active, assignment.expires_at)}
        </Badge>
      </div>

      <Separator />

      {/* Assignment Details */}
      <div className="grid grid-cols-2 gap-6">
        {/* Principal Information */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Principal Information
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Type:</span>
              <div className="flex items-center space-x-2">
                <IconComponent
                  name={getPrincipalIcon(assignment.principal_type)}
                  className="h-4 w-4"
                />
                <span className="text-sm font-medium capitalize">
                  {assignment.principal_type.replace("_", " ")}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Name:</span>
              <span className="text-sm font-medium">
                {assignment.principal_name}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">ID:</span>
              <code className="text-xs bg-muted px-2 py-1 rounded">
                {assignment.principal_id}
              </code>
            </div>
          </div>
        </div>

        {/* Role Information */}
        <div className="space-y-4">
          <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Role Information
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Role:</span>
              <span className="text-sm font-medium">
                {assignment.role_name}
              </span>
            </div>
            {role?.description && (
              <div className="flex flex-col space-y-1">
                <span className="text-sm text-muted-foreground">
                  Description:
                </span>
                <span className="text-sm">{role.description}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Role ID:</span>
              <code className="text-xs bg-muted px-2 py-1 rounded">
                {assignment.role_id}
              </code>
            </div>
          </div>
        </div>
      </div>

      <Separator />

      {/* Scope Information */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Scope Information
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Scope Type:</span>
            <div className="flex items-center space-x-2">
              <IconComponent
                name={getScopeIcon(assignment.scope_type)}
                className="h-4 w-4"
              />
              <Badge variant="outline" className="text-xs">
                {assignment.scope_type}
              </Badge>
            </div>
          </div>
          {assignment.scope_name && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Scope Name:</span>
              <span className="text-sm font-medium">
                {assignment.scope_name}
              </span>
            </div>
          )}
          {assignment.scope_id && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Scope ID:</span>
              <code className="text-xs bg-muted px-2 py-1 rounded">
                {assignment.scope_id}
              </code>
            </div>
          )}
        </div>
      </div>

      <Separator />

      {/* Assignment Metadata */}
      <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Assignment Metadata
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Granted By:</span>
            <span className="text-sm font-medium">
              {assignment.granted_by_name}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Granted At:</span>
            <span className="text-sm font-medium">
              {formatDate(assignment.granted_at)}
            </span>
          </div>
          {assignment.expires_at && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Expires At:</span>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">
                  {formatDate(assignment.expires_at)}
                </span>
                {new Date(assignment.expires_at) < new Date() && (
                  <IconComponent
                    name="AlertTriangle"
                    className="h-4 w-4 text-destructive"
                  />
                )}
              </div>
            </div>
          )}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Status:</span>
            <Badge
              variant={getStatusColor(
                assignment.is_active,
                assignment.expires_at,
              )}
            >
              {getStatusText(assignment.is_active, assignment.expires_at)}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Assignment ID:
            </span>
            <code className="text-xs bg-muted px-2 py-1 rounded">
              {assignment.id}
            </code>
          </div>
        </div>
      </div>

      {/* Permissions Summary */}
      {role?.permissions && role.permissions.length > 0 && (
        <>
          <Separator />
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Granted Permissions
            </h4>
            <div className="flex flex-wrap gap-2">
              {role.permissions.map((permission, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  <IconComponent name="Key" className="mr-1 h-3 w-3" />
                  {permission}
                </Badge>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
      </div>
    </div>
  );
}

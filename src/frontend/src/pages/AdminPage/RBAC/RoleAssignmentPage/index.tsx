import IconComponent from "../../../../components/common/genericIconComponent";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../../components/ui/card";

export default function RoleAssignmentPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <IconComponent name="Users" className="w-6 h-6" />
        <h2 className="text-2xl font-bold">Role Assignments</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Manage Role Assignments</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Assign roles to users and service accounts across different scopes.
          </p>
          <div className="mt-4 p-4 border rounded-lg bg-muted">
            <p className="text-sm">
              🚧 Role Assignment interface is under development. This will
              include user and service account role management with hierarchical
              scoping.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

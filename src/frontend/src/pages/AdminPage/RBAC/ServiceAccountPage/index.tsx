import IconComponent from "../../../../components/common/genericIconComponent";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";

export default function ServiceAccountPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <IconComponent name="Bot" className="w-6 h-6" />
        <h2 className="text-2xl font-bold">Service Accounts</h2>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Manage Service Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Create and manage service accounts for automated systems and integrations.
          </p>
          <div className="mt-4 p-4 border rounded-lg bg-muted">
            <p className="text-sm">
              🚧 Service Account management interface is under development.
              This will include token generation, scoping, and automated access management.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
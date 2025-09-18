import IconComponent from "../../../../components/common/genericIconComponent";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../../../components/ui/card";

export default function AuditLogsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <IconComponent name="FileText" className="w-6 h-6" />
        <h2 className="text-2xl font-bold">Audit Logs</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Security Audit Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            View and analyze security events, permission changes, and user
            activities.
          </p>
          <div className="mt-4 p-4 border rounded-lg bg-muted">
            <p className="text-sm">
              🚧 Audit Logs interface is under development. This will include
              searchable logs, filtering, and export capabilities.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

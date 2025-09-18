import IconComponent from "../../../../components/common/genericIconComponent";
import { Card, CardContent, CardHeader, CardTitle } from "../../../../components/ui/card";

export default function ComplianceReportsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <IconComponent name="CheckCircle" className="w-6 h-6" />
        <h2 className="text-2xl font-bold">Compliance Reports</h2>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Generate Compliance Reports</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Generate and export compliance reports for SOC2, ISO27001, GDPR, and CCPA standards.
          </p>
          <div className="mt-4 p-4 border rounded-lg bg-muted">
            <p className="text-sm">
              🚧 Compliance Reports interface is under development.
              This will include report generation for multiple compliance standards and export options.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
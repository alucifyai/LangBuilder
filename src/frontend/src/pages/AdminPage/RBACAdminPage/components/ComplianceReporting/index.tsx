import { useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import { DatePickerWithRange } from "@/components/ui/date-range-picker";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function ComplianceReporting() {
  const [reportType, setReportType] = useState("");
  const [dateRange, setDateRange] = useState({
    from: new Date(new Date().setDate(new Date().getDate() - 30)),
    to: new Date(),
  });

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between p-6 border-b">
        <div className="flex items-center space-x-4">
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select Report Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user-access">User Access Report</SelectItem>
              <SelectItem value="role-assignments">Role Assignments</SelectItem>
              <SelectItem value="audit-logs">Audit Logs</SelectItem>
              <SelectItem value="permission-matrix">
                Permission Matrix
              </SelectItem>
            </SelectContent>
          </Select>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Date Range:</span>
            <DatePickerWithRange
              date={dateRange}
              onDateChange={(range) => range && setDateRange(range)}
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="outline" className="flex items-center space-x-2">
            <IconComponent name="Download" className="h-4 w-4" />
            <span>Export CSV</span>
          </Button>
          <Button className="flex items-center space-x-2">
            <IconComponent name="FileText" className="h-4 w-4" />
            <span>Generate Report</span>
          </Button>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className="text-center space-y-4">
          <IconComponent
            name="FileText"
            className="h-16 w-16 text-muted-foreground mx-auto"
          />
          <div>
            <h3 className="text-lg font-semibold">
              Compliance & Audit Reporting
            </h3>
            <p className="text-muted-foreground">
              Generate compliance reports and audit trails for governance
              requirements
            </p>
          </div>
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>• User access and permission reports</p>
            <p>• Audit trail exports with immutable logs</p>
            <p>• SOC 2 / ISO 27001 compliance reports</p>
            <p>• Role assignment history tracking</p>
          </div>
        </div>
      </div>
    </div>
  );
}

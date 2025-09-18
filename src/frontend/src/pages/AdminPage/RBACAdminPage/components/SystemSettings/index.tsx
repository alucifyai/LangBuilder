import { useState } from "react";
import IconComponent from "@/components/common/genericIconComponent";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";

export default function SystemSettings() {
  const [ssoEnabled, setSsoEnabled] = useState(false);
  const [scimEnabled, setScimEnabled] = useState(false);
  const [auditRetention, setAuditRetention] = useState("365");
  const [sessionTimeout, setSessionTimeout] = useState("1440");

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between p-6 border-b">
        <div>
          <h2 className="text-lg font-semibold">System Settings</h2>
          <p className="text-sm text-muted-foreground">
            Configure RBAC system-wide settings and integrations
          </p>
        </div>
        <Button className="flex items-center space-x-2">
          <IconComponent name="Save" className="h-4 w-4" />
          <span>Save Changes</span>
        </Button>
      </div>

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Authentication Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <IconComponent name="Key" className="h-5 w-5" />
              <span>Authentication</span>
            </CardTitle>
            <CardDescription>
              Configure authentication methods and session settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Single Sign-On (SSO)</Label>
                <p className="text-sm text-muted-foreground">
                  Enable OIDC/SAML SSO integration
                </p>
              </div>
              <Switch checked={ssoEnabled} onCheckedChange={setSsoEnabled} />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="session-timeout">Session Timeout (minutes)</Label>
              <Input
                id="session-timeout"
                value={sessionTimeout}
                onChange={(e) => setSessionTimeout(e.target.value)}
                className="w-32"
              />
              <p className="text-xs text-muted-foreground">
                Default session timeout for all users
              </p>
            </div>
          </CardContent>
        </Card>

        {/* User Provisioning */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <IconComponent name="Users" className="h-5 w-5" />
              <span>User Provisioning</span>
            </CardTitle>
            <CardDescription>
              Automated user and group synchronization settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>SCIM Provisioning</Label>
                <p className="text-sm text-muted-foreground">
                  Enable SCIM 2.0 user and group synchronization
                </p>
              </div>
              <Switch checked={scimEnabled} onCheckedChange={setScimEnabled} />
            </div>
          </CardContent>
        </Card>

        {/* Audit & Compliance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <IconComponent name="FileText" className="h-5 w-5" />
              <span>Audit & Compliance</span>
            </CardTitle>
            <CardDescription>
              Configure audit logging and compliance settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="audit-retention">Audit Log Retention (days)</Label>
              <Input
                id="audit-retention"
                value={auditRetention}
                onChange={(e) => setAuditRetention(e.target.value)}
                className="w-32"
              />
              <p className="text-xs text-muted-foreground">
                How long to retain audit logs (minimum 90 days for compliance)
              </p>
            </div>

            <Separator />

            <div className="space-y-4">
              <Label>System Initialization</Label>
              <div className="flex items-center space-x-4">
                <Button variant="outline" className="flex items-center space-x-2">
                  <IconComponent name="RefreshCw" className="h-4 w-4" />
                  <span>Initialize System Roles</span>
                </Button>
                <Button variant="outline" className="flex items-center space-x-2">
                  <IconComponent name="Database" className="h-4 w-4" />
                  <span>Initialize Permissions</span>
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Reset and initialize system roles and permissions to defaults
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Performance Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <IconComponent name="Zap" className="h-5 w-5" />
              <span>Performance</span>
            </CardTitle>
            <CardDescription>
              Permission caching and performance optimization
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm font-medium">Permission Cache TTL</p>
                <p className="text-2xl font-bold">5 minutes</p>
                <p className="text-xs text-muted-foreground">Cache duration for permissions</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium">Average Response Time</p>
                <p className="text-2xl font-bold text-green-600">< 50ms</p>
                <p className="text-xs text-muted-foreground">Permission check latency</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
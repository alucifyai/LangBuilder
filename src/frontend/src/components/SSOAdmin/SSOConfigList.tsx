/**
 * SSO Configuration List Component
 *
 * Displays list of SSO configurations with management actions
 */

import { useState } from "react";
import { Button } from "../ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { Badge } from "../ui/badge";
import type { SSOConfigResponse } from "../../types/sso";
import { SSOEnforcement, SSOProvider } from "../../types/sso";
import CreateSSOConfigModal from "./CreateSSOConfigModal";
import EditSSOConfigModal from "./EditSSOConfigModal";
import DeleteSSOConfigDialog from "./DeleteSSOConfigDialog";

interface SSOConfigListProps {
  configs: SSOConfigResponse[];
  onConfigCreated: () => void;
  onConfigUpdated: () => void;
  onConfigDeleted: () => void;
}

export default function SSOConfigList({
  configs,
  onConfigCreated,
  onConfigUpdated,
  onConfigDeleted,
}: SSOConfigListProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SSOConfigResponse | null>(
    null
  );
  const [deletingConfig, setDeletingConfig] =
    useState<SSOConfigResponse | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">SSO Configurations</h2>
          <p className="text-sm text-muted-foreground">
            Manage Single Sign-On authentication providers
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Add SSO Configuration
        </Button>
      </div>

      {configs.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <h3 className="text-lg font-semibold">No SSO configurations</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Get started by adding your first SSO provider
          </p>
          <Button
            className="mt-4"
            variant="outline"
            onClick={() => setShowCreateModal(true)}
          >
            Add SSO Configuration
          </Button>
        </div>
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Domain</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Enforcement</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Organization</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {configs.map((config) => (
                <TableRow key={config.id}>
                  <TableCell className="font-medium">{config.domain}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {config.provider_type === SSOProvider.OIDC
                        ? "OIDC"
                        : "SAML"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <EnforcementBadge enforcement={config.enforcement} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge enabled={config.enabled} />
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {config.organization_id}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditingConfig(config)}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeletingConfig(config)}
                      >
                        Delete
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {showCreateModal && (
        <CreateSSOConfigModal
          open={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            onConfigCreated();
          }}
        />
      )}

      {editingConfig && (
        <EditSSOConfigModal
          config={editingConfig}
          open={!!editingConfig}
          onClose={() => setEditingConfig(null)}
          onSuccess={() => {
            setEditingConfig(null);
            onConfigUpdated();
          }}
        />
      )}

      {deletingConfig && (
        <DeleteSSOConfigDialog
          config={deletingConfig}
          open={!!deletingConfig}
          onClose={() => setDeletingConfig(null)}
          onSuccess={() => {
            setDeletingConfig(null);
            onConfigDeleted();
          }}
        />
      )}
    </div>
  );
}

function EnforcementBadge({ enforcement }: { enforcement: SSOEnforcement }) {
  const variants: Record<
    SSOEnforcement,
    { label: string; className: string }
  > = {
    [SSOEnforcement.DISABLED]: {
      label: "Disabled",
      className: "bg-gray-100 text-gray-800",
    },
    [SSOEnforcement.OPTIONAL]: {
      label: "Optional",
      className: "bg-blue-100 text-blue-800",
    },
    [SSOEnforcement.ENFORCED]: {
      label: "Enforced",
      className: "bg-green-100 text-green-800",
    },
  };

  const { label, className } = variants[enforcement];

  return <Badge className={className}>{label}</Badge>;
}

function StatusBadge({ enabled }: { enabled: boolean }) {
  return (
    <Badge className={enabled ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
      {enabled ? "Enabled" : "Disabled"}
    </Badge>
  );
}

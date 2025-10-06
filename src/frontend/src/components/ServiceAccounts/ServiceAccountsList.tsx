/**
 * Service Accounts List Component
 */

import { useState } from "react";
import { Button } from "../ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/table";
import { Badge } from "../ui/badge";
import type { ServiceAccountResponse } from "../../types/service-accounts";
import CreateServiceAccountModal from "./CreateServiceAccountModal";
import ServiceAccountTokensModal from "./ServiceAccountTokensModal";

interface ServiceAccountsListProps {
  accounts: ServiceAccountResponse[];
  onAccountCreated: () => void;
  onAccountDeleted: () => void;
}

export default function ServiceAccountsList({
  accounts,
  onAccountCreated,
  onAccountDeleted,
}: ServiceAccountsListProps) {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<ServiceAccountResponse | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Service Accounts</h2>
          <p className="text-sm text-muted-foreground">
            Manage API access for automated systems
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Create Service Account
        </Button>
      </div>

      {accounts.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <h3 className="text-lg font-semibold">No service accounts</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Create a service account to generate API tokens
          </p>
          <Button className="mt-4" variant="outline" onClick={() => setShowCreateModal(true)}>
            Create Service Account
          </Button>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Description</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Used</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((account) => (
              <TableRow key={account.id}>
                <TableCell className="font-medium">{account.name}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {account.description || "-"}
                </TableCell>
                <TableCell>
                  <Badge className={account.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}>
                    {account.is_active ? "Active" : "Inactive"}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {account.last_used_at
                    ? new Date(account.last_used_at).toLocaleDateString()
                    : "Never"}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedAccount(account)}
                  >
                    Manage Tokens
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {showCreateModal && (
        <CreateServiceAccountModal
          open={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            onAccountCreated();
          }}
        />
      )}

      {selectedAccount && (
        <ServiceAccountTokensModal
          account={selectedAccount}
          open={!!selectedAccount}
          onClose={() => setSelectedAccount(null)}
        />
      )}
    </div>
  );
}

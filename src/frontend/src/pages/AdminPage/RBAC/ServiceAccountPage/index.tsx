import { cloneDeep } from "lodash";
import { useContext, useEffect, useRef, useState } from "react";
import PaginatorComponent from "@/components/common/paginatorComponent";
import {
  useCreateServiceAccount,
  useDeleteServiceAccount,
  useGetServiceAccounts,
  useUpdateServiceAccount,
  useCreateServiceAccountToken,
  useGetServiceAccountTokens,
  useDeleteServiceAccountToken,
} from "@/controllers/API/queries/rbac/use-service-accounts";
import { useGetWorkspaces } from "@/controllers/API/queries/rbac";
import type { ServiceAccount, ServiceAccountToken } from "@/controllers/API/queries/rbac/use-service-accounts";
import CustomLoader from "@/customization/components/custom-loader";
import IconComponent from "../../../../components/common/genericIconComponent";
import ShadTooltip from "../../../../components/common/shadTooltipComponent";
import { Button } from "../../../../components/ui/button";
import { CheckBoxDiv } from "../../../../components/ui/checkbox";
import { Input } from "../../../../components/ui/input";
import { Label } from "../../../../components/ui/label";
import { Badge } from "../../../../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../../components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../../../components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../../../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../../../components/ui/tabs";
import {
  PAGINATION_PAGE,
  PAGINATION_ROWS_COUNT,
  PAGINATION_SIZE,
} from "../../../../constants/constants";
import { AuthContext } from "../../../../contexts/authContext";
import ConfirmationModal from "../../../../modals/confirmationModal";
import useAlertStore from "../../../../stores/alertStore";

interface CreateServiceAccountData {
  name: string;
  description: string;
  workspace_id: string;
  service_type: string;
  integration_name: string;
  max_tokens: number;
  token_expiry_days: number;
  allowed_ips: string[];
  allowed_permissions: string[];
}

export default function ServiceAccountPage() {
  const [inputValue, setInputValue] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState("");
  const [size, setPageSize] = useState(PAGINATION_SIZE);
  const [index, setPageIndex] = useState(PAGINATION_PAGE);
  const [totalRowsCount, setTotalRowsCount] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [selectedServiceAccount, setSelectedServiceAccount] = useState<ServiceAccount | null>(null);
  const [tokens, setTokens] = useState<ServiceAccountToken[]>([]);
  const [newTokenData, setNewTokenData] = useState({ name: "", expires_in_days: 365 });

  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const { userData } = useContext(AuthContext);

  const serviceAccountList = useRef<ServiceAccount[]>([]);
  const workspaceList = useRef<any[]>([]);

  const [filterServiceAccountList, setFilterServiceAccountList] = useState(
    serviceAccountList.current,
  );

  // API hooks
  const { mutate: mutateGetServiceAccounts, isPending, isIdle } = useGetServiceAccounts({});
  const { mutate: mutateCreateServiceAccount } = useCreateServiceAccount();
  const { mutate: mutateUpdateServiceAccount } = useUpdateServiceAccount();
  const { mutate: mutateDeleteServiceAccount } = useDeleteServiceAccount();
  const { mutate: mutateGetWorkspaces } = useGetWorkspaces({});
  const { mutate: mutateCreateToken } = useCreateServiceAccountToken();
  const { mutate: mutateGetTokens } = useGetServiceAccountTokens({});
  const { mutate: mutateDeleteToken } = useDeleteServiceAccountToken();

  // Form state
  const [createForm, setCreateForm] = useState<CreateServiceAccountData>({
    name: "",
    description: "",
    workspace_id: "",
    service_type: "api",
    integration_name: "",
    max_tokens: 5,
    token_expiry_days: 365,
    allowed_ips: [],
    allowed_permissions: [],
  });

  useEffect(() => {
    getWorkspaces();
  }, []);

  useEffect(() => {
    if (workspaceList.current.length > 0 && !selectedWorkspace) {
      setSelectedWorkspace(workspaceList.current[0].id);
    }
  }, [workspaceList.current]);

  useEffect(() => {
    if (selectedWorkspace) {
      getServiceAccounts();
    }
  }, [selectedWorkspace]);

  function getWorkspaces() {
    mutateGetWorkspaces(
      { skip: 0, limit: 1000 },
      {
        onSuccess: (data) => {
          workspaceList.current = data.workspaces;
          if (data.workspaces.length > 0 && !selectedWorkspace) {
            setSelectedWorkspace(data.workspaces[0].id);
          }
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load workspaces",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function getServiceAccounts() {
    if (!selectedWorkspace) return;

    mutateGetServiceAccounts(
      {
        workspace_id: selectedWorkspace,
        page: index,
        page_size: size,
        search: inputValue || undefined,
      },
      {
        onSuccess: (data) => {
          setTotalRowsCount(data.total_count);
          serviceAccountList.current = data.service_accounts;
          setFilterServiceAccountList(data.service_accounts);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load service accounts",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleCreateServiceAccount() {
    if (!createForm.name.trim() || !createForm.workspace_id) return;

    mutateCreateServiceAccount(
      {
        ...createForm,
        workspace_id: createForm.workspace_id || selectedWorkspace,
      },
      {
        onSuccess: () => {
          setShowCreateModal(false);
          resetCreateForm();
          getServiceAccounts();
          setSuccessData({ title: "Service account created successfully" });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to create service account",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleToggleActive(serviceAccount: ServiceAccount) {
    mutateUpdateServiceAccount(
      {
        service_account_id: serviceAccount.id,
        data: { is_active: !serviceAccount.is_active },
      },
      {
        onSuccess: () => {
          getServiceAccounts();
          setSuccessData({
            title: `Service account ${serviceAccount.is_active ? 'deactivated' : 'activated'} successfully`
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update service account",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleDeleteServiceAccount(serviceAccount: ServiceAccount) {
    mutateDeleteServiceAccount(
      { service_account_id: serviceAccount.id },
      {
        onSuccess: () => {
          getServiceAccounts();
          setSuccessData({ title: "Service account deleted successfully" });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete service account",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleManageTokens(serviceAccount: ServiceAccount) {
    setSelectedServiceAccount(serviceAccount);
    setShowTokenModal(true);

    mutateGetTokens(
      { service_account_id: serviceAccount.id },
      {
        onSuccess: (data) => {
          setTokens(data);
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to load tokens",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleCreateToken() {
    if (!selectedServiceAccount || !newTokenData.name.trim()) return;

    mutateCreateToken(
      {
        service_account_id: selectedServiceAccount.id,
        name: newTokenData.name,
        expires_at: newTokenData.expires_in_days > 0
          ? new Date(Date.now() + newTokenData.expires_in_days * 24 * 60 * 60 * 1000).toISOString()
          : undefined,
      },
      {
        onSuccess: (data) => {
          setNewTokenData({ name: "", expires_in_days: 365 });
          // Show the token to user (only time it's visible)
          setSuccessData({
            title: "Token created successfully",
            list: [`Token: ${data.token}`, "Save this token - it won't be shown again!"],
          });
          // Refresh tokens list
          mutateGetTokens(
            { service_account_id: selectedServiceAccount.id },
            {
              onSuccess: (data) => setTokens(data),
            },
          );
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to create token",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleDeleteToken(tokenId: string) {
    if (!selectedServiceAccount) return;

    mutateDeleteToken(
      {
        service_account_id: selectedServiceAccount.id,
        token_id: tokenId,
      },
      {
        onSuccess: () => {
          setSuccessData({ title: "Token deleted successfully" });
          // Refresh tokens list
          mutateGetTokens(
            { service_account_id: selectedServiceAccount.id },
            {
              onSuccess: (data) => setTokens(data),
            },
          );
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete token",
            list: [error.message || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function resetCreateForm() {
    setCreateForm({
      name: "",
      description: "",
      workspace_id: selectedWorkspace,
      service_type: "api",
      integration_name: "",
      max_tokens: 5,
      token_expiry_days: 365,
      allowed_ips: [],
      allowed_permissions: [],
    });
  }

  function handleChangePagination(pageIndex: number, pageSize: number) {
    setPageSize(pageSize);
    setPageIndex(pageIndex);
  }

  const handleFilterChange = (value: string) => {
    setInputValue(value);
    // Debounce the API call or trigger search
    setTimeout(() => {
      getServiceAccounts();
    }, 300);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <IconComponent name="Bot" className="w-6 h-6" />
          <h2 className="text-2xl font-bold">Service Accounts</h2>
        </div>
      </div>

      {/* Workspace Selection */}
      <div className="flex items-center gap-4">
        <Label htmlFor="workspace-select" className="text-sm font-medium">
          Workspace:
        </Label>
        <Select value={selectedWorkspace} onValueChange={setSelectedWorkspace}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select workspace" />
          </SelectTrigger>
          <SelectContent>
            {workspaceList.current.map((workspace) => (
              <SelectItem key={workspace.id} value={workspace.id}>
                {workspace.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Controls */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Input
            placeholder="Search service accounts..."
            value={inputValue}
            onChange={(e) => handleFilterChange(e.target.value)}
            className="w-64"
          />
        </div>

        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogTrigger asChild>
            <Button onClick={resetCreateForm}>
              <IconComponent name="Plus" className="w-4 h-4 mr-2" />
              Create Service Account
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Create Service Account</DialogTitle>
              <DialogDescription>
                Create a new service account for automated system access.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="e.g., ci-bot, monitoring-service"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Brief description of purpose"
                />
              </div>
              <div>
                <Label htmlFor="service-type">Service Type</Label>
                <Select
                  value={createForm.service_type}
                  onValueChange={(value) => setCreateForm({ ...createForm, service_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="api">API</SelectItem>
                    <SelectItem value="webhook">Webhook</SelectItem>
                    <SelectItem value="integration">Integration</SelectItem>
                    <SelectItem value="bot">Bot</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="max-tokens">Max Tokens</Label>
                <Input
                  id="max-tokens"
                  type="number"
                  min="1"
                  max="10"
                  value={createForm.max_tokens}
                  onChange={(e) => setCreateForm({ ...createForm, max_tokens: parseInt(e.target.value) || 5 })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleCreateServiceAccount}
                disabled={!createForm.name.trim()}
              >
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Service Accounts Table */}
      {isPending || isIdle ? (
        <div className="flex h-64 w-full items-center justify-center">
          <CustomLoader remSize={12} />
        </div>
      ) : serviceAccountList.current.length === 0 && !isIdle ? (
        <div className="text-center py-12">
          <IconComponent name="Bot" className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-medium mb-2">No service accounts found</h3>
          <p className="text-muted-foreground mb-4">
            Create your first service account to get started with automated access.
          </p>
        </div>
      ) : (
        <>
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Tokens</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filterServiceAccountList.map((serviceAccount) => (
                  <TableRow key={serviceAccount.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{serviceAccount.name}</div>
                        {serviceAccount.description && (
                          <div className="text-sm text-muted-foreground">
                            {serviceAccount.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {serviceAccount.service_type || "api"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <ConfirmationModal
                        size="x-small"
                        title="Toggle Status"
                        titleHeader={`${serviceAccount.name}`}
                        modalContentTitle="Confirm Status Change"
                        cancelText="Cancel"
                        confirmationText="Confirm"
                        icon="UserCog2"
                        data={serviceAccount}
                        onConfirm={() => handleToggleActive(serviceAccount)}
                      >
                        <ConfirmationModal.Content>
                          <span>
                            Are you sure you want to {serviceAccount.is_active ? 'deactivate' : 'activate'} this service account?
                          </span>
                        </ConfirmationModal.Content>
                        <ConfirmationModal.Trigger>
                          <div className="flex items-center">
                            <CheckBoxDiv checked={serviceAccount.is_active} />
                            <span className="ml-2">
                              {serviceAccount.is_active ? "Active" : "Inactive"}
                            </span>
                          </div>
                        </ConfirmationModal.Trigger>
                      </ConfirmationModal>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">
                        {serviceAccount.active_token_count || 0} / {serviceAccount.max_tokens}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {serviceAccount.last_used_at
                          ? new Date(serviceAccount.last_used_at).toLocaleDateString()
                          : "Never"
                        }
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {new Date(serviceAccount.created_at).toLocaleDateString()}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <ShadTooltip content="Manage tokens">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleManageTokens(serviceAccount)}
                          >
                            <IconComponent name="Key" className="h-4 w-4" />
                          </Button>
                        </ShadTooltip>

                        <ConfirmationModal
                          size="small"
                          title="Delete Service Account"
                          titleHeader="Confirm Deletion"
                          modalContentTitle="This action cannot be undone"
                          cancelText="Cancel"
                          confirmationText="Delete"
                          icon="Trash2"
                          data={serviceAccount}
                          onConfirm={() => handleDeleteServiceAccount(serviceAccount)}
                        >
                          <ConfirmationModal.Content>
                            <span>
                              Are you sure you want to delete "{serviceAccount.name}"?
                              This will also delete all associated tokens and cannot be undone.
                            </span>
                          </ConfirmationModal.Content>
                          <ConfirmationModal.Trigger>
                            <ShadTooltip content="Delete service account">
                              <Button variant="ghost" size="sm">
                                <IconComponent name="Trash2" className="h-4 w-4" />
                              </Button>
                            </ShadTooltip>
                          </ConfirmationModal.Trigger>
                        </ConfirmationModal>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <PaginatorComponent
            pageIndex={index}
            pageSize={size}
            totalRowsCount={totalRowsCount}
            paginate={handleChangePagination}
            rowsCount={PAGINATION_ROWS_COUNT}
          />
        </>
      )}

      {/* Token Management Modal */}
      <Dialog open={showTokenModal} onOpenChange={setShowTokenModal}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              Manage Tokens - {selectedServiceAccount?.name}
            </DialogTitle>
            <DialogDescription>
              Create and manage API tokens for this service account.
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="tokens" className="w-full">
            <TabsList>
              <TabsTrigger value="tokens">Active Tokens</TabsTrigger>
              <TabsTrigger value="create">Create Token</TabsTrigger>
            </TabsList>

            <TabsContent value="tokens" className="space-y-4">
              {tokens.length === 0 ? (
                <div className="text-center py-8">
                  <IconComponent name="Key" className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">No tokens created yet</p>
                </div>
              ) : (
                <div className="border rounded-md">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Prefix</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Last Used</TableHead>
                        <TableHead>Expires</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {tokens.map((token) => (
                        <TableRow key={token.id}>
                          <TableCell className="font-medium">{token.name}</TableCell>
                          <TableCell>
                            <code className="text-sm bg-muted px-2 py-1 rounded">
                              {token.token_prefix}...
                            </code>
                          </TableCell>
                          <TableCell>
                            <Badge variant={token.is_active ? "default" : "secondary"}>
                              {token.is_active ? "Active" : "Inactive"}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-muted-foreground">
                              {token.last_used_at
                                ? new Date(token.last_used_at).toLocaleDateString()
                                : "Never"
                              }
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-muted-foreground">
                              {token.expires_at
                                ? new Date(token.expires_at).toLocaleDateString()
                                : "Never"
                              }
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <ConfirmationModal
                              size="small"
                              title="Delete Token"
                              titleHeader="Confirm Deletion"
                              modalContentTitle="This action cannot be undone"
                              cancelText="Cancel"
                              confirmationText="Delete"
                              icon="Trash2"
                              data={token}
                              onConfirm={() => handleDeleteToken(token.id)}
                            >
                              <ConfirmationModal.Content>
                                <span>
                                  Are you sure you want to delete token "{token.name}"?
                                  This action cannot be undone.
                                </span>
                              </ConfirmationModal.Content>
                              <ConfirmationModal.Trigger>
                                <Button variant="ghost" size="sm">
                                  <IconComponent name="Trash2" className="h-4 w-4" />
                                </Button>
                              </ConfirmationModal.Trigger>
                            </ConfirmationModal>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </TabsContent>

            <TabsContent value="create" className="space-y-4">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="token-name">Token Name *</Label>
                  <Input
                    id="token-name"
                    value={newTokenData.name}
                    onChange={(e) => setNewTokenData({ ...newTokenData, name: e.target.value })}
                    placeholder="e.g., production-api-key"
                  />
                </div>
                <div>
                  <Label htmlFor="expires-in">Expires in (days)</Label>
                  <Input
                    id="expires-in"
                    type="number"
                    min="1"
                    max="3650"
                    value={newTokenData.expires_in_days}
                    onChange={(e) => setNewTokenData({
                      ...newTokenData,
                      expires_in_days: parseInt(e.target.value) || 365
                    })}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Set to 0 for tokens that never expire (not recommended)
                  </p>
                </div>
                <Button
                  onClick={handleCreateToken}
                  disabled={!newTokenData.name.trim()}
                >
                  <IconComponent name="Key" className="w-4 h-4 mr-2" />
                  Create Token
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </div>
  );
}

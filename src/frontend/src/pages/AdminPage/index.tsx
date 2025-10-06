import { cloneDeep } from "lodash";
import { useContext, useEffect, useRef, useState } from "react";
import PaginatorComponent from "@/components/common/paginatorComponent";
import { RoleListView } from "@/components/RoleManagement/RoleListView";
import { AuditLogView } from "@/components/RoleManagement/AuditLogView";
import { GrantListView } from "@/components/GrantManagement/GrantListView";
import { EnhancedAuditLogView } from "@/components/AuditLogs/EnhancedAuditLogView";
import { SecurityDashboard } from "@/components/AuditLogs/SecurityDashboard";
import { AccessReviewCampaigns } from "@/components/AccessReviews/AccessReviewCampaigns";
import { AnomalyDashboard } from "@/components/AccessReviews/AnomalyDashboard";
import { ComplianceReportsList } from "@/components/Compliance/ComplianceReportsList";
import { GenerateReportModal } from "@/components/Compliance/GenerateReportModal";
import { ComplianceControlsManager } from "@/components/Compliance/ComplianceControlsManager";
import SSOConfigList from "@/components/SSOAdmin/SSOConfigList";
import ServiceAccountsList from "@/components/ServiceAccounts/ServiceAccountsList";
import InvitesList from "@/components/UserInvites/InvitesList";
import { TemporaryGrantsList } from "@/components/TemporaryGrants/TemporaryGrantsList";
import { CreateTemporaryGrantModal } from "@/components/TemporaryGrants/CreateTemporaryGrantModal";
import { getSSOConfigByOrg } from "@/api/sso";
import { listServiceAccounts } from "@/api/service-accounts";
import { listInvites } from "@/api/user-invites";
import { listTemporaryGrants } from "@/api/temporary-grants";
import {
  useAddUser,
  useDeleteUsers,
  useGetUsers,
  useUpdateUser,
} from "@/controllers/API/queries/auth";
import CustomLoader from "@/customization/components/custom-loader";
import IconComponent from "../../components/common/genericIconComponent";
import ShadTooltip from "../../components/common/shadTooltipComponent";
import { Button } from "../../components/ui/button";
import { CheckBoxDiv } from "../../components/ui/checkbox";
import { Input } from "../../components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../components/ui/table";
import {
  USER_ADD_ERROR_ALERT,
  USER_ADD_SUCCESS_ALERT,
  USER_DEL_ERROR_ALERT,
  USER_DEL_SUCCESS_ALERT,
  USER_EDIT_ERROR_ALERT,
  USER_EDIT_SUCCESS_ALERT,
} from "../../constants/alerts_constants";
import {
  ADMIN_HEADER_DESCRIPTION,
  ADMIN_HEADER_TITLE,
  PAGINATION_PAGE,
  PAGINATION_ROWS_COUNT,
  PAGINATION_SIZE,
} from "../../constants/constants";
import { AuthContext } from "../../contexts/authContext";
import ConfirmationModal from "../../modals/confirmationModal";
import UserManagementModal from "../../modals/userManagementModal";
import useAlertStore from "../../stores/alertStore";
import type { Users } from "../../types/api";
import type { UserInputType } from "../../types/components";

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<"users" | "roles" | "grants" | "audit" | "security" | "access-reviews" | "anomalies" | "compliance-reports" | "compliance-controls" | "sso" | "service-accounts" | "invites" | "temporary-grants">("users");
  const [inputValue, setInputValue] = useState("");
  const [ssoConfigs, setSsoConfigs] = useState([]);
  const [ssoLoading, setSsoLoading] = useState(false);
  const [serviceAccounts, setServiceAccounts] = useState([]);
  const [userInvites, setUserInvites] = useState([]);
  const [temporaryGrants, setTemporaryGrants] = useState([]);
  const [isGenerateReportModalOpen, setIsGenerateReportModalOpen] = useState(false);

  const [size, setPageSize] = useState(PAGINATION_SIZE);
  const [index, setPageIndex] = useState(PAGINATION_PAGE);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const { userData } = useContext(AuthContext);
  const [totalRowsCount, setTotalRowsCount] = useState(0);

  const { mutate: mutateDeleteUser } = useDeleteUsers();
  const { mutate: mutateUpdateUser } = useUpdateUser();
  const { mutate: mutateAddUser } = useAddUser();

  const userList = useRef([]);

  useEffect(() => {
    setTimeout(() => {
      getUsers();
    }, 500);
  }, []);

  useEffect(() => {
    if (activeTab === "sso" && userData?.id) {
      loadSSOConfigs(userData.id);
    } else if (activeTab === "service-accounts" && userData?.id) {
      loadServiceAccounts(userData.id);
    } else if (activeTab === "invites") {
      loadInvites();
    } else if (activeTab === "temporary-grants") {
      loadTemporaryGrants();
    }
  }, [activeTab, userData]);

  const [filterUserList, setFilterUserList] = useState(userList.current);

  const { mutate: mutateGetUsers, isPending, isIdle } = useGetUsers({});

  function getUsers() {
    mutateGetUsers(
      {
        skip: size * (index - 1),
        limit: size,
      },
      {
        onSuccess: (users) => {
          setTotalRowsCount(users["total_count"]);
          userList.current = users["users"];
          setFilterUserList(users["users"]);
        },
        onError: () => {},
      },
    );
  }

  async function loadSSOConfigs(orgId: string) {
    setSsoLoading(true);
    try {
      const config = await getSSOConfigByOrg(orgId);
      setSsoConfigs(config ? [config] : []);
    } catch (error) {
      // No SSO config found, that's ok
      setSsoConfigs([]);
    } finally {
      setSsoLoading(false);
    }
  }

  async function loadServiceAccounts(orgId: string) {
    try {
      const accounts = await listServiceAccounts(orgId);
      setServiceAccounts(accounts);
    } catch (error) {
      setServiceAccounts([]);
    }
  }

  async function loadInvites() {
    try {
      const invites = await listInvites();
      setUserInvites(invites);
    } catch (error) {
      setUserInvites([]);
    }
  }

  async function loadTemporaryGrants() {
    try {
      const grants = await listTemporaryGrants(false); // Don't include expired
      setTemporaryGrants(grants);
    } catch (error) {
      setTemporaryGrants([]);
    }
  }

  function handleChangePagination(pageIndex: number, pageSize: number) {
    setPageSize(pageSize);
    setPageIndex(pageIndex);

    mutateGetUsers(
      {
        skip: pageSize * (pageIndex - 1),
        limit: pageSize,
      },
      {
        onSuccess: (users) => {
          setTotalRowsCount(users["total_count"]);
          userList.current = users["users"];
          setFilterUserList(users["users"]);
        },
      },
    );
  }

  function resetFilter() {
    setPageIndex(PAGINATION_PAGE);
    setPageSize(PAGINATION_SIZE);
    getUsers();
  }

  function handleFilterUsers(input: string) {
    setInputValue(input);

    if (input === "") {
      setFilterUserList(userList.current);
    } else {
      const filteredList = userList.current.filter((user: Users) =>
        user.username.toLowerCase().includes(input.toLowerCase()),
      );
      setFilterUserList(filteredList);
    }
  }

  function handleDeleteUser(user) {
    mutateDeleteUser(
      { user_id: user.id },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: USER_DEL_SUCCESS_ALERT,
          });
        },
        onError: (error) => {
          setErrorData({
            title: USER_DEL_ERROR_ALERT,
            list: [error["response"]["data"]["detail"]],
          });
        },
      },
    );
  }

  function handleEditUser(userId, user) {
    mutateUpdateUser(
      { user_id: userId, user: user },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: USER_EDIT_SUCCESS_ALERT,
          });
        },
        onError: (error) => {
          setErrorData({
            title: USER_EDIT_ERROR_ALERT,
            list: [error["response"]["data"]["detail"]],
          });
        },
      },
    );
  }

  function handleDisableUser(check, userId, user) {
    const userEdit = cloneDeep(user);
    userEdit.is_active = !check;

    mutateUpdateUser(
      { user_id: userId, user: userEdit },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: USER_EDIT_SUCCESS_ALERT,
          });
        },
        onError: (error) => {
          setErrorData({
            title: USER_EDIT_ERROR_ALERT,
            list: [error["response"]["data"]["detail"]],
          });
        },
      },
    );
  }

  function handleSuperUserEdit(check, userId, user) {
    const userEdit = cloneDeep(user);
    userEdit.is_superuser = !check;

    mutateUpdateUser(
      { user_id: userId, user: userEdit },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: USER_EDIT_SUCCESS_ALERT,
          });
        },
        onError: (error) => {
          setErrorData({
            title: USER_EDIT_ERROR_ALERT,
            list: [error["response"]["data"]["detail"]],
          });
        },
      },
    );
  }

  function handleNewUser(user: UserInputType) {
    mutateAddUser(user, {
      onSuccess: (res) => {
        mutateUpdateUser(
          {
            user_id: res["id"],
            user: {
              is_active: user.is_active,
              is_superuser: user.is_superuser,
            },
          },
          {
            onSuccess: () => {
              resetFilter();
              setSuccessData({
                title: USER_ADD_SUCCESS_ALERT,
              });
            },
            onError: (error) => {
              setErrorData({
                title: USER_ADD_ERROR_ALERT,
                list: [error["response"]["data"]["detail"]],
              });
            },
          },
        );
      },
      onError: (error) => {
        setErrorData({
          title: USER_ADD_ERROR_ALERT,
          list: [error["response"]["data"]["detail"]],
        });
      },
    });
  }

  return (
    <>
      {userData && (
        <div className="admin-page-panel flex h-full flex-col pb-8">
          <div className="main-page-nav-arrangement">
            <span className="main-page-nav-title">
              <IconComponent name="Shield" className="w-6" />
              {ADMIN_HEADER_TITLE}
            </span>
          </div>
          <span className="admin-page-description-text">
            {ADMIN_HEADER_DESCRIPTION}
          </span>

          {/* Tab Navigation */}
          <div className="flex gap-1 border-b px-4 mt-4">
            <button
              onClick={() => setActiveTab("users")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "users"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Users
            </button>
            <button
              onClick={() => setActiveTab("roles")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "roles"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Roles
            </button>
            <button
              onClick={() => setActiveTab("grants")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "grants"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Grants
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "audit"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Audit Logs
            </button>
            <button
              onClick={() => setActiveTab("security")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "security"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Security
            </button>
            <button
              onClick={() => setActiveTab("access-reviews")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "access-reviews"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Access Reviews
            </button>
            <button
              onClick={() => setActiveTab("anomalies")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "anomalies"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Anomalies
            </button>
            <button
              onClick={() => setActiveTab("compliance-reports")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "compliance-reports"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Compliance Reports
            </button>
            <button
              onClick={() => setActiveTab("compliance-controls")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "compliance-controls"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Controls
            </button>
            <button
              onClick={() => setActiveTab("sso")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "sso"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              SSO
            </button>
            <button
              onClick={() => setActiveTab("service-accounts")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "service-accounts"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Service Accounts
            </button>
            <button
              onClick={() => setActiveTab("invites")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "invites"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Invites
            </button>
            <button
              onClick={() => setActiveTab("temporary-grants")}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === "temporary-grants"
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              Temporary Grants
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === "users" && (
            <>
              <div className="flex w-full justify-between px-4 mt-4">
                <div className="flex w-96 items-center gap-4">
                  <Input
                    placeholder="Search Username"
                    value={inputValue}
                    onChange={(e) => handleFilterUsers(e.target.value)}
                  />
                  {inputValue.length > 0 ? (
                    <div
                      className="cursor-pointer"
                      onClick={() => {
                        setInputValue("");
                        setFilterUserList(userList.current);
                      }}
                    >
                      <IconComponent name="X" className="w-6 text-foreground" />
                    </div>
                  ) : (
                    <div>
                      <IconComponent
                        name="Search"
                        className="w-6 text-foreground"
                      />
                    </div>
                  )}
                </div>
                <div>
                  <UserManagementModal
                    title="New User"
                    titleHeader={"Add a new user"}
                    cancelText="Cancel"
                    confirmationText="Save"
                    icon={"UserPlus2"}
                    onConfirm={(index, user) => {
                      handleNewUser(user);
                    }}
                    asChild
                  >
                    <Button variant="primary">New User</Button>
                  </UserManagementModal>
                </div>
              </div>
              {isPending || isIdle ? (
                <div className="flex h-full w-full items-center justify-center">
                  <CustomLoader remSize={12} />
                </div>
              ) : userList.current.length === 0 && !isIdle ? (
                <>
                  <div className="m-4 flex items-center justify-between text-sm">
                    No users registered.
                  </div>
                </>
              ) : (
                <>
                  <div
                    className={
                      "m-4 h-fit overflow-x-hidden overflow-y-scroll rounded-md border-2 bg-background custom-scroll" +
                      (isPending ? " border-0" : "")
                    }
                  >
                    <Table className={"table-fixed outline-1"}>
                      <TableHeader
                        className={
                          isPending ? "hidden" : "table-fixed bg-muted outline-1"
                        }
                      >
                        <TableRow>
                          <TableHead className="h-10">Id</TableHead>
                          <TableHead className="h-10">Username</TableHead>
                          <TableHead className="h-10">Active</TableHead>
                          <TableHead className="h-10">Superuser</TableHead>
                          <TableHead className="h-10">Created At</TableHead>
                          <TableHead className="h-10">Updated At</TableHead>
                          <TableHead className="h-10 w-[100px] text-right"></TableHead>
                        </TableRow>
                      </TableHeader>
                      {!isPending && (
                        <TableBody>
                          {filterUserList.map((user: UserInputType, index) => (
                            <TableRow key={index}>
                              <TableCell className="truncate py-2 font-medium">
                                <ShadTooltip content={user.id}>
                                  <span className="cursor-default">{user.id}</span>
                                </ShadTooltip>
                              </TableCell>
                              <TableCell className="truncate py-2">
                                <ShadTooltip content={user.username}>
                                  <span className="cursor-default">
                                    {user.username}
                                  </span>
                                </ShadTooltip>
                              </TableCell>
                              <TableCell className="relative left-1 truncate py-2 text-align-last-left">
                                <ConfirmationModal
                                  size="x-small"
                                  title="Edit"
                                  titleHeader={`${user.username}`}
                                  modalContentTitle="Attention!"
                                  cancelText="Cancel"
                                  confirmationText="Confirm"
                                  icon={"UserCog2"}
                                  data={user}
                                  index={index}
                                  onConfirm={(index, user) => {
                                    handleDisableUser(
                                      user.is_active,
                                      user.id,
                                      user,
                                    );
                                  }}
                                >
                                  <ConfirmationModal.Content>
                                    <span>
                                      Are you completely confident about the changes
                                      you are making to this user?
                                    </span>
                                  </ConfirmationModal.Content>
                                  <ConfirmationModal.Trigger>
                                    <div className="flex w-fit">
                                      <CheckBoxDiv checked={user.is_active} />
                                    </div>
                                  </ConfirmationModal.Trigger>
                                </ConfirmationModal>
                              </TableCell>
                              <TableCell className="relative left-1 truncate py-2 text-align-last-left">
                                <ConfirmationModal
                                  size="x-small"
                                  title="Edit"
                                  titleHeader={`${user.username}`}
                                  modalContentTitle="Attention!"
                                  cancelText="Cancel"
                                  confirmationText="Confirm"
                                  icon={"UserCog2"}
                                  data={user}
                                  index={index}
                                  onConfirm={(index, user) => {
                                    handleSuperUserEdit(
                                      user.is_superuser,
                                      user.id,
                                      user,
                                    );
                                  }}
                                >
                                  <ConfirmationModal.Content>
                                    <span>
                                      Are you completely confident about the changes
                                      you are making to this user?
                                    </span>
                                  </ConfirmationModal.Content>
                                  <ConfirmationModal.Trigger>
                                    <div className="flex w-fit">
                                      <CheckBoxDiv checked={user.is_superuser} />
                                    </div>
                                  </ConfirmationModal.Trigger>
                                </ConfirmationModal>
                              </TableCell>
                              <TableCell className="truncate py-2">
                                {
                                  new Date(user.create_at!)
                                    .toISOString()
                                    .split("T")[0]
                                }
                              </TableCell>
                              <TableCell className="truncate py-2">
                                {
                                  new Date(user.updated_at!)
                                    .toISOString()
                                    .split("T")[0]
                                }
                              </TableCell>
                              <TableCell className="flex w-[100px] py-2 text-right">
                                <div className="flex">
                                  <UserManagementModal
                                    title="Edit"
                                    titleHeader={`${user.id}`}
                                    cancelText="Cancel"
                                    confirmationText="Save"
                                    icon={"UserPlus2"}
                                    data={user}
                                    index={index}
                                    onConfirm={(index, editUser) => {
                                      handleEditUser(user.id, editUser);
                                    }}
                                  >
                                    <ShadTooltip content="Edit" side="top">
                                      <IconComponent
                                        name="Pencil"
                                        className="h-4 w-4 cursor-pointer"
                                      />
                                    </ShadTooltip>
                                  </UserManagementModal>

                                  <ConfirmationModal
                                    size="x-small"
                                    title="Delete"
                                    titleHeader="Delete User"
                                    modalContentTitle="Attention!"
                                    cancelText="Cancel"
                                    confirmationText="Delete"
                                    icon={"UserMinus2"}
                                    data={user}
                                    index={index}
                                    onConfirm={(index, user) => {
                                      handleDeleteUser(user);
                                    }}
                                  >
                                    <ConfirmationModal.Content>
                                      <span>
                                        Are you sure you want to delete this user?
                                        This action cannot be undone.
                                      </span>
                                    </ConfirmationModal.Content>
                                    <ConfirmationModal.Trigger>
                                      <IconComponent
                                        name="Trash2"
                                        className="ml-2 h-4 w-4 cursor-pointer"
                                      />
                                    </ConfirmationModal.Trigger>
                                  </ConfirmationModal>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      )}
                    </Table>
                  </div>

                  <PaginatorComponent
                    pageIndex={index}
                    pageSize={size}
                    totalRowsCount={totalRowsCount}
                    paginate={handleChangePagination}
                    rowsCount={PAGINATION_ROWS_COUNT}
                  ></PaginatorComponent>
                </>
              )}
            </>
          )}

          {activeTab === "roles" && (
            <div className="p-4">
              <RoleListView />
            </div>
          )}

          {activeTab === "grants" && (
            <div className="p-4">
              <GrantListView />
            </div>
          )}

          {activeTab === "audit" && (
            <div className="p-4">
              <EnhancedAuditLogView />
            </div>
          )}

          {activeTab === "security" && (
            <div className="p-4">
              <SecurityDashboard />
            </div>
          )}

          {activeTab === "access-reviews" && (
            <div className="p-4">
              <AccessReviewCampaigns />
            </div>
          )}

          {activeTab === "anomalies" && (
            <div className="p-4">
              <AnomalyDashboard />
            </div>
          )}

          {activeTab === "compliance-reports" && (
            <div className="p-4">
              <ComplianceReportsList
                onGenerateClick={() => setIsGenerateReportModalOpen(true)}
              />
              <GenerateReportModal
                open={isGenerateReportModalOpen}
                onOpenChange={setIsGenerateReportModalOpen}
                onSuccess={() => {
                  // Force re-render of compliance reports list
                  setActiveTab("compliance-reports");
                }}
              />
            </div>
          )}

          {activeTab === "compliance-controls" && (
            <div className="p-4">
              <ComplianceControlsManager />
            </div>
          )}

          {activeTab === "sso" && (
            <div className="p-4">
              <SSOConfigList
                configs={ssoConfigs}
                onConfigCreated={() => {
                  // Reload SSO configs
                  if (userData?.id) {
                    loadSSOConfigs(userData.id);
                  }
                }}
                onConfigUpdated={() => {
                  if (userData?.id) {
                    loadSSOConfigs(userData.id);
                  }
                }}
                onConfigDeleted={() => {
                  if (userData?.id) {
                    loadSSOConfigs(userData.id);
                  }
                }}
              />
            </div>
          )}

          {activeTab === "service-accounts" && (
            <div className="p-4">
              <ServiceAccountsList
                accounts={serviceAccounts}
                onAccountCreated={() => {
                  if (userData?.id) {
                    loadServiceAccounts(userData.id);
                  }
                }}
                onAccountDeleted={() => {
                  if (userData?.id) {
                    loadServiceAccounts(userData.id);
                  }
                }}
              />
            </div>
          )}

          {activeTab === "invites" && (
            <div className="p-4">
              <InvitesList
                invites={userInvites}
                onInviteCreated={() => loadInvites()}
                onInviteRevoked={() => loadInvites()}
              />
            </div>
          )}

          {activeTab === "temporary-grants" && (
            <div className="p-4 space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-2xl font-bold">Temporary Grants</h2>
                  <p className="text-sm text-gray-500 mt-1">
                    Manage time-limited role assignments with auto-expiration
                  </p>
                </div>
                <CreateTemporaryGrantModal
                  onGrantCreated={() => loadTemporaryGrants()}
                />
              </div>
              <TemporaryGrantsList
                grants={temporaryGrants}
                onGrantCreated={() => loadTemporaryGrants()}
                onGrantUpdated={() => loadTemporaryGrants()}
                onGrantDeleted={() => loadTemporaryGrants()}
              />
            </div>
          )}
        </div>
      )}
    </>
  );
}

import { cloneDeep } from "lodash";
import { useContext, useEffect, useRef, useState } from "react";
import PaginatorComponent from "@/components/common/paginatorComponent";
import {
  useCreateRole,
  useDeleteRole,
  useGetRoles,
  useGetWorkspaces,
  useUpdateRole,
} from "@/controllers/API/queries/rbac";
import type { Role } from "@/controllers/API/queries/rbac/use-get-roles";
import type { Workspace } from "@/controllers/API/queries/rbac/use-get-workspaces";
import CustomLoader from "@/customization/components/custom-loader";
import IconComponent from "../../../../components/common/genericIconComponent";
import ShadTooltip from "../../../../components/common/shadTooltipComponent";
import { Button } from "../../../../components/ui/button";
import { CheckBoxDiv } from "../../../../components/ui/checkbox";
import { Input } from "../../../../components/ui/input";
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
  PAGINATION_PAGE,
  PAGINATION_ROWS_COUNT,
  PAGINATION_SIZE,
} from "../../../../constants/constants";
import { AuthContext } from "../../../../contexts/authContext";
import ConfirmationModal from "../../../../modals/confirmationModal";
import useAlertStore from "../../../../stores/alertStore";
import RoleManagementModal from "../components/RoleManagementModal";

export default function RoleManagementPage() {
  const [inputValue, setInputValue] = useState("");
  const [size, setPageSize] = useState(PAGINATION_SIZE);
  const [index, setPageIndex] = useState(PAGINATION_PAGE);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>("");
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const { userData } = useContext(AuthContext);
  const [totalRowsCount, setTotalRowsCount] = useState(0);

  const { mutate: mutateDeleteRole } = useDeleteRole();
  const { mutate: mutateUpdateRole } = useUpdateRole();
  const { mutate: mutateCreateRole } = useCreateRole();
  const { mutate: mutateGetWorkspaces } = useGetWorkspaces();

  const roleList = useRef<Role[]>([]);
  const workspaceList = useRef<Workspace[]>([]);

  useEffect(() => {
    setTimeout(() => {
      getWorkspaces();
      getRoles();
    }, 500);
  }, []);

  const [filterRoleList, setFilterRoleList] = useState(roleList.current);

  const { mutate: mutateGetRoles, isPending, isIdle } = useGetRoles({});

  function getWorkspaces() {
    mutateGetWorkspaces(
      { limit: 1000 },
      {
        onSuccess: (data) => {
          workspaceList.current = data.workspaces;
        },
        onError: () => {},
      },
    );
  }

  function getRoles() {
    mutateGetRoles(
      {
        workspace_id: selectedWorkspace || undefined,
        skip: size * (index - 1),
        limit: size,
        include_system_roles: true,
      },
      {
        onSuccess: (data) => {
          setTotalRowsCount(data.total_count);
          roleList.current = data.roles;
          setFilterRoleList(data.roles);
        },
        onError: () => {},
      },
    );
  }

  function handleChangePagination(pageIndex: number, pageSize: number) {
    setPageSize(pageSize);
    setPageIndex(pageIndex);

    mutateGetRoles(
      {
        workspace_id: selectedWorkspace || undefined,
        skip: pageSize * (pageIndex - 1),
        limit: pageSize,
        include_system_roles: true,
      },
      {
        onSuccess: (data) => {
          setTotalRowsCount(data.total_count);
          roleList.current = data.roles;
          setFilterRoleList(data.roles);
        },
      },
    );
  }

  function resetFilter() {
    setPageIndex(PAGINATION_PAGE);
    setPageSize(PAGINATION_SIZE);
    getRoles();
  }

  function handleFilterRoles(input: string) {
    setInputValue(input);

    if (input === "") {
      setFilterRoleList(roleList.current);
    } else {
      const filteredList = roleList.current.filter((role: Role) =>
        role.name.toLowerCase().includes(input.toLowerCase()),
      );
      setFilterRoleList(filteredList);
    }
  }

  function handleWorkspaceChange(workspaceId: string) {
    setSelectedWorkspace(workspaceId);
    setPageIndex(PAGINATION_PAGE);

    mutateGetRoles(
      {
        workspace_id: workspaceId || undefined,
        skip: 0,
        limit: size,
        include_system_roles: true,
      },
      {
        onSuccess: (data) => {
          setTotalRowsCount(data.total_count);
          roleList.current = data.roles;
          setFilterRoleList(data.roles);
        },
      },
    );
  }

  function handleDeleteRole(role: Role) {
    mutateDeleteRole(
      { role_id: role.id },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: "Role deleted successfully",
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete role",
            list: [error?.response?.data?.detail || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleEditRole(roleId: string, role: Partial<Role>) {
    mutateUpdateRole(
      { role_id: roleId, role: role },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: "Role updated successfully",
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update role",
            list: [error?.response?.data?.detail || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleToggleActive(checked: boolean, roleId: string, role: Role) {
    const roleEdit = cloneDeep(role);
    roleEdit.is_active = !checked;

    mutateUpdateRole(
      { role_id: roleId, role: roleEdit },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: "Role status updated successfully",
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update role status",
            list: [error?.response?.data?.detail || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleNewRole(roleData: {
    name: string;
    description?: string;
    permissions: string[];
    workspace_id: string;
    is_active?: boolean;
  }) {
    mutateCreateRole(roleData, {
      onSuccess: () => {
        resetFilter();
        setSuccessData({
          title: "Role created successfully",
        });
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to create role",
          list: [error?.response?.data?.detail || "Unknown error occurred"],
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
              Role Management
            </span>
          </div>
          <span className="admin-page-description-text">
            Create and manage roles with specific permissions
          </span>
          <div className="flex w-full justify-between px-4 mb-4">
            <div className="flex items-center gap-4">
              <div className="w-64">
                <Select
                  value={selectedWorkspace}
                  onValueChange={handleWorkspaceChange}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="All Workspaces" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Workspaces</SelectItem>
                    {workspaceList.current.map((workspace) => (
                      <SelectItem key={workspace.id} value={workspace.id}>
                        {workspace.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex w-96 items-center gap-4">
                <Input
                  placeholder="Search Roles"
                  value={inputValue}
                  onChange={(e) => handleFilterRoles(e.target.value)}
                />
                {inputValue.length > 0 ? (
                  <div
                    className="cursor-pointer"
                    onClick={() => {
                      setInputValue("");
                      setFilterRoleList(roleList.current);
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
            </div>
            <div>
              <RoleManagementModal
                title="New Role"
                titleHeader="Create a new role"
                cancelText="Cancel"
                confirmationText="Create"
                icon="Plus"
                workspaces={workspaceList.current}
                onConfirm={(roleData) => {
                  handleNewRole(roleData);
                }}
                asChild
              >
                <Button variant="primary">New Role</Button>
              </RoleManagementModal>
            </div>
          </div>
          {isPending || isIdle ? (
            <div className="flex h-full w-full items-center justify-center">
              <CustomLoader remSize={12} />
            </div>
          ) : roleList.current.length === 0 && !isIdle ? (
            <>
              <div className="m-4 flex items-center justify-between text-sm">
                No roles found.
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
                <Table className="table-fixed outline-1">
                  <TableHeader
                    className={
                      isPending ? "hidden" : "table-fixed bg-muted outline-1"
                    }
                  >
                    <TableRow>
                      <TableHead className="h-10">Name</TableHead>
                      <TableHead className="h-10">Description</TableHead>
                      <TableHead className="h-10">Permissions</TableHead>
                      <TableHead className="h-10">System Role</TableHead>
                      <TableHead className="h-10">Active</TableHead>
                      <TableHead className="h-10">Assignments</TableHead>
                      <TableHead className="h-10">Created At</TableHead>
                      <TableHead className="h-10 w-[100px] text-right">
                        Actions
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  {!isPending && (
                    <TableBody>
                      {filterRoleList.map((role: Role, index) => (
                        <TableRow key={role.id}>
                          <TableCell className="truncate py-2 font-medium">
                            <ShadTooltip content={role.name}>
                              <span className="cursor-default">
                                {role.name}
                              </span>
                            </ShadTooltip>
                          </TableCell>
                          <TableCell className="truncate py-2">
                            <ShadTooltip
                              content={role.description || "No description"}
                            >
                              <span className="cursor-default">
                                {role.description || "—"}
                              </span>
                            </ShadTooltip>
                          </TableCell>
                          <TableCell className="truncate py-2">
                            <ShadTooltip content={role.permissions.join(", ")}>
                              <span className="cursor-default">
                                {role.permissions.length} permission
                                {role.permissions.length !== 1 ? "s" : ""}
                              </span>
                            </ShadTooltip>
                          </TableCell>
                          <TableCell className="py-2">
                            {role.is_system_role ? (
                              <IconComponent
                                name="Shield"
                                className="h-4 w-4 text-blue-500"
                              />
                            ) : (
                              "—"
                            )}
                          </TableCell>
                          <TableCell className="relative left-1 truncate py-2 text-align-last-left">
                            {!role.is_system_role ? (
                              <ConfirmationModal
                                size="x-small"
                                title="Toggle Status"
                                titleHeader={`${role.name}`}
                                modalContentTitle="Attention!"
                                cancelText="Cancel"
                                confirmationText="Confirm"
                                icon="AlertTriangle"
                                data={role}
                                index={index}
                                onConfirm={(index, role) => {
                                  handleToggleActive(
                                    role.is_active,
                                    role.id,
                                    role,
                                  );
                                }}
                              >
                                <ConfirmationModal.Content>
                                  <span>
                                    Are you sure you want to{" "}
                                    {role.is_active ? "deactivate" : "activate"}{" "}
                                    this role?
                                  </span>
                                </ConfirmationModal.Content>
                                <ConfirmationModal.Trigger>
                                  <div className="flex w-fit">
                                    <CheckBoxDiv checked={role.is_active} />
                                  </div>
                                </ConfirmationModal.Trigger>
                              </ConfirmationModal>
                            ) : (
                              <CheckBoxDiv checked={role.is_active} disabled />
                            )}
                          </TableCell>
                          <TableCell className="truncate py-2">
                            {role.assignment_count || 0}
                          </TableCell>
                          <TableCell className="truncate py-2">
                            {
                              new Date(role.created_at)
                                .toISOString()
                                .split("T")[0]
                            }
                          </TableCell>
                          <TableCell className="flex w-[100px] py-2 text-right">
                            <div className="flex">
                              {!role.is_system_role && (
                                <>
                                  <RoleManagementModal
                                    title="Edit"
                                    titleHeader={`Edit ${role.name}`}
                                    cancelText="Cancel"
                                    confirmationText="Save"
                                    icon="Pencil"
                                    data={role}
                                    workspaces={workspaceList.current}
                                    index={index}
                                    onConfirm={(roleData) => {
                                      handleEditRole(role.id, roleData);
                                    }}
                                  >
                                    <ShadTooltip content="Edit" side="top">
                                      <IconComponent
                                        name="Pencil"
                                        className="h-4 w-4 cursor-pointer"
                                      />
                                    </ShadTooltip>
                                  </RoleManagementModal>

                                  <ConfirmationModal
                                    size="x-small"
                                    title="Delete"
                                    titleHeader="Delete Role"
                                    modalContentTitle="Attention!"
                                    cancelText="Cancel"
                                    confirmationText="Delete"
                                    icon="Trash2"
                                    data={role}
                                    index={index}
                                    onConfirm={(index, role) => {
                                      handleDeleteRole(role);
                                    }}
                                  >
                                    <ConfirmationModal.Content>
                                      <span>
                                        Are you sure you want to delete this
                                        role? This will remove all role
                                        assignments and cannot be undone.
                                      </span>
                                    </ConfirmationModal.Content>
                                    <ConfirmationModal.Trigger>
                                      <IconComponent
                                        name="Trash2"
                                        className="ml-2 h-4 w-4 cursor-pointer"
                                      />
                                    </ConfirmationModal.Trigger>
                                  </ConfirmationModal>
                                </>
                              )}
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
              />
            </>
          )}
        </div>
      )}
    </>
  );
}

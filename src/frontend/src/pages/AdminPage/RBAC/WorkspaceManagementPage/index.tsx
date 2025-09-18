import { cloneDeep } from "lodash";
import { useContext, useEffect, useRef, useState } from "react";
import PaginatorComponent from "@/components/common/paginatorComponent";
import {
  useCreateWorkspace,
  useDeleteWorkspace,
  useGetWorkspaces,
  useUpdateWorkspace,
} from "@/controllers/API/queries/rbac";
import type { Workspace } from "@/controllers/API/queries/rbac/use-get-workspaces";
import CustomLoader from "@/customization/components/custom-loader";
import IconComponent from "../../../../components/common/genericIconComponent";
import ShadTooltip from "../../../../components/common/shadTooltipComponent";
import { Button } from "../../../../components/ui/button";
import { CheckBoxDiv } from "../../../../components/ui/checkbox";
import { Input } from "../../../../components/ui/input";
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
import WorkspaceManagementModal from "../components/WorkspaceManagementModal";

export default function WorkspaceManagementPage() {
  const [inputValue, setInputValue] = useState("");
  const [size, setPageSize] = useState(PAGINATION_SIZE);
  const [index, setPageIndex] = useState(PAGINATION_PAGE);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);
  const { userData } = useContext(AuthContext);
  const [totalRowsCount, setTotalRowsCount] = useState(0);

  const { mutate: mutateDeleteWorkspace } = useDeleteWorkspace();
  const { mutate: mutateUpdateWorkspace } = useUpdateWorkspace();
  const { mutate: mutateCreateWorkspace } = useCreateWorkspace();

  const workspaceList = useRef<Workspace[]>([]);

  useEffect(() => {
    setTimeout(() => {
      getWorkspaces();
    }, 500);
  }, []);

  const [filterWorkspaceList, setFilterWorkspaceList] = useState(
    workspaceList.current,
  );

  const {
    mutate: mutateGetWorkspaces,
    isPending,
    isIdle,
  } = useGetWorkspaces({});

  function getWorkspaces() {
    mutateGetWorkspaces(
      {
        skip: size * (index - 1),
        limit: size,
      },
      {
        onSuccess: (data) => {
          setTotalRowsCount(data.total_count);
          workspaceList.current = data.workspaces;
          setFilterWorkspaceList(data.workspaces);
        },
        onError: () => {},
      },
    );
  }

  function handleChangePagination(pageIndex: number, pageSize: number) {
    setPageSize(pageSize);
    setPageIndex(pageIndex);

    mutateGetWorkspaces(
      {
        skip: pageSize * (pageIndex - 1),
        limit: pageSize,
      },
      {
        onSuccess: (data) => {
          setTotalRowsCount(data.total_count);
          workspaceList.current = data.workspaces;
          setFilterWorkspaceList(data.workspaces);
        },
      },
    );
  }

  function resetFilter() {
    setPageIndex(PAGINATION_PAGE);
    setPageSize(PAGINATION_SIZE);
    getWorkspaces();
  }

  function handleFilterWorkspaces(input: string) {
    setInputValue(input);

    if (input === "") {
      setFilterWorkspaceList(workspaceList.current);
    } else {
      const filteredList = workspaceList.current.filter(
        (workspace: Workspace) =>
          workspace.name.toLowerCase().includes(input.toLowerCase()),
      );
      setFilterWorkspaceList(filteredList);
    }
  }

  function handleDeleteWorkspace(workspace: Workspace) {
    mutateDeleteWorkspace(
      { workspace_id: workspace.id },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: "Workspace deleted successfully",
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to delete workspace",
            list: [error?.response?.data?.detail || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleEditWorkspace(
    workspaceId: string,
    workspace: Partial<Workspace>,
  ) {
    mutateUpdateWorkspace(
      { workspace_id: workspaceId, workspace: workspace },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: "Workspace updated successfully",
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update workspace",
            list: [error?.response?.data?.detail || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleToggleActive(
    checked: boolean,
    workspaceId: string,
    workspace: Workspace,
  ) {
    const workspaceEdit = cloneDeep(workspace);
    workspaceEdit.is_active = !checked;

    mutateUpdateWorkspace(
      { workspace_id: workspaceId, workspace: workspaceEdit },
      {
        onSuccess: () => {
          resetFilter();
          setSuccessData({
            title: "Workspace status updated successfully",
          });
        },
        onError: (error) => {
          setErrorData({
            title: "Failed to update workspace status",
            list: [error?.response?.data?.detail || "Unknown error occurred"],
          });
        },
      },
    );
  }

  function handleNewWorkspace(workspaceData: {
    name: string;
    description?: string;
    is_active?: boolean;
  }) {
    mutateCreateWorkspace(workspaceData, {
      onSuccess: () => {
        resetFilter();
        setSuccessData({
          title: "Workspace created successfully",
        });
      },
      onError: (error) => {
        setErrorData({
          title: "Failed to create workspace",
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
              <IconComponent name="Building" className="w-6" />
              Workspace Management
            </span>
          </div>
          <span className="admin-page-description-text">
            Manage workspaces and organize your LangBuilder resources
          </span>
          <div className="flex w-full justify-between px-4">
            <div className="flex w-96 items-center gap-4">
              <Input
                placeholder="Search Workspaces"
                value={inputValue}
                onChange={(e) => handleFilterWorkspaces(e.target.value)}
              />
              {inputValue.length > 0 ? (
                <div
                  className="cursor-pointer"
                  onClick={() => {
                    setInputValue("");
                    setFilterWorkspaceList(workspaceList.current);
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
              <WorkspaceManagementModal
                title="New Workspace"
                titleHeader="Create a new workspace"
                cancelText="Cancel"
                confirmationText="Create"
                icon="Plus"
                onConfirm={(workspaceData) => {
                  handleNewWorkspace(workspaceData);
                }}
                asChild
              >
                <Button variant="primary">New Workspace</Button>
              </WorkspaceManagementModal>
            </div>
          </div>
          {isPending || isIdle ? (
            <div className="flex h-full w-full items-center justify-center">
              <CustomLoader remSize={12} />
            </div>
          ) : workspaceList.current.length === 0 && !isIdle ? (
            <>
              <div className="m-4 flex items-center justify-between text-sm">
                No workspaces found.
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
                      <TableHead className="h-10">Active</TableHead>
                      <TableHead className="h-10">Members</TableHead>
                      <TableHead className="h-10">Roles</TableHead>
                      <TableHead className="h-10">Created At</TableHead>
                      <TableHead className="h-10 w-[100px] text-right">
                        Actions
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  {!isPending && (
                    <TableBody>
                      {filterWorkspaceList.map(
                        (workspace: Workspace, index) => (
                          <TableRow key={workspace.id}>
                            <TableCell className="truncate py-2 font-medium">
                              <ShadTooltip content={workspace.name}>
                                <span className="cursor-default">
                                  {workspace.name}
                                </span>
                              </ShadTooltip>
                            </TableCell>
                            <TableCell className="truncate py-2">
                              <ShadTooltip
                                content={
                                  workspace.description || "No description"
                                }
                              >
                                <span className="cursor-default">
                                  {workspace.description || "—"}
                                </span>
                              </ShadTooltip>
                            </TableCell>
                            <TableCell className="relative left-1 truncate py-2 text-align-last-left">
                              <ConfirmationModal
                                size="x-small"
                                title="Toggle Status"
                                titleHeader={`${workspace.name}`}
                                modalContentTitle="Attention!"
                                cancelText="Cancel"
                                confirmationText="Confirm"
                                icon="AlertTriangle"
                                data={workspace}
                                index={index}
                                onConfirm={(index, workspace) => {
                                  handleToggleActive(
                                    workspace.is_active,
                                    workspace.id,
                                    workspace,
                                  );
                                }}
                              >
                                <ConfirmationModal.Content>
                                  <span>
                                    Are you sure you want to{" "}
                                    {workspace.is_active
                                      ? "deactivate"
                                      : "activate"}{" "}
                                    this workspace?
                                  </span>
                                </ConfirmationModal.Content>
                                <ConfirmationModal.Trigger>
                                  <div className="flex w-fit">
                                    <CheckBoxDiv
                                      checked={workspace.is_active}
                                    />
                                  </div>
                                </ConfirmationModal.Trigger>
                              </ConfirmationModal>
                            </TableCell>
                            <TableCell className="truncate py-2">
                              {workspace.member_count || 0}
                            </TableCell>
                            <TableCell className="truncate py-2">
                              {workspace.role_count || 0}
                            </TableCell>
                            <TableCell className="truncate py-2">
                              {
                                new Date(workspace.created_at)
                                  .toISOString()
                                  .split("T")[0]
                              }
                            </TableCell>
                            <TableCell className="flex w-[100px] py-2 text-right">
                              <div className="flex">
                                <WorkspaceManagementModal
                                  title="Edit"
                                  titleHeader={`Edit ${workspace.name}`}
                                  cancelText="Cancel"
                                  confirmationText="Save"
                                  icon="Pencil"
                                  data={workspace}
                                  index={index}
                                  onConfirm={(workspaceData) => {
                                    handleEditWorkspace(
                                      workspace.id,
                                      workspaceData,
                                    );
                                  }}
                                >
                                  <ShadTooltip content="Edit" side="top">
                                    <IconComponent
                                      name="Pencil"
                                      className="h-4 w-4 cursor-pointer"
                                    />
                                  </ShadTooltip>
                                </WorkspaceManagementModal>

                                <ConfirmationModal
                                  size="x-small"
                                  title="Delete"
                                  titleHeader="Delete Workspace"
                                  modalContentTitle="Attention!"
                                  cancelText="Cancel"
                                  confirmationText="Delete"
                                  icon="Trash2"
                                  data={workspace}
                                  index={index}
                                  onConfirm={(index, workspace) => {
                                    handleDeleteWorkspace(workspace);
                                  }}
                                >
                                  <ConfirmationModal.Content>
                                    <span>
                                      Are you sure you want to delete this
                                      workspace? This action cannot be undone
                                      and will remove all associated data.
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
                        ),
                      )}
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

import { useEffect, useState } from "react";
import { useGetWorkspaces } from "../../../../controllers/API/queries/rbac/use-get-workspaces";
import {
  useGetUserGroups,
  useCreateUserGroup,
  useUpdateUserGroup,
  useDeleteUserGroup,
  useGetUserGroupMembers,
  useAddUserGroupMember,
  useRemoveUserGroupMember,
  useSyncUserGroup,
  type UserGroup,
  type UserGroupMembership,
  GroupType,
  getGroupTypeColor,
  formatGroupType,
} from "../../../../controllers/API/queries/rbac/use-user-groups";
import { Card } from "../../../../components/ui/card";
import { Badge } from "../../../../components/ui/badge";
import { Button } from "../../../../components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../../../components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../../../components/ui/tabs";
import { Separator } from "../../../../components/ui/separator";

export default function UserGroupsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedWorkspace, setSelectedWorkspace] = useState("");
  const [selectedGroupType, setSelectedGroupType] = useState<GroupType | "">("");
  const [isCreating, setIsCreating] = useState(false);
  const [editingGroup, setEditingGroup] = useState<UserGroup | null>(null);
  const [viewingGroup, setViewingGroup] = useState<UserGroup | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [newUserEmail, setNewUserEmail] = useState("");

  const [newGroup, setNewGroup] = useState({
    name: "",
    description: "",
    workspace_id: "",
    group_type: GroupType.MANUAL,
    tags: [] as string[],
  });

  const {
    mutate: fetchGroups,
    data: groupsData,
    isPending: isLoading,
    error: groupsError,
  } = useGetUserGroups({
    onSuccess: (data) => {
      console.log("User groups fetched successfully:", data);
    },
    onError: (error) => {
      console.error("Failed to fetch user groups:", error);
    },
  });

  const { mutate: fetchWorkspaces, data: workspacesData } = useGetWorkspaces();

  const { mutate: createGroup, isPending: isCreatingGroup } = useCreateUserGroup({
    onSuccess: () => {
      setIsCreating(false);
      setNewGroup({
        name: "",
        description: "",
        workspace_id: "",
        group_type: GroupType.MANUAL,
        tags: [],
      });
      setCreateError(null);
      fetchGroups({ workspace_id: selectedWorkspace });
    },
    onError: (error) => {
      setCreateError(error?.message || "Failed to create group");
    },
  });

  const { mutate: updateGroup, isPending: isUpdatingGroup } = useUpdateUserGroup({
    onSuccess: () => {
      setEditingGroup(null);
      fetchGroups({ workspace_id: selectedWorkspace });
    },
    onError: (error) => {
      console.error("Failed to update group:", error);
    },
  });

  const { mutate: deleteGroup } = useDeleteUserGroup({
    onSuccess: () => {
      fetchGroups({ workspace_id: selectedWorkspace });
    },
    onError: (error) => {
      console.error("Failed to delete group:", error);
    },
  });

  const {
    mutate: fetchMembers,
    data: membersData,
    isPending: isLoadingMembers,
  } = useGetUserGroupMembers();

  const { mutate: addMember, isPending: isAddingMember } = useAddUserGroupMember({
    onSuccess: () => {
      setNewUserEmail("");
      if (viewingGroup) {
        fetchMembers({ group_id: viewingGroup.id });
      }
    },
    onError: (error) => {
      console.error("Failed to add member:", error);
    },
  });

  const { mutate: removeMember } = useRemoveUserGroupMember({
    onSuccess: () => {
      if (viewingGroup) {
        fetchMembers({ group_id: viewingGroup.id });
      }
    },
    onError: (error) => {
      console.error("Failed to remove member:", error);
    },
  });

  const { mutate: syncGroup, isPending: isSyncing } = useSyncUserGroup({
    onSuccess: () => {
      fetchGroups({ workspace_id: selectedWorkspace });
      if (viewingGroup) {
        fetchMembers({ group_id: viewingGroup.id });
      }
    },
    onError: (error) => {
      console.error("Failed to sync group:", error);
    },
  });

  useEffect(() => {
    fetchWorkspaces({});
  }, []);

  useEffect(() => {
    fetchGroups({
      workspace_id: selectedWorkspace || undefined,
      search: searchTerm || undefined,
      group_type: selectedGroupType || undefined,
    });
  }, [selectedWorkspace, searchTerm, selectedGroupType]);

  useEffect(() => {
    if (viewingGroup) {
      fetchMembers({ group_id: viewingGroup.id });
    }
  }, [viewingGroup]);

  const handleCreateGroup = () => {
    if (newGroup.name.trim() && newGroup.workspace_id) {
      setCreateError(null);
      createGroup({
        name: newGroup.name.trim(),
        description: newGroup.description.trim() || undefined,
        workspace_id: newGroup.workspace_id,
        group_type: newGroup.group_type,
        tags: newGroup.tags.length > 0 ? newGroup.tags : undefined,
      });
    } else {
      setCreateError("Name and workspace are required");
    }
  };

  const handleUpdateGroup = () => {
    if (editingGroup) {
      updateGroup({
        group_id: editingGroup.id,
        data: {
          name: editingGroup.name,
          description: editingGroup.description,
          is_active: editingGroup.is_active,
          sync_enabled: editingGroup.sync_enabled,
          tags: editingGroup.tags,
        },
      });
    }
  };

  const handleDeleteGroup = (group: UserGroup) => {
    if (confirm(`Are you sure you want to delete the group "${group.name}"?`)) {
      deleteGroup({ group_id: group.id });
    }
  };

  const handleAddMember = () => {
    if (viewingGroup && newUserEmail.trim()) {
      // In a real app, you'd need to resolve email to user_id
      // For now, we'll use the email as the user_id
      addMember({
        group_id: viewingGroup.id,
        user_id: newUserEmail.trim(),
        membership_type: "direct",
      });
    }
  };

  const handleRemoveMember = (membership: UserGroupMembership) => {
    if (confirm(`Remove ${membership.user_name || membership.user_id} from the group?`)) {
      removeMember({
        group_id: membership.group_id,
        user_id: membership.user_id,
      });
    }
  };

  const handleSyncGroup = (group: UserGroup) => {
    if (confirm(`Sync group "${group.name}" from external source?`)) {
      syncGroup({ group_id: group.id });
    }
  };

  const groups = groupsData?.user_groups || [];
  const workspaces = Array.isArray(workspacesData) ? workspacesData : workspacesData?.workspaces || [];
  const members = membersData || [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">User Groups</h1>
          <p className="text-gray-600">Manage user groups and their members</p>
        </div>
        <Button onClick={() => setIsCreating(true)} disabled={isCreatingGroup}>
          {isCreatingGroup ? "Creating..." : "Create Group"}
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex space-x-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-1">Search Groups</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or description..."
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Workspace</label>
            <select
              value={selectedWorkspace}
              onChange={(e) => setSelectedWorkspace(e.target.value)}
              className="border rounded px-3 py-2"
            >
              <option value="">All Workspaces</option>
              {workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>
                  {workspace.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Group Type</label>
            <select
              value={selectedGroupType}
              onChange={(e) => setSelectedGroupType(e.target.value as GroupType | "")}
              className="border rounded px-3 py-2"
            >
              <option value="">All Types</option>
              {Object.values(GroupType).map((type) => (
                <option key={type} value={type}>
                  {formatGroupType(type)}
                </option>
              ))}
            </select>
          </div>
          <Button
            onClick={() => {
              setSearchTerm("");
              setSelectedWorkspace("");
              setSelectedGroupType("");
            }}
            variant="outline"
          >
            Clear Filters
          </Button>
        </div>
      </Card>

      {/* Groups List */}
      {groupsError && (
        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          Error loading groups: {groupsError.message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <div className="col-span-full text-center py-8 text-gray-500">
            Loading groups...
          </div>
        ) : groups.length === 0 ? (
          <div className="col-span-full text-center py-8 text-gray-500">
            No groups found. Create your first group!
          </div>
        ) : (
          groups.map((group) => (
            <Card key={group.id} className="p-4 hover:shadow-md transition-shadow">
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{group.name}</h3>
                    <p className="text-sm text-gray-600">{group.description || "No description"}</p>
                  </div>
                  <Badge variant="outline" className={`bg-${getGroupTypeColor(group.group_type)}-100`}>
                    {formatGroupType(group.group_type)}
                  </Badge>
                </div>

                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>{group.member_count || 0} members</span>
                  <span className={group.is_active ? "text-green-600" : "text-gray-400"}>
                    {group.is_active ? "Active" : "Inactive"}
                  </span>
                </div>

                {group.sync_enabled && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-blue-600">Sync Enabled</span>
                    {group.sync_last_run && (
                      <span className="text-gray-500">
                        Last: {new Date(group.sync_last_run).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                )}

                <Separator />

                <div className="flex space-x-2 text-sm">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setViewingGroup(group)}
                  >
                    View
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setEditingGroup({ ...group })}
                  >
                    Edit
                  </Button>
                  {group.sync_enabled && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleSyncGroup(group)}
                      disabled={isSyncing}
                    >
                      Sync
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDeleteGroup(group)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Create Group Dialog */}
      <Dialog open={isCreating} onOpenChange={setIsCreating}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Group</DialogTitle>
          </DialogHeader>

          {createError && (
            <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded text-sm">
              {createError}
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Group Name</label>
              <input
                type="text"
                value={newGroup.name}
                onChange={(e) => setNewGroup(prev => ({ ...prev, name: e.target.value }))}
                className="w-full border rounded px-3 py-2"
                placeholder="Enter group name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={newGroup.description}
                onChange={(e) => setNewGroup(prev => ({ ...prev, description: e.target.value }))}
                className="w-full border rounded px-3 py-2"
                rows={2}
                placeholder="Enter description (optional)"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Workspace</label>
              <select
                value={newGroup.workspace_id}
                onChange={(e) => setNewGroup(prev => ({ ...prev, workspace_id: e.target.value }))}
                className="w-full border rounded px-3 py-2"
              >
                <option value="">Select Workspace</option>
                {workspaces.map((workspace) => (
                  <option key={workspace.id} value={workspace.id}>
                    {workspace.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Group Type</label>
              <select
                value={newGroup.group_type}
                onChange={(e) => setNewGroup(prev => ({ ...prev, group_type: e.target.value as GroupType }))}
                className="w-full border rounded px-3 py-2"
              >
                {Object.values(GroupType).map((type) => (
                  <option key={type} value={type}>
                    {formatGroupType(type)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex space-x-2 justify-end">
            <Button
              variant="outline"
              onClick={() => {
                setIsCreating(false);
                setCreateError(null);
                setNewGroup({
                  name: "",
                  description: "",
                  workspace_id: "",
                  group_type: GroupType.MANUAL,
                  tags: [],
                });
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateGroup}
              disabled={!newGroup.name.trim() || !newGroup.workspace_id || isCreatingGroup}
            >
              {isCreatingGroup ? "Creating..." : "Create"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit Group Dialog */}
      <Dialog open={!!editingGroup} onOpenChange={() => setEditingGroup(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Group</DialogTitle>
          </DialogHeader>

          {editingGroup && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Group Name</label>
                <input
                  type="text"
                  value={editingGroup.name}
                  onChange={(e) => setEditingGroup(prev => prev ? { ...prev, name: e.target.value } : null)}
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={editingGroup.description || ""}
                  onChange={(e) => setEditingGroup(prev => prev ? { ...prev, description: e.target.value } : null)}
                  className="w-full border rounded px-3 py-2"
                  rows={2}
                />
              </div>

              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={editingGroup.is_active}
                    onChange={(e) => setEditingGroup(prev => prev ? { ...prev, is_active: e.target.checked } : null)}
                    className="mr-2"
                  />
                  Active
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={editingGroup.sync_enabled}
                    onChange={(e) => setEditingGroup(prev => prev ? { ...prev, sync_enabled: e.target.checked } : null)}
                    className="mr-2"
                  />
                  Sync Enabled
                </label>
              </div>
            </div>
          )}

          <div className="flex space-x-2 justify-end">
            <Button variant="outline" onClick={() => setEditingGroup(null)}>
              Cancel
            </Button>
            <Button
              onClick={handleUpdateGroup}
              disabled={isUpdatingGroup || !editingGroup?.name.trim()}
            >
              {isUpdatingGroup ? "Saving..." : "Save"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Group Details Dialog */}
      <Dialog open={!!viewingGroup} onOpenChange={() => setViewingGroup(null)}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Group Details: {viewingGroup?.name}</DialogTitle>
          </DialogHeader>

          {viewingGroup && (
            <Tabs defaultValue="info" className="w-full">
              <TabsList>
                <TabsTrigger value="info">Information</TabsTrigger>
                <TabsTrigger value="members">Members ({members.length})</TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Name</label>
                    <p className="mt-1">{viewingGroup.name}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Type</label>
                    <Badge className={`mt-1 bg-${getGroupTypeColor(viewingGroup.group_type)}-100`}>
                      {formatGroupType(viewingGroup.group_type)}
                    </Badge>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Description</label>
                    <p className="mt-1">{viewingGroup.description || "No description"}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Status</label>
                    <p className={`mt-1 ${viewingGroup.is_active ? 'text-green-600' : 'text-gray-500'}`}>
                      {viewingGroup.is_active ? "Active" : "Inactive"}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Created</label>
                    <p className="mt-1">{new Date(viewingGroup.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last Updated</label>
                    <p className="mt-1">{new Date(viewingGroup.updated_at).toLocaleString()}</p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="members" className="space-y-4">
                <div className="flex space-x-2">
                  <input
                    type="email"
                    value={newUserEmail}
                    onChange={(e) => setNewUserEmail(e.target.value)}
                    placeholder="Enter user email"
                    className="flex-1 border rounded px-3 py-2"
                  />
                  <Button
                    onClick={handleAddMember}
                    disabled={!newUserEmail.trim() || isAddingMember}
                  >
                    {isAddingMember ? "Adding..." : "Add Member"}
                  </Button>
                </div>

                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">User</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Email</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Type</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Added</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {isLoadingMembers ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                            Loading members...
                          </td>
                        </tr>
                      ) : members.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                            No members in this group
                          </td>
                        </tr>
                      ) : (
                        members.map((member) => (
                          <tr key={member.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 font-medium">
                              {member.user_name || member.user_id}
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {member.user_email || "N/A"}
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant="outline">{member.membership_type}</Badge>
                            </td>
                            <td className="px-4 py-3 text-gray-600">
                              {new Date(member.added_at).toLocaleDateString()}
                            </td>
                            <td className="px-4 py-3">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleRemoveMember(member)}
                                className="text-red-600 hover:text-red-800"
                              >
                                Remove
                              </Button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </TabsContent>
            </Tabs>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
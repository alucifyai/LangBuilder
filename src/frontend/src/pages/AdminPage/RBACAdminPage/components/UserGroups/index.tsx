// User Groups Component - Epic 2: Identity management + SCIM integration
// Implements group management with SCIM synchronization support

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Checkbox } from "@/components/ui/checkbox";
import IconComponent from "@/components/common/genericIconComponent";
import { UserGroup, User, CreateUserGroupRequest } from "../../types/rbac";

// Mock data
const MOCK_USERS: User[] = [
  { id: "user-1", email: "alice@company.com", name: "Alice Johnson", is_active: true, created_at: "2024-01-01T00:00:00Z", updated_at: "2024-01-25T00:00:00Z" },
  { id: "user-2", email: "bob@company.com", name: "Bob Smith", is_active: true, created_at: "2024-01-02T00:00:00Z", updated_at: "2024-01-24T00:00:00Z" },
  { id: "user-3", email: "carol@company.com", name: "Carol Davis", is_active: true, created_at: "2024-01-03T00:00:00Z", updated_at: "2024-01-23T00:00:00Z" },
  { id: "user-4", email: "david@company.com", name: "David Wilson", is_active: true, created_at: "2024-01-04T00:00:00Z", updated_at: "2024-01-22T00:00:00Z" },
  { id: "user-5", email: "eve@company.com", name: "Eve Anderson", is_active: false, created_at: "2024-01-05T00:00:00Z", updated_at: "2024-01-21T00:00:00Z" },
];

const MOCK_USER_GROUPS: UserGroup[] = [
  {
    id: "group-1",
    name: "Data Team",
    description: "Data science and analytics team",
    member_count: 5,
    external_id: "okta-group-12345", // SCIM integration
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-20T00:00:00Z",
  },
  {
    id: "group-2",
    name: "Platform Engineering",
    description: "Infrastructure and platform team",
    member_count: 3,
    external_id: "okta-group-67890", // SCIM integration
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-21T00:00:00Z",
  },
  {
    id: "group-3",
    name: "ML Engineering",
    description: "Machine learning engineering team",
    member_count: 4,
    created_at: "2024-01-03T00:00:00Z",
    updated_at: "2024-01-22T00:00:00Z",
  },
  {
    id: "group-4",
    name: "Security Team",
    description: "Information security team",
    member_count: 2,
    external_id: "okta-group-security",
    created_at: "2024-01-04T00:00:00Z",
    updated_at: "2024-01-23T00:00:00Z",
  },
];

// Mock group memberships
const MOCK_GROUP_MEMBERSHIPS = [
  { group_id: "group-1", user_id: "user-1" },
  { group_id: "group-1", user_id: "user-2" },
  { group_id: "group-1", user_id: "user-3" },
  { group_id: "group-2", user_id: "user-2" },
  { group_id: "group-2", user_id: "user-4" },
  { group_id: "group-3", user_id: "user-1" },
  { group_id: "group-3", user_id: "user-3" },
  { group_id: "group-3", user_id: "user-4" },
];

interface GroupBuilderProps {
  group?: UserGroup;
  onSave: (groupData: CreateUserGroupRequest) => void;
  onCancel: () => void;
}

function GroupBuilder({ group, onSave, onCancel }: GroupBuilderProps) {
  const [name, setName] = useState(group?.name || "");
  const [description, setDescription] = useState(group?.description || "");
  const [selectedUserIds, setSelectedUserIds] = useState<Set<string>>(new Set());
  const [syncWithSCIM, setSyncWithSCIM] = useState(!!group?.external_id);
  const [externalId, setExternalId] = useState(group?.external_id || "");

  const [nameError, setNameError] = useState("");

  const handleUserToggle = (userId: string) => {
    const newSelected = new Set(selectedUserIds);
    if (newSelected.has(userId)) {
      newSelected.delete(userId);
    } else {
      newSelected.add(userId);
    }
    setSelectedUserIds(newSelected);
  };

  const handleSave = () => {
    if (!name.trim()) {
      setNameError("Group name is required");
      return;
    }

    if (syncWithSCIM && !externalId.trim()) {
      setNameError("External ID is required for SCIM sync");
      return;
    }

    setNameError("");

    const groupData: CreateUserGroupRequest = {
      name: name.trim(),
      description: description.trim() || undefined,
      user_ids: Array.from(selectedUserIds),
    };

    onSave(groupData);
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4">
        <div>
          <Label htmlFor="group-name">Group Name *</Label>
          <Input
            id="group-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter group name"
            className={nameError ? "border-red-500" : ""}
          />
          {nameError && <p className="text-sm text-red-500 mt-1">{nameError}</p>}
        </div>
        <div>
          <Label htmlFor="group-description">Description</Label>
          <Textarea
            id="group-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Enter group description"
            rows={3}
          />
        </div>
      </div>

      <Separator />

      {/* SCIM Integration - PRD Epic 2: Story 2.3 */}
      <div className="space-y-4">
        <h4 className="text-lg font-medium">SCIM Integration</h4>
        <div className="flex items-center justify-between p-4 border rounded-lg">
          <div>
            <Label className="text-sm font-medium">Sync with Identity Provider</Label>
            <p className="text-sm text-muted-foreground">
              Automatically sync group membership from your IdP (SCIM)
            </p>
          </div>
          <Switch checked={syncWithSCIM} onCheckedChange={setSyncWithSCIM} />
        </div>

        {syncWithSCIM && (
          <div>
            <Label htmlFor="external-id">External Group ID</Label>
            <Input
              id="external-id"
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              placeholder="e.g., okta-group-12345"
            />
            <p className="text-sm text-muted-foreground mt-1">
              The group identifier from your identity provider
            </p>
          </div>
        )}
      </div>

      <Separator />

      {/* Manual Member Selection (disabled if SCIM) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-lg font-medium">Group Members</h4>
            <p className="text-sm text-muted-foreground">
              {syncWithSCIM
                ? "Members will be automatically synced from your IdP"
                : "Select users to add to this group"
              }
            </p>
          </div>
          <Badge variant="outline">
            {selectedUserIds.size} selected
          </Badge>
        </div>

        {!syncWithSCIM && (
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {MOCK_USERS.map((user) => (
              <div
                key={user.id}
                className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-muted/50"
              >
                <Checkbox
                  id={user.id}
                  checked={selectedUserIds.has(user.id)}
                  onCheckedChange={() => handleUserToggle(user.id)}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor={user.id} className="text-sm font-medium cursor-pointer">
                        {user.name}
                      </Label>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                    <Badge variant={user.is_active ? "outline" : "secondary"}>
                      {user.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex justify-end space-x-2 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSave} disabled={!name.trim()}>
          {group ? "Update Group" : "Create Group"}
        </Button>
      </div>
    </div>
  );
}

interface GroupMembersDialogProps {
  group: UserGroup;
  isOpen: boolean;
  onClose: () => void;
}

function GroupMembersDialog({ group, isOpen, onClose }: GroupMembersDialogProps) {
  const groupMembers = useMemo(() => {
    const memberIds = MOCK_GROUP_MEMBERSHIPS
      .filter(m => m.group_id === group.id)
      .map(m => m.user_id);
    return MOCK_USERS.filter(u => memberIds.includes(u.id));
  }, [group.id]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Members of {group.name}</DialogTitle>
          <DialogDescription>
            {group.external_id
              ? "Members are automatically synced from your identity provider"
              : "Manually managed group members"
            }
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {group.external_id && (
            <div className="flex items-center space-x-2 p-3 bg-blue-50 rounded-lg">
              <IconComponent name="Sync" className="h-4 w-4 text-blue-600" />
              <div className="text-sm">
                <div className="font-medium text-blue-900">SCIM Synchronized</div>
                <div className="text-blue-700">External ID: {group.external_id}</div>
              </div>
            </div>
          )}

          <div className="space-y-2">
            {groupMembers.map((user) => (
              <div key={user.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-900">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <div className="font-medium">{user.name}</div>
                    <div className="text-sm text-muted-foreground">{user.email}</div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant={user.is_active ? "outline" : "secondary"}>
                    {user.is_active ? "Active" : "Inactive"}
                  </Badge>
                  {user.last_login && (
                    <span className="text-xs text-muted-foreground">
                      Last: {new Date(user.last_login).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {groupMembers.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No members in this group
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function GroupTable({ groups, onEdit, onDelete, onViewMembers, onSync }: {
  groups: UserGroup[];
  onEdit: (group: UserGroup) => void;
  onDelete: (groupId: string) => void;
  onViewMembers: (group: UserGroup) => void;
  onSync: (group: UserGroup) => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSync, setFilterSync] = useState<string>("all");

  const filteredGroups = useMemo(() => {
    return groups.filter((group) => {
      const matchesSearch = group.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           (group.description?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);

      const matchesSync = filterSync === "all" ||
                         (filterSync === "scim" && group.external_id) ||
                         (filterSync === "manual" && !group.external_id);

      return matchesSearch && matchesSync;
    });
  }, [groups, searchTerm, filterSync]);

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Input
          placeholder="Search groups..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="max-w-sm"
        />
        <Select value={filterSync} onValueChange={setFilterSync}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by sync" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Groups</SelectItem>
            <SelectItem value="scim">SCIM Synced</SelectItem>
            <SelectItem value="manual">Manual</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Group</TableHead>
                <TableHead>Members</TableHead>
                <TableHead>Sync Status</TableHead>
                <TableHead>Updated</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredGroups.map((group) => (
                <TableRow key={group.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium flex items-center">
                        <IconComponent name="Users" className="h-4 w-4 mr-2" />
                        {group.name}
                      </div>
                      {group.description && (
                        <div className="text-sm text-muted-foreground">
                          {group.description}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewMembers(group)}
                      className="p-0 h-auto font-normal"
                    >
                      {group.member_count} members
                    </Button>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      {group.external_id ? (
                        <Badge variant="outline" className="text-blue-700">
                          <IconComponent name="Sync" className="h-3 w-3 mr-1" />
                          SCIM
                        </Badge>
                      ) : (
                        <Badge variant="outline">Manual</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(group.updated_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-1">
                      {group.external_id && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onSync(group)}
                          title="Sync with IdP"
                        >
                          <IconComponent name="RefreshCw" className="h-4 w-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(group)}
                        title="Edit Group"
                      >
                        <IconComponent name="Edit" className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(group.id)}
                        title="Delete Group"
                        disabled={!!group.external_id} // Can't delete SCIM groups
                      >
                        <IconComponent name="Trash2" className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

export default function UserGroups() {
  const [groups, setGroups] = useState<UserGroup[]>(MOCK_USER_GROUPS);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingGroup, setEditingGroup] = useState<UserGroup | null>(null);
  const [viewMembersGroup, setViewMembersGroup] = useState<UserGroup | null>(null);

  const handleCreateGroup = (groupData: CreateUserGroupRequest) => {
    const newGroup: UserGroup = {
      id: `group-${Date.now()}`,
      name: groupData.name,
      description: groupData.description,
      member_count: groupData.user_ids?.length || 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setGroups([...groups, newGroup]);
    setIsCreateDialogOpen(false);
  };

  const handleUpdateGroup = (groupData: CreateUserGroupRequest) => {
    if (!editingGroup) return;

    const updatedGroup: UserGroup = {
      ...editingGroup,
      name: groupData.name,
      description: groupData.description,
      member_count: groupData.user_ids?.length || editingGroup.member_count,
      updated_at: new Date().toISOString(),
    };

    setGroups(groups.map(g => g.id === editingGroup.id ? updatedGroup : g));
    setEditingGroup(null);
  };

  const handleDeleteGroup = (groupId: string) => {
    if (confirm("Are you sure you want to delete this group?")) {
      setGroups(groups.filter(g => g.id !== groupId));
    }
  };

  const handleSyncGroup = (group: UserGroup) => {
    // PRD Epic 2: Story 2.3 - SCIM sync
    alert(`Syncing ${group.name} with identity provider...`);
    // In real implementation, this would trigger SCIM sync
  };

  // Calculate statistics
  const scimGroups = groups.filter(g => g.external_id).length;
  const manualGroups = groups.filter(g => !g.external_id).length;
  const totalMembers = groups.reduce((sum, g) => sum + g.member_count, 0);

  return (
    <div className="h-full flex flex-col p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">User Groups Management</h2>
          <p className="text-muted-foreground">
            Manage user groups with SCIM synchronization and manual membership
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <IconComponent name="RefreshCw" className="h-4 w-4 mr-2" />
            Sync All
          </Button>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <IconComponent name="Plus" className="h-4 w-4 mr-2" />
                Create Group
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create User Group</DialogTitle>
                <DialogDescription>
                  Create a new user group for organizing team members and permissions.
                </DialogDescription>
              </DialogHeader>
              <GroupBuilder
                onSave={handleCreateGroup}
                onCancel={() => setIsCreateDialogOpen(false)}
              />
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Groups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{groups.length}</div>
            <p className="text-xs text-muted-foreground">User groups</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center">
              <IconComponent name="Sync" className="h-4 w-4 mr-1" />
              SCIM Synced
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scimGroups}</div>
            <p className="text-xs text-muted-foreground">Auto-synced groups</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Manual Groups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{manualGroups}</div>
            <p className="text-xs text-muted-foreground">Manually managed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Members</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalMembers}</div>
            <p className="text-xs text-muted-foreground">Across all groups</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 overflow-hidden">
        <GroupTable
          groups={groups}
          onEdit={setEditingGroup}
          onDelete={handleDeleteGroup}
          onViewMembers={setViewMembersGroup}
          onSync={handleSyncGroup}
        />
      </div>

      {/* Edit Group Dialog */}
      <Dialog open={!!editingGroup} onOpenChange={() => setEditingGroup(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Group: {editingGroup?.name}</DialogTitle>
            <DialogDescription>
              Modify group settings and membership.
            </DialogDescription>
          </DialogHeader>
          {editingGroup && (
            <GroupBuilder
              group={editingGroup}
              onSave={handleUpdateGroup}
              onCancel={() => setEditingGroup(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* View Members Dialog */}
      {viewMembersGroup && (
        <GroupMembersDialog
          group={viewMembersGroup}
          isOpen={!!viewMembersGroup}
          onClose={() => setViewMembersGroup(null)}
        />
      )}
    </div>
  );
}
/**
 * Group and Group Membership Types
 */

export interface Group {
  id: string;
  name: string;
  description: string | null;
  organization_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateGroupRequest {
  name: string;
  description?: string;
  organization_id?: string;
}

export interface UpdateGroupRequest {
  name?: string;
  description?: string;
}

export interface AddMemberRequest {
  user_id: string;
}

/**
 * API client for Group Management
 */

import axios from "axios";
import type {
  AddMemberRequest,
  CreateGroupRequest,
  Group,
  UpdateGroupRequest,
} from "../types/groups";

const API_BASE = "/api/v1/groups";

// Group operations
export async function createGroup(request: CreateGroupRequest): Promise<Group> {
  const response = await axios.post<Group>(API_BASE, request);
  return response.data;
}

export async function listGroups(
  organizationId?: string,
  limit?: number
): Promise<Group[]> {
  const response = await axios.get<Group[]>(API_BASE, {
    params: {
      organization_id: organizationId,
      limit,
    },
  });
  return response.data;
}

export async function getGroup(groupId: string): Promise<Group> {
  const response = await axios.get<Group>(`${API_BASE}/${groupId}`);
  return response.data;
}

export async function updateGroup(
  groupId: string,
  request: UpdateGroupRequest
): Promise<Group> {
  const response = await axios.patch<Group>(`${API_BASE}/${groupId}`, request);
  return response.data;
}

export async function deleteGroup(groupId: string): Promise<void> {
  await axios.delete(`${API_BASE}/${groupId}`);
}

// Group membership operations
export async function addMemberToGroup(
  groupId: string,
  request: AddMemberRequest
): Promise<{ message: string }> {
  const response = await axios.post<{ message: string }>(
    `${API_BASE}/${groupId}/members`,
    request
  );
  return response.data;
}

export async function removeMemberFromGroup(
  groupId: string,
  userId: string
): Promise<void> {
  await axios.delete(`${API_BASE}/${groupId}/members/${userId}`);
}

export async function getGroupMembers(groupId: string): Promise<string[]> {
  const response = await axios.get<string[]>(`${API_BASE}/${groupId}/members`);
  return response.data;
}

export async function getUserGroups(userId: string): Promise<string[]> {
  const response = await axios.get<string[]>(`${API_BASE}/users/${userId}/groups`);
  return response.data;
}

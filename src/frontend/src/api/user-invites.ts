/**
 * User Invites API Client
 */

import axios from "axios";
import type {
  AcceptInviteRequest,
  InviteCreate,
  InviteResponse,
  InviteStatus,
  RevokeInviteRequest,
} from "../types/user-invites";

const API_BASE = "/api/v1/invites";

export async function createInvite(data: InviteCreate): Promise<InviteResponse> {
  const response = await axios.post<InviteResponse>(API_BASE, data);
  return response.data;
}

export async function listInvites(
  status?: InviteStatus,
  skip: number = 0,
  limit: number = 100
): Promise<InviteResponse[]> {
  const response = await axios.get<InviteResponse[]>(API_BASE, {
    params: { status, skip, limit },
  });
  return response.data;
}

export async function acceptInvite(
  token: string,
  data: AcceptInviteRequest
): Promise<{ message: string; user_id: string }> {
  const response = await axios.post(`${API_BASE}/${token}/accept`, data);
  return response.data;
}

export async function revokeInvite(
  inviteId: string,
  data: RevokeInviteRequest
): Promise<InviteResponse> {
  const response = await axios.post<InviteResponse>(
    `${API_BASE}/${inviteId}/revoke`,
    data
  );
  return response.data;
}

export async function deleteInvite(inviteId: string): Promise<void> {
  await axios.delete(`${API_BASE}/${inviteId}`);
}

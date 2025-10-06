/**
 * API client for Access Reviews
 */

import axios from "axios";
import type {
  AccessAnomaly,
  AccessReviewCampaign,
  AccessReviewItem,
  BulkReviewRequest,
  CreateCampaignRequest,
  ReviewDecisionRequest,
} from "../types/access-reviews";

const API_BASE = "/api/v1/access-reviews";

// Campaign operations
export async function createCampaign(
  request: CreateCampaignRequest
): Promise<AccessReviewCampaign> {
  const response = await axios.post<AccessReviewCampaign>(
    `${API_BASE}/campaigns`,
    request
  );
  return response.data;
}

export async function listCampaigns(
  status?: string,
  createdBy?: string,
  activeOnly?: boolean
): Promise<AccessReviewCampaign[]> {
  const response = await axios.get<AccessReviewCampaign[]>(
    `${API_BASE}/campaigns`,
    {
      params: { status, created_by: createdBy, active_only: activeOnly },
    }
  );
  return response.data;
}

export async function getCampaign(
  campaignId: string
): Promise<AccessReviewCampaign> {
  const response = await axios.get<AccessReviewCampaign>(
    `${API_BASE}/campaigns/${campaignId}`
  );
  return response.data;
}

export async function updateCampaignStatus(
  campaignId: string,
  status: string
): Promise<AccessReviewCampaign> {
  const response = await axios.patch<AccessReviewCampaign>(
    `${API_BASE}/campaigns/${campaignId}/status`,
    null,
    {
      params: { status },
    }
  );
  return response.data;
}

// Review item operations
export async function listCampaignItems(
  campaignId: string,
  status?: string,
  reviewerId?: string
): Promise<AccessReviewItem[]> {
  const response = await axios.get<AccessReviewItem[]>(
    `${API_BASE}/campaigns/${campaignId}/items`,
    {
      params: { status, reviewer_id: reviewerId },
    }
  );
  return response.data;
}

export async function getReviewItem(
  itemId: string
): Promise<AccessReviewItem> {
  const response = await axios.get<AccessReviewItem>(
    `${API_BASE}/items/${itemId}`
  );
  return response.data;
}

export async function reviewItem(
  itemId: string,
  request: ReviewDecisionRequest
): Promise<AccessReviewItem> {
  const response = await axios.post<AccessReviewItem>(
    `${API_BASE}/items/${itemId}/review`,
    request
  );
  return response.data;
}

export async function bulkReviewItems(
  request: BulkReviewRequest
): Promise<{ reviewed_count: number; message: string }> {
  const response = await axios.post<{ reviewed_count: number; message: string }>(
    `${API_BASE}/items/bulk-review`,
    request
  );
  return response.data;
}

export async function processOverdueReviews(): Promise<{
  revoked_count: number;
  message: string;
}> {
  const response = await axios.post<{ revoked_count: number; message: string }>(
    `${API_BASE}/process-overdue`
  );
  return response.data;
}

// Anomaly operations
export async function listAnomalies(
  status?: string,
  severity?: string,
  anomalyType?: string,
  principalId?: string,
  limit?: number
): Promise<AccessAnomaly[]> {
  const response = await axios.get<AccessAnomaly[]>(
    `${API_BASE}/anomalies`,
    {
      params: {
        status,
        severity,
        anomaly_type: anomalyType,
        principal_id: principalId,
        limit,
      },
    }
  );
  return response.data;
}

export async function getAnomaly(anomalyId: string): Promise<AccessAnomaly> {
  const response = await axios.get<AccessAnomaly>(
    `${API_BASE}/anomalies/${anomalyId}`
  );
  return response.data;
}

export async function resolveAnomaly(
  anomalyId: string,
  status: string,
  resolutionNotes?: string
): Promise<AccessAnomaly> {
  const response = await axios.post<AccessAnomaly>(
    `${API_BASE}/anomalies/${anomalyId}/resolve`,
    {
      status,
      resolution_notes: resolutionNotes,
    }
  );
  return response.data;
}

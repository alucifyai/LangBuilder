/**
 * Access Review Types
 * Periodic access certification and anomaly detection
 */

export interface AccessReviewCampaign {
  id: string;
  name: string;
  description: string | null;
  campaign_type: string;
  scope_type: string;
  scope_id: string | null;
  start_date: string;
  due_date: string;
  status: string;
  total_items: number;
  reviewed_items: number;
  approved_items: number;
  revoked_items: number;
  created_by: string;
  reviewers: string[];
  compliance_framework: string | null;
  auto_revoke_on_no_response: boolean;
  is_recurring: boolean;
  recurrence_interval_days: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface AccessReviewItem {
  id: string;
  campaign_id: string;
  grant_id: string;
  principal_id: string;
  principal_email: string | null;
  role_id: string;
  role_name: string | null;
  resource_type: string | null;
  resource_id: string | null;
  status: string;
  reviewer_id: string | null;
  reviewed_at: string | null;
  decision: string | null;
  justification: string | null;
  last_used_at: string | null;
  usage_count: number;
  anomaly_score: number | null;
  anomaly_reasons: string[] | null;
  risk_level: string;
  created_at: string;
  updated_at: string;
}

export interface AccessAnomaly {
  id: string;
  anomaly_type: string;
  severity: string;
  confidence: number;
  principal_id: string;
  principal_email: string | null;
  grant_id: string | null;
  title: string;
  description: string;
  evidence: Record<string, any> | null;
  recommendations: string[] | null;
  status: string;
  assigned_to: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  detected_at: string;
  updated_at: string;
}

export interface CreateCampaignRequest {
  name: string;
  start_date: string;
  due_date: string;
  scope_type?: string;
  scope_id?: string;
  description?: string;
  campaign_type?: string;
  reviewers?: string[];
  compliance_framework?: string;
  auto_revoke_on_no_response?: boolean;
  is_recurring?: boolean;
  recurrence_interval_days?: number;
}

export interface ReviewDecisionRequest {
  decision: "approve" | "revoke";
  justification?: string;
}

export interface BulkReviewRequest {
  item_ids: string[];
  decision: "approve" | "revoke";
  justification?: string;
}

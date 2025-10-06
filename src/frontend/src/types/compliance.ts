/**
 * Compliance Report Types
 * SOC2, GDPR, ISO 27001 compliance reporting
 */

export interface ComplianceReport {
  id: string;
  name: string;
  report_type: string;
  framework_version: string | null;
  description: string | null;
  period_start: string;
  period_end: string;
  status: string;
  completion_percentage: number;
  summary: Record<string, any> | null;
  findings: Array<Record<string, any>> | null;
  recommendations: Array<Record<string, any>> | null;
  controls: Array<Record<string, any>> | null;
  metrics: Record<string, any> | null;
  generated_by: string;
  organization_id: string | null;
  attestation_required: boolean;
  attested_by: string | null;
  attested_at: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface ComplianceControl {
  id: string;
  control_id: string;
  framework: string;
  category: string;
  name: string;
  description: string;
  requirements: string[];
  implementation_status: string;
  implementation_notes: string | null;
  responsible_party: string | null;
  evidence_required: boolean;
  evidence_items: string[] | null;
  last_tested_at: string | null;
  test_frequency_days: number | null;
  test_results: Record<string, any> | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GenerateReportRequest {
  name: string;
  report_type: "soc2" | "gdpr" | "iso27001" | "custom" | "access";
  period_start: string;
  period_end: string;
  framework_version?: string;
  description?: string;
  organization_id?: string;
}

export interface UpdateControlRequest {
  implementation_status: string;
  implementation_notes?: string;
}

export interface RecordTestRequest {
  test_results: Record<string, any>;
}

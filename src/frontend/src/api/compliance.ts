/**
 * API client for Compliance Reports
 */

import axios from "axios";
import type {
  ComplianceControl,
  ComplianceReport,
  GenerateReportRequest,
  RecordTestRequest,
  UpdateControlRequest,
} from "../types/compliance";

const API_BASE = "/api/v1/compliance";

// Report operations
export async function generateReport(
  request: GenerateReportRequest
): Promise<ComplianceReport> {
  const response = await axios.post<ComplianceReport>(
    `${API_BASE}/reports`,
    request
  );
  return response.data;
}

export async function listReports(
  reportType?: string,
  status?: string,
  organizationId?: string,
  limit?: number
): Promise<ComplianceReport[]> {
  const response = await axios.get<ComplianceReport[]>(`${API_BASE}/reports`, {
    params: {
      report_type: reportType,
      status,
      organization_id: organizationId,
      limit,
    },
  });
  return response.data;
}

export async function getReport(reportId: string): Promise<ComplianceReport> {
  const response = await axios.get<ComplianceReport>(
    `${API_BASE}/reports/${reportId}`
  );
  return response.data;
}

export async function attestReport(
  reportId: string
): Promise<ComplianceReport> {
  const response = await axios.post<ComplianceReport>(
    `${API_BASE}/reports/${reportId}/attest`
  );
  return response.data;
}

// Control operations
export async function listControls(
  framework?: string,
  implementationStatus?: string,
  activeOnly?: boolean
): Promise<ComplianceControl[]> {
  const response = await axios.get<ComplianceControl[]>(
    `${API_BASE}/controls`,
    {
      params: {
        framework,
        implementation_status: implementationStatus,
        active_only: activeOnly,
      },
    }
  );
  return response.data;
}

export async function getControl(
  controlId: string
): Promise<ComplianceControl> {
  const response = await axios.get<ComplianceControl>(
    `${API_BASE}/controls/${controlId}`
  );
  return response.data;
}

export async function updateControlImplementation(
  controlId: string,
  request: UpdateControlRequest
): Promise<ComplianceControl> {
  const response = await axios.patch<ComplianceControl>(
    `${API_BASE}/controls/${controlId}/implementation`,
    request
  );
  return response.data;
}

export async function recordControlTest(
  controlId: string,
  request: RecordTestRequest
): Promise<ComplianceControl> {
  const response = await axios.post<ComplianceControl>(
    `${API_BASE}/controls/${controlId}/test`,
    request
  );
  return response.data;
}

export async function seedSOC2Controls(): Promise<{ message: string }> {
  const response = await axios.post<{ message: string }>(
    `${API_BASE}/seed/soc2-controls`
  );
  return response.data;
}

/**
 * Compliance Reports List
 * Display and manage compliance reports
 */

import React, { useState, useEffect } from "react";
import type { ComplianceReport } from "../../types/compliance";
import { listReports, attestReport } from "../../api/compliance";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Progress } from "../ui/progress";

interface ComplianceReportsListProps {
  onGenerateClick: () => void;
}

export function ComplianceReportsList({
  onGenerateClick,
}: ComplianceReportsListProps) {
  const [reports, setReports] = useState<ComplianceReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ComplianceReport | null>(
    null
  );
  const [isAttestModalOpen, setIsAttestModalOpen] = useState(false);
  const [filter, setFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    loadReports();
  }, [filter]);

  const loadReports = async () => {
    setLoading(true);
    try {
      const data = await listReports(filter, undefined, undefined, 100);
      setReports(data);
    } catch (error) {
      console.error("Failed to load reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "warning" | "destructive"> = {
      draft: "default",
      in_progress: "warning",
      completed: "default",
      attested: "default",
    };
    return (
      <Badge variant={variants[status] || "default"}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  const getReportTypeBadge = (reportType: string) => {
    const colors: Record<string, string> = {
      soc2: "bg-blue-100 text-blue-800",
      gdpr: "bg-green-100 text-green-800",
      iso27001: "bg-purple-100 text-purple-800",
      access: "bg-orange-100 text-orange-800",
      custom: "bg-gray-100 text-gray-800",
    };
    return (
      <Badge
        className={colors[reportType] || colors.custom}
        variant="outline"
      >
        {reportType.toUpperCase()}
      </Badge>
    );
  };

  const handleAttest = (report: ComplianceReport) => {
    setSelectedReport(report);
    setIsAttestModalOpen(true);
  };

  const handleAttestSubmit = async () => {
    if (!selectedReport) return;

    try {
      await attestReport(selectedReport.id);
      setIsAttestModalOpen(false);
      setSelectedReport(null);
      loadReports();
    } catch (error) {
      console.error("Failed to attest report:", error);
      alert("Failed to attest report");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Compliance Reports</h2>
          <p className="text-sm text-gray-500 mt-1">
            Generate and manage compliance reports for various frameworks
          </p>
        </div>
        <Button onClick={onGenerateClick}>Generate Report</Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setFilter(undefined)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === undefined
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter("soc2")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "soc2"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          SOC2
        </button>
        <button
          onClick={() => setFilter("gdpr")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "gdpr"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          GDPR
        </button>
        <button
          onClick={() => setFilter("iso27001")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "iso27001"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          ISO 27001
        </button>
        <button
          onClick={() => setFilter("access")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "access"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Access
        </button>
      </div>

      {/* Reports Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Period</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : reports.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-gray-500">
                  No reports found
                </TableCell>
              </TableRow>
            ) : (
              reports.map((report) => (
                <TableRow key={report.id}>
                  <TableCell className="font-medium max-w-xs truncate">
                    {report.name}
                  </TableCell>
                  <TableCell>{getReportTypeBadge(report.report_type)}</TableCell>
                  <TableCell className="text-sm">
                    {new Date(report.period_start).toLocaleDateString()} -{" "}
                    {new Date(report.period_end).toLocaleDateString()}
                  </TableCell>
                  <TableCell>{getStatusBadge(report.status)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Progress
                        value={report.completion_percentage}
                        className="w-24"
                      />
                      <span className="text-sm">
                        {report.completion_percentage}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm">
                    {new Date(report.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {report.attestation_required && !report.attested_at && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleAttest(report)}
                      >
                        Attest
                      </Button>
                    )}
                    {report.attested_at && (
                      <Badge variant="default">Attested</Badge>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Attest Modal */}
      <Dialog open={isAttestModalOpen} onOpenChange={setIsAttestModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Attest Compliance Report</DialogTitle>
            <DialogDescription>
              By attesting this report, you certify that the information is
              accurate and complete
            </DialogDescription>
          </DialogHeader>

          {selectedReport && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-gray-50 p-4">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-semibold">{selectedReport.name}</p>
                  {getReportTypeBadge(selectedReport.report_type)}
                </div>
                <p className="text-sm text-gray-600">
                  Period: {new Date(selectedReport.period_start).toLocaleDateString()}{" "}
                  - {new Date(selectedReport.period_end).toLocaleDateString()}
                </p>
                {selectedReport.description && (
                  <p className="text-sm text-gray-600 mt-2">
                    {selectedReport.description}
                  </p>
                )}
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-sm text-yellow-800">
                  <strong>Warning:</strong> Attestation creates an immutable
                  record with your identity and timestamp. This action cannot be
                  undone.
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsAttestModalOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleAttestSubmit}>Attest Report</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * Anomaly Dashboard
 * Display and manage detected access anomalies
 */

import React, { useState, useEffect } from "react";
import type { AccessAnomaly } from "../../types/access-reviews";
import { listAnomalies, resolveAnomaly } from "../../api/access-reviews";
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
import { Textarea } from "../ui/textarea";
import { Label } from "../ui/label";

export function AnomalyDashboard() {
  const [anomalies, setAnomalies] = useState<AccessAnomaly[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAnomaly, setSelectedAnomaly] = useState<AccessAnomaly | null>(null);
  const [isResolveModalOpen, setIsResolveModalOpen] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [filter, setFilter] = useState<"all" | "open" | "resolved">("open");

  useEffect(() => {
    loadAnomalies();
  }, [filter]);

  const loadAnomalies = async () => {
    setLoading(true);
    try {
      const data = await listAnomalies(
        filter === "all" ? undefined : filter,
        undefined,
        undefined,
        undefined,
        100
      );
      setAnomalies(data);
    } catch (error) {
      console.error("Failed to load anomalies:", error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, "default" | "warning" | "destructive"> = {
      low: "default",
      medium: "warning",
      high: "destructive",
      critical: "destructive",
    };
    return (
      <Badge variant={variants[severity] || "default"}>
        {severity.toUpperCase()}
      </Badge>
    );
  };

  const handleResolve = (anomaly: AccessAnomaly) => {
    setSelectedAnomaly(anomaly);
    setIsResolveModalOpen(true);
  };

  const handleResolveSubmit = async (status: "resolved" | "false_positive") => {
    if (!selectedAnomaly) return;

    try {
      await resolveAnomaly(selectedAnomaly.id, status, resolutionNotes);
      setIsResolveModalOpen(false);
      setResolutionNotes("");
      setSelectedAnomaly(null);
      loadAnomalies();
    } catch (error) {
      console.error("Failed to resolve anomaly:", error);
      alert("Failed to resolve anomaly");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Access Anomalies</h2>
          <p className="text-sm text-gray-500 mt-1">
            Detected unusual access patterns requiring investigation
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setFilter("open")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "open"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Open
        </button>
        <button
          onClick={() => setFilter("resolved")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "resolved"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Resolved
        </button>
        <button
          onClick={() => setFilter("all")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "all"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          All
        </button>
      </div>

      {/* Anomalies Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Detected</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Title</TableHead>
              <TableHead>Principal</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : anomalies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-gray-500">
                  No anomalies found
                </TableCell>
              </TableRow>
            ) : (
              anomalies.map((anomaly) => (
                <TableRow key={anomaly.id}>
                  <TableCell className="text-sm">
                    {new Date(anomaly.detected_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>{getSeverityBadge(anomaly.severity)}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{anomaly.anomaly_type}</Badge>
                  </TableCell>
                  <TableCell className="font-medium max-w-xs truncate">
                    {anomaly.title}
                  </TableCell>
                  <TableCell className="text-sm">
                    {anomaly.principal_email || anomaly.principal_id}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${anomaly.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">
                        {Math.round(anomaly.confidence * 100)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={anomaly.status === "open" ? "warning" : "default"}
                    >
                      {anomaly.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {anomaly.status === "open" && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleResolve(anomaly)}
                      >
                        Resolve
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Resolve Modal */}
      <Dialog open={isResolveModalOpen} onOpenChange={setIsResolveModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Resolve Anomaly</DialogTitle>
            <DialogDescription>
              Mark this anomaly as resolved or a false positive
            </DialogDescription>
          </DialogHeader>

          {selectedAnomaly && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-gray-50 p-3">
                <p className="font-semibold">{selectedAnomaly.title}</p>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedAnomaly.description}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="resolution-notes">Resolution Notes</Label>
                <Textarea
                  id="resolution-notes"
                  placeholder="Describe how this was resolved..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsResolveModalOpen(false)}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => handleResolveSubmit("false_positive")}
            >
              Mark as False Positive
            </Button>
            <Button onClick={() => handleResolveSubmit("resolved")}>
              Mark as Resolved
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

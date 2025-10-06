/**
 * Compliance Controls Manager
 * Manage security control library and testing
 */

import React, { useState, useEffect } from "react";
import type { ComplianceControl } from "../../types/compliance";
import {
  listControls,
  updateControlImplementation,
  recordControlTest,
  seedSOC2Controls,
} from "../../api/compliance";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Textarea } from "../ui/textarea";
import { Label } from "../ui/label";

export function ComplianceControlsManager() {
  const [controls, setControls] = useState<ComplianceControl[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedControl, setSelectedControl] =
    useState<ComplianceControl | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [implementationStatus, setImplementationStatus] = useState("");
  const [implementationNotes, setImplementationNotes] = useState("");
  const [testResults, setTestResults] = useState("");
  const [frameworkFilter, setFrameworkFilter] = useState<string | undefined>(
    undefined
  );

  useEffect(() => {
    loadControls();
  }, [frameworkFilter]);

  const loadControls = async () => {
    setLoading(true);
    try {
      const data = await listControls(frameworkFilter, undefined, true);
      setControls(data);
    } catch (error) {
      console.error("Failed to load controls:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedSOC2 = async () => {
    try {
      await seedSOC2Controls();
      alert("SOC2 controls seeded successfully");
      loadControls();
    } catch (error) {
      console.error("Failed to seed SOC2 controls:", error);
      alert("Failed to seed SOC2 controls");
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<
      string,
      "default" | "warning" | "destructive" | "outline"
    > = {
      not_implemented: "destructive",
      planned: "warning",
      in_progress: "warning",
      implemented: "default",
      tested: "default",
    };
    return (
      <Badge variant={variants[status] || "default"}>
        {status.replace("_", " ").toUpperCase()}
      </Badge>
    );
  };

  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      "Access Control": "bg-blue-100 text-blue-800",
      Authentication: "bg-green-100 text-green-800",
      "Change Management": "bg-purple-100 text-purple-800",
      "System Operations": "bg-orange-100 text-orange-800",
      "Risk Mitigation": "bg-red-100 text-red-800",
    };
    return (
      <Badge
        className={colors[category] || "bg-gray-100 text-gray-800"}
        variant="outline"
      >
        {category}
      </Badge>
    );
  };

  const handleUpdateImplementation = (control: ComplianceControl) => {
    setSelectedControl(control);
    setImplementationStatus(control.implementation_status);
    setImplementationNotes(control.implementation_notes || "");
    setIsUpdateModalOpen(true);
  };

  const handleRecordTest = (control: ComplianceControl) => {
    setSelectedControl(control);
    setTestResults("");
    setIsTestModalOpen(true);
  };

  const handleUpdateSubmit = async () => {
    if (!selectedControl) return;

    try {
      await updateControlImplementation(selectedControl.id, {
        implementation_status: implementationStatus,
        implementation_notes: implementationNotes,
      });
      setIsUpdateModalOpen(false);
      setSelectedControl(null);
      loadControls();
    } catch (error) {
      console.error("Failed to update control:", error);
      alert("Failed to update control");
    }
  };

  const handleTestSubmit = async () => {
    if (!selectedControl) return;

    try {
      let parsedResults;
      try {
        parsedResults = JSON.parse(testResults);
      } catch {
        parsedResults = { notes: testResults, timestamp: new Date().toISOString() };
      }

      await recordControlTest(selectedControl.id, {
        test_results: parsedResults,
      });
      setIsTestModalOpen(false);
      setSelectedControl(null);
      loadControls();
    } catch (error) {
      console.error("Failed to record test:", error);
      alert("Failed to record test");
    }
  };

  const getTestStatus = (control: ComplianceControl) => {
    if (!control.last_tested_at) return "Never tested";

    const lastTested = new Date(control.last_tested_at);
    const daysSinceTest = Math.floor(
      (Date.now() - lastTested.getTime()) / (1000 * 60 * 60 * 24)
    );

    if (control.test_frequency_days && daysSinceTest > control.test_frequency_days) {
      return <Badge variant="destructive">Overdue</Badge>;
    }

    return (
      <span className="text-sm text-gray-600">
        {lastTested.toLocaleDateString()} ({daysSinceTest}d ago)
      </span>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Compliance Controls</h2>
          <p className="text-sm text-gray-500 mt-1">
            Manage security control library and testing schedule
          </p>
        </div>
        <Button onClick={handleSeedSOC2} variant="outline">
          Seed SOC2 Controls
        </Button>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setFrameworkFilter(undefined)}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            frameworkFilter === undefined
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFrameworkFilter("SOC2")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            frameworkFilter === "SOC2"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          SOC2
        </button>
        <button
          onClick={() => setFrameworkFilter("ISO27001")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            frameworkFilter === "ISO27001"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          ISO 27001
        </button>
        <button
          onClick={() => setFrameworkFilter("GDPR")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            frameworkFilter === "GDPR"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          GDPR
        </button>
      </div>

      {/* Controls Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Control ID</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Tested</TableHead>
              <TableHead>Responsible</TableHead>
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
            ) : controls.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-gray-500">
                  No controls found. Click "Seed SOC2 Controls" to get started.
                </TableCell>
              </TableRow>
            ) : (
              controls.map((control) => (
                <TableRow key={control.id}>
                  <TableCell className="font-mono text-sm">
                    {control.control_id}
                  </TableCell>
                  <TableCell>{getCategoryBadge(control.category)}</TableCell>
                  <TableCell className="max-w-xs truncate">
                    {control.name}
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(control.implementation_status)}
                  </TableCell>
                  <TableCell>{getTestStatus(control)}</TableCell>
                  <TableCell className="text-sm">
                    {control.responsible_party || "Unassigned"}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleUpdateImplementation(control)}
                      >
                        Update
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRecordTest(control)}
                      >
                        Test
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Update Implementation Modal */}
      <Dialog open={isUpdateModalOpen} onOpenChange={setIsUpdateModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Control Implementation</DialogTitle>
            <DialogDescription>
              Update the implementation status and notes for this control
            </DialogDescription>
          </DialogHeader>

          {selectedControl && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-gray-50 p-3">
                <p className="font-semibold">
                  {selectedControl.control_id}: {selectedControl.name}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedControl.description}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="implementation_status">
                  Implementation Status
                </Label>
                <Select
                  value={implementationStatus}
                  onValueChange={setImplementationStatus}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="not_implemented">
                      Not Implemented
                    </SelectItem>
                    <SelectItem value="planned">Planned</SelectItem>
                    <SelectItem value="in_progress">In Progress</SelectItem>
                    <SelectItem value="implemented">Implemented</SelectItem>
                    <SelectItem value="tested">Tested</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="implementation_notes">
                  Implementation Notes
                </Label>
                <Textarea
                  id="implementation_notes"
                  placeholder="Describe the implementation approach..."
                  value={implementationNotes}
                  onChange={(e) => setImplementationNotes(e.target.value)}
                  rows={4}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsUpdateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdateSubmit}>Update Control</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Record Test Modal */}
      <Dialog open={isTestModalOpen} onOpenChange={setIsTestModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Control Test</DialogTitle>
            <DialogDescription>
              Document the results of testing this control
            </DialogDescription>
          </DialogHeader>

          {selectedControl && (
            <div className="space-y-4">
              <div className="rounded-lg border bg-gray-50 p-3">
                <p className="font-semibold">
                  {selectedControl.control_id}: {selectedControl.name}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {selectedControl.description}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="test_results">Test Results</Label>
                <Textarea
                  id="test_results"
                  placeholder='Enter JSON or plain text. E.g., {"status": "passed", "findings": "No issues"}'
                  value={testResults}
                  onChange={(e) => setTestResults(e.target.value)}
                  rows={6}
                />
                <p className="text-xs text-gray-500">
                  Enter JSON for structured results or plain text for notes
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsTestModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleTestSubmit}>Record Test</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

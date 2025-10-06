/**
 * Security Dashboard
 * Overview of security events and anomalies
 */

import React, { useState, useEffect } from "react";
import type { SecurityEventsSummary, FailedAuthByIP } from "../../types/audit-logs";
import { getSecurityEvents, getFailedAuthAttempts } from "../../api/audit-logs";
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

export function SecurityDashboard() {
  const [summary, setSummary] = useState<SecurityEventsSummary | null>(null);
  const [failedAuth, setFailedAuth] = useState<FailedAuthByIP>({});
  const [loading, setLoading] = useState(false);
  const [timeRange, setTimeRange] = useState(24);

  useEffect(() => {
    loadSecurityData();
  }, [timeRange]);

  const loadSecurityData = async () => {
    setLoading(true);
    try {
      const [summaryData, failedAuthData] = await Promise.all([
        getSecurityEvents(timeRange),
        getFailedAuthAttempts(timeRange, 3),
      ]);
      setSummary(summaryData);
      setFailedAuth(failedAuthData);
    } catch (error) {
      console.error("Failed to load security data:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Security Dashboard</h2>
          <p className="text-sm text-gray-500 mt-1">
            Security events and anomaly detection
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={timeRange === 24 ? "default" : "outline"}
            onClick={() => setTimeRange(24)}
          >
            24h
          </Button>
          <Button
            variant={timeRange === 72 ? "default" : "outline"}
            onClick={() => setTimeRange(72)}
          >
            72h
          </Button>
          <Button
            variant={timeRange === 168 ? "default" : "outline"}
            onClick={() => setTimeRange(168)}
          >
            7d
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-5 gap-4">
          <div className="border rounded-lg p-4">
            <p className="text-sm text-gray-600">Total Events</p>
            <p className="text-3xl font-bold mt-1">{summary.total_events}</p>
          </div>
          <div className="border rounded-lg p-4 bg-red-50">
            <p className="text-sm text-red-600">Critical</p>
            <p className="text-3xl font-bold mt-1 text-red-700">
              {summary.critical_count}
            </p>
          </div>
          <div className="border rounded-lg p-4 bg-orange-50">
            <p className="text-sm text-orange-600">Errors</p>
            <p className="text-3xl font-bold mt-1 text-orange-700">
              {summary.error_count}
            </p>
          </div>
          <div className="border rounded-lg p-4 bg-yellow-50">
            <p className="text-sm text-yellow-600">Warnings</p>
            <p className="text-3xl font-bold mt-1 text-yellow-700">
              {summary.warning_count}
            </p>
          </div>
          <div className="border rounded-lg p-4 bg-blue-50">
            <p className="text-sm text-blue-600">Failed Auth</p>
            <p className="text-3xl font-bold mt-1 text-blue-700">
              {summary.failed_auth_count}
            </p>
          </div>
        </div>
      )}

      {/* Failed Authentication Attempts */}
      <div className="border rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">
          Suspicious Failed Login Attempts
        </h3>
        {Object.keys(failedAuth).length === 0 ? (
          <p className="text-gray-500 text-center py-4">
            No suspicious failed login attempts detected
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>IP Address</TableHead>
                <TableHead>Attempt Count</TableHead>
                <TableHead>First Attempt</TableHead>
                <TableHead>Last Attempt</TableHead>
                <TableHead>Risk Level</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(failedAuth).map(([ip, data]) => (
                <TableRow key={ip}>
                  <TableCell className="font-mono">{ip}</TableCell>
                  <TableCell>
                    <Badge variant="destructive">{data.count}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatTimestamp(data.first_attempt)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatTimestamp(data.last_attempt)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        data.count >= 10
                          ? "destructive"
                          : data.count >= 5
                          ? "warning"
                          : "default"
                      }
                    >
                      {data.count >= 10
                        ? "High"
                        : data.count >= 5
                        ? "Medium"
                        : "Low"}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Recent Security Events */}
      <div className="border rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-4">Recent Security Events</h3>
        {summary && summary.events.length === 0 ? (
          <p className="text-gray-500 text-center py-4">
            No security events in the selected time range
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Event</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Severity</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {summary?.events.slice(0, 10).map((event) => (
                <TableRow key={event.id}>
                  <TableCell className="text-sm">
                    {formatTimestamp(event.timestamp)}
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{event.event_type}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {event.action}
                  </TableCell>
                  <TableCell className="text-sm">
                    {event.actor_email || event.actor_id || "-"}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        event.severity === "critical"
                          ? "destructive"
                          : event.severity === "error"
                          ? "destructive"
                          : event.severity === "warning"
                          ? "warning"
                          : "default"
                      }
                    >
                      {event.severity}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        event.status === "success" ? "success" : "destructive"
                      }
                    >
                      {event.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}

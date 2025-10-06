/**
 * Access Review Campaigns Component
 * Manage periodic access certification campaigns
 */

import React, { useState, useEffect } from "react";
import type { AccessReviewCampaign } from "../../types/access-reviews";
import {
  listCampaigns,
  updateCampaignStatus,
} from "../../api/access-reviews";
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
import { CreateCampaignModal } from "./CreateCampaignModal";
import { useNavigate } from "react-router-dom";

export function AccessReviewCampaigns() {
  const [campaigns, setCampaigns] = useState<AccessReviewCampaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");
  const navigate = useNavigate();

  useEffect(() => {
    loadCampaigns();
  }, [filter]);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const data = await listCampaigns(
        filter === "all" ? undefined : filter,
        undefined,
        filter === "active"
      );
      setCampaigns(data);
    } catch (error) {
      console.error("Failed to load campaigns:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (campaign: AccessReviewCampaign) => {
    const variants: Record<string, "default" | "success" | "warning" | "destructive"> = {
      draft: "default",
      active: "warning",
      completed: "success",
      cancelled: "destructive",
    };
    return (
      <Badge variant={variants[campaign.status] || "default"}>
        {campaign.status.toUpperCase()}
      </Badge>
    );
  };

  const getProgressPercentage = (campaign: AccessReviewCampaign) => {
    if (campaign.total_items === 0) return 0;
    return Math.round((campaign.reviewed_items / campaign.total_items) * 100);
  };

  const handleActivateCampaign = async (campaignId: string) => {
    try {
      await updateCampaignStatus(campaignId, "active");
      loadCampaigns();
    } catch (error) {
      console.error("Failed to activate campaign:", error);
      alert("Failed to activate campaign");
    }
  };

  const handleCompleteCampaign = async (campaignId: string) => {
    if (!confirm("Are you sure you want to complete this campaign?")) return;

    try {
      await updateCampaignStatus(campaignId, "completed");
      loadCampaigns();
    } catch (error) {
      console.error("Failed to complete campaign:", error);
      alert("Failed to complete campaign");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Access Review Campaigns</h2>
          <p className="text-sm text-gray-500 mt-1">
            Periodic access certification for compliance
          </p>
        </div>
        <CreateCampaignModal onCampaignCreated={loadCampaigns} />
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setFilter("all")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "all"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          All Campaigns
        </button>
        <button
          onClick={() => setFilter("active")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "active"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Active
        </button>
        <button
          onClick={() => setFilter("completed")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            filter === "completed"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Completed
        </button>
      </div>

      {/* Campaigns Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Due Date</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Items</TableHead>
              <TableHead>Framework</TableHead>
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
            ) : campaigns.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-gray-500">
                  No campaigns found
                </TableCell>
              </TableRow>
            ) : (
              campaigns.map((campaign) => (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">{campaign.name}</TableCell>
                  <TableCell>{getStatusBadge(campaign)}</TableCell>
                  <TableCell>{formatDate(campaign.due_date)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${getProgressPercentage(campaign)}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm">
                        {getProgressPercentage(campaign)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <div>{campaign.reviewed_items} / {campaign.total_items} reviewed</div>
                      <div className="text-gray-500">
                        {campaign.approved_items} approved, {campaign.revoked_items} revoked
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    {campaign.compliance_framework ? (
                      <Badge variant="outline">
                        {campaign.compliance_framework}
                      </Badge>
                    ) : (
                      "-"
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          navigate(`/admin/access-reviews/${campaign.id}`)
                        }
                      >
                        Review Items
                      </Button>
                      {campaign.status === "draft" && (
                        <Button
                          size="sm"
                          onClick={() => handleActivateCampaign(campaign.id)}
                        >
                          Activate
                        </Button>
                      )}
                      {campaign.status === "active" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleCompleteCampaign(campaign.id)}
                        >
                          Complete
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

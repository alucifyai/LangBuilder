/**
 * Create Grant Modal
 * Assign roles to users/groups/service accounts at specific scopes
 */

import React, { useState } from "react";
import type { CreateGrantRequest } from "../../types/grants";
import { createGrant } from "../../api/grants";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";

interface CreateGrantModalProps {
  onGrantCreated: () => void;
}

export function CreateGrantModal({ onGrantCreated }: CreateGrantModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state
  const [principalType, setPrincipalType] = useState<"user" | "group" | "service_account">("user");
  const [principalId, setPrincipalId] = useState("");
  const [roleId, setRoleId] = useState("");
  const [scopeType, setScopeType] = useState<"workspace" | "project" | "environment" | "flow" | "component">("workspace");
  const [scopeId, setScopeId] = useState("");
  const [expiresAt, setExpiresAt] = useState("");

  const resetForm = () => {
    setPrincipalType("user");
    setPrincipalId("");
    setRoleId("");
    setScopeType("workspace");
    setScopeId("");
    setExpiresAt("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const request: CreateGrantRequest = {
        principal_type: principalType,
        principal_id: principalId,
        role_id: roleId,
        scope_type: scopeType,
        scope_id: scopeId,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : undefined,
      };

      await createGrant(request);
      setIsOpen(false);
      resetForm();
      onGrantCreated();
    } catch (error) {
      console.error("Failed to create grant:", error);
      alert("Failed to create grant. Please check all fields.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button>Assign Role (Create Grant)</Button>
      </DialogTrigger>

      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Assign Role to Principal</DialogTitle>
          <DialogDescription>
            Grant a role to a user, group, or service account at a specific scope
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Principal Selection */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="principal-type">
                Principal Type <span className="text-red-500">*</span>
              </Label>
              <Select
                value={principalType}
                onValueChange={(v) => setPrincipalType(v as any)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="group">Group</SelectItem>
                  <SelectItem value="service_account">Service Account</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="principal-id">
                Principal ID/Email <span className="text-red-500">*</span>
              </Label>
              <Input
                id="principal-id"
                placeholder={
                  principalType === "user"
                    ? "user@example.com"
                    : principalType === "group"
                    ? "Group ID"
                    : "Service Account ID"
                }
                value={principalId}
                onChange={(e) => setPrincipalId(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Role Selection */}
          <div className="space-y-2">
            <Label htmlFor="role-id">
              Role ID <span className="text-red-500">*</span>
            </Label>
            <Input
              id="role-id"
              placeholder="Enter role ID (e.g., viewer, editor, admin)"
              value={roleId}
              onChange={(e) => setRoleId(e.target.value)}
              required
            />
            <p className="text-sm text-gray-500">
              Tip: Use the Roles tab to find available role IDs
            </p>
          </div>

          {/* Scope Selection */}
          <div className="space-y-2">
            <Label>Scope (Where the role applies)</Label>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="scope-type">
                  Scope Type <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={scopeType}
                  onValueChange={(v) => setScopeType(v as any)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="workspace">Workspace</SelectItem>
                    <SelectItem value="project">Project</SelectItem>
                    <SelectItem value="environment">Environment</SelectItem>
                    <SelectItem value="flow">Flow</SelectItem>
                    <SelectItem value="component">Component</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="scope-id">
                  Scope ID <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="scope-id"
                  placeholder={`${scopeType.charAt(0).toUpperCase() + scopeType.slice(1)} ID`}
                  value={scopeId}
                  onChange={(e) => setScopeId(e.target.value)}
                  required
                />
              </div>
            </div>
            <p className="text-sm text-gray-500">
              Hierarchy: Workspace → Project → Environment → Flow → Component
            </p>
          </div>

          {/* Optional Expiration */}
          <div className="space-y-2">
            <Label htmlFor="expires-at">Expiration (optional)</Label>
            <Input
              id="expires-at"
              type="datetime-local"
              value={expiresAt}
              onChange={(e) => setExpiresAt(e.target.value)}
              min={new Date().toISOString().slice(0, 16)}
            />
            <p className="text-sm text-gray-500">
              Leave empty for permanent grant
            </p>
          </div>

          {/* Example */}
          <div className="rounded-lg bg-blue-50 p-3 text-sm">
            <p className="font-semibold text-blue-900">Example:</p>
            <p className="text-blue-800 mt-1">
              To give "carol@acme.com" the "Editor" role in Project "PRJ1":
            </p>
            <ul className="list-disc ml-5 mt-1 text-blue-700">
              <li>Principal Type: User</li>
              <li>Principal ID: carol@acme.com</li>
              <li>Role ID: editor</li>
              <li>Scope Type: Project</li>
              <li>Scope ID: PRJ1</li>
            </ul>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating Grant..." : "Create Grant"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

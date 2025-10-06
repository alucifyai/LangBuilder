/**
 * Delete SSO Configuration Dialog
 */

import { useState } from "react";
import { Button } from "../ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { deleteSSOConfig } from "../../api/sso";
import type { SSOConfigResponse } from "../../types/sso";
import useAlertStore from "../../stores/alertStore";

interface DeleteSSOConfigDialogProps {
  config: SSOConfigResponse;
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function DeleteSSOConfigDialog({
  config,
  open,
  onClose,
  onSuccess,
}: DeleteSSOConfigDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const setSuccessData = useAlertStore((state) => state.setSuccessData);
  const setErrorData = useAlertStore((state) => state.setErrorData);

  const handleDelete = async () => {
    setIsDeleting(true);

    try {
      await deleteSSOConfig(config.id);

      setSuccessData({
        title: "SSO Configuration Deleted",
      });

      onSuccess();
    } catch (error: any) {
      setErrorData({
        title: "Failed to delete SSO configuration",
        list: [error?.response?.data?.detail || error.message],
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete SSO Configuration</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete the SSO configuration for{" "}
            <strong>{config.domain}</strong>?
            <br />
            <br />
            This action cannot be undone. Users will no longer be able to sign in
            using SSO for this domain.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-destructive hover:bg-destructive/90"
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

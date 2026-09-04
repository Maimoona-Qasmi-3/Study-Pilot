"use client";

import React, { useState, useEffect } from "react";
import { RefreshCw, CheckCircle2, AlertCircle, ShieldCheck, ExternalLink } from "lucide-react";
import { triggerMoodleSync, fetchSyncStatus } from "@/lib/api";
import { SyncStatus } from "@/types";

export function Header({ onSyncCompleted }: { onSyncCompleted?: () => void }) {
  const [syncStatus, setSyncStatus] = useState<SyncStatus>({
    is_syncing: false,
    current_stage: "idle",
    progress_message: "Ready",
    sync_run_id: null,
  });
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Poll sync status when syncing is active
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (syncStatus.is_syncing) {
      timer = setInterval(async () => {
        try {
          const status = await fetchSyncStatus();
          setSyncStatus(status);
          if (!status.is_syncing) {
            clearInterval(timer);
            if (onSyncCompleted) onSyncCompleted();
          }
        } catch (err) {
          console.error("Polling error", err);
        }
      }, 1500);
    }
    return () => clearInterval(timer);
  }, [syncStatus.is_syncing, onSyncCompleted]);

  // Initial check on load
  useEffect(() => {
    fetchSyncStatus()
      .then((s) => setSyncStatus(s))
      .catch(() => {});
  }, []);

  const handleCheckMoodleNow = async () => {
    setErrorMsg(null);
    try {
      setSyncStatus((prev) => ({
        ...prev,
        is_syncing: true,
        progress_message: "Initiating check...",
      }));
      await triggerMoodleSync();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to trigger sync");
      setSyncStatus((prev) => ({ ...prev, is_syncing: false }));
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-10">
      <div className="flex items-center space-x-3">
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
          University Workspace
        </span>
        {errorMsg && (
          <span className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-1 rounded flex items-center gap-1">
            <AlertCircle className="w-3.5 h-3.5" />
            {errorMsg}
          </span>
        )}
      </div>

      <div className="flex items-center space-x-4">
        {syncStatus.is_syncing && (
          <div className="flex items-center space-x-2 text-xs text-blue-400 animate-pulse bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-md">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span className="font-medium">{syncStatus.progress_message}</span>
          </div>
        )}

        <button
          onClick={handleCheckMoodleNow}
          disabled={syncStatus.is_syncing}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium text-sm transition-all shadow-sm ${
            syncStatus.is_syncing
              ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
              : "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20 hover:shadow-blue-500/30 active:scale-98"
          }`}
          title="Manually trigger immediate Moodle synchronization"
        >
          <RefreshCw className={`w-4 h-4 ${syncStatus.is_syncing ? "animate-spin" : ""}`} />
          <span>{syncStatus.is_syncing ? "Checking Moodle..." : "Check Moodle Now"}</span>
        </button>
      </div>
    </header>
  );
}

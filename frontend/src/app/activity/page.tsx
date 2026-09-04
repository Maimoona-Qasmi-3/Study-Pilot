"use client";

import React, { useState, useEffect } from "react";
import { Activity, ShieldCheck, AlertCircle, Info, RefreshCw } from "lucide-react";
import { fetchLogs, fetchSyncRuns } from "@/lib/api";
import { AgentLog, SyncRun } from "@/types";

export default function ActivityLogPage() {
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [runs, setRuns] = useState<SyncRun[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [logsData, runsData] = await Promise.all([
        fetchLogs(),
        fetchSyncRuns(),
      ]);
      setLogs(logsData);
      setRuns(runsData);
    } catch (err) {
      console.error("Failed to load activity logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case "error":
        return <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
      case "success":
        return <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />;
      default:
        return <Info className="w-4 h-4 text-blue-400 shrink-0" />;
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">System & Agent Activity Log</h1>
        <p className="text-sm text-slate-400 mt-1">
          Complete audit trail of Moodle checks, course discoveries, sync operations, and workflow events.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Granular Activity Timeline */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Event Stream</h2>
            <button
              onClick={loadData}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>

          {loading ? (
            <div className="py-12 text-center text-slate-400 text-sm">Loading logs...</div>
          ) : logs.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
              No activity logs recorded yet. Events will populate as Moodle is checked.
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-start space-x-3.5"
                >
                  {getSeverityIcon(log.severity)}
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-blue-400 font-semibold uppercase">{log.event_type}</span>
                      <span className="text-slate-400">{new Date(log.timestamp).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-slate-200">{log.message}</p>
                    {log.details_json && (
                      <pre className="text-[11px] font-mono bg-slate-950 p-2 rounded border border-slate-800 text-slate-400 overflow-x-auto mt-2">
                        {log.details_json}
                      </pre>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Col: Sync Run Records */}
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-white">Sync Runs (SyncRun Table)</h2>
          {runs.length === 0 ? (
            <div className="py-8 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-xl">
              No sync runs recorded yet.
            </div>
          ) : (
            <div className="space-y-3">
              {runs.map((r) => (
                <div key={r.id} className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-white capitalize">{r.trigger} Sync</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        r.status === "completed"
                          ? "bg-emerald-500/20 text-emerald-400"
                          : r.status === "failed"
                          ? "bg-rose-500/20 text-rose-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>
                  <div className="text-slate-400 space-y-0.5">
                    <div>Started: {new Date(r.started_at).toLocaleTimeString()}</div>
                    {r.completed_at && <div>Completed: {new Date(r.completed_at).toLocaleTimeString()}</div>}
                  </div>
                  <div className="pt-2 border-t border-slate-800 flex justify-between text-slate-300 font-mono text-[11px]">
                    <span>Courses: {r.courses_found}</span>
                    <span>Items: {r.activities_found}</span>
                    <span className="text-emerald-400">New: {r.new_items_found}</span>
                  </div>
                  {r.error_message && (
                    <div className="text-rose-400 text-[11px] bg-rose-500/10 p-2 rounded border border-rose-500/20">
                      {r.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

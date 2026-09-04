import React from "react";
import { ActivityType, ActivityStatus, Priority } from "@/types";

export function ActivityTypeBadge({ type }: { type: ActivityType }) {
  const styles: Record<ActivityType, string> = {
    assignment: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    quiz: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    resource: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    file: "bg-teal-500/10 text-teal-400 border-teal-500/20",
    forum: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    attendance: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
    other: "bg-gray-500/10 text-gray-400 border-gray-500/20",
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border uppercase tracking-wider ${styles[type] || styles.other}`}>
      {type}
    </span>
  );
}

export function StatusBadge({ status }: { status: ActivityStatus }) {
  const styles: Record<ActivityStatus, string> = {
    new: "bg-sky-500/20 text-sky-300 border-sky-500/30",
    not_started: "bg-slate-500/20 text-slate-300 border-slate-500/30",
    agent_working: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30 animate-pulse",
    ready_for_review: "bg-amber-500/20 text-amber-300 border-amber-500/30 font-semibold",
    changes_requested: "bg-rose-500/20 text-rose-300 border-rose-500/30",
    approved: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    uploading: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
    uploaded: "bg-teal-500/20 text-teal-300 border-teal-500/30",
    submitted: "bg-green-500/20 text-green-300 border-green-500/30",
    needs_attention: "bg-orange-500/20 text-orange-300 border-orange-500/30",
    ignored: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
  };

  const label = status.replace(/_/g, " ");

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border capitalize ${styles[status] || styles.new}`}>
      {label}
    </span>
  );
}

export function PriorityBadge({ priority }: { priority: Priority }) {
  const styles: Record<Priority, string> = {
    low: "text-slate-400",
    medium: "text-blue-400",
    high: "text-amber-400 font-medium",
    urgent: "text-rose-400 font-bold",
  };

  return (
    <span className={`text-xs capitalize ${styles[priority] || styles.medium}`}>
      {priority}
    </span>
  );
}

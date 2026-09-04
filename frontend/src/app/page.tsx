"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  BookOpen,
  Calendar,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowRight,
  ShieldAlert,
  Activity,
  Zap,
} from "lucide-react";
import { fetchDashboardStats, fetchActivities, fetchLogs, fetchCourses } from "@/lib/api";
import { DashboardStats, MoodleActivity, AgentLog, Course } from "@/types";
import { ActivityTypeBadge, StatusBadge, PriorityBadge } from "@/components/ui/ActivityBadge";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [upcoming, setUpcoming] = useState<MoodleActivity[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [statsData, upcomingData, coursesData, logsData] = await Promise.all([
        fetchDashboardStats(),
        fetchActivities({ has_deadline: true, upcoming_only: true }),
        fetchCourses(true),
        fetchLogs(),
      ]);
      setStats(statsData);
      setUpcoming(upcomingData.slice(0, 5));
      setCourses(coursesData.slice(0, 4));
      setLogs(logsData.slice(0, 6));
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatDate = (isoStr: string | null) => {
    if (!isoStr) return "No deadline";
    const date = new Date(isoStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-8">
      {/* Header section */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Academic Operations Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">
          Real-time monitoring of university Moodle courses, deadlines, and activity workflows.
        </p>
      </div>

      {/* Auth warning banner if not connected */}
      {stats && !stats.is_authenticated && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start space-x-3 text-amber-300">
          <ShieldAlert className="w-5 h-5 shrink-0 text-amber-400 mt-0.5" />
          <div className="text-sm flex-1">
            <p className="font-semibold text-amber-200">Moodle Account Not Connected</p>
            <p className="text-amber-300/80 mt-0.5">
              Study Pilot needs an authenticated Moodle session to discover your active courses and assignments.
            </p>
          </div>
          <Link
            href="/settings"
            className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 text-xs font-semibold shrink-0 transition"
          >
            Connect Now
          </Link>
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Active Courses */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Active Courses</span>
            <BookOpen className="w-4 h-4 text-blue-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">
              {stats ? stats.active_courses_count : "—"}
            </span>
            <Link href="/courses" className="text-xs text-blue-400 hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Strict Upcoming Deadlines */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Due Deadlines</span>
            <Calendar className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">
              {stats ? stats.upcoming_deadlines_count : "—"}
            </span>
            <Link href="/calendar" className="text-xs text-amber-400 hover:underline flex items-center gap-1">
              Calendar <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* New Activities */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">New Items</span>
            <Zap className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-bold text-white">
              {stats ? stats.new_activities_count : "—"}
            </span>
            <Link href="/activities?status=new" className="text-xs text-emerald-400 hover:underline flex items-center gap-1">
              Review <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
        </div>

        {/* Latest Sync Status */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-medium uppercase tracking-wider">Last Sync</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="mt-3">
            <div className="flex items-center gap-1.5">
              {stats?.latest_sync?.status === "completed" && (
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              )}
              {stats?.latest_sync?.status === "failed" && (
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              )}
              <span className="text-sm font-semibold text-white capitalize">
                {stats?.latest_sync ? `${stats.latest_sync.status} (${stats.latest_sync.trigger})` : "Never"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              {stats?.latest_sync?.completed_at ? formatDate(stats.latest_sync.completed_at) : "Pending first run"}
            </p>
          </div>
        </div>
      </div>

      {/* Main split view */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Deadlines & Courses */}
        <div className="lg:col-span-2 space-y-6">
          {/* Strict Upcoming Deadlines Card */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white">Upcoming Deadlines</h2>
                <p className="text-xs text-slate-400">Assignments with strict due dates tracked in calendar</p>
              </div>
              <Link href="/calendar" className="text-xs text-blue-400 hover:underline font-medium">
                Full Calendar
              </Link>
            </div>

            {upcoming.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
                No upcoming deadlines found. Click &quot;Check Moodle Now&quot; to scan for new assignments.
              </div>
            ) : (
              <div className="space-y-3">
                {upcoming.map((act) => (
                  <div
                    key={act.id}
                    className="p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition flex items-center justify-between"
                  >
                    <div className="space-y-1 min-w-0 pr-4">
                      <div className="flex items-center space-x-2">
                        <ActivityTypeBadge type={act.activity_type} />
                        <span className="text-xs text-slate-400 font-medium truncate">{act.course_name}</span>
                      </div>
                      <h3 className="text-sm font-semibold text-slate-200 truncate">{act.title}</h3>
                    </div>

                    <div className="flex items-center space-x-4 shrink-0 text-right">
                      <div>
                        <span className="text-xs font-bold text-amber-400 flex items-center gap-1 justify-end">
                          <Clock className="w-3 h-3" />
                          {formatDate(act.due_date)}
                        </span>
                        <StatusBadge status={act.status} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active Courses Card */}
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white">Active Courses</h2>
                <p className="text-xs text-slate-400">Currently enrolled semester courses discovered from Moodle</p>
              </div>
              <Link href="/courses" className="text-xs text-blue-400 hover:underline font-medium">
                All Courses
              </Link>
            </div>

            {courses.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
                No active courses synced yet. Click &quot;Check Moodle Now&quot; to scan Moodle.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {courses.map((course) => (
                  <Link
                    key={course.id}
                    href={`/courses/${course.id}`}
                    className="p-4 rounded-lg bg-slate-950/70 border border-slate-800 hover:border-blue-500/30 transition block group"
                  >
                    <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                      <span className="font-mono text-blue-400 font-medium">{course.short_name || "Course"}</span>
                      <span>{course.activity_count || 0} activities</span>
                    </div>
                    <h3 className="text-sm font-semibold text-white group-hover:text-blue-300 transition line-clamp-2">
                      {course.full_name}
                    </h3>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Agent Activity Audit Timeline */}
        <div className="space-y-6">
          <div className="p-6 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Activity className="w-4 h-4 text-blue-400" />
                <h2 className="text-base font-semibold text-white">Agent Activity Log</h2>
              </div>
              <Link href="/activity" className="text-xs text-blue-400 hover:underline font-medium">
                View Full
              </Link>
            </div>

            {logs.length === 0 ? (
              <div className="py-8 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-lg">
                No agent logs recorded yet.
              </div>
            ) : (
              <div className="space-y-4">
                {logs.map((log) => (
                  <div key={log.id} className="text-xs border-l-2 border-blue-500/30 pl-3 py-1 space-y-0.5">
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="font-mono uppercase text-[10px] text-blue-400 font-semibold">{log.event_type}</span>
                      <span>{new Date(log.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                    </div>
                    <p className="text-slate-200">{log.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import { Search, Filter, ExternalLink, Calendar, Clock } from "lucide-react";
import { fetchActivities, fetchCourses, updateActivity } from "@/lib/api";
import { MoodleActivity, Course, ActivityType, ActivityStatus } from "@/types";
import { ActivityTypeBadge, StatusBadge, PriorityBadge } from "@/components/ui/ActivityBadge";

export default function ActivitiesPage() {
  const [activities, setActivities] = useState<MoodleActivity[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [selectedType, setSelectedType] = useState<string>("");
  const [deadlineFilter, setDeadlineFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadActivities = async () => {
    try {
      const params: any = {};
      if (selectedCourse) params.course_id = selectedCourse;
      if (selectedType) params.activity_type = selectedType;
      if (deadlineFilter === "deadline_only") params.has_deadline = true;
      if (deadlineFilter === "no_deadline") params.has_deadline = false;

      const [actData, coursesData] = await Promise.all([
        fetchActivities(params),
        fetchCourses(false),
      ]);
      setActivities(actData);
      setCourses(coursesData);
    } catch (err) {
      console.error("Failed to load activities:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, [selectedCourse, selectedType, deadlineFilter]);

  const handleStatusChange = async (actId: string, newStatus: string) => {
    try {
      await updateActivity(actId, { status: newStatus });
      loadActivities();
    } catch (err) {
      console.error("Failed to update activity status:", err);
    }
  };

  const filteredActivities = activities.filter((a) =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

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

  const statusOptions: ActivityStatus[] = [
    "new",
    "not_started",
    "agent_working",
    "ready_for_review",
    "changes_requested",
    "approved",
    "uploading",
    "uploaded",
    "submitted",
    "needs_attention",
    "ignored",
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Moodle Activities & Tasks</h1>
        <p className="text-sm text-slate-400 mt-1">
          Complete registry of discovered assignments, quizzes, files, and course materials.
        </p>
      </div>

      {/* Filter bar */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
          {/* Search input */}
          <div className="relative flex-1 max-w-xs">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Course filter */}
          <select
            value={selectedCourse}
            onChange={(e) => setSelectedCourse(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-sm rounded-lg px-3 py-1.5 text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Courses</option>
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.short_name || c.full_name}
              </option>
            ))}
          </select>

          {/* Type filter */}
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-sm rounded-lg px-3 py-1.5 text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Types</option>
            <option value="assignment">Assignment</option>
            <option value="quiz">Quiz</option>
            <option value="resource">Resource</option>
            <option value="file">File</option>
            <option value="forum">Forum</option>
            <option value="attendance">Attendance</option>
            <option value="other">Other</option>
          </select>

          {/* Deadline Filter */}
          <select
            value={deadlineFilter}
            onChange={(e) => setDeadlineFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-sm rounded-lg px-3 py-1.5 text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Items</option>
            <option value="deadline_only">With Strict Deadline</option>
            <option value="no_deadline">No Deadline Only</option>
          </select>
        </div>

        <span className="text-xs text-slate-400 font-medium">
          Showing {filteredActivities.length} items
        </span>
      </div>

      {/* Table view */}
      {loading ? (
        <div className="py-16 text-center text-slate-400 text-sm">Loading activities...</div>
      ) : filteredActivities.length === 0 ? (
        <div className="py-16 text-center text-slate-500 text-sm border border-dashed border-slate-800 rounded-xl">
          No activities match your filters.
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4 font-semibold">Title & Course</th>
                  <th className="py-3 px-4 font-semibold">Type</th>
                  <th className="py-3 px-4 font-semibold">Due Date</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredActivities.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-800/30 transition">
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-white max-w-md truncate">{act.title}</div>
                      <div className="text-xs text-slate-400 mt-0.5 truncate">{act.course_name}</div>
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <ActivityTypeBadge type={act.activity_type} />
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {act.has_deadline && act.due_date ? (
                        <div className="flex items-center space-x-1.5 text-xs text-amber-400 font-medium">
                          <Clock className="w-3.5 h-3.5" />
                          <span>{formatDate(act.due_date)}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500 italic">No deadline</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <select
                        value={act.status}
                        onChange={(e) => handleStatusChange(act.id, e.target.value)}
                        className="bg-slate-950 border border-slate-800 text-xs rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-blue-500 cursor-pointer"
                      >
                        {statusOptions.map((opt) => (
                          <option key={opt} value={opt}>
                            {opt.replace(/_/g, " ")}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <a
                        href={act.moodle_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1 text-xs text-blue-400 hover:text-blue-300 font-medium transition"
                      >
                        <span>Moodle</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

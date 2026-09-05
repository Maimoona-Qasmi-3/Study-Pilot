"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  ExternalLink,
  Clock,
  FolderPlus,
  Folder,
  Code2,
  Terminal,
  FileText,
  Download,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  Sparkles,
} from "lucide-react";
import {
  fetchActivities,
  fetchCourses,
  updateActivity,
  fetchWorkflowProfiles,
  initWorkspace,
  launchWorkspaceTool,
  generateWorkspaceReport,
  getReportDownloadUrl,
} from "@/lib/api";
import {
  MoodleActivity,
  Course,
  ActivityType,
  ActivityStatus,
  WorkflowProfile,
} from "@/types";
import { ActivityTypeBadge, StatusBadge, PriorityBadge } from "@/components/ui/ActivityBadge";

export default function ActivitiesPage() {
  const [activities, setActivities] = useState<MoodleActivity[]>([]);
  const [courses, setCourses] = useState<Course[]>([]);
  const [profiles, setProfiles] = useState<WorkflowProfile[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>("");
  const [selectedType, setSelectedType] = useState<string>("");
  const [deadlineFilter, setDeadlineFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [loading, setLoading] = useState(true);

  // Workspace modal and action states
  const [modalActivity, setModalActivity] = useState<MoodleActivity | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("");
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [feedbackMessage, setFeedbackMessage] = useState<{
    type: "success" | "error" | "info";
    text: string;
  } | null>(null);

  const loadData = async () => {
    try {
      const params: any = {};
      if (selectedCourse) params.course_id = selectedCourse;
      if (selectedType) params.activity_type = selectedType;
      if (deadlineFilter === "deadline_only") params.has_deadline = true;
      if (deadlineFilter === "no_deadline") params.has_deadline = false;

      const [actData, coursesData, profilesData] = await Promise.all([
        fetchActivities(params),
        fetchCourses(false),
        fetchWorkflowProfiles().catch(() => []),
      ]);
      setActivities(actData);
      setCourses(coursesData);
      setProfiles(profilesData);
    } catch (err) {
      console.error("Failed to load activities:", err);
      showFeedback("error", "Failed to load activities or workspaces");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCourse, selectedType, deadlineFilter]);

  const showFeedback = (type: "success" | "error" | "info", text: string) => {
    setFeedbackMessage({ type, text });
    setTimeout(() => {
      setFeedbackMessage(null);
    }, 5000);
  };

  const handleStatusChange = async (actId: string, newStatus: string) => {
    try {
      await updateActivity(actId, { status: newStatus });
      loadData();
    } catch (err) {
      console.error("Failed to update activity status:", err);
      showFeedback("error", "Failed to update status");
    }
  };

  const handleOpenInitModal = (activity: MoodleActivity) => {
    setModalActivity(activity);
    // Find course default profile
    const course = courses.find((c) => c.id === activity.course_id);
    const courseCode = course?.short_name || course?.full_name || "";
    let defaultId = "generic_lab";

    const text = courseCode.toUpperCase();
    if (text.includes("CSC-103") || text.includes("OOP")) defaultId = "cpp_coding";
    else if (text.includes("CSC-210") || text.includes("DISCRETE")) defaultId = "python_scripting";
    else if (text.includes("ELE-205") || text.includes("DIGITAL LOGIC")) defaultId = "digital_logic";
    else if (text.includes("ENG-102") || text.includes("EXPOSITORY")) defaultId = "academic_writing";
    else if (text.includes("MGT-302") || text.includes("ENTREPRENEURSHIP")) defaultId = "academic_writing";
    else if (text.includes("MTH-208") || text.includes("LINEAR ALGEBRA")) defaultId = "linear_algebra";

    setSelectedProfileId(defaultId);
  };

  const handleConfirmInitWorkspace = async () => {
    if (!modalActivity) return;
    const actId = modalActivity.id;
    setActionLoadingId(`init-${actId}`);
    try {
      const res = await initWorkspace(actId, selectedProfileId);
      showFeedback("success", `Workspace initialized: ${res.workspace_path}`);
      setModalActivity(null);
      await loadData();
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to initialize workspace");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleLaunchTool = async (actId: string, tool: "vscode" | "explorer" | "terminal") => {
    setActionLoadingId(`${tool}-${actId}`);
    try {
      const res = await launchWorkspaceTool(actId, tool);
      showFeedback("success", res.message || `Launched ${tool}`);
    } catch (err: any) {
      showFeedback("error", err.message || `Failed to launch ${tool}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleGenerateReport = async (actId: string) => {
    setActionLoadingId(`report-${actId}`);
    try {
      const res = await generateWorkspaceReport(actId);
      showFeedback("success", `Report generated: ${res.filename} (${(res.file_size_bytes / 1024).toFixed(1)} KB)`);
      await loadData();
    } catch (err: any) {
      showFeedback("error", err.message || "Failed to generate report");
    } finally {
      setActionLoadingId(null);
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Moodle Activities & Workspaces</h1>
          <p className="text-sm text-slate-400 mt-1">
            Manage assignments, generate local project workspaces, and compile standardized academic reports.
          </p>
        </div>
      </div>

      {/* Feedback Toast */}
      {feedbackMessage && (
        <div
          className={`p-3 rounded-lg border flex items-center justify-between text-sm transition-all ${
            feedbackMessage.type === "success"
              ? "bg-emerald-950/60 border-emerald-800 text-emerald-300"
              : feedbackMessage.type === "error"
              ? "bg-rose-950/60 border-rose-800 text-rose-300"
              : "bg-blue-950/60 border-blue-800 text-blue-300"
          }`}
        >
          <div className="flex items-center space-x-2">
            {feedbackMessage.type === "success" && <CheckCircle2 className="w-4 h-4" />}
            {feedbackMessage.type === "error" && <AlertCircle className="w-4 h-4" />}
            <span>{feedbackMessage.text}</span>
          </div>
          <button onClick={() => setFeedbackMessage(null)} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

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
                  <th className="py-3 px-4 font-semibold">Workspace & Actions</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Moodle</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredActivities.map((act) => {
                  const hasWorkspace = Boolean(act.workspace_path);
                  const isCompleted = act.workspace_status === "completed";

                  return (
                    <tr key={act.id} className="hover:bg-slate-800/30 transition">
                      {/* Title & Course */}
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-white max-w-md truncate">{act.title}</div>
                        <div className="text-xs text-slate-400 mt-0.5 truncate">{act.course_name}</div>
                      </td>

                      {/* Type */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <ActivityTypeBadge type={act.activity_type} />
                      </td>

                      {/* Due Date */}
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

                      {/* Workspace Controls */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {!hasWorkspace ? (
                          <button
                            onClick={() => handleOpenInitModal(act)}
                            disabled={actionLoadingId === `init-${act.id}`}
                            className="inline-flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium rounded-md bg-blue-600/20 text-blue-400 border border-blue-500/30 hover:bg-blue-600/30 transition"
                          >
                            {actionLoadingId === `init-${act.id}` ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <FolderPlus className="w-3.5 h-3.5" />
                            )}
                            <span>Init Workspace</span>
                          </button>
                        ) : (
                          <div className="flex items-center space-x-1.5">
                            {/* Launch VS Code */}
                            <button
                              onClick={() => handleLaunchTool(act.id, "vscode")}
                              disabled={actionLoadingId === `vscode-${act.id}`}
                              title="Open in VS Code (code .)"
                              className="p-1.5 rounded bg-slate-800 text-blue-400 hover:bg-blue-900/40 hover:text-blue-300 transition"
                            >
                              {actionLoadingId === `vscode-${act.id}` ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Code2 className="w-3.5 h-3.5" />
                              )}
                            </button>

                            {/* Launch Explorer */}
                            <button
                              onClick={() => handleLaunchTool(act.id, "explorer")}
                              disabled={actionLoadingId === `explorer-${act.id}`}
                              title="Open in File Explorer"
                              className="p-1.5 rounded bg-slate-800 text-amber-400 hover:bg-amber-900/40 hover:text-amber-300 transition"
                            >
                              {actionLoadingId === `explorer-${act.id}` ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Folder className="w-3.5 h-3.5" />
                              )}
                            </button>

                            {/* Launch Terminal */}
                            <button
                              onClick={() => handleLaunchTool(act.id, "terminal")}
                              disabled={actionLoadingId === `terminal-${act.id}`}
                              title="Open Terminal"
                              className="p-1.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition"
                            >
                              {actionLoadingId === `terminal-${act.id}` ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Terminal className="w-3.5 h-3.5" />
                              )}
                            </button>

                            {/* Generate Report */}
                            <button
                              onClick={() => handleGenerateReport(act.id)}
                              disabled={actionLoadingId === `report-${act.id}`}
                              title="Generate Standardized DOCX Report"
                              className={`p-1.5 rounded transition ${
                                isCompleted
                                  ? "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 hover:bg-emerald-900/50"
                                  : "bg-purple-950/60 text-purple-400 border border-purple-800/60 hover:bg-purple-900/50"
                              }`}
                            >
                              {actionLoadingId === `report-${act.id}` ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <FileText className="w-3.5 h-3.5" />
                              )}
                            </button>

                            {/* Download Report (if completed) */}
                            {isCompleted && (
                              <a
                                href={getReportDownloadUrl(act.id)}
                                download
                                title="Download Generated DOCX"
                                className="p-1.5 rounded bg-emerald-900/40 text-emerald-300 hover:bg-emerald-800/60 transition"
                              >
                                <Download className="w-3.5 h-3.5" />
                              </a>
                            )}
                          </div>
                        )}
                      </td>

                      {/* Status Dropdown */}
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

                      {/* Moodle link */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <a
                          href={act.moodle_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center space-x-1 text-xs text-blue-400 hover:text-blue-300 font-medium transition"
                        >
                          <span>Portal</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Workspace Initialization Modal */}
      {modalActivity && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FolderPlus className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-bold text-white">Initialize Activity Workspace</h3>
              </div>
              <button
                onClick={() => setModalActivity(null)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-medium text-white">{modalActivity.title}</div>
              <div className="text-xs text-slate-400">{modalActivity.course_name}</div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Select Workflow Profile:
              </label>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {profiles.map((p) => (
                  <label
                    key={p.id}
                    onClick={() => setSelectedProfileId(p.id)}
                    className={`block p-3 rounded-lg border cursor-pointer transition ${
                      selectedProfileId === p.id
                        ? "bg-blue-950/40 border-blue-500 text-white"
                        : "bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm text-slate-200">{p.name}</span>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        {p.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{p.description}</p>
                  </label>
                ))}
              </div>
            </div>

            <p className="text-xs text-slate-500 italic">
              Workspace will be created under <code className="text-slate-400">data/workspaces/</code> with <code className="text-slate-400">src/</code>, <code className="text-slate-400">evidence/</code>, and <code className="text-slate-400">output/</code>.
            </p>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                onClick={() => setModalActivity(null)}
                className="px-4 py-2 text-xs font-medium rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmInitWorkspace}
                disabled={actionLoadingId !== null}
                className="px-4 py-2 text-xs font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-500 transition flex items-center space-x-1.5"
              >
                {actionLoadingId ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <FolderPlus className="w-4 h-4" />
                )}
                <span>Create Workspace</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

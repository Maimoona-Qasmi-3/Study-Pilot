import { DashboardStats, Course, MoodleActivity, SyncRun, SyncStatus, AgentLog } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/dashboard/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load dashboard stats");
  return res.json();
}

export async function fetchCourses(activeOnly = false): Promise<Course[]> {
  const url = activeOnly ? `${API_BASE}/courses?active_only=true` : `${API_BASE}/courses`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load courses");
  return res.json();
}

export async function fetchCourse(id: string): Promise<Course & { activities: MoodleActivity[] }> {
  const res = await fetch(`${API_BASE}/courses/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load course details");
  return res.json();
}

export async function updateCourse(id: string, data: { is_active?: boolean; default_workflow_id?: string | null }): Promise<Course> {
  const res = await fetch(`${API_BASE}/courses/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update course");
  return res.json();
}

export async function fetchActivities(params?: {
  course_id?: string;
  activity_type?: string;
  has_deadline?: boolean;
  status?: string;
  upcoming_only?: boolean;
}): Promise<MoodleActivity[]> {
  const query = new URLSearchParams();
  if (params?.course_id) query.set("course_id", params.course_id);
  if (params?.activity_type) query.set("activity_type", params.activity_type);
  if (params?.has_deadline !== undefined) query.set("has_deadline", String(params.has_deadline));
  if (params?.status) query.set("status", params.status);
  if (params?.upcoming_only) query.set("upcoming_only", "true");

  const res = await fetch(`${API_BASE}/activities?${query.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load activities");
  return res.json();
}

export async function fetchCalendarEvents(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/activities/calendar/events`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load calendar events");
  return res.json();
}

export async function updateActivity(
  id: string,
  data: { status?: string; priority?: string; workflow_id?: string | null }
): Promise<MoodleActivity> {
  const res = await fetch(`${API_BASE}/activities/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update activity");
  return res.json();
}

export async function triggerMoodleSync(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/moodle/sync`, { method: "POST" });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to trigger sync" }));
    throw new Error(errorData.detail || "Failed to trigger sync");
  }
  return res.json();
}

export async function fetchSyncStatus(): Promise<SyncStatus> {
  const res = await fetch(`${API_BASE}/moodle/sync/status`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load sync status");
  return res.json();
}

export async function fetchSyncRuns(): Promise<SyncRun[]> {
  const res = await fetch(`${API_BASE}/moodle/runs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load sync history");
  return res.json();
}

export async function fetchLogs(): Promise<AgentLog[]> {
  const res = await fetch(`${API_BASE}/logs`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load activity logs");
  return res.json();
}

export async function fetchSettings(): Promise<{ settings: Record<string, string>; is_authenticated: boolean }> {
  const res = await fetch(`${API_BASE}/settings`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load settings");
  return res.json();
}

export async function updateSettings(settings: Record<string, string>): Promise<any> {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error("Failed to save settings");
  return res.json();
}

export async function launchMoodleLogin(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/moodle/auth/login`, { method: "POST" });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: "Failed to launch login" }));
    throw new Error(errorData.detail || "Failed to launch login");
  }
  return res.json();
}

export async function verifyMoodleSession(): Promise<{ valid: boolean; expired: boolean; message: string }> {
  const res = await fetch(`${API_BASE}/moodle/auth/verify`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to verify session");
  return res.json();
}

export async function fetchLoginProgress(): Promise<{
  is_logging_in: boolean;
  status: "idle" | "in_progress" | "success" | "failed";
  message: string;
  last_updated: number;
}> {
  const res = await fetch(`${API_BASE}/moodle/auth/progress`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load login progress");
  return res.json();
}

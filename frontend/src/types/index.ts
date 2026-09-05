export type ActivityType =
  | "assignment"
  | "quiz"
  | "resource"
  | "file"
  | "forum"
  | "attendance"
  | "other";

export type ActivityStatus =
  | "new"
  | "not_started"
  | "agent_working"
  | "ready_for_review"
  | "changes_requested"
  | "approved"
  | "uploading"
  | "uploaded"
  | "submitted"
  | "needs_attention"
  | "ignored";

export type Priority = "low" | "medium" | "high" | "urgent";

export interface Course {
  id: string;
  moodle_course_id: string;
  full_name: string;
  short_name: string | null;
  moodle_url: string;
  term_or_category: string | null;
  is_active: boolean;
  default_workflow_id: string | null;
  activity_count?: number;
  created_at: string;
  updated_at: string;
  last_synced_at: string | null;
}

export interface MoodleActivity {
  id: string;
  course_id: string;
  course_name?: string;
  moodle_item_id: string;
  title: string;
  description_html: string | null;
  description_text: string | null;
  activity_type: ActivityType;
  moodle_url: string;
  has_deadline: boolean;
  due_date: string | null;
  cutoff_date: string | null;
  status: ActivityStatus;
  priority: Priority;
  workflow_id: string | null;
  workspace_path?: string | null;
  workspace_status?: "uninitialized" | "ready" | "in_progress" | "completed";
  submission_status_moodle: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowProfile {
  id: string;
  name: string;
  description: string;
  category: string;
}

export interface WorkspaceInfo {
  initialized: boolean;
  activity_id: string;
  workspace_status: "uninitialized" | "ready" | "in_progress" | "completed";
  workspace_path: string | null;
  absolute_path?: string;
  workflow_profile_id?: string;
  workflow_profile_name?: string;
  src_files: string[];
  evidence_files: string[];
  output_files: string[];
  has_report: boolean;
  report_filename?: string | null;
  metadata?: Record<string, any>;
}

export interface SyncRun {
  id: string;
  started_at: string;
  completed_at: string | null;
  status: "running" | "completed" | "failed";
  trigger: "manual" | "scheduled";
  courses_found: number;
  activities_found: number;
  new_items_found: number;
  error_message: string | null;
}

export interface DashboardStats {
  active_courses_count: number;
  new_activities_count: number;
  upcoming_deadlines_count: number;
  ready_for_review_count: number;
  is_authenticated: boolean;
  is_expired?: boolean;
  session_message?: string;
  latest_sync: SyncRun | null;
}

export interface LoginProgress {
  is_logging_in: boolean;
  status: "idle" | "in_progress" | "success" | "failed";
  message: string;
  last_updated: number;
}

export interface SyncStatus {
  is_syncing: boolean;
  current_stage: string;
  progress_message: string;
  sync_run_id: string | null;
}

export interface AgentLog {
  id: string;
  timestamp: string;
  event_type: string;
  message: string;
  details_json: string | null;
  severity: "info" | "success" | "warning" | "error";
}

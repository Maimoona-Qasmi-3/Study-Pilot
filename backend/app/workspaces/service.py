"""
Workspace Service for Study Pilot.
Orchestrates local directory scaffolding, starter templates, metadata management,
and deterministic raw Moodle instruction storage.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlmodel import Session, select

from ..config import WORKSPACES_DIR
from ..models import MoodleActivity, Course
from .profiles import (
    get_profile,
    get_default_profile_for_course,
    WorkflowProfile,
)


def slugify(text: str, max_length: int = 50) -> str:
    """Create a clean, filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:max_length] if text else "task"


def clean_course_code(code_or_name: str) -> str:
    """Extract standard course code e.g. 'CSC-103 (2601-1185)' -> 'CSC-103'."""
    match = re.search(r"([A-Za-z]{2,4}-\d{3})", code_or_name)
    if match:
        return match.group(1).upper()
    return slugify(code_or_name, max_length=20).upper()


class WorkspaceService:
    @staticmethod
    def resolve_workspace_dir(course_code: str, activity_title: str, item_id: str) -> Path:
        """Resolve deterministic workspace directory path safely within WORKSPACES_DIR."""
        c_code = clean_course_code(course_code)
        a_slug = slugify(activity_title)
        folder_name = f"{a_slug}_{item_id}"
        target_dir = (WORKSPACES_DIR / c_code / folder_name).resolve()

        # Security check against directory traversal
        if not str(target_dir).startswith(str(WORKSPACES_DIR.resolve())):
            raise ValueError(f"Security error: Invalid workspace path {target_dir}")

        return target_dir

    @staticmethod
    def initialize_workspace(
        activity_id: str,
        session: Session,
        workflow_profile_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Idempotently initialize a local activity workspace.
        Never overwrites existing user files.
        Preserves raw Moodle instructions deterministically.
        """
        activity = session.get(MoodleActivity, activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        course = session.get(Course, activity.course_id)
        if not course:
            raise ValueError(f"Course {activity.course_id} not found")

        course_code = course.short_name or course.full_name

        # Resolve workflow profile
        profile: Optional[WorkflowProfile] = None
        if workflow_profile_id:
            profile = get_profile(workflow_profile_id)
        if not profile and activity.workflow_id:
            profile = get_profile(activity.workflow_id)
        if not profile and course.default_workflow_id:
            profile = get_profile(course.default_workflow_id)
        if not profile:
            profile = get_default_profile_for_course(course_code)

        # Resolve path
        workspace_dir = WorkspaceService.resolve_workspace_dir(
            course_code=course_code,
            activity_title=activity.title,
            item_id=activity.moodle_item_id,
        )

        # Create subdirectories
        src_dir = workspace_dir / "src"
        evidence_dir = workspace_dir / "evidence"
        output_dir = workspace_dir / "output"

        for d in [workspace_dir, src_dir, evidence_dir, output_dir]:
            d.mkdir(parents=True, exist_ok=True)

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now_iso = datetime.now(timezone.utc).isoformat()

        # Populate starter files without overwriting existing files
        created_files: List[str] = []
        preserved_files: List[str] = []

        template_replacements = {
            "{course_name}": course.full_name,
            "{course_code}": clean_course_code(course_code),
            "{activity_title}": activity.title,
            "{created_date}": now_str,
        }

        for rel_path, content in profile.default_files.items():
            dest_file = workspace_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            if not dest_file.exists():
                formatted_content = content
                for placeholder, val in template_replacements.items():
                    formatted_content = formatted_content.replace(placeholder, val)
                dest_file.write_text(formatted_content, encoding="utf-8")
                created_files.append(rel_path)
            else:
                preserved_files.append(rel_path)

        # Save Raw Moodle Instructions
        instructions_md_path = workspace_dir / "instructions.md"
        instructions_content = f"""# {activity.title}

- **Course**: {course.full_name} ({clean_course_code(course_code)})
- **Moodle URL**: {activity.moodle_url}
- **Due Date**: {activity.due_date.isoformat() if activity.due_date else "No due date specified"}
- **Cutoff Date**: {activity.cutoff_date.isoformat() if activity.cutoff_date else "None"}
- **Status**: {activity.submission_status_moodle or "No attempt recorded"}

---

## Instructions & Brief
{activity.description_text or "No written instructions extracted from Moodle."}
"""
        instructions_md_path.write_text(instructions_content, encoding="utf-8")

        if activity.description_html:
            instructions_html_path = workspace_dir / "instructions.html"
            instructions_html_path.write_text(activity.description_html, encoding="utf-8")

        # Save / update workspace.json
        meta_path = workspace_dir / "workspace.json"
        metadata: Dict[str, Any] = {}
        if meta_path.exists():
            try:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                metadata = {}

        metadata.update({
            "activity_id": activity.id,
            "moodle_item_id": activity.moodle_item_id,
            "course_id": course.id,
            "course_name": course.full_name,
            "course_code": clean_course_code(course_code),
            "activity_title": activity.title,
            "workflow_profile_id": profile.id,
            "workflow_profile_name": profile.name,
            "workflow_category": profile.category,
            "relative_workspace_path": str(workspace_dir.relative_to(WORKSPACES_DIR)).replace("\\", "/"),
            "updated_at": now_iso,
        })
        if "created_at" not in metadata:
            metadata["created_at"] = now_iso

        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # Update database record
        rel_workspace_path = str(workspace_dir.relative_to(WORKSPACES_DIR)).replace("\\", "/")
        activity.workspace_path = rel_workspace_path
        if activity.workspace_status == "uninitialized":
            activity.workspace_status = "ready"
        activity.workflow_id = profile.id
        activity.updated_at = datetime.now(timezone.utc)
        session.add(activity)
        session.commit()
        session.refresh(activity)

        return {
            "success": True,
            "activity_id": activity.id,
            "workspace_path": rel_workspace_path,
            "absolute_path": str(workspace_dir),
            "workflow_profile": profile.model_dump(),
            "created_files": created_files,
            "preserved_files": preserved_files,
            "instructions_saved": True,
        }

    @staticmethod
    def get_workspace_info(activity_id: str, session: Session) -> Dict[str, Any]:
        """Inspect the current workspace on disk for an activity."""
        activity = session.get(MoodleActivity, activity_id)
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        course = session.get(Course, activity.course_id)
        course_code = course.short_name or course.full_name if course else "COURSE"

        if not activity.workspace_path:
            # Check if expected path exists on disk anyway
            expected_dir = WorkspaceService.resolve_workspace_dir(
                course_code=course_code,
                activity_title=activity.title,
                item_id=activity.moodle_item_id,
            )
            if not expected_dir.exists():
                return {
                    "initialized": False,
                    "activity_id": activity.id,
                    "workspace_status": "uninitialized",
                    "workspace_path": None,
                }
            workspace_dir = expected_dir
        else:
            workspace_dir = WORKSPACES_DIR / activity.workspace_path

        if not workspace_dir.exists():
            return {
                "initialized": False,
                "activity_id": activity.id,
                "workspace_status": "uninitialized",
                "workspace_path": None,
            }

        # Inspect disk contents
        src_files = [f.name for f in (workspace_dir / "src").glob("*") if f.is_file()] if (workspace_dir / "src").exists() else []
        evidence_files = [
            f.name for f in (workspace_dir / "evidence").glob("*")
            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".txt", ".log"]
        ] if (workspace_dir / "evidence").exists() else []

        output_files = [f.name for f in (workspace_dir / "output").glob("*") if f.is_file()] if (workspace_dir / "output").exists() else []
        docx_reports = [f for f in output_files if f.lower().endswith(".docx")]

        metadata: Dict[str, Any] = {}
        meta_path = workspace_dir / "workspace.json"
        if meta_path.exists():
            try:
                metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        return {
            "initialized": True,
            "activity_id": activity.id,
            "workspace_status": activity.workspace_status or "ready",
            "workspace_path": str(workspace_dir.relative_to(WORKSPACES_DIR)).replace("\\", "/"),
            "absolute_path": str(workspace_dir),
            "workflow_profile_id": metadata.get("workflow_profile_id", activity.workflow_id),
            "workflow_profile_name": metadata.get("workflow_profile_name"),
            "src_files": src_files,
            "evidence_files": evidence_files,
            "output_files": output_files,
            "has_report": len(docx_reports) > 0,
            "report_filename": docx_reports[0] if docx_reports else None,
            "metadata": metadata,
        }

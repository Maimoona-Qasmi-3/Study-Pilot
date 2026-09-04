import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from playwright.sync_api import sync_playwright
from sqlmodel import Session, select

from ..config import STORAGE_STATE_FILE, LOGS_DIR
from ..database import engine
from ..models import Course, MoodleActivity, SyncRun, AgentActivityLog, SystemSetting

logger = logging.getLogger("studypilot.moodle.sync")

# Global sync lock to prevent overlapping runs
_sync_lock = threading.Lock()
_current_sync_status: Dict[str, Any] = {
    "is_syncing": False,
    "current_stage": "idle",
    "progress_message": "Ready",
    "sync_run_id": None
}

def get_sync_status() -> Dict[str, Any]:
    """Returns the current state of synchronization for frontend polling."""
    return dict(_current_sync_status)

def _log_activity(session: Session, event_type: str, message: str, severity: str = "info", details: Optional[dict] = None) -> None:
    log_entry = AgentActivityLog(
        timestamp=datetime.now(timezone.utc),
        event_type=event_type,
        message=message,
        severity=severity,
        details_json=json.dumps(details) if details else None
    )
    session.add(log_entry)
    session.commit()

def run_moodle_sync(trigger: str = "manual") -> SyncRun:
    """
    Unified Moodle synchronization service.
    Invoked identically by:
      1. FastAPI "Check Moodle Now" endpoint (manual)
      2. Windows Task Scheduler daily CLI task (scheduled)
    """
    global _current_sync_status

    if not _sync_lock.acquire(blocking=False):
        raise RuntimeError("A Moodle synchronization is already in progress.")

    _current_sync_status["is_syncing"] = True
    _current_sync_status["current_stage"] = "initializing"
    _current_sync_status["progress_message"] = f"Starting {trigger} sync..."

    with Session(engine, expire_on_commit=False) as session:
        # Create SyncRun record
        sync_run = SyncRun(
            started_at=datetime.now(timezone.utc),
            status="running",
            trigger=trigger
        )
        session.add(sync_run)
        session.commit()
        session.refresh(sync_run)
        _current_sync_status["sync_run_id"] = sync_run.id

        _log_activity(
            session,
            event_type="moodle_check_started",
            message=f"Moodle sync started ({trigger})",
            severity="info",
            details={"sync_run_id": sync_run.id, "trigger": trigger}
        )

        try:
            # 1. Retrieve Moodle URL
            setting_moodle_url = session.get(SystemSetting, "moodle_url")
            moodle_url = setting_moodle_url.value.strip() if setting_moodle_url and setting_moodle_url.value else None

            if not moodle_url:
                raise ValueError("Moodle URL is not configured. Please set your university Moodle URL in Settings.")

            # 2. Check for saved authentication session
            if not STORAGE_STATE_FILE.exists():
                raise FileNotFoundError(
                    "Moodle session not found. Please log in first via Settings -> Connect Moodle."
                )

            _current_sync_status["current_stage"] = "authenticating"
            _current_sync_status["progress_message"] = "Connecting to Moodle with saved session..."

            courses_found_count = 0
            activities_found_count = 0
            new_items_count = 0

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    context = browser.new_context(storage_state=str(STORAGE_STATE_FILE))
                    page = context.new_page()

                    # Navigate to Moodle home / dashboard
                    target_url = moodle_url.rstrip("/") + "/my/"
                    _current_sync_status["current_stage"] = "fetching_dashboard"
                    _current_sync_status["progress_message"] = f"Loading dashboard: {target_url}..."
                    response = page.goto(target_url, timeout=45000, wait_until="domcontentloaded")

                    # Check if redirected to login page (session expired)
                    if "login" in page.url.lower():
                        raise PermissionError(
                            "Moodle session has expired. Please re-authenticate via Settings."
                        )

                    # Save diagnostic DOM snapshot to logs for inspection of real university markup
                    snapshot_file = LOGS_DIR / "moodle_dashboard_snapshot.html"
                    snapshot_file.write_text(page.content(), encoding="utf-8", errors="replace")
                    logger.info(f"Saved diagnostic snapshot to {snapshot_file}")

                    _current_sync_status["current_stage"] = "discovering_courses"
                    _current_sync_status["progress_message"] = "Discovering courses..."

                    # Extract all course links on dashboard
                    course_elements = page.query_selector_all('a[href*="/course/view.php?id="]')
                    discovered_courses: Dict[str, Dict[str, str]] = {}

                    for elem in course_elements:
                        href = elem.get_attribute("href") or ""
                        text = (elem.inner_text() or "").strip()
                        if "/course/view.php?id=" in href:
                            # Extract course ID from query param
                            try:
                                cid = href.split("id=")[1].split("&")[0]
                                if cid and cid.isdigit() and text and len(text) > 2:
                                    if cid not in discovered_courses:
                                        discovered_courses[cid] = {
                                            "id": cid,
                                            "name": text,
                                            "url": href
                                        }
                            except Exception:
                                continue

                    courses_found_count = len(discovered_courses)
                    logger.info(f"Discovered {courses_found_count} candidate courses on dashboard")

                    # Upsert discovered courses into database
                    for cid, cinfo in discovered_courses.items():
                        existing_course = session.exec(
                            select(Course).where(Course.moodle_course_id == cid)
                        ).first()

                        if not existing_course:
                            new_course = Course(
                                moodle_course_id=cid,
                                full_name=cinfo["name"],
                                moodle_url=cinfo["url"],
                                is_active=True,
                                last_synced_at=datetime.now(timezone.utc)
                            )
                            session.add(new_course)
                            session.commit()
                            session.refresh(new_course)
                            new_items_count += 1
                            _log_activity(
                                session,
                                event_type="course_discovered",
                                message=f"Discovered new course: {cinfo['name']}",
                                severity="info",
                                details={"course_id": new_course.id, "moodle_course_id": cid}
                            )
                        else:
                            existing_course.last_synced_at = datetime.now(timezone.utc)
                            session.add(existing_course)
                            session.commit()

                    # Scan each active course for activities
                    active_courses = session.exec(select(Course).where(Course.is_active == True)).all()
                    for idx, c in enumerate(active_courses):
                        _current_sync_status["current_stage"] = "scanning_activities"
                        _current_sync_status["progress_message"] = f"Scanning activities for {c.full_name} ({idx+1}/{len(active_courses)})..."

                        try:
                            page.goto(c.moodle_url, timeout=30000, wait_until="domcontentloaded")
                            page.wait_for_timeout(1000)

                            # Save course snapshot
                            c_snapshot = LOGS_DIR / f"course_{c.moodle_course_id}_snapshot.html"
                            c_snapshot.write_text(page.content(), encoding="utf-8", errors="replace")

                            # Look for activity links
                            activity_links = page.query_selector_all('a[href*="/mod/"]')
                            for alink in activity_links:
                                ahref = alink.get_attribute("href") or ""
                                atitle = (alink.inner_text() or "").strip()
                                if not ahref or not atitle or len(atitle) < 2:
                                    continue

                                # Determine activity type from URL
                                act_type = "other"
                                if "/mod/assign/" in ahref:
                                    act_type = "assignment"
                                elif "/mod/quiz/" in ahref:
                                    act_type = "quiz"
                                elif "/mod/resource/" in ahref or "/mod/folder/" in ahref:
                                    act_type = "resource"
                                elif "/mod/forum/" in ahref:
                                    act_type = "forum"
                                elif "/mod/attendance/" in ahref:
                                    act_type = "attendance"

                                # Extract unique item ID
                                item_id = ahref
                                if "id=" in ahref:
                                    item_id = ahref.split("id=")[1].split("&")[0]

                                existing_act = session.exec(
                                    select(MoodleActivity).where(MoodleActivity.moodle_item_id == item_id)
                                ).first()

                                activities_found_count += 1

                                if not existing_act:
                                    new_act = MoodleActivity(
                                        course_id=c.id,
                                        moodle_item_id=item_id,
                                        title=atitle,
                                        activity_type=act_type,
                                        moodle_url=ahref,
                                        has_deadline=False,
                                        due_date=None,
                                        status="new"
                                    )
                                    session.add(new_act)
                                    session.commit()
                                    new_items_count += 1
                                    _log_activity(
                                        session,
                                        event_type="activity_discovered",
                                        message=f"Discovered {act_type}: {atitle} ({c.full_name})",
                                        severity="info",
                                        details={"activity_type": act_type, "course": c.full_name}
                                    )
                        except Exception as ce:
                            logger.warning(f"Error scanning course {c.full_name}: {ce}")
                            continue

                finally:
                    browser.close()

            # Mark sync run as completed successfully
            sync_run.completed_at = datetime.now(timezone.utc)
            sync_run.status = "completed"
            sync_run.courses_found = courses_found_count
            sync_run.activities_found = activities_found_count
            sync_run.new_items_found = new_items_count
            session.add(sync_run)
            session.commit()
            session.refresh(sync_run)

            _log_activity(
                session,
                event_type="moodle_check_completed",
                message=f"Moodle sync completed: {courses_found_count} courses, {activities_found_count} activities ({new_items_count} new)",
                severity="success",
                details={
                    "courses_found": courses_found_count,
                    "activities_found": activities_found_count,
                    "new_items_found": new_items_count
                }
            )

            _current_sync_status["current_stage"] = "completed"
            _current_sync_status["progress_message"] = f"Sync complete! Found {courses_found_count} courses, {activities_found_count} activities ({new_items_count} new items)."
            return sync_run

        except Exception as e:
            error_str = str(e)
            logger.error(f"Sync failed: {error_str}", exc_info=True)
            sync_run.completed_at = datetime.now(timezone.utc)
            sync_run.status = "failed"
            sync_run.error_message = error_str
            session.add(sync_run)
            session.commit()
            session.refresh(sync_run)

            _log_activity(
                session,
                event_type="error",
                message=f"Moodle sync failed: {error_str}",
                severity="error",
                details={"error": error_str}
            )

            _current_sync_status["current_stage"] = "failed"
            _current_sync_status["progress_message"] = f"Sync failed: {error_str}"
            return sync_run

        finally:
            _current_sync_status["is_syncing"] = False
            _sync_lock.release()

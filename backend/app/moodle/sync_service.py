import re
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

def parse_moodle_datetime(raw: str) -> Optional[datetime]:
    """Parses various Moodle date formats into a timezone-aware UTC datetime."""
    if not raw:
        return None
    raw = raw.strip()
    formats = [
        "%A, %d %B %Y, %I:%M %p",
        "%d %B %Y, %I:%M %p",
        "%A, %d %b %Y, %I:%M %p",
        "%d %b %Y, %I:%M %p",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    # Regex fallback if date is embedded in longer string (e.g. "Due: Sunday, 31 May 2026, 11:59 PM")
    match = re.search(r'([A-Za-z]+,\s+\d{1,2}\s+[A-Za-z]+\s+\d{4},\s+\d{1,2}:\d{2}\s+[AP]M)', raw)
    if match:
        for fmt in formats:
            try:
                dt = datetime.strptime(match.group(1), fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None

def clean_course_title(raw_text: str) -> str:
    """Removes redundant UI label prefixes from course titles."""
    text = raw_text.strip()
    # Remove leading 'Course name\n' if present
    text = re.sub(r'^Course name\s+', '', text, flags=re.IGNORECASE)
    # Take first clean line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        text = lines[0]
    return text

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
                    "Moodle session not found. Please click 'Sign in with Microsoft Edge' in Settings."
                )

            _current_sync_status["current_stage"] = "authenticating"
            _current_sync_status["progress_message"] = "Connecting to Moodle via Microsoft Edge..."

            courses_found_count = 0
            activities_found_count = 0
            new_items_count = 0

            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(channel="msedge", headless=True)
                except Exception:
                    browser = p.chromium.launch(headless=True)

                try:
                    context = browser.new_context(storage_state=str(STORAGE_STATE_FILE))
                    page = context.new_page()

                    # 3. Discover courses from /my/courses.php (Moodle 4 primary courses directory)
                    my_courses_url = moodle_url.rstrip("/") + "/my/courses.php"
                    _current_sync_status["current_stage"] = "discovering_courses"
                    _current_sync_status["progress_message"] = f"Loading course catalog: {my_courses_url}..."
                    logger.info(f"Navigating to courses page: {my_courses_url}")
                    
                    try:
                        page.goto(my_courses_url, timeout=45000, wait_until="domcontentloaded")
                        page.wait_for_timeout(2000)
                    except Exception as nav_err:
                        logger.warning(f"Failed to load /my/courses.php ({nav_err}), trying /my/...")
                        page.goto(moodle_url.rstrip("/") + "/my/", timeout=45000, wait_until="domcontentloaded")
                        page.wait_for_timeout(2000)

                    # Check if session has expired (redirected to Microsoft or login page)
                    current_url = page.url.lower()
                    if any(ms in current_url for ms in ["microsoft", "live.com", "msft"]) or ("/login/" in current_url and "/my" not in current_url):
                        raise PermissionError("Moodle session expired — Sign in again")

                    # Save diagnostic snapshot
                    snapshot_file = LOGS_DIR / "moodle_dashboard_snapshot.html"
                    snapshot_file.write_text(page.content(), encoding="utf-8", errors="replace")

                    # Extract all course cards from Moodle DOM
                    course_cards = page.query_selector_all('.dashboard-card, [data-region="course-content"], .course-info-container')
                    raw_courses: Dict[str, Dict[str, Any]] = {}

                    for card in course_cards:
                        link = card.query_selector('a[href*="/course/view.php?id="]')
                        if not link:
                            continue
                        href = link.get_attribute("href") or ""
                        if "id=" not in href:
                            continue
                        cid = href.split("id=")[1].split("&")[0]
                        if not cid or not cid.isdigit():
                            continue

                        # Extract title
                        title_elem = card.query_selector('.coursename, .course-name, h5, .multiline')
                        title_text = title_elem.inner_text().strip() if title_elem else link.inner_text().strip()
                        cleaned_title = clean_course_title(title_text)

                        # Extract course short name / category / semester code
                        cat_elem = card.query_selector('.categoryname, .text-muted, .course-category')
                        short_name_text = cat_elem.inner_text().strip() if cat_elem else ""
                        short_name_clean = re.sub(r'^Course short name\s*', '', short_name_text, flags=re.IGNORECASE).strip()

                        # Extract 4-digit semester code (e.g. 2601, 2503)
                        sem_match = re.search(r'\((\d{4})-\d+\)', short_name_clean) or re.search(r'\((\d{4})\)', short_name_clean)
                        semester_code = int(sem_match.group(1)) if sem_match else None

                        raw_courses[cid] = {
                            "id": cid,
                            "title": cleaned_title,
                            "short_name": short_name_clean,
                            "semester_code": semester_code,
                            "url": href,
                        }

                    courses_found_count = len(raw_courses)
                    logger.info(f"Discovered {courses_found_count} courses on Moodle")

                    # Determine the active semester (highest semester code, e.g. 2601)
                    max_semester = None
                    semester_codes = [c["semester_code"] for c in raw_courses.values() if c["semester_code"]]
                    if semester_codes:
                        max_semester = max(semester_codes)
                        logger.info(f"Detected latest/current semester code: {max_semester}")

                    # Upsert discovered courses
                    for cid, cinfo in raw_courses.items():
                        is_active = (cinfo["semester_code"] == max_semester) if max_semester else True
                        existing_course = session.exec(
                            select(Course).where(Course.moodle_course_id == cid)
                        ).first()

                        term_tag = f"Semester {cinfo['semester_code']}" if cinfo["semester_code"] else None

                        if not existing_course:
                            new_course = Course(
                                moodle_course_id=cid,
                                full_name=cinfo["title"],
                                short_name=cinfo["short_name"],
                                term_or_category=term_tag,
                                moodle_url=cinfo["url"],
                                is_active=is_active,
                                last_synced_at=datetime.now(timezone.utc)
                            )
                            session.add(new_course)
                            session.commit()
                            session.refresh(new_course)
                            new_items_count += 1
                            _log_activity(
                                session,
                                event_type="course_discovered",
                                message=f"Discovered course: {cinfo['title']} ({'Active' if is_active else 'Archived'})",
                                severity="info",
                                details={"course_id": new_course.id, "moodle_course_id": cid, "active": is_active}
                            )
                        else:
                            existing_course.full_name = cinfo["title"]
                            existing_course.short_name = cinfo["short_name"]
                            existing_course.term_or_category = term_tag
                            existing_course.is_active = is_active
                            existing_course.last_synced_at = datetime.now(timezone.utc)
                            session.add(existing_course)
                            session.commit()

                    # 4. Scan active courses for activities & deadlines
                    active_courses = session.exec(select(Course).where(Course.is_active == True)).all()
                    for idx, c in enumerate(active_courses):
                        _current_sync_status["current_stage"] = "scanning_activities"
                        _current_sync_status["progress_message"] = f"Scanning {c.full_name} ({idx+1}/{len(active_courses)})..."
                        logger.info(f"Scanning course: {c.full_name} (ID {c.moodle_course_id})")

                        try:
                            page.goto(c.moodle_url, timeout=35000, wait_until="domcontentloaded")
                            page.wait_for_timeout(1500)

                            # Find all activity links (/mod/)
                            mod_links = page.query_selector_all('a[href*="/mod/"]')
                            course_activities: Dict[str, Dict[str, Any]] = {}

                            for alink in mod_links:
                                ahref = alink.get_attribute("href") or ""
                                atitle = (alink.inner_text() or "").strip()
                                if not ahref or "id=" not in ahref:
                                    continue

                                # Clean title
                                atitle_clean = atitle.split("\n")[0].strip()
                                item_id = ahref.split("id=")[1].split("&")[0]

                                # Classify activity type
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
                                elif "/mod/url/" in ahref:
                                    act_type = "resource"

                                if item_id not in course_activities and atitle_clean:
                                    course_activities[item_id] = {
                                        "id": item_id,
                                        "title": atitle_clean,
                                        "type": act_type,
                                        "url": ahref,
                                    }

                            # Deep inspect assignments for due date & submission status
                            for item_id, ainfo in course_activities.items():
                                activities_found_count += 1
                                due_date = None
                                has_deadline = False
                                submission_status = None
                                act_status = "new"

                                if ainfo["type"] == "assignment":
                                    try:
                                        page.goto(ainfo["url"], timeout=25000, wait_until="domcontentloaded")
                                        page.wait_for_timeout(1000)

                                        # Parse submission status table
                                        rows = page.query_selector_all('.submissionstatustable tr, .generaltable tr')
                                        for row in rows:
                                            th = row.query_selector('th, td:first-child')
                                            td = row.query_selector('td:last-child')
                                            if not th or not td:
                                                continue
                                            header = th.inner_text().strip().lower()
                                            val = td.inner_text().strip()

                                            if "due" in header:
                                                parsed_dt = parse_moodle_datetime(val)
                                                if parsed_dt:
                                                    due_date = parsed_dt
                                                    has_deadline = True
                                            elif "submission status" in header:
                                                submission_status = val
                                                if "submitted" in val.lower():
                                                    act_status = "submitted"

                                        # Fallback to instructions snippet if due date not in table
                                        if not has_deadline:
                                            intro_elem = page.query_selector('[data-region="activity-information"], #intro, .activity-description')
                                            if intro_elem:
                                                intro_text = intro_elem.inner_text()
                                                parsed_dt = parse_moodle_datetime(intro_text)
                                                if parsed_dt:
                                                    due_date = parsed_dt
                                                    has_deadline = True
                                    except Exception as aerr:
                                        logger.debug(f"Could not inspect assignment {ainfo['title']}: {aerr}")

                                # Upsert activity into database
                                existing_act = session.exec(
                                    select(MoodleActivity).where(MoodleActivity.moodle_item_id == item_id)
                                ).first()

                                if not existing_act:
                                    new_act = MoodleActivity(
                                        course_id=c.id,
                                        moodle_item_id=item_id,
                                        title=ainfo["title"],
                                        activity_type=ainfo["type"],
                                        moodle_url=ainfo["url"],
                                        has_deadline=has_deadline,
                                        due_date=due_date,
                                        status=act_status,
                                        submission_status_moodle=submission_status,
                                        created_at=datetime.now(timezone.utc),
                                        updated_at=datetime.now(timezone.utc)
                                    )
                                    session.add(new_act)
                                    session.commit()
                                    new_items_count += 1
                                    _log_activity(
                                        session,
                                        event_type="activity_discovered",
                                        message=f"Discovered {ainfo['type']}: {ainfo['title']} ({c.short_name or c.full_name})",
                                        severity="info",
                                        details={
                                            "type": ainfo["type"],
                                            "title": ainfo["title"],
                                            "has_deadline": has_deadline,
                                            "due_date": due_date.isoformat() if due_date else None
                                        }
                                    )
                                else:
                                    # Update dynamic fields
                                    existing_act.has_deadline = has_deadline
                                    existing_act.due_date = due_date
                                    if submission_status:
                                        existing_act.submission_status_moodle = submission_status
                                    if act_status == "submitted" and existing_act.status != "submitted":
                                        existing_act.status = "submitted"
                                    existing_act.updated_at = datetime.now(timezone.utc)
                                    session.add(existing_act)
                                    session.commit()

                        except Exception as ce:
                            logger.warning(f"Error scanning course {c.full_name}: {ce}")
                            continue

                finally:
                    browser.close()

            # Finalize SyncRun
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
                message=f"Sync completed: {courses_found_count} courses ({len(active_courses)} active), {activities_found_count} activities ({new_items_count} new)",
                severity="success",
                details={
                    "courses_found": courses_found_count,
                    "active_courses": len(active_courses),
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

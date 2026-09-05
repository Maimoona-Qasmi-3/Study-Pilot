import pytest
from datetime import datetime, timezone
from sqlmodel import Session, SQLModel, create_engine
from app.models import Course, MoodleActivity, SystemSetting, SyncRun
from app.api.dashboard import get_dashboard_stats
from app.api.courses import list_courses, get_course, update_course, CourseUpdate
from app.api.activities import list_activities, get_calendar_events, update_activity, ActivityUpdate
from app.api.settings import get_settings, update_settings
from app.api.moodle import sync_status, get_auth_progress

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_dashboard_stats_empty(session: Session):
    stats = get_dashboard_stats(session=session)
    assert stats["active_courses_count"] == 0
    assert stats["new_activities_count"] == 0
    assert stats["upcoming_deadlines_count"] == 0
    assert "is_expired" in stats
    assert "session_message" in stats

def test_dashboard_stats_detects_expired_session(session: Session):
    # Add a failed sync run with expired message
    failed_sync = SyncRun(
        status="failed",
        trigger="manual",
        error_message="Moodle session expired — Sign in again"
    )
    session.add(failed_sync)
    session.commit()

    stats = get_dashboard_stats(session=session)
    assert stats["is_expired"] is True
    assert stats["session_message"] == "Moodle session expired — Sign in again"

def test_courses_and_activities_endpoints(session: Session):
    # Create test course
    course = Course(
        moodle_course_id="202",
        full_name="Software Engineering (CS3001)",
        short_name="SE",
        moodle_url="https://moodle.university.edu/course/view.php?id=202",
        is_active=True
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    # Activity 1: With due date
    act1 = MoodleActivity(
        course_id=course.id,
        moodle_item_id="assign_1",
        title="Sprint 1 Backlog",
        activity_type="assignment",
        moodle_url="https://moodle.university.edu/mod/assign/view.php?id=1",
        has_deadline=True,
        due_date=datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc),
        status="new"
    )
    # Activity 2: No deadline
    act2 = MoodleActivity(
        course_id=course.id,
        moodle_item_id="res_2",
        title="Lecture Notes PDF",
        activity_type="resource",
        moodle_url="https://moodle.university.edu/mod/resource/view.php?id=2",
        has_deadline=False,
        due_date=None,
        status="new"
    )
    session.add(act1)
    session.add(act2)
    session.commit()

    # Test list_courses
    courses = list_courses(active_only=True, session=session)
    assert len(courses) == 1
    assert courses[0]["activity_count"] == 2

    # Test get_calendar_events (must only return strict deadline items)
    calendar_events = get_calendar_events(session=session)
    assert len(calendar_events) == 1
    assert calendar_events[0]["title"] == "Sprint 1 Backlog"

    # Test list_activities with has_deadline=False filter
    no_deadline_items = list_activities(has_deadline=False, session=session)
    assert len(no_deadline_items) == 1
    assert no_deadline_items[0]["title"] == "Lecture Notes PDF"

    # Test update_activity status
    updated = update_activity(
        activity_id=act1.id,
        update_data=ActivityUpdate(status="ready_for_review"),
        session=session
    )
    assert updated.status == "ready_for_review"

def test_settings_endpoints(session: Session):
    update_res = update_settings(payload={"moodle_url": "https://moodle.myuniversity.edu"}, session=session)
    assert update_res["status"] == "ok"

    current = get_settings(session=session)
    assert current["settings"]["moodle_url"] == "https://moodle.myuniversity.edu"

def test_moodle_sync_status_endpoint():
    status = sync_status()
    assert "is_syncing" in status
    assert "progress_message" in status

def test_auth_progress_endpoint():
    prog = get_auth_progress()
    assert "is_logging_in" in prog
    assert "status" in prog
    assert "message" in prog

def test_workspaces_api_endpoints(session: Session):
    import shutil
    from pathlib import Path
    from app.api.workspaces import (
        list_workflow_profiles,
        get_workspace_info,
        initialize_workspace,
        WorkspaceInitRequest,
        generate_report,
        download_report,
    )

    # 1. Test profiles list
    profiles = list_workflow_profiles()
    assert len(profiles) >= 6

    # 2. Setup course & activity
    course = Course(
        moodle_course_id="api_course_1",
        full_name="Discrete Structures",
        short_name="CSC-210",
        moodle_url="https://lms.shu.edu.pk/course/view.php?id=210",
        is_active=True
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    act = MoodleActivity(
        course_id=course.id,
        moodle_item_id="api_item_555",
        title="Propositional Logic Lab",
        description_text="Implement truth table generator.",
        activity_type="assignment",
        moodle_url="https://lms.shu.edu.pk/mod/assign/view.php?id=555",
        has_deadline=True,
    )
    session.add(act)
    session.commit()
    session.refresh(act)

    # 3. Test uninitialized info
    info = get_workspace_info(activity_id=act.id, session=session)
    assert info["initialized"] is False

    # 4. Test initialize
    init_res = initialize_workspace(
        activity_id=act.id,
        req=WorkspaceInitRequest(workflow_profile_id="python_scripting"),
        session=session
    )
    assert init_res["success"] is True
    workspace_dir = Path(init_res["absolute_path"])

    try:
        # Check info again
        info2 = get_workspace_info(activity_id=act.id, session=session)
        assert info2["initialized"] is True
        assert "main.py" in info2["src_files"]

        # 5. Test generate report
        report_res = generate_report(activity_id=act.id, session=session)
        assert report_res["success"] is True
        assert report_res["filename"].endswith(".docx")

        # 6. Test download report endpoint
        resp = download_report(activity_id=act.id, session=session)
        assert resp.media_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert resp.filename == report_res["filename"]

    finally:
        if workspace_dir.exists():
            shutil.rmtree(workspace_dir)

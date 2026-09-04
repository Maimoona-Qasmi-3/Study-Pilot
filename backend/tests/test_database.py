import pytest
from datetime import datetime, timezone
from sqlmodel import Session, create_engine, SQLModel, select
from app.models import Course, MoodleActivity, SyncRun, AgentActivityLog, SystemSetting

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_and_query_course(session: Session):
    course = Course(
        moodle_course_id="101",
        full_name="Object Oriented Programming",
        short_name="OOP",
        moodle_url="https://moodle.university.edu/course/view.php?id=101",
        term_or_category="Spring 2026",
        is_active=True
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    assert course.id is not None
    assert course.full_name == "Object Oriented Programming"
    assert course.is_active is True

    # Query
    db_course = session.exec(select(Course).where(Course.moodle_course_id == "101")).first()
    assert db_course is not None
    assert db_course.short_name == "OOP"

def test_moodle_activity_deadline_distinction(session: Session):
    course = Course(
        moodle_course_id="102",
        full_name="Digital Logic Design",
        moodle_url="https://moodle.university.edu/course/view.php?id=102"
    )
    session.add(course)
    session.commit()
    session.refresh(course)

    # Activity with real deadline
    assign = MoodleActivity(
        course_id=course.id,
        moodle_item_id="assign_555",
        title="Lab 1: Logic Gates",
        activity_type="assignment",
        moodle_url="https://moodle.university.edu/mod/assign/view.php?id=555",
        has_deadline=True,
        due_date=datetime(2026, 9, 15, 23, 59, tzinfo=timezone.utc),
        status="new"
    )

    # Resource without deadline
    resource = MoodleActivity(
        course_id=course.id,
        moodle_item_id="resource_666",
        title="Lecture 1 Slides PDF",
        activity_type="resource",
        moodle_url="https://moodle.university.edu/mod/resource/view.php?id=666",
        has_deadline=False,
        due_date=None,
        status="new"
    )

    session.add(assign)
    session.add(resource)
    session.commit()

    # Query only activities with deadlines
    deadline_items = session.exec(select(MoodleActivity).where(MoodleActivity.has_deadline == True)).all()
    assert len(deadline_items) == 1
    assert deadline_items[0].title == "Lab 1: Logic Gates"
    assert deadline_items[0].due_date is not None

    # Query no deadline items
    no_deadline_items = session.exec(select(MoodleActivity).where(MoodleActivity.has_deadline == False)).all()
    assert len(no_deadline_items) == 1
    assert no_deadline_items[0].title == "Lecture 1 Slides PDF"
    assert no_deadline_items[0].due_date is None

def test_sync_run_record(session: Session):
    sync_run = SyncRun(
        trigger="manual",
        status="running"
    )
    session.add(sync_run)
    session.commit()
    session.refresh(sync_run)

    assert sync_run.status == "running"
    assert sync_run.trigger == "manual"

    # Complete run
    sync_run.status = "completed"
    sync_run.completed_at = datetime.now(timezone.utc)
    sync_run.courses_found = 4
    sync_run.activities_found = 12
    sync_run.new_items_found = 2
    session.add(sync_run)
    session.commit()

    latest = session.exec(select(SyncRun).order_by(SyncRun.started_at.desc())).first()
    assert latest is not None
    assert latest.courses_found == 4
    assert latest.new_items_found == 2

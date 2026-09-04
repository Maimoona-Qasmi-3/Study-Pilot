from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from ..database import get_session
from ..models import Course, MoodleActivity, SyncRun
from ..config import STORAGE_STATE_FILE

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(session: Session = Depends(get_session)):
    now = datetime.now(timezone.utc)

    # Active courses
    active_courses_count = session.exec(
        select(func.count(Course.id)).where(Course.is_active == True)
    ).one()

    # New activities
    new_activities_count = session.exec(
        select(func.count(MoodleActivity.id)).where(MoodleActivity.status == "new")
    ).one()

    # Upcoming deadlines (strict deadline, not yet submitted)
    upcoming_deadlines_count = session.exec(
        select(func.count(MoodleActivity.id))
        .where(MoodleActivity.has_deadline == True)
        .where(MoodleActivity.due_date >= now)
        .where(MoodleActivity.status != "submitted")
    ).one()

    # Ready for review
    ready_for_review_count = session.exec(
        select(func.count(MoodleActivity.id)).where(MoodleActivity.status == "ready_for_review")
    ).one()

    # Latest sync run
    latest_sync = session.exec(
        select(SyncRun).order_by(SyncRun.started_at.desc())
    ).first()

    return {
        "active_courses_count": active_courses_count,
        "new_activities_count": new_activities_count,
        "upcoming_deadlines_count": upcoming_deadlines_count,
        "ready_for_review_count": ready_for_review_count,
        "is_authenticated": STORAGE_STATE_FILE.exists(),
        "latest_sync": latest_sync,
    }

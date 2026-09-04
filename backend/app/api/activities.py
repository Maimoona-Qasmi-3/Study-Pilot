from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from ..database import get_session
from ..models import MoodleActivity, Course

router = APIRouter(prefix="/activities", tags=["activities"])

class ActivityUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    workflow_id: Optional[str] = None

@router.get("/")
def list_activities(
    course_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    has_deadline: Optional[bool] = None,
    status: Optional[str] = None,
    upcoming_only: bool = False,
    session: Session = Depends(get_session)
):
    query = select(MoodleActivity)
    if course_id:
        query = query.where(MoodleActivity.course_id == course_id)
    if activity_type:
        query = query.where(MoodleActivity.activity_type == activity_type)
    if has_deadline is not None:
        query = query.where(MoodleActivity.has_deadline == has_deadline)
    if status:
        query = query.where(MoodleActivity.status == status)
    if upcoming_only:
        now = datetime.now(timezone.utc)
        query = query.where(MoodleActivity.has_deadline == True).where(MoodleActivity.due_date >= now)

    query = query.order_by(MoodleActivity.due_date.asc().nulls_last(), MoodleActivity.created_at.desc())
    activities = session.exec(query).all()

    # Join course names for UI convenience
    results = []
    course_cache = {}
    for act in activities:
        if act.course_id not in course_cache:
            c = session.get(Course, act.course_id)
            course_cache[act.course_id] = c.full_name if c else "Unknown Course"
        results.append({
            **act.model_dump(),
            "course_name": course_cache[act.course_id]
        })
    return results

@router.get("/calendar/events")
def get_calendar_events(session: Session = Depends(get_session)):
    """Returns only activities with confirmed due dates for the calendar."""
    query = select(MoodleActivity).where(
        MoodleActivity.has_deadline == True
    ).where(
        MoodleActivity.due_date.is_not(None)
    ).order_by(MoodleActivity.due_date.asc())

    activities = session.exec(query).all()
    events = []
    course_cache = {}
    for act in activities:
        if act.course_id not in course_cache:
            c = session.get(Course, act.course_id)
            course_cache[act.course_id] = c.full_name if c else "Course"
        events.append({
            "id": act.id,
            "title": act.title,
            "course_id": act.course_id,
            "course_name": course_cache[act.course_id],
            "due_date": act.due_date.isoformat() if act.due_date else None,
            "activity_type": act.activity_type,
            "status": act.status,
            "priority": act.priority,
            "moodle_url": act.moodle_url
        })
    return events

@router.get("/{activity_id}")
def get_activity(activity_id: str, session: Session = Depends(get_session)):
    activity = session.get(MoodleActivity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    course = session.get(Course, activity.course_id)
    return {
        **activity.model_dump(),
        "course": course
    }

@router.patch("/{activity_id}")
def update_activity(activity_id: str, update_data: ActivityUpdate, session: Session = Depends(get_session)):
    activity = session.get(MoodleActivity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if update_data.status is not None:
        activity.status = update_data.status
    if update_data.priority is not None:
        activity.priority = update_data.priority
    if update_data.workflow_id is not None:
        activity.workflow_id = update_data.workflow_id
    activity.updated_at = datetime.now(timezone.utc)
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity

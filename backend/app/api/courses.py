from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from ..database import get_session
from ..models import Course, MoodleActivity

router = APIRouter(prefix="/courses", tags=["courses"])

class CourseUpdate(BaseModel):
    is_active: Optional[bool] = None
    default_workflow_id: Optional[str] = None

@router.get("/")
def list_courses(
    active_only: bool = False,
    search: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(Course)
    if active_only:
        query = query.where(Course.is_active == True)
    if search:
        query = query.where(Course.full_name.contains(search))
    query = query.order_by(Course.full_name)
    courses = session.exec(query).all()

    results = []
    for c in courses:
        activity_count = len(session.exec(select(MoodleActivity.id).where(MoodleActivity.course_id == c.id)).all())
        results.append({
            **c.model_dump(),
            "activity_count": activity_count
        })
    return results

@router.get("/{course_id}")
def get_course(course_id: str, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    activities = session.exec(
        select(MoodleActivity).where(MoodleActivity.course_id == course_id).order_by(MoodleActivity.due_date.asc())
    ).all()
    return {
        **course.model_dump(),
        "activities": activities
    }

@router.patch("/{course_id}")
def update_course(course_id: str, update_data: CourseUpdate, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if update_data.is_active is not None:
        course.is_active = update_data.is_active
    if update_data.default_workflow_id is not None:
        course.default_workflow_id = update_data.default_workflow_id
    session.add(course)
    session.commit()
    session.refresh(course)
    return course

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class MoodleActivity(SQLModel, table=True):
    __tablename__ = "moodle_activity"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    course_id: str = Field(foreign_key="course.id", index=True, description="Foreign key to Course")
    moodle_item_id: str = Field(index=True, unique=True, description="Unique Moodle item identifier e.g. cmid or assign id")
    title: str = Field(description="Title of the activity")
    description_html: Optional[str] = Field(default=None, description="Raw HTML description/instructions from Moodle")
    description_text: Optional[str] = Field(default=None, description="Sanitized plain text description")
    activity_type: str = Field(
        default="other",
        index=True,
        description="Type: assignment, quiz, resource, file, forum, attendance, other"
    )
    moodle_url: str = Field(description="URL to the activity in Moodle")
    has_deadline: bool = Field(default=False, index=True, description="True if activity has a verifiable due date")
    due_date: Optional[datetime] = Field(default=None, index=True, description="Submission due date (NULL if no deadline)")
    cutoff_date: Optional[datetime] = Field(default=None, description="Late cutoff date if configured")
    status: str = Field(
        default="new",
        index=True,
        description="Status: new, not_started, agent_working, ready_for_review, changes_requested, approved, uploading, uploaded, submitted, needs_attention, ignored"
    )
    priority: str = Field(default="medium", description="Priority: low, medium, high, urgent")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID assigned to this activity")
    workspace_path: Optional[str] = Field(default=None, description="Relative path to local workspace")
    workspace_status: str = Field(default="uninitialized", index=True, description="Workspace status: uninitialized, ready, in_progress, completed")
    submission_status_moodle: Optional[str] = Field(default=None, description="Moodle submission state e.g. Submitted for grading, No attempt")
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

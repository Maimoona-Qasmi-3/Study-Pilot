import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Course(SQLModel, table=True):
    __tablename__ = "course"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    moodle_course_id: str = Field(index=True, unique=True, description="Unique ID from Moodle URL e.g. course/view.php?id=XYZ")
    full_name: str = Field(description="Full course title")
    short_name: Optional[str] = Field(default=None, description="Course abbreviation or code")
    moodle_url: str = Field(description="URL to the course home")
    term_or_category: Optional[str] = Field(default=None, description="Academic term or category tag")
    is_active: bool = Field(default=True, index=True, description="Active status in Moodle")
    default_workflow_id: Optional[str] = Field(default=None, description="Bound default workflow ID")
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)
    last_synced_at: Optional[datetime] = Field(default=None)

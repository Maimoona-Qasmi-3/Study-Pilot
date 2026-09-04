import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AgentActivityLog(SQLModel, table=True):
    __tablename__ = "agent_activity_log"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    timestamp: datetime = Field(default_factory=get_utc_now, index=True)
    event_type: str = Field(index=True, description="moodle_check_started, course_discovered, activity_discovered, error, etc.")
    message: str = Field(description="Human readable description of the event")
    details_json: Optional[str] = Field(default=None, description="Serialized JSON with context data")
    severity: str = Field(default="info", description="info, success, warning, error")

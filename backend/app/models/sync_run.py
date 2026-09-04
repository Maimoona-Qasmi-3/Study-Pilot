import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SyncRun(SQLModel, table=True):
    __tablename__ = "sync_run"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    started_at: datetime = Field(default_factory=get_utc_now, index=True)
    completed_at: Optional[datetime] = Field(default=None)
    status: str = Field(default="running", index=True, description="running, completed, failed")
    trigger: str = Field(default="manual", index=True, description="manual or scheduled")
    courses_found: int = Field(default=0)
    activities_found: int = Field(default=0)
    new_items_found: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SystemSetting(SQLModel, table=True):
    __tablename__ = "system_setting"

    key: str = Field(primary_key=True, description="Setting key e.g. moodle_url, check_interval")
    value: str = Field(description="Stored value (string or JSON)")
    updated_at: datetime = Field(default_factory=get_utc_now)

from typing import Dict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..database import get_session
from ..models import SystemSetting
from ..config import STORAGE_STATE_FILE

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("/")
def get_settings(session: Session = Depends(get_session)):
    settings_records = session.exec(select(SystemSetting)).all()
    settings_dict = {s.key: s.value for s in settings_records}

    # Ensure default keys
    if "moodle_url" not in settings_dict:
        settings_dict["moodle_url"] = ""

    return {
        "settings": settings_dict,
        "is_authenticated": STORAGE_STATE_FILE.exists(),
        "storage_state_path": str(STORAGE_STATE_FILE),
    }

@router.put("/")
def update_settings(payload: Dict[str, str], session: Session = Depends(get_session)):
    for key, val in payload.items():
        existing = session.get(SystemSetting, key)
        if existing:
            existing.value = val
            existing.updated_at = datetime.now(timezone.utc)
            session.add(existing)
        else:
            session.add(SystemSetting(key=key, value=val))
    session.commit()
    return {"status": "ok", "updated_keys": list(payload.keys())}

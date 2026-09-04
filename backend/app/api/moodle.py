import threading
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from ..database import get_session
from ..models import SyncRun, SystemSetting
from ..moodle.sync_service import run_moodle_sync, get_sync_status
from ..moodle.auth import launch_interactive_login, verify_session, is_session_saved

router = APIRouter(prefix="/moodle", tags=["moodle"])

@router.post("/sync")
def trigger_manual_sync(background_tasks: BackgroundTasks):
    """
    Triggers manual 'Check Moodle Now' sync.
    Runs asynchronously and updates sync status for polling.
    """
    status = get_sync_status()
    if status.get("is_syncing"):
        raise HTTPException(status_code=409, detail="A synchronization is already running.")

    # Run in background task
    background_tasks.add_task(run_moodle_sync, trigger="manual")
    return {
        "status": "started",
        "message": "Moodle sync triggered successfully"
    }

@router.get("/sync/status")
def sync_status():
    """Returns live sync status for frontend polling."""
    return get_sync_status()

@router.get("/runs")
def list_sync_runs(limit: int = 10, session: Session = Depends(get_session)):
    """Returns the history of sync runs."""
    runs = session.exec(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(limit)).all()
    return runs

@router.post("/auth/login")
def start_interactive_login(background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """
    Launches interactive headed browser window for user to log into Moodle.
    """
    setting = session.get(SystemSetting, "moodle_url")
    moodle_url = setting.value.strip() if setting and setting.value else None
    if not moodle_url:
        raise HTTPException(
            status_code=400,
            detail="Moodle URL is not configured. Please save your university Moodle URL in Settings first."
        )

    # Launch in separate thread
    thread = threading.Thread(target=launch_interactive_login, args=(moodle_url,), daemon=True)
    thread.start()

    return {
        "status": "launched",
        "message": "Browser login window opened. Please complete your university login in the browser window."
    }

@router.get("/auth/verify")
def verify_moodle_session(session: Session = Depends(get_session)):
    """Verifies whether the current saved session works headlessly."""
    setting = session.get(SystemSetting, "moodle_url")
    moodle_url = setting.value.strip() if setting and setting.value else None
    if not moodle_url:
        return {"valid": False, "message": "Moodle URL not configured."}
    return verify_session(moodle_url)

"""
Workspace API endpoints for Study Pilot.
Provides initialization, state querying, OS process launching, and report downloads.
"""

from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session

from ..database import get_session
from ..config import WORKSPACES_DIR
from ..models import MoodleActivity
from ..workspaces.profiles import get_all_profiles, WorkflowProfile
from ..workspaces.service import WorkspaceService
from ..workspaces.launcher import WindowsLauncher
from ..workspaces.docgen import DocumentGenerator

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceInitRequest(BaseModel):
    workflow_profile_id: Optional[str] = None


class WorkspaceLaunchRequest(BaseModel):
    tool: str  # "vscode", "explorer", "terminal"


@router.get("/profiles", response_model=List[WorkflowProfile])
def list_workflow_profiles():
    """List all available workflow profiles and templates."""
    return get_all_profiles()


@router.get("/{activity_id}")
def get_workspace_info(activity_id: str, session: Session = Depends(get_session)):
    """Get the current workspace status and disk contents for an activity."""
    try:
        return WorkspaceService.get_workspace_info(activity_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inspect workspace: {str(e)}")


@router.post("/{activity_id}/init")
def initialize_workspace(
    activity_id: str,
    req: WorkspaceInitRequest = WorkspaceInitRequest(),
    session: Session = Depends(get_session)
):
    """
    Idempotently initialize local workspace directories and starter files.
    Never overwrites existing user files.
    """
    try:
        return WorkspaceService.initialize_workspace(
            activity_id=activity_id,
            session=session,
            workflow_profile_id=req.workflow_profile_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize workspace: {str(e)}")


@router.post("/{activity_id}/launch")
def launch_workspace_tool(
    activity_id: str,
    req: WorkspaceLaunchRequest,
    session: Session = Depends(get_session)
):
    """Launch native Windows tools (VS Code, File Explorer, Terminal) in the workspace directory."""
    activity = session.get(MoodleActivity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    if not activity.workspace_path:
        # Auto-initialize if not yet initialized
        WorkspaceService.initialize_workspace(activity_id, session)
        session.refresh(activity)

    workspace_dir = WORKSPACES_DIR / activity.workspace_path
    if not workspace_dir.exists():
        raise HTTPException(status_code=404, detail="Workspace folder does not exist on disk")

    try:
        result = WindowsLauncher.launch(workspace_dir, req.tool)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch tool: {str(e)}")


@router.post("/{activity_id}/generate-report")
def generate_report(activity_id: str, session: Session = Depends(get_session)):
    """Generate standardized university DOCX report from workspace files and Moodle instructions."""
    try:
        result = DocumentGenerator.generate_report(activity_id, session)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/{activity_id}/download-report")
def download_report(activity_id: str, session: Session = Depends(get_session)):
    """Download the generated DOCX report for an activity."""
    activity = session.get(MoodleActivity, activity_id)
    if not activity or not activity.workspace_path:
        raise HTTPException(status_code=404, detail="Workspace not found")

    output_dir = WORKSPACES_DIR / activity.workspace_path / "output"
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="No output directory found")

    docx_files = list(output_dir.glob("*.docx"))
    if not docx_files:
        raise HTTPException(status_code=404, detail="No generated report found in workspace output")

    report_file = docx_files[0]
    return FileResponse(
        path=str(report_file),
        filename=report_file.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from ..database import get_session
from ..models import AgentActivityLog

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/")
def list_logs(
    limit: int = 50,
    severity: Optional[str] = None,
    session: Session = Depends(get_session)
):
    query = select(AgentActivityLog)
    if severity:
        query = query.where(AgentActivityLog.severity == severity)
    query = query.order_by(AgentActivityLog.timestamp.desc()).limit(limit)
    return session.exec(query).all()

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, CurrentUser
from app.services.metrics_service import MetricsService, AgentService

router = APIRouter(tags=["agents"])


class ChatIn(BaseModel):
    session_id: str | None = None
    message: str


@router.get("/metrics")
async def metrics(session_id: str = Query(...),
                  user: CurrentUser = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    return await MetricsService(db, user.company_id).session_metrics(session_id)


@router.get("/traces")
async def traces(session_id: str = Query(...),
                 user: CurrentUser = Depends(get_current_user),
                 db: AsyncSession = Depends(get_db)):
    rows = await AgentService(db, user.company_id).traces(session_id)
    return [
        {"agent_type": t.agent_type, "step": t.step, "status": t.status,
         "output_summary": t.output_summary,
         "created_at": t.created_at.isoformat() if t.created_at else None}
        for t in rows
    ]


@router.post("/agents/chat")
async def chat(data: ChatIn, user: CurrentUser = Depends(get_current_user),
               db: AsyncSession = Depends(get_db)):
    return await AgentService(db, user.company_id).chat(data.session_id, data.message)


@router.post("/agents/diagnose")
async def diagnose(session_id: str = Query(...),
                   user: CurrentUser = Depends(get_current_user),
                   db: AsyncSession = Depends(get_db)):
    return await AgentService(db, user.company_id).diagnose(session_id)

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, min_role, CurrentUser
from app.core import job_status
from app.schemas.forecasts import (
    GenerateIn, GenerateOut, SessionOut, StatusOut, ForecastRowOut,
)
from app.services.forecast_service import ForecastService
from app.tasks.forecast_tasks import generate_forecast

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


def _sess_out(s) -> SessionOut:
    return SessionOut(
        session_id=s.session_id, dataset_name=s.dataset_name, horizon=s.horizon,
        aggregation=s.aggregation, status=s.status, model_used=s.model_used,
        sku_count=s.sku_count, row_count=s.row_count, metrics=s.metrics,
        generated_at=s.generated_at.isoformat() if s.generated_at else None,
        published_at=s.published_at.isoformat() if s.published_at else None,
    )


@router.post("/generate", response_model=GenerateOut)
async def generate(data: GenerateIn, user: CurrentUser = Depends(min_role("planner")),
                   db: AsyncSession = Depends(get_db)):
    svc = ForecastService(db, user.company_id)
    sess = await svc.create_session(data, user.id)
    await db.commit()
    await job_status.set_status(sess.session_id, job_status.RUNNING)
    generate_forecast.delay(
        sess.session_id, user.company_id, data.aggregation,
        data.horizon, data.mapping, data.dataset_name,
    )
    return GenerateOut(session_id=sess.session_id, status="running")


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: CurrentUser = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    return [_sess_out(s) for s in await ForecastService(db, user.company_id).list_sessions()]


@router.get("/sessions/{session_id}", response_model=SessionOut)
async def get_session(session_id: str, user: CurrentUser = Depends(get_current_user),
                      db: AsyncSession = Depends(get_db)):
    s = await ForecastService(db, user.company_id).get_session(session_id)
    if not s:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found")
    return _sess_out(s)


@router.get("/sessions/{session_id}/status", response_model=StatusOut)
async def get_status(session_id: str, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    st = await job_status.get_status(session_id)
    if st is None:
        s = await ForecastService(db, user.company_id).get_session(session_id)
        st = (s.status if s else "unknown")
    return StatusOut(session_id=session_id, status=st)


@router.get("", response_model=list[ForecastRowOut])
async def list_forecasts(session_id: str = Query(...), product_id: str | None = Query(None),
                         user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    rows = await ForecastService(db, user.company_id).forecast_rows(session_id, product_id)
    return [
        ForecastRowOut(
            product_id=r.product_id, date=r.date.isoformat(),
            forecast_value=float(r.forecast_value),
            confidence_lower=float(r.confidence_lower) if r.confidence_lower is not None else None,
            confidence_upper=float(r.confidence_upper) if r.confidence_upper is not None else None,
            forecast_type=r.forecast_type,
        ) for r in rows
    ]


@router.post("/sessions/{session_id}/publish", response_model=SessionOut)
async def publish(session_id: str, user: CurrentUser = Depends(min_role("planner")),
                  db: AsyncSession = Depends(get_db)):
    try:
        s = await ForecastService(db, user.company_id).publish(session_id, user.id)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    await db.commit()
    return _sess_out(s)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user, CurrentUser
from app.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/kpis")
async def kpis(
    category: str | None = Query(None), brand: str | None = Query(None),
    state: str | None = Query(None), region: str | None = Query(None),
    channel: str | None = Query(None),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = {k: v for k, v in dict(
        category=category, brand=brand, state=state, region=region, channel=channel
    ).items() if v}
    return await DashboardService(db, user.company_id).kpis(filters)


@router.get("/filters")
async def filters(user: CurrentUser = Depends(get_current_user),
                  db: AsyncSession = Depends(get_db)):
    return await DashboardService(db, user.company_id).filters()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import min_role, CurrentUser
from app.schemas.importing import (
    SourceConfigIn, SourceConfigOut, MappingIn,
    ImportIn, ImportOut, LookupImportIn, LookupImportOut,
)
from app.services.import_service import ImportService

router = APIRouter(prefix="/import", tags=["import"])


def _src_out(s) -> SourceConfigOut:
    return SourceConfigOut(id=str(s.id), file_name=s.file_name, file_type=s.file_type,
                           column_mappings=s.column_mappings or {}, is_active=s.is_active)


@router.get("/sources", response_model=list[SourceConfigOut])
async def list_sources(user: CurrentUser = Depends(min_role("planner")),
                       db: AsyncSession = Depends(get_db)):
    return [_src_out(s) for s in await ImportService(db, user.company_id).list_sources()]


@router.post("/sources", response_model=SourceConfigOut)
async def create_source(data: SourceConfigIn, user: CurrentUser = Depends(min_role("planner")),
                        db: AsyncSession = Depends(get_db)):
    s = await ImportService(db, user.company_id).create_source(data)
    await db.commit()
    return _src_out(s)


@router.put("/sources/{source_id}/mapping", response_model=SourceConfigOut)
async def update_mapping(source_id: str, data: MappingIn,
                         user: CurrentUser = Depends(min_role("planner")),
                         db: AsyncSession = Depends(get_db)):
    try:
        s = await ImportService(db, user.company_id).update_mapping(source_id, data.column_mappings)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    await db.commit()
    return _src_out(s)


@router.post("/sources/{source_id}/import", response_model=ImportOut)
async def import_data(source_id: str, data: ImportIn,
                      user: CurrentUser = Depends(min_role("planner")),
                      db: AsyncSession = Depends(get_db)):
    try:
        up = await ImportService(db, user.company_id).import_data(
            source_id, data.rows, data.upload_date
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
    await db.commit()
    cols = list(up.data[0].keys()) if up.data else []
    return ImportOut(upload_id=str(up.id), row_count=up.row_count, columns=cols)


@router.post("/lookup", response_model=LookupImportOut)
async def import_lookup(data: LookupImportIn,
                        user: CurrentUser = Depends(min_role("planner")),
                        db: AsyncSession = Depends(get_db)):
    n = await ImportService(db, user.company_id).import_lookup(data.rows, data.column_mappings)
    await db.commit()
    return LookupImportOut(inserted=n)

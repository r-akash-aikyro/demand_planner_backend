from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import LoginIn, SignupIn, RefreshIn, LogoutIn, TokenOut, MeOut
from app.services.auth_service import AuthService
from app.core.deps import get_current_user, CurrentUser
from app.models import User
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=True)


@router.post("/signup", response_model=TokenOut)
async def signup(data: SignupIn, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user = await svc.signup(data)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    access, refresh = svc.issue_tokens(user)
    await db.commit()
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        user = await svc.authenticate(data.email, data.password)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    access, refresh = svc.issue_tokens(user)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenOut)
async def refresh(data: RefreshIn, db: AsyncSession = Depends(get_db)):
    svc = AuthService(db)
    try:
        access, new_refresh = await svc.refresh(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(e))
    return TokenOut(access_token=access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    body: LogoutIn | None = Body(default=None),
    db: AsyncSession = Depends(get_db),
):
    await AuthService(db).logout(creds.credentials, body.refresh_token if body else None)
    return {"status": "logged_out"}


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(User).where(User.id == user.id))).scalar_one()
    return MeOut(
        id=str(row.id), email=row.email, role=row.role,
        company_id=str(row.company_id), full_name=row.full_name,
    )

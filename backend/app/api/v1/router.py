from fastapi import APIRouter
from app.api.v1 import (
    auth, users, importing, dashboard, forecasts, overrides, agents,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(importing.router)
api_router.include_router(dashboard.router)
api_router.include_router(forecasts.router)
api_router.include_router(overrides.router)
api_router.include_router(agents.router)

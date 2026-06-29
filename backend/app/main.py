from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from app.core.config import settings
from app.core.ratelimit import limiter
from app.api.v1.health import router as health_router
from app.api.v1.router import api_router

app = FastAPI(title="Demand Planner Backend", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Required for the Limiter's default_limits to actually apply to every route;
# without this middleware slowapi only enforces per-route @limiter.limit decorators.
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"service": "dpb-backend", "docs": "/docs", "health": "/health"}

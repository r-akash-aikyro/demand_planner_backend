from pydantic import BaseModel
from typing import Any


class GenerateIn(BaseModel):
    dataset_name: str = "default"
    horizon: int = 28
    aggregation: str = "monthly"   # weekly|monthly|yearly
    mapping: dict[str, str] = {}   # canonical -> user column (final mapping)


class SessionOut(BaseModel):
    session_id: str
    dataset_name: str | None = None
    horizon: int
    aggregation: str
    status: str
    model_used: str | None = None
    sku_count: int
    row_count: int
    metrics: dict[str, Any] | None = None
    generated_at: str | None = None
    published_at: str | None = None


class GenerateOut(BaseModel):
    session_id: str
    status: str


class StatusOut(BaseModel):
    session_id: str
    status: str


class ForecastRowOut(BaseModel):
    product_id: str
    date: str
    forecast_value: float
    confidence_lower: float | None = None
    confidence_upper: float | None = None
    forecast_type: str

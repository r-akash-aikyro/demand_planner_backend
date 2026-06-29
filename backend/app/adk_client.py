"""HTTP client to the ADK service (separate repo). Guarded by X-ADK-Secret."""
import httpx
from app.core.config import settings


async def run_forecast(session_id: str, company_id: str, aggregation: str,
                       horizon: int, mapping: dict, dataset_name: str) -> dict:
    payload = {
        "session_id": session_id,
        "company_id": company_id,
        "aggregation": aggregation,
        "horizon": horizon,
        "mapping": mapping,
        "dataset_name": dataset_name,
    }
    headers = {"X-ADK-Secret": settings.ADK_SECRET}
    timeout = httpx.Timeout(60.0, read=1800.0)  # forecasts can be slow on CPU
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{settings.ADK_URL}/run", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Forecast, DataUpload, SourceConfig, AgentTrace


class MetricsService:
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    async def _actuals(self) -> dict[tuple[str, str], float]:
        """Actuals keyed by (product_id, date) from uploads of file_type='actuals'."""
        src_ids = (await self.db.execute(
            select(SourceConfig.id).where(
                SourceConfig.company_id == self.company_id,
                SourceConfig.file_type == "actuals",
            )
        )).scalars().all()
        if not src_ids:
            return {}
        uploads = (await self.db.execute(
            select(DataUpload).where(
                DataUpload.company_id == self.company_id,
                DataUpload.source_config_id.in_(src_ids),
            )
        )).scalars().all()
        out: dict[tuple[str, str], float] = {}
        for u in uploads:
            for r in (u.data or []):
                pid, d, q = r.get("product_id"), r.get("date"), r.get("quantity")
                if pid and d and q is not None:
                    try:
                        out[(str(pid), str(d)[:10])] = float(q)
                    except (TypeError, ValueError):
                        pass
        return out

    async def session_metrics(self, session_id: str) -> dict:
        forecasts = (await self.db.execute(
            select(Forecast).where(
                Forecast.company_id == self.company_id,
                Forecast.session_id == session_id,
            )
        )).scalars().all()
        actuals = await self._actuals()
        if not forecasts or not actuals:
            return {"matched": 0, "mape": None, "wmape": None, "bias": None,
                    "note": "No overlapping actuals to score yet."}
        abs_pct = wsum = wabs = signed = matched = 0.0
        n = 0
        for f in forecasts:
            key = (f.product_id, f.date.isoformat())
            if key not in actuals:
                continue
            a = actuals[key]
            p = float(f.forecast_value)
            err = p - a
            signed += err
            wabs += abs(err)
            wsum += abs(a)
            if a != 0:
                abs_pct += abs(err) / abs(a)
            matched += 1
            n += 1
        if n == 0:
            return {"matched": 0, "mape": None, "wmape": None, "bias": None}
        return {
            "matched": int(matched),
            "mape": round(abs_pct / n * 100, 2),
            "wmape": round(wabs / wsum * 100, 2) if wsum else None,
            "bias": round(signed / n, 2),
        }


class AgentService:
    """Lightweight Q&A / diagnose over persisted artifacts.
    Can be repointed to the ADK service for full LLM reasoning."""
    def __init__(self, db: AsyncSession, company_id: str):
        self.db = db
        self.company_id = company_id

    async def traces(self, session_id: str):
        return (await self.db.execute(
            select(AgentTrace).where(
                AgentTrace.company_id == self.company_id,
                AgentTrace.session_id == session_id,
            ).order_by(AgentTrace.created_at)
        )).scalars().all()

    async def diagnose(self, session_id: str) -> dict:
        metrics = await MetricsService(self.db, self.company_id).session_metrics(session_id)
        msg = "Forecast looks healthy."
        if metrics.get("mape") is not None:
            if metrics["mape"] > 30:
                msg = f"High error (MAPE {metrics['mape']}%). Consider more history or re-segmenting SKUs."
            elif metrics.get("bias") and abs(metrics["bias"]) > 0:
                msg = f"MAPE {metrics['mape']}%, bias {metrics['bias']}."
        return {"session_id": session_id, "metrics": metrics, "assessment": msg}

    async def chat(self, session_id: str | None, message: str) -> dict:
        # Stub: deterministic helper. Wire to ADK /chat for LLM answers.
        reply = "I can summarize forecast sessions, metrics, and traces. "
        if session_id:
            d = await self.diagnose(session_id)
            reply += f"Session {session_id}: {d['assessment']}"
        else:
            reply += "Provide a session_id for specifics."
        return {"reply": reply}

import asyncio
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal, engine
from app.core import job_status
from app.core.redis import redis_client
from app.adk_client import run_forecast
from app.services.forecast_service import ForecastService


async def _run(session_id, company_id, aggregation, horizon, mapping, dataset_name):
    await job_status.set_status(session_id, job_status.RUNNING)
    try:
        summary = await run_forecast(
            session_id, company_id, aggregation, horizon, mapping, dataset_name
        )
        async with SessionLocal() as db:
            await ForecastService(db, company_id).mark_generated(session_id, summary)
            await db.commit()
        await job_status.set_status(session_id, job_status.COMPLETE)
        return summary
    except Exception as e:  # noqa: BLE001
        await job_status.set_status(session_id, job_status.ERROR)
        raise e
    finally:
        # Celery runs each task in a fresh asyncio.run() loop; the module-level async
        # engine and Redis client bind their connections to the loop that created them.
        # Dispose both so the next task reconnects on its own loop instead of reusing
        # connections bound to a now-closed loop (prefork = one task per process).
        await engine.dispose()
        try:
            await redis_client.aclose()
        except AttributeError:  # redis-py < 5.0.1
            await redis_client.close()


@celery_app.task(name="forecast.generate")
def generate_forecast(session_id, company_id, aggregation, horizon, mapping, dataset_name):
    return asyncio.run(
        _run(session_id, company_id, aggregation, horizon, mapping, dataset_name)
    )

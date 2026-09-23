import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api import (
    admin_events,
    admin_registrations,
    auth,
    checkout,
    events,
    registrations,
    stripe_webhook,
)
from app.config import settings
from app.db import SessionLocal
from app.services.auth import ensure_owner
from app.services.sweep import expire_stale_holds

log = logging.getLogger(__name__)


async def _sweep_loop() -> None:
    while True:
        await asyncio.sleep(settings.sweep_interval_seconds)
        try:
            with SessionLocal() as db:
                await asyncio.to_thread(expire_stale_holds, db)
        except Exception:  # noqa: BLE001
            log.exception("sweep failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        ensure_owner(db)
    task = asyncio.create_task(_sweep_loop()) if settings.sweep_interval_seconds > 0 else None
    try:
        yield
    finally:
        if task:
            task.cancel()


def create_app() -> FastAPI:
    app = FastAPI(title="Matami Möttönen API", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api = APIRouter(prefix="/api")
    for r in (
        auth,
        events,
        checkout,
        registrations,
        stripe_webhook,
        admin_registrations,
        admin_events,
    ):
        api.include_router(r.router)
    app.include_router(api)
    return app


app = create_app()

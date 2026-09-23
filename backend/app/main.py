from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api import admin_events, auth, checkout, events
from app.db import SessionLocal
from app.services.auth import ensure_owner


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    with SessionLocal() as db:
        ensure_owner(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Matami Möttönen API", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    api = APIRouter(prefix="/api")
    api.include_router(auth.router)
    api.include_router(events.router)
    api.include_router(checkout.router)
    api.include_router(admin_events.router)
    app.include_router(api)
    return app


app = create_app()

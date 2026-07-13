import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app import crud
from app.api import api_router, ws_router
from app.config import get_settings
from app.db import get_engine, init_db
from app.glossary import seed_glossary

logger = logging.getLogger(__name__)
DAY_SECONDS = 24 * 60 * 60


def validate_runtime_settings() -> None:
    settings = get_settings()
    if settings.provider_mode == "cloud" and settings.admin_token == "change-me":
        raise RuntimeError("ADMIN_TOKEN must be changed when PROVIDER_MODE=cloud")


async def _purge_old_sessions_daily(retention_days: int) -> None:
    while True:
        await asyncio.sleep(DAY_SECONDS)
        try:
            with Session(get_engine()) as db:
                crud.purge_old_sessions(db, retention_days)
        except Exception:
            logger.exception("interpreter retention purge failed")


@asynccontextmanager
async def interpreter_lifespan(_: FastAPI) -> AsyncIterator[None]:
    validate_runtime_settings()
    settings = get_settings()
    init_db()
    with Session(get_engine()) as db:
        seed_glossary(db)
        crud.purge_old_sessions(db, settings.retention_days)
    purge_task = asyncio.create_task(_purge_old_sessions_daily(settings.retention_days))
    try:
        yield
    finally:
        purge_task.cancel()
        with suppress(asyncio.CancelledError):
            await purge_task


app = FastAPI(title="CarePath Interpreter API", lifespan=interpreter_lifespan)
if get_settings().cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(get_settings().cors_origins),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(api_router)
app.include_router(ws_router)

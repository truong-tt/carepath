from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app import crud
from app.api import api_router, ws_router
from app.config import get_settings
from app.db import get_engine, init_db
from app.glossary import seed_glossary


def validate_runtime_settings() -> None:
    settings = get_settings()
    if settings.provider_mode == "cloud" and settings.admin_token == "change-me":
        raise RuntimeError("ADMIN_TOKEN must be changed when PROVIDER_MODE=cloud")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    validate_runtime_settings()
    settings = get_settings()
    init_db()
    with Session(get_engine()) as db:
        seed_glossary(db)
        # ponytail: startup purge only; add a scheduler when the app runs for weeks unattended.
        crud.purge_old_sessions(db, settings.retention_days)
    yield


app = FastAPI(title="CarePath Interpreter API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
app.include_router(ws_router)

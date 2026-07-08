from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.api import api_router, ws_router
from app.config import get_settings
from app.db import get_engine, init_db
from app.glossary import seed_glossary


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    with Session(get_engine()) as db:
        seed_glossary(db)
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


@app.get("/api/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "provider_mode": settings.provider_mode}

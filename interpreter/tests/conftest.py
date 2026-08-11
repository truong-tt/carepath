import os

# Force hermetic settings BEFORE anything imports app.config or app.main, both
# of which read settings at module scope. Settings loads ../.env, so without
# this a developer with real credentials on disk runs the suite in cloud mode
# and the tests make live network calls. Environment variables take precedence
# over the env file in pydantic-settings, so setting them here wins.
os.environ["PROVIDER_MODE"] = "mock"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["LLM_API_KEY"] = ""
os.environ["ADMIN_TOKEN"] = "change-me"
os.environ["DATABASE_URL"] = "sqlite://"

import pytest  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import init_db, set_engine  # noqa: E402

get_settings.cache_clear()


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.drop_all(engine)
    init_db(engine)
    set_engine(engine)
    with Session(engine) as session:
        yield session
    set_engine(None)

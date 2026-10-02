"""SQLAlchemy engine, session factory and FastAPI database dependency."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from github_insight.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""


settings = get_settings()
if settings.database_url.startswith("sqlite:///./"):
    Path(settings.database_url.removeprefix("sqlite:///./")).parent.mkdir(
        parents=True, exist_ok=True
    )

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a short-lived session and always close it after the request."""

    with SessionLocal() as session:
        yield session

"""Database models for persisted analysis snapshots."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from github_insight.db.database import Base


class AnalysisSnapshot(Base):
    """Immutable snapshot of one completed GitHub profile analysis."""

    __tablename__ = "analysis_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(39), index=True)
    avatar_url: Mapped[str] = mapped_column(String(500))
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    payload: Mapped[dict] = mapped_column(JSON)

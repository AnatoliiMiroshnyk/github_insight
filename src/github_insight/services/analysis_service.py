"""Application use cases: caching, GitHub orchestration and persistence."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from github_insight.core.config import Settings
from github_insight.db.models import AnalysisSnapshot
from github_insight.services.analyzer import build_analysis
from github_insight.services.github_client import GitHubClient


class AnalysisService:
    def __init__(self, db: Session, github: GitHubClient, settings: Settings) -> None:
        self.db = db
        self.github = github
        self.settings = settings

    async def analyze(
        self, username: str, force_refresh: bool = False
    ) -> tuple[AnalysisSnapshot, bool]:
        """Return a recent cached snapshot or fetch and persist a new analysis."""

        normalized = username.lower()
        cutoff = datetime.now(UTC) - timedelta(minutes=self.settings.cache_ttl_minutes)
        cached = self.db.scalar(
            select(AnalysisSnapshot)
            .where(AnalysisSnapshot.username == normalized)
            .order_by(AnalysisSnapshot.analyzed_at.desc())
        )
        if cached and not force_refresh:
            analyzed_at = cached.analyzed_at
            if analyzed_at.tzinfo is None:
                analyzed_at = analyzed_at.replace(tzinfo=UTC)
            if analyzed_at >= cutoff:
                return cached, True

        user = await self.github.get_user(username)
        repositories = await self.github.get_repositories(username)
        events = await self.github.get_public_events(username)
        language_maps = await self.github.get_language_maps(repositories)
        payload = build_analysis(
            user, repositories, events, language_maps, self.github.rate_limit_remaining
        )
        snapshot = AnalysisSnapshot(
            username=normalized,
            avatar_url=user["avatar_url"],
            display_name=user.get("name"),
            payload=payload,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot, False

    def get(self, analysis_id: int) -> AnalysisSnapshot | None:
        return self.db.get(AnalysisSnapshot, analysis_id)

    def history(self, limit: int = 20) -> list[AnalysisSnapshot]:
        return list(
            self.db.scalars(
                select(AnalysisSnapshot)
                .order_by(AnalysisSnapshot.analyzed_at.desc())
                .limit(limit)
            )
        )

    def delete(self, analysis_id: int) -> bool:
        result = self.db.execute(
            delete(AnalysisSnapshot).where(AnalysisSnapshot.id == analysis_id)
        )
        self.db.commit()
        return bool(result.rowcount)

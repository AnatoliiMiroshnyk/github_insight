"""FastAPI dependency factories, isolated for easy test overrides."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from github_insight.core.config import Settings, get_settings
from github_insight.db.database import get_db
from github_insight.services.analysis_service import AnalysisService
from github_insight.services.github_client import GitHubClient

SettingsDep = Annotated[Settings, Depends(get_settings)]
DatabaseDep = Annotated[Session, Depends(get_db)]


def get_github_client(settings: SettingsDep) -> GitHubClient:
    return GitHubClient(settings)


GitHubClientDep = Annotated[GitHubClient, Depends(get_github_client)]


def get_analysis_service(
    db: DatabaseDep, github: GitHubClientDep, settings: SettingsDep
) -> AnalysisService:
    return AnalysisService(db, github, settings)


AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]

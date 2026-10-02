"""Pydantic request and response contracts used by the API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisRequest(BaseModel):
    username: str = Field(min_length=1, max_length=39, examples=["octocat"])
    force_refresh: bool = False

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """Apply GitHub's practical username character rules."""

        username = value.strip()
        allowed = username.replace("-", "").isalnum()
        if not allowed or username.startswith("-") or username.endswith("-"):
            raise ValueError("Username may contain letters, numbers and internal hyphens")
        return username


class LanguageStat(BaseModel):
    name: str
    bytes: int
    percentage: float


class RepositorySummary(BaseModel):
    name: str
    description: str | None = None
    html_url: str
    language: str | None = None
    stars: int
    forks: int
    open_issues: int
    updated_at: datetime | None = None
    archived: bool = False


class ActivityStat(BaseModel):
    event_type: str
    count: int


class ProfileSummary(BaseModel):
    username: str
    name: str | None = None
    avatar_url: str
    html_url: str
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    blog: str | None = None
    followers: int
    following: int
    public_repos: int
    created_at: datetime


class AnalysisPayload(BaseModel):
    profile: ProfileSummary
    totals: dict[str, int]
    languages: list[LanguageStat]
    top_repositories: list[RepositorySummary]
    activity: list[ActivityStat]
    activity_days: dict[str, int]
    insights: list[str]
    rate_limit_remaining: int | None = None


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    analyzed_at: datetime
    cached: bool = False
    data: AnalysisPayload


class HistoryItem(BaseModel):
    id: int
    username: str
    display_name: str | None
    avatar_url: str
    analyzed_at: datetime

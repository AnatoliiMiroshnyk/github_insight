"""Shared isolated database and fake GitHub client for deterministic tests."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from github_insight.api.dependencies import get_github_client
from github_insight.db.database import Base, get_db
from github_insight.main import create_app


class FakeGitHubClient:
    rate_limit_remaining = 4990
    calls = 0

    async def get_user(self, username):
        self.calls += 1
        return {
            "login": username,
            "name": "Ada Dev",
            "avatar_url": "https://example.com/a.png",
            "html_url": f"https://github.com/{username}",
            "bio": "Builds reliable systems",
            "company": "Example",
            "location": "Kyiv",
            "blog": "",
            "followers": 42,
            "following": 8,
            "public_repos": 2,
            "created_at": "2020-01-01T00:00:00Z",
        }

    async def get_repositories(self, username):
        return [
            {
                "name": "api",
                "full_name": f"{username}/api",
                "html_url": "https://github.com/x/api",
                "description": "API service",
                "language": "Python",
                "stargazers_count": 12,
                "forks_count": 3,
                "open_issues_count": 1,
                "updated_at": "2026-09-01T00:00:00Z",
                "archived": False,
                "fork": False,
            }
        ]

    async def get_public_events(self, username):
        return [{"type": "PushEvent", "created_at": "2026-09-29T10:00:00Z"}]

    async def get_language_maps(self, repositories):
        return [{"Python": 800, "HTML": 200}]


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    fake = FakeGitHubClient()
    app = create_app()

    def override_db() -> Generator[Session, None, None]:
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_github_client] = lambda: fake
    with TestClient(app) as test_client:
        test_client.fake_github = fake
        yield test_client

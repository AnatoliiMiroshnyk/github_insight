"""Asynchronous GitHub REST API gateway.

Keeping network concerns in one class makes rate-limit handling and tests much
simpler. The analyzer depends on this abstraction instead of calling HTTPX itself.
"""

import asyncio
from typing import Any

import httpx

from github_insight.core.config import Settings


class GitHubAPIError(Exception):
    """Domain error with an HTTP-friendly status code and safe message."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class GitHubClient:
    """Small async client for the public GitHub resources used by the app."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.rate_limit_remaining: int | None = None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-insight-portfolio-app",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        async with httpx.AsyncClient(
            base_url=self.settings.github_api_url,
            headers=self._headers(),
            timeout=self.settings.request_timeout_seconds,
        ) as client:
            try:
                response = await client.get(path, params=params)
            except httpx.TimeoutException as exc:
                raise GitHubAPIError(504, "GitHub did not respond in time") from exc
            except httpx.HTTPError as exc:
                raise GitHubAPIError(502, "Could not connect to GitHub") from exc

        remaining = response.headers.get("x-ratelimit-remaining")
        self.rate_limit_remaining = int(remaining) if remaining and remaining.isdigit() else None
        if response.status_code == 404:
            raise GitHubAPIError(404, "GitHub user was not found")
        if response.status_code in {403, 429}:
            raise GitHubAPIError(
                429, "GitHub API rate limit reached; try later or configure a token"
            )
        if response.is_error:
            raise GitHubAPIError(502, f"GitHub API returned status {response.status_code}")
        return response.json()

    async def get_user(self, username: str) -> dict[str, Any]:
        return await self._get(f"/users/{username}")

    async def get_repositories(self, username: str) -> list[dict[str, Any]]:
        repositories: list[dict[str, Any]] = []
        for page in range(1, self.settings.max_repository_pages + 1):
            batch = await self._get(
                f"/users/{username}/repos",
                {"per_page": 100, "page": page, "sort": "updated"},
            )
            repositories.extend(batch)
            if len(batch) < 100:
                break
        return repositories

    async def get_public_events(self, username: str) -> list[dict[str, Any]]:
        return await self._get(f"/users/{username}/events/public", {"per_page": 100})

    async def get_languages(self, full_name: str) -> dict[str, int]:
        return await self._get(f"/repos/{full_name}/languages")

    async def get_language_maps(
        self, repositories: list[dict[str, Any]]
    ) -> list[dict[str, int]]:
        """Fetch language byte maps concurrently while limiting parallel pressure."""

        semaphore = asyncio.Semaphore(8)

        async def guarded(repo: dict[str, Any]) -> dict[str, int]:
            async with semaphore:
                try:
                    return await self.get_languages(repo["full_name"])
                except GitHubAPIError:
                    # One inaccessible language endpoint should not fail the whole report.
                    return {}

        selected = [r for r in repositories if not r.get("fork")][
            : self.settings.language_repository_limit
        ]
        return await asyncio.gather(*(guarded(repo) for repo in selected))

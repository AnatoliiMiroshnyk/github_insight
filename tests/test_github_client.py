"""Contract-level tests for request headers without calling GitHub."""

from github_insight.core.config import Settings
from github_insight.services.github_client import GitHubClient


def test_token_is_added_only_when_configured():
    anonymous = GitHubClient(Settings(github_token=None))
    authenticated = GitHubClient(Settings(github_token="secret"))
    assert "Authorization" not in anonymous._headers()
    assert authenticated._headers()["Authorization"] == "Bearer secret"

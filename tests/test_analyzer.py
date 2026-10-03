"""Unit test for deterministic metrics independent of HTTP and persistence."""

from github_insight.services.analyzer import build_analysis


def test_build_analysis_orders_languages_and_repositories():
    user = {
        "login": "dev",
        "name": None,
        "avatar_url": "https://example.com/a",
        "html_url": "https://github.com/dev",
        "bio": None,
        "company": None,
        "location": None,
        "blog": None,
        "followers": 1,
        "following": 2,
        "public_repos": 2,
        "created_at": "2021-01-01T00:00:00Z",
    }
    repositories = [
        {
            "name": "small",
            "html_url": "https://github.com/dev/small",
            "description": None,
            "language": "Go",
            "stargazers_count": 1,
            "forks_count": 0,
            "open_issues_count": 0,
            "updated_at": "2025-01-01T00:00:00Z",
            "archived": False,
            "fork": False,
        },
        {
            "name": "popular",
            "html_url": "https://github.com/dev/popular",
            "description": None,
            "language": "Python",
            "stargazers_count": 10,
            "forks_count": 2,
            "open_issues_count": 1,
            "updated_at": "2026-01-01T00:00:00Z",
            "archived": False,
            "fork": False,
        },
    ]
    events = [{"type": "PushEvent", "created_at": "2026-09-30T00:00:00Z"}]
    result = build_analysis(
        user,
        repositories,
        events,
        [{"Python": 900, "HTML": 100}],
        50,
    )
    assert result["languages"][0]["percentage"] == 90.0
    assert result["top_repositories"][0]["name"] == "popular"
    assert result["totals"]["stars"] == 11

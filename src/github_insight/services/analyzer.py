"""Pure transformation functions that turn GitHub payloads into useful metrics."""

from collections import Counter
from datetime import datetime
from typing import Any


def build_analysis(
    user: dict[str, Any],
    repositories: list[dict[str, Any]],
    events: list[dict[str, Any]],
    language_maps: list[dict[str, int]],
    rate_limit_remaining: int | None,
) -> dict[str, Any]:
    """Aggregate raw API documents into a stable frontend-friendly payload."""

    original_repos = [repo for repo in repositories if not repo.get("fork")]
    totals = {
        "repositories_analyzed": len(repositories),
        "original_repositories": len(original_repos),
        "stars": sum(repo.get("stargazers_count", 0) for repo in repositories),
        "forks": sum(repo.get("forks_count", 0) for repo in repositories),
        "open_issues": sum(repo.get("open_issues_count", 0) for repo in repositories),
        "archived": sum(bool(repo.get("archived")) for repo in repositories),
    }

    language_bytes: Counter[str] = Counter()
    for language_map in language_maps:
        language_bytes.update(language_map)
    byte_total = sum(language_bytes.values())
    languages = [
        {
            "name": name,
            "bytes": size,
            "percentage": round(size / byte_total * 100, 1) if byte_total else 0.0,
        }
        for name, size in language_bytes.most_common(8)
    ]

    ranked = sorted(
        original_repos,
        key=lambda repo: (
            repo.get("stargazers_count", 0),
            repo.get("forks_count", 0),
            repo.get("updated_at", ""),
        ),
        reverse=True,
    )[:8]
    top_repositories = [
        {
            "name": repo["name"],
            "description": repo.get("description"),
            "html_url": repo["html_url"],
            "language": repo.get("language"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "updated_at": repo.get("updated_at"),
            "archived": repo.get("archived", False),
        }
        for repo in ranked
    ]

    event_counts = Counter(event.get("type", "Unknown") for event in events)
    activity = [
        {"event_type": event_type.removesuffix("Event"), "count": count}
        for event_type, count in event_counts.most_common(7)
    ]
    day_counts = Counter(
        event.get("created_at", "")[:10]
        for event in events
        if event.get("created_at")
    )

    insights = _build_insights(user, totals, languages, event_counts)
    return {
        "profile": {
            "username": user["login"],
            "name": user.get("name"),
            "avatar_url": user["avatar_url"],
            "html_url": user["html_url"],
            "bio": user.get("bio"),
            "company": user.get("company"),
            "location": user.get("location"),
            "blog": user.get("blog"),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "public_repos": user.get("public_repos", 0),
            "created_at": user["created_at"],
        },
        "totals": totals,
        "languages": languages,
        "top_repositories": top_repositories,
        "activity": activity,
        "activity_days": dict(sorted(day_counts.items())),
        "insights": insights,
        "rate_limit_remaining": rate_limit_remaining,
    }


def _build_insights(
    user: dict[str, Any],
    totals: dict[str, int],
    languages: list[dict[str, Any]],
    event_counts: Counter[str],
) -> list[str]:
    insights: list[str] = []
    if languages:
        insights.append(
            f"{languages[0]['name']} is the largest detected language by repository bytes "
            f"({languages[0]['percentage']}%)."
        )
    if totals["stars"]:
        insights.append(f"Public repositories have earned {totals['stars']} stars in total.")
    if event_counts:
        event_name, count = event_counts.most_common(1)[0]
        insights.append(
            "The most frequent recent public activity is "
            f"{event_name.removesuffix('Event')} ({count})."
        )
    created_year = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00")).year
    insights.append(f"The account has been active on GitHub since {created_year}.")
    if totals["archived"]:
        insights.append(f"{totals['archived']} analyzed repositories are archived.")
    return insights

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from common import days_since, load_config, repo_key, safe_int


def readme_bonus(repo: dict[str, Any], config: dict[str, Any]) -> int:
    length = safe_int(repo.get("readme_length"))
    bonus = config["scoring"]["readme_bonus"]
    if length >= 5000:
        return bonus["complete"]
    if length >= 1500:
        return bonus["useful"]
    if length >= 300:
        return bonus["minimal"]
    return 0


def recent_push_bonus(repo: dict[str, Any], config: dict[str, Any], now: datetime) -> int:
    pushed_days = days_since(repo.get("pushed_at"), now)
    if pushed_days is None:
        return 0
    thresholds = config["scoring"]["recent_push_days"]
    bonuses = config["scoring"]["recent_push_bonus"]
    if pushed_days <= thresholds["strong"]:
        return bonuses["strong"]
    if pushed_days <= thresholds["medium"]:
        return bonuses["medium"]
    if pushed_days <= thresholds["weak"]:
        return bonuses["weak"]
    return 0


def topic_bonus(repo: dict[str, Any], config: dict[str, Any]) -> int:
    interesting = set(config["search"].get("topics", []))
    repo_topics = set(repo.get("topics", []))
    matches = len(interesting.intersection(repo_topics))
    return matches * config["scoring"].get("topic_relevance_bonus", 5)


def is_awesome_list(repo: dict[str, Any]) -> bool:
    name = repo.get("full_name", "").lower().split("/")[-1]
    description = (repo.get("description") or "").lower()
    readme = (repo.get("readme_summary") or "").lower()
    return (
        name.startswith("awesome-")
        or "awesome list" in description
        or "curated list" in description
        or "# awesome" in readme
    )


def score_repos(
    current_repos: list[dict[str, Any]],
    previous_snapshot: dict[str, Any] | None,
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], bool]:
    now = datetime.now(timezone.utc)
    previous_by_name: dict[str, dict[str, Any]] = {}
    if previous_snapshot and previous_snapshot.get("repos"):
        previous_by_name = {repo_key(repo["full_name"]): repo for repo in previous_snapshot["repos"]}
    baseline = not bool(previous_by_name)

    ranked: list[dict[str, Any]] = []
    for repo in current_repos:
        previous = previous_by_name.get(repo_key(repo["full_name"]))
        delta_stars = safe_int(repo.get("stars")) - safe_int(previous.get("stars")) if previous else 0
        delta_subscribers = safe_int(repo.get("subscribers")) - safe_int(previous.get("subscribers")) if previous else 0
        delta_forks = safe_int(repo.get("forks")) - safe_int(previous.get("forks")) if previous else 0

        delta_stars = max(0, delta_stars)
        delta_subscribers = max(0, delta_subscribers)
        delta_forks = max(0, delta_forks)

        score_parts = {
            "delta_stars": delta_stars,
            "delta_subscribers_weighted": delta_subscribers * config["scoring"]["subscriber_weight"],
            "delta_forks_weighted": delta_forks * config["scoring"]["fork_weight"],
            "recent_push_bonus": recent_push_bonus(repo, config, now),
            "readme_bonus": readme_bonus(repo, config),
            "topic_bonus": topic_bonus(repo, config),
            "awesome_penalty": -config["scoring"]["awesome_penalty"] if is_awesome_list(repo) else 0,
            "stale_penalty": 0,
            "baseline_star_hint": 0,
        }

        pushed_days = days_since(repo.get("pushed_at"), now)
        if pushed_days is not None and pushed_days > config["scoring"]["stale_days"]:
            score_parts["stale_penalty"] = -config["scoring"]["stale_penalty"]

        if baseline:
            score_parts["baseline_star_hint"] = round(
                safe_int(repo.get("stars")) * config["scoring"].get("baseline_star_scale", 0.01),
                2,
            )

        scored = dict(repo)
        scored["delta_stars"] = delta_stars
        scored["delta_subscribers"] = delta_subscribers
        scored["delta_forks"] = delta_forks
        scored["score_parts"] = score_parts
        scored["trend_score"] = round(sum(score_parts.values()), 2)
        ranked.append(scored)

    ranked.sort(
        key=lambda repo: (
            repo["trend_score"],
            repo.get("delta_stars", 0),
            repo.get("stars", 0),
        ),
        reverse=True,
    )
    return ranked, baseline


def main() -> None:
    load_config()
    print("Use scripts/run_loop.py to score repositories as part of the full loop.")


if __name__ == "__main__":
    main()


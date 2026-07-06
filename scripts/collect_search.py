from __future__ import annotations

from typing import Any

import requests

from common import github_get_json, load_config, render_dynamic_dates


def collect_search(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    if not config["search"].get("enabled", True):
        return [], []

    session = requests.Session()
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    api_base = config["github"]["api_base_url"].rstrip("/")
    endpoint = f"{api_base}/search/repositories"
    per_query_limit = min(config["search"].get("per_query_limit", 30), 100)

    raw_queries = list(config["search"].get("queries", []))
    topic_template = config["search"].get("topic_query_template", "topic:{topic} stars:>50")
    for topic in config["search"].get("topics", []):
        raw_queries.append(topic_template.replace("{topic}", topic))

    for raw_query in raw_queries:
        query = render_dynamic_dates(raw_query)
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": per_query_limit,
        }
        payload, error = github_get_json(session, endpoint, config, params=params)
        if error:
            warnings.append(f"Search query failed [{query}]: {error}")
            continue
        for item in payload.get("items", []):
            candidates.append(
                {
                    "full_name": item["full_name"],
                    "html_url": item["html_url"],
                    "description": item.get("description") or "",
                    "source": f"search:{query}",
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "pushed_at": item.get("pushed_at"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                    "language": item.get("language"),
                }
            )

    return candidates, warnings


def main() -> None:
    config = load_config()
    candidates, warnings = collect_search(config)
    print(f"search_candidates={len(candidates)}")
    for warning in warnings:
        print(f"warning: {warning}")


if __name__ == "__main__":
    main()


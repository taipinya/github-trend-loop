from __future__ import annotations

from typing import Any

import requests

from common import (
    github_get_json,
    github_get_text,
    load_config,
    repo_key,
    safe_int,
    truncate_text,
)


def merge_candidates(candidates: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        full_name = candidate.get("full_name", "").strip()
        if not full_name or "/" not in full_name:
            continue
        key = repo_key(full_name)
        if key not in merged:
            merged[key] = {
                "full_name": full_name,
                "html_url": candidate.get("html_url") or f"https://github.com/{full_name}",
                "description": candidate.get("description") or "",
                "sources": [],
            }
        source = candidate.get("source")
        if source and source not in merged[key]["sources"]:
            merged[key]["sources"].append(source)

    repos = list(merged.values())
    return repos[: config["filters"].get("max_candidates", 500)]


def fetch_repo_details(
    candidates: list[dict[str, Any]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    session = requests.Session()
    warnings: list[str] = []
    detailed: list[dict[str, Any]] = []
    api_base = config["github"]["api_base_url"].rstrip("/")
    readme_max_chars = config["details"].get("readme_max_chars", 12000)
    readme_summary_chars = config["details"].get("readme_summary_chars", 700)
    min_stars = config["filters"].get("min_stars", 0)

    for candidate in candidates:
        full_name = candidate["full_name"]
        repo_payload, error = github_get_json(session, f"{api_base}/repos/{full_name}", config)
        if error:
            warnings.append(f"Repo detail failed [{full_name}]: {error}")
            continue

        if config["filters"].get("exclude_archived", True) and repo_payload.get("archived"):
            continue
        if config["filters"].get("exclude_disabled", True) and repo_payload.get("disabled"):
            continue
        if safe_int(repo_payload.get("stargazers_count")) < min_stars:
            continue

        readme_text = ""
        readme_summary = ""
        readme_url = f"{api_base}/repos/{full_name}/readme"
        raw_readme, readme_error = github_get_text(session, readme_url, config, raw=True)
        if raw_readme and not raw_readme.lstrip().startswith("{"):
            readme_text = raw_readme[:readme_max_chars]
            readme_summary = truncate_text(readme_text, readme_summary_chars)
        elif readme_error and readme_error != "not found":
            warnings.append(f"README fetch failed [{full_name}]: {readme_error}")

        detailed.append(
            {
                "full_name": repo_payload["full_name"],
                "html_url": repo_payload["html_url"],
                "description": repo_payload.get("description") or candidate.get("description") or "",
                "homepage": repo_payload.get("homepage") or "",
                "language": repo_payload.get("language") or "",
                "topics": repo_payload.get("topics") or [],
                "stars": safe_int(repo_payload.get("stargazers_count")),
                "forks": safe_int(repo_payload.get("forks_count")),
                "subscribers": safe_int(repo_payload.get("subscribers_count")),
                "open_issues": safe_int(repo_payload.get("open_issues_count")),
                "created_at": repo_payload.get("created_at"),
                "updated_at": repo_payload.get("updated_at"),
                "pushed_at": repo_payload.get("pushed_at"),
                "archived": bool(repo_payload.get("archived")),
                "disabled": bool(repo_payload.get("disabled")),
                "fork": bool(repo_payload.get("fork")),
                "license": (repo_payload.get("license") or {}).get("spdx_id") or "",
                "sources": candidate.get("sources", []),
                "readme_summary": readme_summary,
                "readme_length": len(readme_text),
            }
        )

    return detailed, warnings


def main() -> None:
    config = load_config()
    print("Use scripts/run_loop.py to fetch details as part of the full loop.")


if __name__ == "__main__":
    main()


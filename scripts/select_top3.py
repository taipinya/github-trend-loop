from __future__ import annotations

from typing import Any

from common import load_config


def select_top3(ranked_repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_owners: set[str] = set()

    for repo in ranked_repos:
        owner = repo["full_name"].split("/")[0].lower()
        if owner in seen_owners and len(ranked_repos) > 3:
            continue
        selected.append(repo)
        seen_owners.add(owner)
        if len(selected) == 3:
            return selected

    return ranked_repos[:3]


def main() -> None:
    load_config()
    print("Use scripts/run_loop.py to select Top 3 as part of the full loop.")


if __name__ == "__main__":
    main()


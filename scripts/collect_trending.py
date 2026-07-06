from __future__ import annotations

from typing import Any

import requests
from bs4 import BeautifulSoup

from common import load_config


def collect_trending(config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    if not config["trending"].get("enabled", True):
        return [], []

    session = requests.Session()
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    base_url = config["github"]["trending_base_url"].rstrip("/")
    timeout = config["github"]["request_timeout_seconds"]
    user_agent = config["github"]["user_agent"]

    for language in config["trending"].get("languages", [""]):
        language_path = f"/{language.strip('/')}" if language else ""
        for period in config["trending"].get("periods", ["daily", "weekly"]):
            url = f"{base_url}{language_path}?since={period}"
            try:
                response = session.get(url, headers={"User-Agent": user_agent}, timeout=timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                articles = soup.select("article.Box-row")
                if not articles:
                    warnings.append(f"Trending {period} returned no repository rows")
                    continue

                for article in articles[: config["trending"].get("limit_each", 30)]:
                    link = article.select_one("h2 a")
                    if not link:
                        continue
                    full_name = " ".join(link.get_text(" ", strip=True).split()).replace(" / ", "/")
                    description_node = article.select_one("p")
                    description = description_node.get_text(" ", strip=True) if description_node else ""
                    candidates.append(
                        {
                            "full_name": full_name,
                            "html_url": f"https://github.com/{full_name}",
                            "description": description,
                            "source": f"trending:{period}",
                        }
                    )
            except requests.RequestException as exc:
                warnings.append(f"Trending {period} failed: {exc}")
            except Exception as exc:  # Keep Trending HTML parsing failures from stopping the loop.
                warnings.append(f"Trending {period} parse failed: {exc}")

    return candidates, warnings


def main() -> None:
    config = load_config()
    candidates, warnings = collect_trending(config)
    print(f"trending_candidates={len(candidates)}")
    for warning in warnings:
        print(f"warning: {warning}")


if __name__ == "__main__":
    main()


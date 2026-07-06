from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    load_dotenv()
    config_path = Path(path) if path else ROOT / "config.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def project_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def ensure_output_dirs(config: dict[str, Any]) -> None:
    paths = config["paths"]
    for key in ("data_dir", "reports_dir", "snapshots_dir"):
        project_path(paths[key]).mkdir(parents=True, exist_ok=True)


def read_json(path: str | Path, default: Any = None) -> Any:
    file_path = project_path(path)
    if not file_path.exists():
        return default
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, data: Any) -> None:
    file_path = project_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_text(path: str | Path, text: str) -> None:
    file_path = project_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def append_text(path: str | Path, text: str) -> None:
    file_path = project_path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(text)


def github_headers(config: dict[str, Any], raw: bool = False) -> dict[str, str]:
    headers = {
        "User-Agent": config["github"]["user_agent"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if raw:
        headers["Accept"] = "application/vnd.github.raw"
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_get_json(
    session: requests.Session,
    url: str,
    config: dict[str, Any],
    params: dict[str, Any] | None = None,
) -> tuple[Any | None, str | None]:
    try:
        response = session.get(
            url,
            params=params,
            headers=github_headers(config),
            timeout=config["github"]["request_timeout_seconds"],
        )
        if response.status_code == 403:
            return None, f"GitHub API rate limited or forbidden: {response.text[:200]}"
        if response.status_code == 404:
            return None, "GitHub API returned 404"
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, str(exc)


def github_get_text(
    session: requests.Session,
    url: str,
    config: dict[str, Any],
    raw: bool = False,
) -> tuple[str | None, str | None]:
    try:
        headers = github_headers(config, raw=raw)
        response = session.get(
            url,
            headers=headers,
            timeout=config["github"]["request_timeout_seconds"],
        )
        if response.status_code == 404:
            return None, "not found"
        response.raise_for_status()
        return response.text, None
    except requests.RequestException as exc:
        return None, str(exc)


def render_dynamic_dates(query: str, now: datetime | None = None) -> str:
    base = now or utc_now()

    def date_days_ago(days: int) -> str:
        return (base.date() - timedelta(days=days)).isoformat()

    rendered = query
    rendered = rendered.replace("{date_30d}", date_days_ago(30))
    rendered = rendered.replace("{date_14d}", date_days_ago(14))
    rendered = rendered.replace("{date_7d}", date_days_ago(7))

    def replace_chinese(match: re.Match[str]) -> str:
        days = int(match.group(1))
        return date_days_ago(days)

    return re.sub(r"过去(\d+)天", replace_chinese, rendered)


def repo_key(full_name: str) -> str:
    return full_name.strip().lower()


def parse_github_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_since(value: str | None, now: datetime | None = None) -> int | None:
    parsed = parse_github_datetime(value)
    if parsed is None:
        return None
    base = now or utc_now()
    return max(0, (base - parsed).days)


def truncate_text(text: str, max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0

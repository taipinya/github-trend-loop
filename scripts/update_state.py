from __future__ import annotations

from typing import Any

from common import write_text


def update_state(
    config: dict[str, Any],
    run_at: str,
    baseline: bool,
    candidate_count: int,
    detailed_count: int,
    top3: list[dict[str, Any]],
    warnings: list[str],
    latest_report_path: str,
    archived_report_path: str,
    snapshot_path: str,
    llm_provider: str,
) -> None:
    top_lines = "\n".join(
        f"  - {repo['full_name']} ({repo['html_url']}) score={repo.get('trend_score')}" for repo in top3
    ) or "  - none"
    warning_lines = "\n".join(f"  - {warning}" for warning in warnings[:20]) or "  - none"
    text = f"""# STATE

- Last run: {run_at}
- Baseline status: {"baseline established; next run can calculate deltas" if baseline else "delta mode active"}
- Latest report path: {latest_report_path}
- Latest archived report path: {archived_report_path}
- Latest snapshot path: {snapshot_path}
- Candidate count after merge: {candidate_count}
- Detailed repo count: {detailed_count}
- LLM provider: {llm_provider}
- Current limitations:
  - Trending HTML parsing may fail if GitHub changes page markup.
  - Search API rate limits are lower without `GITHUB_TOKEN`.
  - GitHub does not provide a global 3-day growth leaderboard; deltas come from local snapshot comparison.
  - README summaries and model-written explanations should be checked manually.
  - DeepSeek API/report verification failures should stop CI to avoid committing low-quality reports.
- Latest Top 3:
{top_lines}
- Warnings:
{warning_lines}
- Next run notes:
  - Keep `data/latest_snapshot.json` if you want the next run to compute 3-day deltas.
  - Keep `data/snapshots/` and timestamped `reports/` files for historical traceability.
  - Review `reports/latest.md` through the human gate before sharing.
"""
    write_text(config["paths"]["state"], text)


def main() -> None:
    print("Use scripts/run_loop.py to update STATE.md as part of the full loop.")


if __name__ == "__main__":
    main()

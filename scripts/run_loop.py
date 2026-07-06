from __future__ import annotations

import shutil
import os

from collect_search import collect_search
from collect_trending import collect_trending
from common import (
    ensure_output_dirs,
    iso_now,
    load_config,
    project_path,
    read_json,
    write_json,
    write_text,
    append_text,
)
from fetch_repo_details import fetch_repo_details, merge_candidates
from generate_report_with_codex import generate_report
from score_repos import score_repos
from select_top3 import select_top3
from update_state import update_state
from verify_report import verify_report


def append_run_log(
    config: dict,
    run_at: str,
    candidate_count: int,
    detailed_count: int,
    baseline: bool,
    top3: list[dict],
    warnings: list[str],
    latest_report_path: str,
    archived_report_path: str,
    snapshot_path: str,
    report_verification_result: str,
    llm_provider: str,
) -> None:
    top_lines = "\n".join(
        f"- {repo['full_name']} | score={repo.get('trend_score')} | {repo['html_url']}" for repo in top3
    ) or "- none"
    warning_lines = "\n".join(f"- warning: {warning}" for warning in warnings[:20])
    if not warning_lines:
        warning_lines = "- warning: none"
    entry = f"""
## {run_at}

- Candidate count after merge: {candidate_count}
- Detailed repo count: {detailed_count}
- Baseline: {baseline}
- Latest report path: {latest_report_path}
- Archived report path: {archived_report_path}
- Snapshot path: {snapshot_path}
- Report verification result: {report_verification_result}
- LLM provider: {llm_provider}
- Top 3:
{top_lines}
- Warnings:
{warning_lines}
"""
    log_path = project_path(config["paths"]["run_log"])
    if log_path.exists() and log_path.read_text(encoding="utf-8").strip() == "# Loop Run Log\n\nNo runs yet.":
        write_text(config["paths"]["run_log"], "# Loop Run Log\n")
    append_text(config["paths"]["run_log"], entry)


def main() -> None:
    config = load_config()
    ensure_output_dirs(config)
    run_at = iso_now()
    run_stamp = run_at.replace(":", "")
    archived_report_path = f"{config['paths']['reports_dir']}/{run_stamp}-github-trends.md"
    archived_snapshot_path = f"{config['paths']['snapshots_dir']}/{run_stamp}.json"
    llm_provider = config.get("llm", {}).get("provider", "local")
    warnings: list[str] = []

    if not os.getenv("GITHUB_TOKEN"):
        warnings.append("GITHUB_TOKEN is not set; GitHub API rate limits will be lower.")

    previous_snapshot = read_json(config["paths"]["latest_snapshot"], default=None)

    trending_candidates, trending_warnings = collect_trending(config)
    warnings.extend(trending_warnings)

    search_candidates, search_warnings = collect_search(config)
    warnings.extend(search_warnings)

    merged_candidates = merge_candidates(trending_candidates + search_candidates, config)
    detailed_repos, detail_warnings = fetch_repo_details(merged_candidates, config)
    warnings.extend(detail_warnings)

    snapshot = {
        "run_at": run_at,
        "candidate_count": len(merged_candidates),
        "repo_count": len(detailed_repos),
        "repos": detailed_repos,
        "warnings": warnings,
    }
    write_json(config["paths"]["latest_snapshot"], snapshot)
    write_json(archived_snapshot_path, snapshot)

    ranked, baseline = score_repos(detailed_repos, previous_snapshot, config)
    top3 = select_top3(ranked)

    write_json(config["paths"]["latest_ranked"], {"run_at": run_at, "baseline": baseline, "repos": ranked})
    write_json(config["paths"]["latest_top3"], {"run_at": run_at, "baseline": baseline, "repos": top3})

    try:
        report = generate_report(top3, config, baseline)
        ok, report_errors = verify_report(report, top3)
        if not ok:
            raise RuntimeError("Report verification failed:\n" + "\n".join(report_errors))
        report_verification_result = "passed"
    except Exception as exc:
        append_run_log(
            config=config,
            run_at=run_at,
            candidate_count=len(merged_candidates),
            detailed_count=len(detailed_repos),
            baseline=baseline,
            top3=top3,
            warnings=warnings + [f"fatal: {exc}"],
            latest_report_path=config["paths"]["latest_report"],
            archived_report_path=archived_report_path,
            snapshot_path=archived_snapshot_path,
            report_verification_result="failed",
            llm_provider=llm_provider,
        )
        raise

    write_text(archived_report_path, report)
    write_text(config["paths"]["latest_report"], report)

    # Keep latest.md byte-for-byte aligned with the dated report.
    shutil.copyfile(project_path(archived_report_path), project_path(config["paths"]["latest_report"]))

    update_state(
        config=config,
        run_at=run_at,
        baseline=baseline,
        candidate_count=len(merged_candidates),
        detailed_count=len(detailed_repos),
        top3=top3,
        warnings=warnings,
        latest_report_path=config["paths"]["latest_report"],
        archived_report_path=archived_report_path,
        snapshot_path=archived_snapshot_path,
        llm_provider=llm_provider,
    )
    append_run_log(
        config=config,
        run_at=run_at,
        candidate_count=len(merged_candidates),
        detailed_count=len(detailed_repos),
        baseline=baseline,
        top3=top3,
        warnings=warnings,
        latest_report_path=config["paths"]["latest_report"],
        archived_report_path=archived_report_path,
        snapshot_path=archived_snapshot_path,
        report_verification_result=report_verification_result,
        llm_provider=llm_provider,
    )

    print(f"run_at={run_at}")
    print(f"candidate_count={len(merged_candidates)}")
    print(f"detailed_count={len(detailed_repos)}")
    print(f"baseline={baseline}")
    print(f"report={project_path(config['paths']['latest_report'])}")
    print(f"archived_report={project_path(archived_report_path)}")
    print(f"snapshot={project_path(archived_snapshot_path)}")
    if warnings:
        print(f"warnings={len(warnings)}")


if __name__ == "__main__":
    main()

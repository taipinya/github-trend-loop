from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from common import load_config, project_path


def project_sections(report_text: str) -> list[str]:
    matches = list(re.finditer(r"^###\s+\d+\.\s+.+$", report_text, flags=re.MULTILINE))
    sections: list[str] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(report_text)
        sections.append(report_text[match.start():end])
    return sections


def verify_report(report_text: str, top3: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not re.search(r"[\u4e00-\u9fff]", report_text):
        errors.append("报告必须包含中文内容。")

    project_headings = re.findall(r"^###\s+\d+\.\s+.+$", report_text, flags=re.MULTILINE)
    if len(project_headings) != 3:
        errors.append(f"报告应包含 3 个项目标题，当前为 {len(project_headings)} 个。")

    if top3:
        for repo in top3:
            if repo["html_url"] not in report_text:
                errors.append(f"缺少项目 URL：{repo['html_url']}")
    else:
        github_urls = re.findall(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", report_text)
        if len(set(github_urls)) < 3:
            errors.append(f"报告应包含至少 3 个 GitHub 项目 URL，当前为 {len(set(github_urls))} 个。")

    required_terms = ["项目简介", "README 摘要", "具体怎么用", "应用场景", "风险", "适合谁关注"]
    for term in required_terms:
        count = report_text.count(term)
        if count < 3:
            errors.append(f"报告中 `{term}` 出现次数不足，当前为 {count}。")

    for index, section in enumerate(project_sections(report_text), 1):
        scenario_match = re.search(
            r"####\s+应用场景示例(?P<body>.*?)(?:^####\s+|\Z)",
            section,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not scenario_match:
            errors.append(f"第 {index} 个项目缺少 `应用场景示例` 小节。")
            continue
        scenario_body = scenario_match.group("body")
        bullet_count = len(re.findall(r"^\s*[-*]\s+\S+", scenario_body, flags=re.MULTILINE))
        numbered_count = len(re.findall(r"^\s*\d+[.)、]\s+\S+", scenario_body, flags=re.MULTILINE))
        if bullet_count + numbered_count < 3:
            errors.append(f"第 {index} 个项目的应用场景示例应至少 3 条，当前为 {bullet_count + numbered_count} 条。")

    data_limit_terms = ["GitHub 没有直接提供全站 3 天增长榜", "本地 snapshot", "Trending", "HTML"]
    for term in data_limit_terms:
        if term not in report_text:
            errors.append(f"报告必须说明数据限制，缺少 `{term}`。")

    forbidden_terms = ["#### 一句话判断", "#### 具体使用方式", "#### 下一步验证建议"]
    for term in forbidden_terms:
        if term in report_text:
            errors.append(f"报告不应包含 `{term}`。")

    return not errors, errors


def main() -> None:
    config = load_config()
    report_path = project_path(config["paths"]["latest_report"])
    if not Path(report_path).exists():
        raise SystemExit("latest report not found")
    ok, errors = verify_report(report_path.read_text(encoding="utf-8"), [])
    if not ok:
        raise SystemExit("\n".join(errors))
    print("report_ok=true")


if __name__ == "__main__":
    main()

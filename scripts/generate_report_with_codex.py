from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from common import iso_now, load_config, truncate_text, write_json, write_text


REPORT_WRITER_PROMPT = """你是一个面向计算机专业大学生的前沿开源项目讲解员。

读者画像：
- 读者具备计算机基础，想了解业界生产实践和前沿技术方向。
- 读者不是马上采购或上线项目，而是希望快速看懂项目、获得灵感、找到有趣的课程设计/实验/个人项目方向。
- 读者会自己深入研究安装细节，因此“具体怎么用”应解释理解和探索路径，而不是逐步安装教程。

任务：
基于结构化 GitHub repo 数据和 README 摘要，写一份中文 Markdown 趋势观察报告。

每个项目必须包含：
- URL
- 项目简介：必须用中文说明“这个项目属于什么领域、可能用了什么技术原理、完成了什么任务”。
- 为什么值得关注：结合 stars/forks/subscribers/delta、topic、最近 push、README 结构来讲信息价值。
- README 摘要：先给“中文说明”，解释 README 大概包含哪些结构和内容；再摘取摘要线索。
- 适合人群：面向学生、个人开发者、研究型工程实践者，而不是只面向企业采购者。
- 具体怎么用：说明读者可以从哪些模块、数据流、技术路线或 repo 资料入手理解项目，不要写成安装教程。
- 应用场景示例：必须至少 3 条，贴近具体工业生产或真实业务流程，例如客服质检、工厂巡检、代码审查、企业知识库、机器人仓储、研发平台等。
- 风险或局限：说明信息不足、维护风险、许可证、生产成熟度、依赖成本或工程复杂度。

禁止内容：
- 不要生成“一句话判断”章节。
- 不要生成“具体使用方式”章节；应使用“具体怎么用”章节。
- 不要生成“下一步验证建议”章节。
- 不要写“可用于模型实验、推理链路验证、AI 应用原型或研究复现”这类空泛句子。
- 不要编造安装命令、API、性能数字、融资信息、客户案例或生产落地事实。
- 不要自动 star、fork、comment、open issue、clone 大型仓库或发布报告。

写作风格：
- 像给同专业同学讲一个值得研究的开源项目，清楚、具体、有启发。
- 多解释“技术思路”和“它能启发你做什么项目”，少写“如何一步步安装”。
- 事实和推断要分开；不确定时使用“可能”“从 topic/README 看更像是”等措辞。
- baseline 运行时必须说明：本次没有 3 天增量数据，下一次运行才有 delta。

输出格式硬性要求：
- 必须只输出 Markdown 正文，不要输出解释、前言或代码块。
- 必须包含 exactly 3 个项目标题。
- 项目标题必须使用三级标题，格式必须是 `### 1. owner/repo`、`### 2. owner/repo`、`### 3. owner/repo`。
- 每个项目标题下面必须立即输出一行 `- URL：原始 GitHub URL`，URL 必须和输入数据中的 url 字段完全一致。
- 每个项目标题下必须包含这些四级标题：`#### 项目简介`、`#### 为什么值得关注`、`#### README 摘要`、`#### 具体怎么用`、`#### 适合谁关注`、`#### 应用场景示例`、`#### 风险或局限`。
- 每个项目的 `#### 应用场景示例` 下必须至少有 3 条项目符号列表。
- 报告必须包含 `## 数据限制` 章节，并在该章节中原样包含这些短语：`GitHub 没有直接提供全站 3 天增长榜`、`本地 snapshot`、`Trending`、`HTML`。
- 不要把项目标题写成二级标题、列表项、表格行或加粗文本。
"""


TOPIC_LABELS = {
    "llm": "大语言模型应用",
    "ai-agent": "AI Agent",
    "rag": "检索增强生成",
    "mcp": "模型上下文协议 / 工具调用",
    "code-generation": "代码生成",
    "developer-tools": "开发者工具",
    "machine-learning": "机器学习",
    "robotics": "机器人",
}


README_SIGNAL_KEYWORDS = {
    "安装与快速开始": ["install", "installation", "pip install", "npm install", "uv add", "quickstart"],
    "示例或 Demo": ["example", "examples", "demo", "sample", "tutorial"],
    "文档或指南": ["docs", "documentation", "guide", "usage"],
    "API / SDK": ["api", "sdk", "client", "server"],
    "部署与运行环境": ["deploy", "docker", "compose", "kubernetes", "helm"],
    "评测或性能说明": ["benchmark", "evaluation", "eval", "performance"],
}


def build_llm_prompt(top3: list[dict[str, Any]], baseline: bool) -> str:
    """Build the provider-neutral LLM report prompt; MVP can still render locally."""
    lines = [REPORT_WRITER_PROMPT, "", "以下是本次 Top 3 repo 数据：", ""]
    lines.append(f"- baseline: {baseline}")
    lines.extend(
        [
            "",
            "必须原样使用以下 3 个项目标题，不能改写、不能省略：",
        ]
    )
    for index, repo in enumerate(top3, 1):
        lines.append(f"### {index}. {repo.get('full_name')}")
    lines.extend(
        [
            "",
            "每个项目标题下必须包含这些小节，标题文字也不能改写：",
            "#### 项目简介",
            "#### 为什么值得关注",
            "#### README 摘要",
            "#### 具体怎么用",
            "#### 适合谁关注",
            "#### 应用场景示例",
            "#### 风险或局限",
            "",
            "可以使用的整体结构示例：",
            "# GitHub 趋势项目观察 - YYYY-MM-DD",
            "## 本次结论",
            "## 报告重点",
            "## 数据限制",
            "GitHub 没有直接提供全站 3 天增长榜；增量来自本项目本地 snapshot 对比；Trending 页面来自 HTML 抓取，可能不稳定。",
            "## Top 3 项目",
            "### 1. owner/repo",
            "- URL：https://github.com/owner/repo",
            "#### 项目简介",
            "#### 为什么值得关注",
            "#### README 摘要",
            "#### 具体怎么用",
            "#### 适合谁关注",
            "#### 应用场景示例",
            "#### 风险或局限",
            "",
            "下面是项目数据：",
        ]
    )
    for index, repo in enumerate(top3, 1):
        lines.extend(
            [
                "",
                f"## Repo {index}: {repo.get('full_name')}",
                f"- url: {repo.get('html_url')}",
                f"- description: {repo.get('description')}",
                f"- language: {repo.get('language')}",
                f"- topics: {', '.join(repo.get('topics') or [])}",
                f"- stars: {repo.get('stars')}",
                f"- forks: {repo.get('forks')}",
                f"- subscribers: {repo.get('subscribers')}",
                f"- delta_stars: {repo.get('delta_stars')}",
                f"- delta_forks: {repo.get('delta_forks')}",
                f"- delta_subscribers: {repo.get('delta_subscribers')}",
                f"- pushed_at: {repo.get('pushed_at')}",
                f"- open_issues: {repo.get('open_issues')}",
                f"- license: {repo.get('license')}",
                f"- trend_score: {repo.get('trend_score')}",
                f"- readme_summary: {truncate_text(repo.get('readme_summary') or '', 1400)}",
            ]
        )
    return "\n".join(lines)


def build_codex_prompt(top3: list[dict[str, Any]], baseline: bool) -> str:
    """Backward-compatible alias for older code and docs."""
    return build_llm_prompt(top3, baseline)


def topic_focus(repo: dict[str, Any]) -> list[str]:
    topics = repo.get("topics") or []
    focus = [TOPIC_LABELS[topic] for topic in topics if topic in TOPIC_LABELS]
    return focus[:3] or ["开源软件工程"]


def readme_signals(repo: dict[str, Any]) -> list[str]:
    readme = (repo.get("readme_summary") or "").lower()
    signals: list[str] = []
    for label, keywords in README_SIGNAL_KEYWORDS.items():
        if any(keyword in readme for keyword in keywords):
            signals.append(label)
    return signals


def project_intro(repo: dict[str, Any]) -> str:
    description = repo.get("description") or "仓库没有提供英文简介"
    language = repo.get("language") or "未标明主要语言"
    focus = "、".join(topic_focus(repo))
    topics = set(repo.get("topics") or [])

    if "rag" in topics:
        principle = "核心思路通常是把外部文档切分、向量化检索，再把检索结果交给大模型生成回答"
        task = "帮助系统把企业文档、知识库或长文本资料转成可问答、可检索的应用能力"
    elif "ai-agent" in topics:
        principle = "核心思路通常是让模型根据目标拆解步骤，并通过工具调用、状态管理和反馈循环完成任务"
        task = "把单次问答扩展成可执行的自动化工作流"
    elif "mcp" in topics:
        principle = "核心思路通常是用标准协议把模型、外部工具、数据源和开发环境连接起来"
        task = "让 AI 助手能够安全地读取上下文、调用工具或接入业务系统"
    elif "code-generation" in topics:
        principle = "核心思路通常是结合代码上下文、模板、静态分析或大模型生成来辅助软件开发"
        task = "减少重复编码、迁移、脚手架或代码理解成本"
    elif "robotics" in topics:
        principle = "核心思路通常涉及感知、规划、控制、仿真或机器人软件栈集成"
        task = "让机器人在真实或仿真环境中完成导航、操作、识别或协作任务"
    elif "machine-learning" in topics or "llm" in topics:
        principle = "核心思路通常围绕模型训练、推理、数据处理、评测或大模型应用编排"
        task = "帮助开发者更快构建、评估或部署智能系统"
    elif "developer-tools" in topics:
        principle = "核心思路通常是把常见研发动作封装成 CLI、插件、服务或自动化流程"
        task = "提升代码阅读、构建、测试、部署或团队协作效率"
    else:
        principle = "从 topic 和 README 摘要看，它更像是一个解决特定工程问题的开源工具"
        task = "把某类重复、复杂或新兴的技术任务包装成可复用的软件能力"

    return (
        f"这是一个偏向 {focus} 方向的项目，主要语言是 {language}。"
        f"仓库简介是：“{description}”。"
        f"从当前元数据和 README 摘要推断，{principle}，目标是{task}。"
    )


def momentum_sentence(repo: dict[str, Any], baseline: bool) -> str:
    if baseline:
        return (
            f"本次是 baseline，暂时没有 3 天增量；可见信号是 "
            f"{repo.get('stars', 0)} stars、{repo.get('forks', 0)} forks、"
            f"{repo.get('subscribers', 0)} subscribers，最近 push 时间为 {repo.get('pushed_at') or '未知'}。"
        )

    return (
        f"本轮 3 天增量是 {repo.get('delta_stars', 0)} stars、"
        f"{repo.get('delta_forks', 0)} forks、{repo.get('delta_subscribers', 0)} subscribers。"
        f"当前累计 {repo.get('stars', 0)} stars，最近 push 时间为 {repo.get('pushed_at') or '未知'}。"
    )


def readme_explanation(repo: dict[str, Any]) -> str:
    signals = readme_signals(repo)
    if not repo.get("readme_summary"):
        return "当前没有可用 README 摘要，因此只能从仓库描述、topic 和 GitHub 元数据理解项目；信息价值有限。"
    if signals:
        return (
            "从 README 摘要识别到的结构包括："
            + "、".join(signals)
            + "。这说明 README 至少提供了一部分理解项目定位和工程形态的材料。"
        )
    return "README 摘要中没有明显识别出安装、示例、文档、API 或部署结构，更适合作为初步了解，不宜据此判断成熟度。"


def infer_people(repo: dict[str, Any]) -> str:
    topics = set(repo.get("topics") or [])
    language = repo.get("language") or "相关技术栈"
    if {"llm", "rag", "ai-agent", "mcp"}.intersection(topics):
        return (
            f"适合想理解 AI 应用工程化的学生：例如 RAG、Agent、工具调用、上下文协议、LLM 应用后端。"
            f"如果你会 {language}，可以把它当作课程设计、实验室项目或个人 AI 工具的灵感来源。"
        )
    if {"code-generation", "developer-tools"}.intersection(topics):
        return (
            f"适合对开发者工具、自动化研发平台、代码生成和软件工程效率感兴趣的学生。"
            f"它可能启发你做 IDE 插件、代码审查助手、脚手架或 CI 辅助工具。"
        )
    if {"robotics", "machine-learning"}.intersection(topics):
        return (
            "适合关注机器人、机器学习系统、仿真平台或智能硬件方向的学生。"
            "它可以帮助你理解算法如何被包装成可运行的软件系统。"
        )
    return "适合想扩展技术视野、寻找开源项目选题或观察新兴工程实践的计算机专业学生。"


def infer_how_to_use(repo: dict[str, Any]) -> str:
    topics = set(repo.get("topics") or [])
    readme_summary = repo.get("readme_summary") or ""
    lines = [
        "1. 先把 README 当作项目地图，识别它的输入、核心处理流程和输出结果。",
        "2. 再看 examples、docs、workflow 或 API 相关内容，判断作者希望用户如何把它嵌入真实系统。",
        "3. 最后选一个很小的业务问题，把项目思想改造成自己的课程设计或个人实验。"
    ]
    if "rag" in topics:
        lines.append("4. 重点关注文档切分、索引、检索、重排和生成回答之间的数据流。")
    elif "ai-agent" in topics or "mcp" in topics:
        lines.append("4. 重点关注任务状态、工具权限、上下文传递和失败恢复这些工程问题。")
    elif "code-generation" in topics or "developer-tools" in topics:
        lines.append("4. 重点关注它如何读取代码上下文、生成产物、接入 CLI/CI/IDE 工作流。")
    elif "robotics" in topics:
        lines.append("4. 重点关注感知、规划、控制、仿真和真实设备之间的接口。")
    elif readme_summary:
        lines.append("4. 重点关注 README 中反复出现的名词，它们通常就是项目的核心抽象。")
    return "\n".join(lines)


def infer_scenario(repo: dict[str, Any]) -> str:
    topics = set(repo.get("topics") or [])
    focus = set(topic_focus(repo))

    if "rag" in topics:
        return (
            "- 制造业设备知识库：把设备手册、维修记录、质检规范接入检索系统，一线工程师查询故障原因和备件型号。\n"
            "- 企业客服质检：把客服 SOP、历史工单和质检规则接入问答系统，辅助新人快速定位处理流程。\n"
            "- 高校实验室资料库：把论文、实验记录、项目文档整理成可问答系统，帮助团队复用历史经验。"
        )
    if "ai-agent" in topics:
        return (
            "- 研发运维告警：Agent 读取日志、查询监控、总结异常并生成排查建议。\n"
            "- 销售运营自动化：Agent 根据 CRM 记录、邮件和会议纪要生成客户跟进清单。\n"
            "- 校园项目助手：Agent 管理课程项目 issue、文档和实验数据，提醒成员补齐任务。"
        )
    if "mcp" in topics:
        return (
            "- 企业内部工具接入：把数据库、文件系统、代码仓库或内部 API 包装成标准工具供 AI 助手调用。\n"
            "- 研发知识查询：让模型在受控权限下读取 repo、issue、文档，回答项目上下文问题。\n"
            "- 个人开发环境：把本地脚本、笔记和项目文件暴露为工具，构建可操作的学习助手。"
        )
    if "code-generation" in topics:
        return (
            "- 企业代码迁移：批量改写旧接口、生成适配层或迁移脚手架。\n"
            "- 代码审查辅助：自动解释复杂模块、补充测试建议、标记潜在风险。\n"
            "- 课程项目自动评审：读取学生仓库结构，生成可读性、测试覆盖和架构建议。"
        )
    if "developer-tools" in topics:
        return (
            "- 企业研发平台：把构建、测试、依赖检查、文档生成、发布流程做成统一工具。\n"
            "- 开源项目维护：自动整理 changelog、issue 标签、贡献者文档和 release note。\n"
            "- 学生团队协作：把课程项目的格式检查、测试运行和报告生成做成 CLI。"
        )
    if "robotics" in topics:
        return (
            "- 仓储机器人：在货架之间完成定位、路径规划、避障和任务调度。\n"
            "- 工厂巡检：机器人识别仪表、设备异常和安全隐患，并生成巡检记录。\n"
            "- 校园机器人实验：在仿真环境中复现导航、抓取或多机器人协作任务。"
        )
    if "machine-learning" in topics or "机器学习" in focus or "大语言模型应用" in focus:
        return (
            "- 工业质检：识别产线图片中的划痕、缺件、错装等异常，并交给质检员复核。\n"
            "- 客服工单分类：把用户问题自动归类、聚合高频故障并推荐处理模板。\n"
            "- 设备异常预警：结合传感器数据、日志和历史维修记录预测可能故障。"
        )
    return (
        "- 日志整理：把分散日志解析、归类、摘要并生成排查报告。\n"
        "- 数据同步：把多个系统的数据清洗、对齐并生成可追踪的同步记录。\n"
        "- 项目初始化：把模板、依赖检查、文档生成和 CI 配置封装成一条命令。"
    )


def infer_risk(repo: dict[str, Any], baseline: bool) -> str:
    risks: list[str] = []
    if baseline:
        risks.append("本次是 baseline，没有 3 天增量数据，不能判断它是否正在持续升温。")
    if not repo.get("readme_summary"):
        risks.append("README 摘要不可用，项目定位和技术细节可能需要直接进仓库深挖。")
    elif repo.get("readme_length", 0) < 1000:
        risks.append("README 偏短，可能只展示概念或最小介绍，技术原理和工程边界不够清楚。")
    if repo.get("open_issues", 0) > 200:
        risks.append("open issues 较多，可能意味着项目活跃，也可能意味着问题积压。")
    if repo.get("license") in ("", "NOASSERTION"):
        risks.append("许可证信息不明确，如果将来基于它做公开项目或比赛作品，需要先确认合规。")
    if repo.get("fork"):
        risks.append("这是 fork 仓库，需要区分它和上游项目的差异，避免误判创新点。")
    if not risks:
        risks.append("主要局限是报告只基于 GitHub 元数据和 README 摘要，不能替代阅读源码、文档和 issue。")
    return " ".join(risks)


def score_summary(repo: dict[str, Any]) -> str:
    return (
        f"trend_score={repo.get('trend_score')}, "
        f"3 天新增 Star={repo.get('delta_stars')}, "
        f"新增订阅={repo.get('delta_subscribers')}, "
        f"新增 Fork={repo.get('delta_forks')}, "
        f"当前 Star={repo.get('stars')}"
    )


def generate_report_locally(top3: list[dict[str, Any]], config: dict[str, Any], baseline: bool) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    title = config["report"].get("title", "GitHub 趋势项目观察")
    lines: list[str] = [
        f"# {title} - {today}",
        "",
        "## 本次结论",
        "",
    ]
    if baseline:
        lines.append(
            "本次运行是 baseline：没有 previous snapshot，因此不能计算 3 天增量。"
            "这份报告先建立观察基线，下一次运行开始才会用 delta_stars、delta_subscribers、delta_forks 判断真实增长。"
        )
    else:
        lines.append("本次报告基于 previous snapshot 计算 3 天增量，并结合 README 完整度、topic 相关性和最近 push 情况排序。")

    lines.extend(
        [
            "",
            "## 报告重点",
            "",
            "这份报告面向想了解业界生产和前沿技术的计算机专业学生：重点解释项目所属领域、技术思路、完成的任务、真实业务场景和可能带来的个人项目灵感；不写安装教程或逐步使用说明。",
            "",
            "## 数据限制",
            "",
            "GitHub 没有直接提供全站 3 天增长榜；本报告中的增量来自本项目保存的本地 snapshot 对比。第一次运行只是 baseline，第二次运行开始才有更有意义的 delta_stars、delta_subscribers、delta_forks。Trending 页面来自 HTML 抓取，GitHub 页面结构变化时可能不稳定。",
            "",
            "## Top 3 项目",
            "",
        ]
    )

    for index, repo in enumerate(top3, 1):
        topics = ", ".join(repo.get("topics") or []) or "无"
        readme_summary = truncate_text(repo.get("readme_summary") or "README 摘要暂不可用。", 700)
        signals = "、".join(readme_signals(repo)) or "未识别到明显结构化线索"
        lines.extend(
            [
                f"### {index}. {repo['full_name']}",
                "",
                f"- URL：{repo['html_url']}",
                f"- 主要语言：{repo.get('language') or '未知'}",
                f"- Topics：{topics}",
                f"- README 结构线索：{signals}",
                f"- 评分摘要：{score_summary(repo)}",
                "",
                "#### 项目简介",
                "",
                project_intro(repo),
                "",
                "#### 为什么值得关注",
                "",
                momentum_sentence(repo, baseline),
                f"它落在 {' / '.join(topic_focus(repo))} 方向，可以帮助你观察这个方向的开源项目通常如何组织能力、抽象接口和呈现工程边界。",
                "",
                "#### README 摘要",
                "",
                f"中文说明：{readme_explanation(repo)}",
                "",
                f"摘要线索：{readme_summary}",
                "",
                "#### 具体怎么用",
                "",
                infer_how_to_use(repo),
                "",
                "#### 适合谁关注",
                "",
                infer_people(repo),
                "",
                "#### 应用场景示例",
                "",
                infer_scenario(repo),
                "",
                "#### 风险或局限",
                "",
                infer_risk(repo, baseline),
                "",
            ]
        )

    lines.extend(
        [
            "## Human Gate",
            "",
            "本报告是学习和选题参考，不自动发布。报告中的技术原理和场景推断来自 GitHub 元数据、topic 和 README 摘要，深入使用前仍需要阅读源码、文档、issues 和许可证。",
            "",
        ]
    )
    return "\n".join(lines)


def resolve_llm_config(config: dict[str, Any]) -> dict[str, Any]:
    llm_config = dict(config.get("llm") or {})
    if not llm_config and config.get("openai_report"):
        legacy = config["openai_report"]
        llm_config = {
            "enabled": legacy.get("enabled", False),
            "provider": "openai",
            "model": legacy.get("model"),
            "base_url": "",
            "api_key_env": "OPENAI_API_KEY",
            "max_output_tokens": legacy.get("max_output_tokens", 5000),
            "temperature": legacy.get("temperature", 0.4),
        }

    provider = str(llm_config.get("provider") or "openai").lower()
    llm_config["provider"] = provider

    if provider == "deepseek":
        llm_config["base_url"] = llm_config.get("base_url") or "https://api.deepseek.com"
        llm_config["model"] = llm_config.get("model") or "deepseek-v4-flash"
        llm_config["api_key_env"] = llm_config.get("api_key_env") or "DEEPSEEK_API_KEY"
    elif provider == "openai":
        llm_config["base_url"] = llm_config.get("base_url") or ""
        llm_config["model"] = llm_config.get("model") or "gpt-4.1-mini"
        llm_config["api_key_env"] = llm_config.get("api_key_env") or "OPENAI_API_KEY"
    else:
        llm_config["model"] = llm_config.get("model") or "gpt-4.1-mini"
        llm_config["base_url"] = llm_config.get("base_url") or ""
        llm_config["api_key_env"] = llm_config.get("api_key_env") or "OPENAI_API_KEY"

    llm_config["max_output_tokens"] = int(llm_config.get("max_output_tokens", 5000))
    llm_config["temperature"] = llm_config.get("temperature", 0.4)
    llm_config["enabled"] = bool(llm_config.get("enabled", False))
    llm_config["require_success"] = bool(llm_config.get("require_success", True))
    return llm_config


def extract_chat_completion_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    if not message:
        return ""
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                chunks.append(str(item["text"]))
            elif hasattr(item, "text"):
                chunks.append(str(item.text))
        return "\n".join(chunks).strip()
    return ""


def ensure_required_project_urls(report: str, top3: list[dict[str, Any]]) -> str:
    lines = report.splitlines()
    for index, repo in enumerate(top3, 1):
        url = repo.get("html_url")
        full_name = repo.get("full_name")
        if not url or not full_name or url in "\n".join(lines):
            continue

        expected_heading = f"### {index}. {full_name}"
        inserted = False
        for line_index, line in enumerate(lines):
            if line.strip() == expected_heading:
                lines[line_index + 1:line_index + 1] = ["", f"- URL：{url}"]
                inserted = True
                break

        if not inserted:
            lines.extend(["", f"- URL：{url}"])

    return "\n".join(lines).strip() + "\n"


def generate_report_with_llm(top3: list[dict[str, Any]], config: dict[str, Any], baseline: bool) -> str | None:
    llm_config = resolve_llm_config(config)
    status: dict[str, Any] = {
        "run_at": iso_now(),
        "enabled": llm_config["enabled"],
        "provider": llm_config["provider"],
        "model": llm_config["model"],
        "base_url": llm_config["base_url"],
        "api_key_env": llm_config["api_key_env"],
        "api_key_present": False,
        "attempted": False,
        "used_llm": False,
        "fallback": True,
        "reason": "",
        "failed_report_path": "",
    }

    def save_status(reason: str) -> None:
        status["reason"] = reason
        try:
            write_json("data/latest_llm_status.json", status)
        except Exception as exc:
            print(f"Failed to write LLM status: {exc}")

    def fail_or_fallback(reason: str) -> None:
        save_status(reason)
        if llm_config["require_success"]:
            raise RuntimeError(reason)
        return None

    if not llm_config["enabled"]:
        save_status("llm.disabled")
        return None

    api_key_env = llm_config["api_key_env"]
    api_key = os.getenv(api_key_env)
    status["api_key_present"] = bool(api_key)
    if not api_key:
        reason = f"{api_key_env} is not set in the Python process environment"
        print(f"llm enabled but {api_key_env} is not set.")
        fail_or_fallback(reason)
        return None

    try:
        from openai import OpenAI
    except ImportError:
        reason = "openai package is not installed"
        print("openai package is not installed; run `pip install -r requirements.txt`.")
        fail_or_fallback(reason)
        return None

    model_env = f"{llm_config['provider'].upper()}_MODEL"
    model = os.getenv(model_env) or os.getenv("LLM_MODEL") or llm_config["model"]
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if llm_config.get("base_url"):
        client_kwargs["base_url"] = llm_config["base_url"]

    request: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你必须严格按用户给出的 Markdown 标题格式生成报告。不要输出代码块，不要解释规则。",
            },
            {
                "role": "user",
                "content": build_llm_prompt(top3, baseline),
            }
        ],
        "max_tokens": llm_config["max_output_tokens"],
    }
    if llm_config["temperature"] is not None:
        request["temperature"] = float(llm_config["temperature"])

    try:
        status["attempted"] = True
        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(**request)
        report = extract_chat_completion_text(response)
        report = ensure_required_project_urls(report, top3)
    except Exception as exc:
        provider = llm_config["provider"]
        reason = f"{provider} report generation failed: {exc}"
        print(reason)
        fail_or_fallback(reason)
        return None

    if not report:
        reason = "LLM report generation returned empty text"
        print(reason)
        fail_or_fallback(reason)
        return None

    try:
        from verify_report import verify_report

        ok, errors = verify_report(report, top3)
        if not ok:
            reason = "LLM report failed verification"
            print("LLM report failed verification.")
            for error in errors:
                print(f"report_error: {error}")
            status["verification_errors"] = errors
            failed_report_path = "data/latest_llm_report_failed.md"
            write_text(failed_report_path, report)
            status["failed_report_path"] = failed_report_path
            fail_or_fallback(reason)
            return None
    except Exception as exc:
        reason = f"LLM report verification failed unexpectedly: {exc}"
        print(reason)
        fail_or_fallback(reason)
        return None

    status["used_llm"] = True
    status["fallback"] = False
    save_status("llm.report.generated")
    return report


def generate_report_with_openai(top3: list[dict[str, Any]], config: dict[str, Any], baseline: bool) -> str | None:
    """Backward-compatible wrapper; provider is now selected by config['llm']."""
    return generate_report_with_llm(top3, config, baseline)


def generate_report(top3: list[dict[str, Any]], config: dict[str, Any], baseline: bool) -> str:
    api_report = generate_report_with_llm(top3, config, baseline)
    if api_report:
        return api_report
    return generate_report_locally(top3, config, baseline)


def main() -> None:
    load_config()
    print("Use scripts/run_loop.py to generate reports as part of the full loop.")


if __name__ == "__main__":
    main()

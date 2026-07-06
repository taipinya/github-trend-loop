# trend-triage

## Purpose

用于 GitHub 趋势项目观察 loop 的候选项目收集、去重、过滤与初筛。

## Candidate Sources

1. GitHub Trending daily 前 30。
2. GitHub Trending weekly 前 30。
3. GitHub Search API：
   - `created:>{date_30d} stars:>50`
   - `pushed:>{date_14d} stars:>200`
   - `stars:100..5000 pushed:>{date_14d}`
4. 领域 topic：
   - `llm`
   - `ai-agent`
   - `rag`
   - `mcp`
   - `code-generation`
   - `developer-tools`
   - `machine-learning`
   - `robotics`

## Rules

- 日期占位符必须在运行时转换为 `YYYY-MM-DD`。
- Trending 抓取失败时只记录 warning，不中断 Search API。
- 所有 GitHub API 请求必须带 `User-Agent`。
- 支持 `GITHUB_TOKEN` 环境变量，但不能要求用户必须提供。
- 候选项目按 `owner/repo` 小写形式去重。
- 去重后目标规模是 200 到 500 个 repo；API 限制导致不足时可以继续运行，但必须在 warning 或状态中体现。
- 不 clone 大型仓库，不 star，不 fork，不 comment，不 open issue。

## Output Expectations

Python 程序负责输出结构化候选和 snapshot。Agent 或人工只负责审阅规则是否需要调整。


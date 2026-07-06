# LOOP: GitHub Trend Observer

## 目标

每 3 天观察一次 GitHub 上近期值得关注的项目，结合 Trending、Search API、topic 召回、repo 详情和 README 信息，选出 3 个项目，并生成中文 Markdown 说明文档。

本 loop 的核心目标是建立一个可重复、可检查、可改进的闭环：

1. 收集候选项目。
2. 去重与过滤。
3. 保存本次 snapshot。
4. 与上次 snapshot 比较，计算 3 天增量。
5. 打分并选择 Top 3。
6. 生成中文报告。
7. 验证报告完整性。
8. 更新状态与运行日志。
9. 在 GitHub Actions 中提交本地生成的 data、reports、STATE.md 和 loop-run-log.md。
10. 由人决定是否对外传播、采用项目或调整规则。

## 候选来源

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

日期占位符会在运行时动态替换为 `YYYY-MM-DD`。

## 评分规则

`trend_score` 包含：

- `delta_stars`
- `5 * delta_subscribers`
- `2 * delta_forks`
- 最近 push 加分
- README 完整度加分
- topic 相关性加分
- awesome-list 惩罚
- 长期未维护惩罚

第一次运行没有 previous snapshot，只建立 baseline。报告中必须说明下一次运行才会有增量数据。第二次运行开始按 3 天增量排序。

## 输出文件

- `data/latest_snapshot.json`
- `data/snapshots/YYYY-MM-DDTHHMMSSZ.json`
- `data/latest_ranked.json`
- `data/latest_top3.json`
- `reports/latest.md`
- `reports/YYYY-MM-DDTHHMMSSZ-github-trends.md`
- `STATE.md`
- `loop-run-log.md`

`reports/latest.md` 每次运行会被覆盖为最新报告；带时间戳的历史报告会保留。`data/latest_snapshot.json` 用于下一次运行计算增量；`data/snapshots/` 下的历史 snapshot 会保留，方便追踪每次运行的候选数据。

## 禁止行为

本 loop 不允许：

- 自动 star。
- 自动 fork。
- 自动 comment。
- 自动 open issue。
- clone 大型仓库。
- 自动发布报告。
- 绕过人工审核向外部渠道推送结论。

## Human Gate

GitHub Actions 可以自动提交本地生成的状态、报告和运行日志，但不得自动 star、fork、comment、open issue、发布到外部平台。所有外部传播、项目采用、项目安装和生产使用都必须由人类审核。

报告生成后仍应经过人工检查，尤其是：

- 项目是否真实有价值。
- 项目简介是否准确解释了领域、技术原理和任务。
- 应用场景是否贴近真实业务或工业生产。
- 风险或局限是否充分。
- 是否需要补充人工阅读源码、文档或论文后的结论。
- 是否适合公开发布。

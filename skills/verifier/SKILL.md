# verifier

## Purpose

验证 GitHub 趋势项目观察报告是否满足 MVP 验收标准。

## Acceptance Criteria

报告必须：

- 是中文 Markdown。
- 包含 3 个项目。
- 每个项目包含 URL。
- 每个项目包含项目简介。
- 每个项目包含适合谁关注。
- 每个项目包含具体怎么用。
- 每个项目包含至少 3 个应用场景示例。
- 每个项目包含风险或局限。
- 如果是 baseline，说明下一次运行才有增量数据。
- 说明数据限制，包括 GitHub 没有直接提供全站 3 天增长榜、本地 snapshot 对比、Trending HTML 抓取不稳定。

## Failure Handling

如果报告缺少必填内容，verifier 应返回失败并指出缺失项。MVP 中由 `scripts/verify_report.py` 执行基础验收。

## Prohibited Actions

验证阶段不能自动 star、fork、comment、open issue、clone 大型仓库或发布报告。

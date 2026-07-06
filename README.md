# github-trend-loop

一个轻量的 GitHub 趋势项目观察器：每 3 天自动收集 GitHub Trending 和 Search API 候选项目，计算增量热度，筛出 Top 3，并用 DeepSeek 生成面向计算机专业学生的中文技术观察报告。

它不是榜单搬运工具，而是一个 Loop Engineering 闭环：持续采集、保存 snapshot、对比增量、生成报告、验证质量、提交结果，让你定期看到“最近哪些开源项目值得研究，以及它们能启发什么项目想法”。

## 它会做什么

运行一次 `python scripts/run_loop.py` 后，会自动完成：

- 收集 GitHub Trending daily / weekly 候选项目。
- 使用 GitHub Search API 按新项目、活跃项目、topic 召回候选。
- 去重、过滤、拉取 repo metadata 和 README 摘要。
- 保存最新 snapshot 和历史 snapshot。
- 从第二次运行开始计算 `delta_stars`、`delta_subscribers`、`delta_forks`。
- 根据增量、最近 push、README 完整度、topic 相关性等规则打分。
- 选出 Top 3 项目。
- 调用 DeepSeek 生成中文 Markdown 报告。
- 验证报告结构和质量。
- 更新 `STATE.md` 和 `loop-run-log.md`。
- 在 GitHub Actions 中自动提交新的 data、reports、状态和日志。

项目不会自动 star、fork、comment、open issue，不会 clone 大型仓库，也不会自动发布报告到外部平台。

## 效果展示

生成的报告会保存在：

- `reports/latest.md`：最新报告。
- `reports/YYYY-MM-DDTHHMMSSZ-github-trends.md`：历史报告。

报告不是只列仓库名，而是解释项目是什么、技术思路是什么、适合谁关注、具体怎么用来学习，以及有哪些真实场景启发。

示例片段：

```markdown
### 1. langgenius/dify
- URL：https://github.com/langgenius/dify

#### 项目简介
Dify 是一个 LLM 应用开发平台，属于 AI 工程化领域。它利用了 RAG、Agent 编排、提示词管理等技术，完成从数据集准备到应用部署的全流程。

#### 具体怎么用
建议先通读 README 中的“架构”部分，理解前端、后端、推理引擎、向量数据库的交互关系。然后从“创建知识库”模块入手，观察数据切分、向量化、检索的逻辑。

#### 应用场景示例
- 企业内部知识库问答：将产品手册、FAQ 导入 Dify，员工通过网页或机器人查询。
- 客服助手：上传历史对话记录，建立领域知识库，结合意图识别提供回复建议。
- 代码审查辅助：集成代码库文档，让 AI 根据上下文解释代码逻辑或提出修改建议。
```

每份报告末尾都会固定包含数据限制说明，例如 GitHub 不直接提供全站 3 天增长榜、增量来自本项目保存的本地 snapshot、第一次运行只是 baseline、Trending 来自 HTML 抓取等。

## 适合谁

- 计算机专业学生：用来观察业界开源趋势，找课程设计、毕业设计、个人项目灵感。
- 想学习 AI 工程化的人：定期发现 RAG、Agent、MCP、代码生成、开发者工具等方向的新项目。
- 技术雷达爱好者：用一个可追踪的 loop 保存每次趋势观察结果。
- 开源项目研究者：用历史 snapshot 对比项目热度变化。

## 快速开始

安装依赖：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

PowerShell 设置环境变量并运行：

```powershell
$env:GITHUB_TOKEN="你的 GitHub token"
$env:DEEPSEEK_API_KEY="你的 DeepSeek API key"
python scripts/run_loop.py
```

CMD：

```cmd
set GITHUB_TOKEN=你的 GitHub token
set DEEPSEEK_API_KEY=你的 DeepSeek API key
python scripts/run_loop.py
```

`GITHUB_TOKEN` 缺失时可以继续运行，但 GitHub API rate limit 更低。`DEEPSEEK_API_KEY` 缺失且 `llm.enabled: true` 时会失败，避免提交低质量兜底报告。

## GitHub Actions 部署

进入 GitHub 仓库：

```text
Settings
-> Secrets and variables
-> Actions
-> New repository secret
```

添加：

```text
Name: DEEPSEEK_API_KEY
Value: 你的 DeepSeek API key
```

`GITHUB_TOKEN` 使用 GitHub Actions 内置 token，不需要手动创建 repository secret。

手动触发：

```text
Actions
-> GitHub Trend Loop
-> Run workflow
```

自动运行频率：每 3 天一次。

workflow 成功后会自动提交：

- `data/`
- `reports/`
- `STATE.md`
- `loop-run-log.md`

commit message：

```text
Update GitHub trend loop report
```

## 输出文件

| 文件 | 作用 |
| --- | --- |
| `reports/latest.md` | 最新中文报告，每次运行覆盖 |
| `reports/YYYY-MM-DDTHHMMSSZ-github-trends.md` | 历史报告，每次运行新增 |
| `data/latest_snapshot.json` | 最新 snapshot，用于下一次计算增量 |
| `data/snapshots/YYYY-MM-DDTHHMMSSZ.json` | 历史 snapshot |
| `data/latest_ranked.json` | 最新完整排名 |
| `data/latest_top3.json` | 最新 Top 3 |
| `data/latest_llm_status.json` | LLM 调用诊断状态 |
| `STATE.md` | 当前 loop 状态 |
| `loop-run-log.md` | 每次运行摘要 |

第一次运行没有 previous snapshot，只建立 baseline。第二次运行开始，`delta_stars`、`delta_subscribers`、`delta_forks` 才更有意义。

## 候选来源

- GitHub Trending daily / weekly，各取前 30 个。
- GitHub Search API：
  - `created:>{date_30d} stars:>50`
  - `pushed:>{date_14d} stars:>200`
  - `stars:100..5000 pushed:>{date_14d}`
- 领域 topic：
  - `llm`
  - `ai-agent`
  - `rag`
  - `mcp`
  - `code-generation`
  - `developer-tools`
  - `machine-learning`
  - `robotics`

`{date_30d}` 和 `{date_14d}` 会在运行时动态替换为 `YYYY-MM-DD`。

## 评分规则

`trend_score` 大致由这些因素组成：

- 3 天新增 Star
- `5 x` 3 天新增订阅
- `2 x` 3 天新增 Fork
- 最近 push 加分
- README 完整度加分
- topic 相关性加分
- awesome-list 惩罚
- 长期未维护惩罚

第一版评分不是为了追求完美排序，而是建立一个可以持续迭代的观察闭环。

## LLM 配置

默认使用 DeepSeek，配置在 `config.yaml`：

```yaml
llm:
  enabled: true
  provider: deepseek
  model: deepseek-v4-flash
  base_url: https://api.deepseek.com
  api_key_env: DEEPSEEK_API_KEY
  max_output_tokens: 5000
  temperature: 0.4
  require_success: true
```

项目使用 `openai` Python SDK 调用 OpenAI-compatible provider。切回 OpenAI 时可改为：

```yaml
llm:
  enabled: true
  provider: openai
  model: gpt-4.1-mini
  base_url: ""
  api_key_env: OPENAI_API_KEY
```

API key 只从环境变量读取，不会写入代码、日志、报告或 commit。

## 质量验证与排查

报告必须包含：

- 3 个项目。
- 每个项目的 GitHub URL。
- 项目简介。
- README 摘要。
- 具体怎么用。
- 至少 3 个应用场景示例。
- 适合谁关注。
- 风险或局限。
- 固定的数据限制说明。

如果怀疑 LLM 没有调用，查看：

```powershell
Get-Content .\data\latest_llm_status.json
```

重点字段：

- `api_key_present`：Python 进程是否读到 API key。
- `attempted`：是否发起 LLM API 请求。
- `used_llm`：最终报告是否使用 LLM 输出。
- `fallback`：是否回退到本地模板。
- `reason`：失败或回退原因。
- `failed_report_path`：LLM 原始失败稿路径。

如果 GitHub Actions 失败，优先看：

- `Run trend loop` step 的错误。
- `data/latest_llm_status.json` artifact。
- `data/latest_llm_report_failed.md` artifact。
- GitHub API rate limit warning。
- report verification error。

## 项目结构

```text
.
├─ .github/workflows/trend-loop.yml
├─ config.yaml
├─ data/
│  ├─ latest_snapshot.json
│  ├─ latest_ranked.json
│  ├─ latest_top3.json
│  └─ snapshots/
├─ reports/
│  ├─ latest.md
│  └─ *-github-trends.md
├─ scripts/
│  ├─ run_loop.py
│  ├─ collect_trending.py
│  ├─ collect_search.py
│  ├─ fetch_repo_details.py
│  ├─ score_repos.py
│  ├─ select_top3.py
│  ├─ generate_report_with_codex.py
│  ├─ verify_report.py
│  └─ update_state.py
├─ LOOP.md
├─ STATE.md
└─ loop-run-log.md
```

## 安全边界

本项目只读取公开 GitHub 信息和配置的 API，不会：

- 自动 star。
- 自动 fork。
- 自动 comment。
- 自动 open issue。
- clone 大型仓库。
- 自动发布报告到外部平台。
- 把 `GITHUB_TOKEN` 或 `DEEPSEEK_API_KEY` 写入文件、日志、报告或 commit。

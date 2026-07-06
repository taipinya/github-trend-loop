# github-trend-loop

一个 Python 3.11 的 Loop Engineering MVP：每 3 天观察 GitHub 趋势项目，筛出 3 个值得关注的仓库，调用 DeepSeek 生成中文 Markdown 报告，并保留历史报告、历史 snapshot、状态和运行日志。

项目不会自动 star、fork、comment、open issue，不会 clone 大型仓库，也不会自动发布报告到外部平台。

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_loop.py
```

PowerShell 环境变量：

```powershell
$env:GITHUB_TOKEN="你的 GitHub token"
$env:DEEPSEEK_API_KEY="你的 DeepSeek API key"
python scripts/run_loop.py
```

CMD 环境变量：

```cmd
set GITHUB_TOKEN=你的 GitHub token
set DEEPSEEK_API_KEY=你的 DeepSeek API key
python scripts/run_loop.py
```

`GITHUB_TOKEN` 缺失时可以继续运行，但 GitHub API rate limit 更低。`DEEPSEEK_API_KEY` 缺失且 `llm.enabled: true` 时会失败，避免提交本地兜底报告。

## LLM 配置

项目使用 `openai` Python SDK 调用 OpenAI-compatible provider。默认配置为 DeepSeek：

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

切回 OpenAI 时可改为：

```yaml
llm:
  enabled: true
  provider: openai
  model: gpt-4.1-mini
  base_url: ""
  api_key_env: OPENAI_API_KEY
```

API key 只能从环境变量读取，不会写入代码、日志、报告或 commit。

## 部署到 GitHub Actions

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

`GITHUB_TOKEN` 使用 GitHub Actions 内置 token 即可，不需要手动创建 repository secret。

手动触发 workflow：

```text
Actions
-> GitHub Trend Loop
-> Run workflow
```

自动运行频率：每 3 天运行一次。

GitHub Actions 会：

1. 使用 Python 3.11。
2. 安装 `requirements.txt`。
3. 运行 `python scripts/run_loop.py`。
4. 成功后提交 `data/`、`reports/`、`STATE.md`、`loop-run-log.md`。
5. commit message 为 `Update GitHub trend loop report`。

没有文件变化时 workflow 不会失败。workflow 不会自动发布到外部平台。

## 输出文件

- `reports/latest.md`：最新报告，每次运行覆盖。
- `reports/YYYY-MM-DDTHHMMSSZ-github-trends.md`：历史报告，每次运行新增一份，同一天多次运行也不会覆盖。
- `data/latest_snapshot.json`：最新 snapshot，用于下一次运行计算增量。
- `data/snapshots/YYYY-MM-DDTHHMMSSZ.json`：历史 snapshot，每次运行保留。
- `data/latest_ranked.json`：最新完整排名。
- `data/latest_top3.json`：最新 Top 3。
- `data/latest_llm_status.json`：LLM 调用诊断状态。
- `STATE.md`：当前 loop 状态。
- `loop-run-log.md`：运行日志。

第一次运行没有 previous snapshot，只建立 baseline。第二次运行开始，才会有更有意义的 `delta_stars`、`delta_subscribers`、`delta_forks`。

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

## 验证与排查

报告必须包含 3 个项目、GitHub URL、项目简介、具体怎么用、至少 3 个应用场景示例、适合谁关注、风险或局限，以及数据限制说明。

如果怀疑没有调用 LLM，查看：

```powershell
Get-Content .\data\latest_llm_status.json
```

优先看字段：

- `api_key_present`：Python 进程是否读到 API key。
- `attempted`：是否发起 LLM API 请求。
- `used_llm`：最终报告是否使用 LLM 输出。
- `fallback`：是否回退到本地模板。
- `reason`：失败或回退原因。
- `failed_report_path`：LLM 原始失败稿路径。

如果 GitHub Actions 失败，优先查看：

- `Run trend loop` step 的错误。
- `data/latest_llm_status.json` artifact。
- `data/latest_llm_report_failed.md` artifact。
- GitHub API rate limit warning。
- report verification error。

## 文件说明

- `LOOP.md`：loop 目标、候选来源、评分规则、输出文件、禁止行为和 human gate。
- `STATE.md`：last run、baseline 状态、最新报告和 snapshot 路径、Top 3、限制和下次注意事项。
- `loop-run-log.md`：每次运行摘要。
- `config.yaml`：采集、过滤、评分、LLM 和输出配置。
- `scripts/run_loop.py`：主入口。
- `scripts/generate_report_with_codex.py`：报告生成入口。
- `scripts/verify_report.py`：报告验收。
- `skills/`：Codex Agent 相关的任务边界与验收规范。

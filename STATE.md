# STATE

- Last run: 2026-07-06T05:46:26Z
- Baseline status: delta mode active
- Candidate count after merge: 314
- Detailed repo count: 313
- Current limitations:
  - Trending HTML parsing may fail if GitHub changes page markup.
  - Search API rate limits are lower without `GITHUB_TOKEN`.
  - README summaries are heuristic and should be checked manually.
  - MVP report generation does not call an external Codex service.
- Latest Top 3:
  - langchain-ai/openwiki (https://github.com/langchain-ai/openwiki) score=79
  - asgeirtj/system_prompts_leaks (https://github.com/asgeirtj/system_prompts_leaks) score=79
  - xbtlin/ai-berkshire (https://github.com/xbtlin/ai-berkshire) score=69
- Warnings:
  - none
- Next run notes:
  - Keep `data/latest_snapshot.json` if you want the next run to compute 3-day deltas.
  - Review `reports/latest.md` through the human gate before sharing.

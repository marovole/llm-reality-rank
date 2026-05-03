# Coding reviewed alpha table / AI 编程 Alpha 表

Snapshot: `2026-05-alpha`

> Alpha / 不完整覆盖：本表只使用 reviewed snapshot `2026-05-alpha` 中已复核的数据。它不是正式综合排名，不代表全面、最终或官方结论。

Description: Rows with reviewed Coding dimension data from the snapshot.

Generated from: `snapshots/llm-reality-rank/2026-05-alpha/scores.json` and `manifest.json`

| Rank | Model | Provider | Coding (编程能力) | Confidence | Eligibility | Coverage | Missing dimensions | Sources |
|---:|---|---|---:|---|---|---|---|---|
| 1 | `Gemini 2.5 Pro` | Google | 83.10 | Medium (45.70) | provisional | 2 sources / 2 scenarios | General, Reasoning_Math, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [aider_leaderboards](https://aider.chat/docs/leaderboards/), [artificial_analysis_llm](https://artificialanalysis.ai/models/gemini-2-5-pro) |
| 2 | `o3` | OpenAI | 69.96 | Medium (52.55) | provisional | 3 sources / 2 scenarios | General, Reasoning_Math, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [aider_leaderboards](https://aider.chat/docs/leaderboards/), [swe_bench_verified](https://www.swebench.com/index.html), [artificial_analysis_llm](https://artificialanalysis.ai/models/o3) |
| 3 | `Claude 3.5 Sonnet (2024-10-22)` | Anthropic | 49.00 | Medium (45.48) | provisional | 2 sources / 2 scenarios | General, Reasoning_Math, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [swe_bench_verified](https://www.swebench.com/index.html), [artificial_analysis_llm](https://artificialanalysis.ai/models/claude-35-sonnet) |

Caveat: rows with Low confidence, ineligible status, or many missing dimensions should be treated as evidence excerpts, not settled recommendations.

Included snapshot limitations:
- Alpha snapshot: intentionally small reviewed seed dataset for downstream content and site integration; it is not comprehensive or final.
- Reviewed snapshot data is traceable but remains benchmark-dependent and should not be treated as absolute truth.
- Sparse or missing dimensions are exposed explicitly rather than imputed.

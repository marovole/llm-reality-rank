# Value/API reviewed alpha table / 性价比与 API Alpha 表

Snapshot: `2026-05-beta`

> Alpha / 不完整覆盖：本表只使用 reviewed snapshot `2026-05-beta` 中已复核的数据。它不是正式综合排名，不代表全面、最终或官方结论。

Description: Rows with reviewed Practicality data, currently centered on API/intelligence-index evidence when available.

Generated from: `snapshots/llm-reality-rank/2026-05-beta/scores.json` and `manifest.json`

| Rank | Model | Provider | Practicality (成本/速度/上下文) | Confidence | Eligibility | Coverage | Missing dimensions | Sources |
|---:|---|---|---:|---|---|---|---|---|
| 1 | `o3` | OpenAI | 38.00 | Medium (52.55) | provisional | 3 sources / 2 scenarios | General, Reasoning_Math, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [aider_leaderboards](https://aider.chat/docs/leaderboards/), [swe_bench_verified](https://www.swebench.com/index.html), [artificial_analysis_llm](https://artificialanalysis.ai/models/o3) |
| 2 | `Gemini 2.5 Pro` | Google | 35.00 | Medium (45.70) | provisional | 2 sources / 2 scenarios | General, Reasoning_Math, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [aider_leaderboards](https://aider.chat/docs/leaderboards/), [artificial_analysis_llm](https://artificialanalysis.ai/models/gemini-2-5-pro) |
| 3 | `GPT-4o (2024-08-06)` | OpenAI | 17.00 | Low (34.33) | ineligible | 1 sources / 1 scenarios | General, Reasoning_Math, Coding, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [artificial_analysis_llm](https://artificialanalysis.ai/models/gpt-4o) |
| 4 | `Claude 3.5 Sonnet (2024-10-22)` | Anthropic | 16.00 | Medium (45.48) | provisional | 2 sources / 2 scenarios | General, Reasoning_Math, Chinese, Multimodal_Doc, Agent_ToolUse, Ecosystem | [swe_bench_verified](https://www.swebench.com/index.html), [artificial_analysis_llm](https://artificialanalysis.ai/models/claude-35-sonnet) |

Caveat: rows with Low confidence, ineligible status, or many missing dimensions should be treated as evidence excerpts, not settled recommendations.

Included snapshot limitations:
- Alpha snapshot: intentionally small reviewed seed dataset for downstream content and site integration; it is not comprehensive or final.
- Reviewed snapshot data is traceable but remains benchmark-dependent and should not be treated as absolute truth.
- Sparse or missing dimensions are exposed explicitly rather than imputed.

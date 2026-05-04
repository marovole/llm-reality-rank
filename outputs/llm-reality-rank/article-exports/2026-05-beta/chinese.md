# Chinese reviewed alpha table / 中文能力 Alpha 表

Snapshot: `2026-05-beta`

> Alpha / 不完整覆盖：本表只使用 reviewed snapshot `2026-05-beta` 中已复核的数据。它不是正式综合排名，不代表全面、最终或官方结论。

Description: Rows with reviewed Chinese dimension data from the snapshot.

Generated from: `snapshots/llm-reality-rank/2026-05-beta/scores.json` and `manifest.json`

| Rank | Model | Provider | Chinese (中文能力) | Confidence | Eligibility | Coverage | Missing dimensions | Sources |
|---:|---|---|---:|---|---|---|---|---|
| 1 | `GPT-5.5 (high)` | OpenAI | 81.73 | Medium (57.83) | provisional | 4 sources / 2 scenarios | Reasoning_Math, Coding, Multimodal_Doc, Agent_ToolUse, Practicality, Ecosystem | [livebench](https://raw.githubusercontent.com/LiveBench/LiveBench.github.io/main/public/table_2026_01_08.csv), [superclue](https://superclueai.com/), [ceval](https://cevalbenchmark.com/static/leaderboard.html), [opencompass_llm](https://rank.opencompass.org.cn/leaderboard-llm-v2) |
| 2 | `DeepSeek V3 (2025-03-24)` | DeepSeek | 79.69 | Low (43.49) | ineligible | 3 sources / 1 scenarios | General, Reasoning_Math, Coding, Multimodal_Doc, Agent_ToolUse, Practicality, Ecosystem | [superclue](https://superclueai.com/), [ceval](https://cevalbenchmark.com/static/leaderboard.html), [opencompass_llm](https://rank.opencompass.org.cn/leaderboard-llm-v2) |
| 3 | `Qwen3-Max` | Alibaba Qwen | 79.55 | Low (43.49) | ineligible | 3 sources / 1 scenarios | General, Reasoning_Math, Coding, Multimodal_Doc, Agent_ToolUse, Practicality, Ecosystem | [superclue](https://superclueai.com/), [ceval](https://cevalbenchmark.com/static/leaderboard.html), [opencompass_llm](https://rank.opencompass.org.cn/leaderboard-llm-v2) |
| 4 | `Claude Opus 4.7` | Anthropic | 79.39 | Medium (57.83) | provisional | 4 sources / 2 scenarios | Reasoning_Math, Coding, Multimodal_Doc, Agent_ToolUse, Practicality, Ecosystem | [livebench](https://raw.githubusercontent.com/LiveBench/LiveBench.github.io/main/public/table_2026_01_08.csv), [superclue](https://superclueai.com/), [ceval](https://cevalbenchmark.com/static/leaderboard.html), [opencompass_llm](https://rank.opencompass.org.cn/leaderboard-llm-v2) |
| 5 | `Gemini 3.1 Pro Preview` | Google | 78.90 | Medium (47.31) | provisional | 2 sources / 2 scenarios | Reasoning_Math, Coding, Multimodal_Doc, Agent_ToolUse, Practicality, Ecosystem | [livebench](https://raw.githubusercontent.com/LiveBench/LiveBench.github.io/main/public/table_2026_01_08.csv), [superclue](https://superclueai.com/) |

Caveat: rows with Low confidence, ineligible status, or many missing dimensions should be treated as evidence excerpts, not settled recommendations.

Included snapshot limitations:
- Alpha snapshot: intentionally small reviewed seed dataset for downstream content and site integration; it is not comprehensive or final.
- Reviewed snapshot data is traceable but remains benchmark-dependent and should not be treated as absolute truth.
- Sparse or missing dimensions are exposed explicitly rather than imputed.

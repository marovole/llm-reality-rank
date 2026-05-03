# LLM Reality Rank 方法论公开草稿：先看真实使用价值，而不是只看考试分

> Snapshot: `2026-05-alpha` · Release stage: Alpha / 不完整覆盖 · Generated: 2026-05-03

这是一篇面向中文高阶 AI 用户、开发者和创作者的公开方法论草稿。它使用的表格和结论只来自 reviewed snapshot `2026-05-alpha`；当前快照是一个小规模 Alpha 种子，不是正式综合排名，也不是对所有主流模型的全面最终结论。

## 这份榜单想解决什么问题

LLM Reality Rank 不是再做一个“谁智商最高”的单一 benchmark 榜。我们更关心一个现实问题：当你今天要写作、编程、处理中文内容、做 Agent 工作流、控制 API 成本或选择可长期使用的模型时，哪些模型有可解释、可追溯的使用价值证据？

因此，本项目把模型评价拆成能力、专项、实用、生态和置信度五个层次。考试分、偏好分、代码任务、中文任务、价格速度、上下文、工具调用和可用性都只是证据的一部分，不能单独被当成最终答案。

## 当前 reviewed snapshot

- Snapshot manifest: [`snapshots/llm-reality-rank/2026-05-alpha/manifest.json`](../snapshots/llm-reality-rank/2026-05-alpha/manifest.json)
- Score records: [`snapshots/llm-reality-rank/2026-05-alpha/scores.json`](../snapshots/llm-reality-rank/2026-05-alpha/scores.json)
- Source evidence: [`snapshots/llm-reality-rank/2026-05-alpha/source-evidence.json`](../snapshots/llm-reality-rank/2026-05-alpha/source-evidence.json)
- Source registry: [`docs/llm-reality-rank-source-registry.md`](llm-reality-rank-source-registry.md)
- Scoring methodology: [`docs/llm-reality-rank-scoring-methodology.md`](llm-reality-rank-scoring-methodology.md)

当前 Alpha 快照包含的已复核来源：

- `aider_leaderboards` — [Aider LLM Leaderboards](https://aider.chat/docs/leaderboards/)
- `artificial_analysis_llm` — [Artificial Analysis LLM Leaderboard / Intelligence Index](https://artificialanalysis.ai/leaderboards/models)
- `livebench` — [LiveBench](https://livebench.ai/)
- `swe_bench_verified` — [SWE-bench Verified](https://www.swebench.com/)

数据观察日期范围：`2026-05-03` 到 `2026-05-03`。行数：raw `11`，model scores `7`。

## Article-ready exports

下列表格由脚本可复现生成，来源均为同一个 reviewed snapshot：

- [Overall reviewed alpha table / 综合 Alpha 表](../outputs/llm-reality-rank/article-exports/2026-05-alpha/overall.md)
- [Coding reviewed alpha table / AI 编程 Alpha 表](../outputs/llm-reality-rank/article-exports/2026-05-alpha/coding.md)
- [Chinese reviewed alpha table / 中文能力 Alpha 表](../outputs/llm-reality-rank/article-exports/2026-05-alpha/chinese.md)
- [Value/API reviewed alpha table / 性价比与 API Alpha 表](../outputs/llm-reality-rank/article-exports/2026-05-alpha/value-api.md)
- [Multimodal reviewed alpha table / 多模态 Alpha 表](../outputs/llm-reality-rank/article-exports/2026-05-alpha/multimodal.md)
- [Agent reviewed alpha table / Agent Alpha 表](../outputs/llm-reality-rank/article-exports/2026-05-alpha/agent.md)

这些表格会保留模型名、分数、置信度、资格状态、覆盖来源数、缺失维度和来源链接。若某个子榜当前没有 reviewed 数据，表格会显式显示缺失状态，而不是用未复核数据补齐。

## 分数如何理解

综合分使用项目方法论中的场景维度：General、Reasoning/Math、Coding、Chinese、Multimodal/Doc、Agent/ToolUse、Practicality、Ecosystem。不同来源先被标准化到 0-100，再按来源可信度、污染风险、独立性和新鲜度加权。当前 Alpha 快照覆盖很稀疏，所以更适合展示管线和证据格式，而不适合被解读成完整主榜。

## 置信度如何理解

置信度不是模型能力分，而是“这条分数有多可信”的提示。它主要受来源数量、维度覆盖、来源质量、数据新鲜度和模型版本清晰度影响。当前 `2026-05-alpha` 中大量记录仍然是 Low 或 Medium confidence，并伴随 `insufficient_sources`、`insufficient_scenarios`、`missing_dimensions` 等标记；这些标记必须和任何排名表一起展示。

## 为什么不声称这是正式排名

当前快照是 Alpha / 不完整覆盖。它只包含少量已经人工复核、可追溯的种子数据，且缺少中文、多模态、Agent、生态等关键来源的完整覆盖。模型版本也可能存在 `unknown` 标签，需要在后续快照中继续复核。因此本文只能说“在当前 reviewed alpha evidence 中呈现的相对位置”，不能说“最终谁最强”。

## 局限

- Alpha snapshot: intentionally small reviewed seed dataset for downstream content and site integration; it is not comprehensive or final.
- Reviewed snapshot data is traceable but remains benchmark-dependent and should not be treated as absolute truth.
- Sparse or missing dimensions are exposed explicitly rather than imputed.
- Benchmark 可能被训练污染；偏好榜也会受回答风格影响。
- 价格、速度、上下文和 API 可用性会频繁变化。
- Agent 能力高度依赖 scaffold，不完全等同于 base model 能力。
- 中文、多模态和开放权重模型覆盖在当前 Alpha 快照中仍明显不足。

## 推荐引用方式

推荐表述：`基于 LLM Reality Rank reviewed alpha snapshot 2026-05-alpha 的有限证据，某模型在已覆盖维度上显示出相对优势，但该快照不是完整或最终排名。`

不推荐表述：把 Alpha 快照写成定稿名次、全网最强模型榜，或宣称低置信度模型已经被证明更强。

# LLM Reality Rank

LLM Reality Rank（大模型真实使用价值榜）是一个面向中文高阶 AI 用户、开发者和创作者的 LLM 综合评价项目。

核心口号：不是只看考试分，而是看真实使用价值。

这个项目的目标不是再做一个单一 benchmark 排名，而是聚合主流 LLM 排行榜、专项 benchmark、价格速度数据和真实使用信号，形成一个可解释、可追溯、可持续更新的综合评价体系。

## 定位

LLM Reality Rank 优先回答这些问题：

- 今天最值得普通用户使用的模型是谁？
- AI Coding 场景应该选 GPT、Claude、Gemini、DeepSeek、Qwen 还是其他模型？
- 中文写作、中文知识和中国语境下哪个模型更稳？
- 哪些模型不是绝对最强，但性价比极高？
- 哪些模型适合 Agent、工具调用、长任务和真实工作流？
- 开源/开放权重模型在实际使用中已经到什么位置？

## 核心方法

Reality Value Index 拆成五层：

1. Capability Score：能力分
2. Specialty Score：专项分
3. Practicality Score：实用分
4. Ecosystem Score：生态分
5. Confidence Score：置信分

综合使用价值榜不是简单平均所有 benchmark，而是按场景权重聚合：

- 通用能力
- 推理/数学
- 编程能力
- 中文能力
- 多模态/文档理解
- Agent/工具调用
- 成本/速度/上下文
- 生态/可用性

## 当前状态

当前是 early data foundation 阶段，已经包含：

- 主流榜单来源登记表
- 评分方法论
- 模型名称归一化规则
- 第一版 machine-readable sources.yaml
- 第一版 canonical models.yaml
- P0 来源 raw_rankings.csv 录入模板
- scoring pipeline 实施计划

还没有发布正式排名。当前数据中的 TODO 占位不应被当成结论引用。

## 项目结构

```text
docs/
  llm-reality-rank-source-registry.md
  llm-reality-rank-scoring-methodology.md
  llm-reality-rank-model-normalization.md
  llm-reality-rank-scoring-pipeline-plan.md

data/llm-reality-rank/
  sources.yaml
  models.yaml
  raw_rankings.csv

scripts/llm-reality-rank/
  validate_data.py

outputs/llm-reality-rank/
  .gitkeep

tests/llm-reality-rank/
  .gitkeep
```

## 快速验证

```bash
python3 scripts/llm-reality-rank/validate_data.py
```

预期输出：

```text
VALIDATION PASSED
```

## 第一版收录来源

P0 来源包括：

- LMArena / Chatbot Arena
- Artificial Analysis LLM Leaderboard
- LiveBench
- OpenCompass LLM Leaderboard
- Hugging Face Open LLM Leaderboard
- Stanford HELM / HELM Lite
- SWE-bench Verified
- Aider Leaderboards
- LiveCodeBench
- SuperCLUE
- C-Eval
- CMMLU
- MMMU
- MathVista
- GAIA
- Berkeley Function Calling / Gorilla
- OpenRouter Rankings

完整来源见：

```text
docs/llm-reality-rank-source-registry.md
data/llm-reality-rank/sources.yaml
```

## 下一步

1. 填入 P0 来源的真实分数。
2. 实现 normalize_scores.py。
3. 实现 aggregate_scores.py。
4. 生成第一版 model_scores.csv 和 model_scores.md。
5. 写第一篇方法论长文。
6. 开发静态网页榜单。

## License

MIT

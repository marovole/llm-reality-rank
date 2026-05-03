# LLM Reality Rank 项目交接文档 + 长期目标 PRD

更新时间：2026-05-03

仓库：Hermes-marovole/llm-reality-rank

GitHub： https://github.com/Hermes-marovole/llm-reality-rank

本地路径：/Users/marovole/Workspace/HermesWork/llm-reality-rank

目标读者：接手继续开发/研究/数据录入/产品化的同事或 Agent。本文假设读者没有参与过前面的讨论。

---

## 0. 一句话概览

LLM Reality Rank（大模型真实使用价值榜）是一个面向中文高阶 AI 用户、开发者和创作者的 LLM 综合评价项目。它不是单一 benchmark 排名，而是聚合 LMArena、Artificial Analysis、LiveBench、SWE-bench、Aider、SuperCLUE、OpenCompass、MMMU、GAIA 等主流来源，形成一个可解释、可追溯、可持续更新的综合评价体系。

核心口号：

不是只看考试分，而是看真实使用价值。

长期愿景：

成为中文圈最有解释力、最透明、最实用、可持续更新的 LLM 选型基础设施：既能支撑公开长文/个人品牌传播，也能支撑网页排行榜、月度报告、API、模型选型工具和 Agent 模型路由。

---

## 1. 背景与项目初衷

用户希望做一个全面的 LLM 排行榜，聚合主流排行榜信息，并做一个综合评价排行榜。经过 brainstorming 后，项目定位确定为：

D. 综合大众榜 + 垂直子榜

交付形态确定为：

D. 长文 + 静态网页

也就是说，本项目不是只做一个内部 CSV，也不是只写一篇文章，而是分阶段构建：

1. 数据方法论和来源体系
2. 可运行的数据管线
3. 第一篇高质量公开长文
4. 可持续更新的静态网页排行榜
5. 半自动/自动更新机制
6. 长期成为个人品牌和模型选型基础设施

---

## 2. 项目命名与定位

项目名：LLM Reality Rank

中文名：大模型真实使用价值榜

推荐公开表达：

- LLM Reality Rank：大模型真实使用价值榜
- 不是谁考试最高，而是谁最值得用
- 面向真实使用场景的 LLM 综合排行榜

不要把它称为“最强模型榜”。这个说法容易引战，也不符合方法论。推荐用：

- 综合使用价值榜
- AI Coding 榜
- 中文能力榜
- 性价比榜
- 多模态榜
- Agent 能力榜
- 开源/开放权重模型榜

---

## 3. 当前仓库状态

当前仓库已经创建并推送到 GitHub：

https://github.com/Hermes-marovole/llm-reality-rank

当前 main 分支最新提交：

- 290a23a feat: add scoring pipeline scripts
- c7c2346 Initial commit: add LLM Reality Rank foundation

当前已完成：

1. 项目仓库初始化
2. README / LICENSE / .gitignore
3. 来源登记表
4. 评分方法论
5. 模型名称归一化规则
6. scoring pipeline 实施计划
7. machine-readable sources.yaml
8. seed models.yaml
9. raw_rankings.csv 模板
10. validate_data.py
11. normalize_scores.py
12. aggregate_scores.py
13. 基础测试
14. 少量 seed numeric rows 用于跑通 pipeline
15. 输出 draft model_scores.csv / model_scores.md

当前还没有完成：

1. 正式数据采集
2. 完整 P0 来源录入
3. 正式综合榜计算
4. 数据可视化网页
5. 第一篇公开方法论长文
6. 自动化抓取/定时更新
7. CI/CD

重要提醒：

当前输出的 ranking 只是 smoke test，绝对不能当正式榜单发布。

---

## 4. 当前目录结构

```text
.
├── README.md
├── LICENSE
├── .gitignore
├── data/
│   └── llm-reality-rank/
│       ├── sources.yaml
│       ├── models.yaml
│       └── raw_rankings.csv
├── docs/
│   ├── llm-reality-rank-source-registry.md
│   ├── llm-reality-rank-scoring-methodology.md
│   ├── llm-reality-rank-model-normalization.md
│   ├── llm-reality-rank-scoring-pipeline-plan.md
│   └── HANDOFF.md
├── scripts/
│   └── llm-reality-rank/
│       ├── validate_data.py
│       ├── normalize_scores.py
│       └── aggregate_scores.py
├── outputs/
│   └── llm-reality-rank/
│       ├── normalized_scores.csv
│       ├── model_scores.csv
│       ├── model_scores.md
│       └── first-draft-leaderboard.md
└── tests/
    └── llm-reality-rank/
        ├── test_normalize_scores.py
        └── test_aggregate_scores.py
```

注意：`outputs/` 是 generated artifacts。当前 .gitignore 忽略生成的 CSV/MD，只保留 .gitkeep。不要把 smoke-test output 当成权威数据提交，除非后续明确决定发布某个 snapshot。

---

## 5. 快速启动

进入项目：

```bash
cd /Users/marovole/Workspace/HermesWork/llm-reality-rank
```

验证数据结构：

```bash
python3 scripts/llm-reality-rank/validate_data.py
```

预期：

```text
VALIDATION PASSED
```

运行测试：

```bash
pytest tests/llm-reality-rank -q
```

预期：

```text
6 passed
```

运行完整 pipeline：

```bash
python3 scripts/llm-reality-rank/validate_data.py
python3 scripts/llm-reality-rank/normalize_scores.py
python3 scripts/llm-reality-rank/aggregate_scores.py
```

当前 smoke-test 输出：

```text
outputs/llm-reality-rank/normalized_scores.csv
outputs/llm-reality-rank/model_scores.csv
outputs/llm-reality-rank/model_scores.md
outputs/llm-reality-rank/first-draft-leaderboard.md
```

---

## 6. 核心文档说明

### 6.1 来源登记表

路径：docs/llm-reality-rank-source-registry.md

作用：

记录 40 个主流 LLM 排行榜/Benchmark，按 P0/P1/P2 分级。

P0 第一版必须收录：

1. LMArena / Chatbot Arena
2. Artificial Analysis LLM Leaderboard
3. LiveBench
4. OpenCompass LLM Leaderboard
5. Hugging Face Open LLM Leaderboard
6. Stanford HELM / HELM Lite
7. SWE-bench Verified
8. Aider Leaderboards
9. LiveCodeBench
10. SuperCLUE
11. C-Eval
12. CMMLU
13. MMMU
14. MathVista
15. GAIA
16. Berkeley Function Calling / Gorilla
17. OpenRouter Rankings

P1/P2 见文档和 sources.yaml。

### 6.2 评分方法论

路径：docs/llm-reality-rank-scoring-methodology.md

核心思想：Reality Value Index 由五层组成：

1. Capability Score：能力分
2. Specialty Score：专项分
3. Practicality Score：实用分
4. Ecosystem Score：生态分
5. Confidence Score：置信分

综合使用价值榜第一版权重：

- 通用能力：20%
- 推理/数学：15%
- 编程能力：15%
- 中文能力：15%
- 多模态/文档理解：10%
- Agent/工具调用：10%
- 成本/速度/上下文：10%
- 生态/可用性：5%

### 6.3 模型名称归一化规则

路径：docs/llm-reality-rank-model-normalization.md

作用：解决不同榜单中模型名称不一致的问题。

canonical_id 格式：

```text
provider_slug/model_family/model_variant@version_or_date
```

例子：

```text
openai/gpt-4o@2024-08-06
anthropic/claude-3.5-sonnet@2024-10-22
google/gemini-2.5-pro@unknown
deepseek/deepseek-v3@2025-03-24
qwen/qwen3-max@unknown
```

关键原则：

- mini / full / pro / flash / lite 不同，必须拆分
- base / instruct / chat 不同，必须拆分
- preview / stable 不同，默认拆分或标注低置信
- 不同日期 API suffix，必须拆分
- thinking/reasoning 和 non-thinking，视榜单是否独立评估处理
- 模型版本 unknown 时降低 confidence

### 6.4 scoring pipeline plan

路径：docs/llm-reality-rank-scoring-pipeline-plan.md

作用：记录第一版 pipeline 的实施计划。部分内容已经完成，包括 validate/normalize/aggregate 脚本。

---

## 7. 数据文件说明

### 7.1 sources.yaml

路径：data/llm-reality-rank/sources.yaml

当前包含 40 个来源。

每个 source 包含：

- source_id
- priority
- name
- urls
- organization
- categories
- metric_types
- source_trust
- contamination_risk
- recommended_weight
- update_frequency
- use_in
- ingestion_method
- notes

后续工作：

- 为每个 P0 source 增加更明确的 ingestion strategy
- 标注是否可 scrape / browser-only / manual / API / HF Space
- 标注官方许可或使用限制

### 7.2 models.yaml

路径：data/llm-reality-rank/models.yaml

当前包含 26 个 seed models。包括 OpenAI、Anthropic、Google、xAI、DeepSeek、Qwen、Meta、Mistral、Moonshot、Zhipu、MiniMax 等。

重要提醒：

有些模型的 version 是 unknown，match_confidence 是 low，只是为了跑通 pipeline 和记录当前榜单可见名称。正式发布前必须核对。

### 7.3 raw_rankings.csv

路径：data/llm-reality-rank/raw_rankings.csv

这是最重要的待填数据表。

字段：

```csv
source_id,source_name,source_priority,category_primary,metric_name,metric_type,model_name_raw,canonical_id,provider,rank_raw,score_raw,score_unit,score_higher_is_better,date_published,date_observed,source_url,evaluation_independence,source_trust,contamination_risk,freshness_weight,notes
```

当前包含：

- 17 行 P0 来源 TODO 占位
- 少量 seed numeric rows，用于验证 pipeline

严禁把当前 seed rows 当正式数据发布。

---

## 8. 脚本说明

### 8.1 validate_data.py

路径：scripts/llm-reality-rank/validate_data.py

功能：

- 验证 sources.yaml 结构
- 验证 models.yaml 结构
- 验证 raw_rankings.csv header
- 验证 raw_rankings.csv 中 source_id 是否存在
- 验证 canonical_id 是否存在
- 验证 score_higher_is_better 是否为 true/false/empty

运行：

```bash
python3 scripts/llm-reality-rank/validate_data.py
```

### 8.2 normalize_scores.py

路径：scripts/llm-reality-rank/normalize_scores.py

功能：

- 读取 raw_rankings.csv
- 将 score_raw 转为 0-100
- 将 rank_raw 转为 0-100
- 计算 source_effective_weight
- 输出 normalized_scores.csv

当前标准化逻辑：

- score_raw 如果是 0-1，乘以 100
- score_raw 如果是 0-100，直接使用
- rank_raw 如果没有 score_raw，则按同 source_id + metric_name 分组转换
- 没有 numeric score/rank 的行跳过

当前 source_effective_weight：

```text
trust × contamination × independence × freshness
```

### 8.3 aggregate_scores.py

路径：scripts/llm-reality-rank/aggregate_scores.py

功能：

- 读取 normalized_scores.csv
- 将 category_primary 映射到 scenario
- 按模型和 scenario 加权平均
- 按 scenario 权重计算 overall_score
- 输出 CSV 和 Markdown

输出：

```text
outputs/llm-reality-rank/model_scores.csv
outputs/llm-reality-rank/model_scores.md
outputs/llm-reality-rank/first-draft-leaderboard.md
```

---

## 9. 当前 smoke-test 结果

最近一次运行结果：

```text
VALIDATION PASSED
6 passed
Wrote 8 normalized rows
Skipped 16 rows without numeric score/rank
Wrote 5 model scores
```

当前 draft 排名：

1. openai/gpt-5.5-high@unknown — 86.33
2. google/gemini-3.1-pro-preview@unknown — 85.67
3. anthropic/claude-opus-4.7@unknown — 85.67
4. google/gemini-2.5-pro@unknown — 83.10
5. openai/o3@unknown — 81.30

重要说明：

这是 pipeline smoke test，不是正式榜单。原因：

- 数据量极少
- 多个 canonical_id 版本 unknown
- 部分 seed rows 来自浏览器可见 snapshot
- 没有完成 P0 来源的系统录入
- 没有进行人工复核

---

## 10. 下一步工作清单：短期

### 10.1 清理工程基础

优先级：高

任务：

1. 更新 README 中项目结构，补上 normalize_scores.py / aggregate_scores.py / tests。
2. 确认 outputs 是否应完全 gitignore。建议继续 ignore generated outputs，正式 snapshot 另存到 `snapshots/`。
3. 添加 `requirements.txt` 或 `pyproject.toml`。
4. 添加 GitHub Actions：push/PR 时运行 validate + pytest。
5. 删除 `.pytest_cache` 本地文件，不要提交。

验收标准：

```bash
python3 scripts/llm-reality-rank/validate_data.py
pytest tests/llm-reality-rank -q
```

全部通过。

### 10.2 正式补齐 P0 数据

优先级：最高

第一批建议只做 5 个来源，不要一口气做 17 个：

1. LMArena / Chatbot Arena
2. Artificial Analysis
3. Aider Leaderboards
4. LiveBench
5. SWE-bench Verified

每个来源先录入 Top 10-20 模型。

要求：

- 每条数据必须有 source_url
- date_observed 必须填当天日期
- score_raw/rank_raw 至少一个必须填
- notes 写明“manual snapshot / scrape / API / HF Space”
- 不确定的 model_name 必须先写 raw_name，不要强行归一化
- canonical_id 不确定时，先补 models.yaml，并标 low confidence

验收标准：

- raw_rankings.csv 至少 50 条 numeric rows
- normalized_scores.csv 至少 50 条
- model_scores.csv 至少 15 个模型
- 每个模型 source_count 尽量 >= 2

### 10.3 模型归一化复核

优先级：最高

当前需要重点核对：

- GPT-5.5 / GPT-5 / o3 / o4-mini
- Claude Opus/Sonnet 4.x
- Gemini 3.x / Gemini 2.5
- DeepSeek V3/R1/V4
- Qwen3-Max / Qwen3-Coder
- Kimi K2/K2.6
- GLM 5.x/4.5
- Grok 4.x

要求：

- 不知道版本就保留 @unknown，不要假装知道
- unknown 模型进入榜单时 confidence 必须是 Low 或 Medium
- 对于只在 leaderboard visible snapshot 出现的未来/最新模型，notes 必须写清楚来源和不确定性

### 10.4 改进 normalization

优先级：中高

当前 normalization 对 Elo 直接 clamp 到 100，这不对。LMArena Elo 如 1488 会被 clamp 成 100，导致信息损失。

需要改：

- Elo 应在同一 source_id + metric_name 分组内做 min-max 或 percentile
- rank-only 来源按 rank 转 percentile
- accuracy/pass_rate 继续直接 0-100
- price/speed/latency 需要单独方向和公式

建议：

```text
metric_type = elo -> percentile/min-max within group
metric_type = usage_ranking -> inverse rank percentile
metric_type = accuracy/pass_rate -> raw percentage
metric_type = price -> inverse percentile or capability/price later
metric_type = speed -> percentile
metric_type = latency -> inverse percentile
```

验收：

- 添加测试覆盖 Elo normalization
- LMArena 多行输入时分数不再全部 100

### 10.5 改进 aggregation

优先级：中高

当前 aggregation 会对 available scenarios 重新归一化。这个适合 smoke test，但正式榜单会高估单项模型。

建议改为：

- 主榜入选：至少 3 个来源，至少 3 个核心维度
- 不满足条件则进入子榜，不进入主榜
- 缺失维度不记 0，但降低 confidence
- 输出 missing_dimensions
- 输出 eligibility: eligible / insufficient_data

---

## 11. 中期路线图

### Phase 1：Data Foundation（当前阶段）

目标：让数据可信、可复现。

交付物：

- sources.yaml 稳定
- models.yaml 稳定
- raw_rankings.csv 至少覆盖 P0 Top 20 模型
- normalize/aggregate 可复现
- CI 通过
- 生成第一版内部 draft leaderboard

成功标准：

- 至少 100 条 raw numeric rows
- 至少 25 个 canonical models
- 至少 5 个 P0 来源
- 每个 Top 10 模型至少 3 个来源支持
- 所有数据有 source_url/date_observed

### Phase 2：First Public Article

目标：发布第一篇方法论长文。

标题建议：

《我做了一个“大模型真实使用价值榜”：不是谁考试最高，而是谁最值得用》

或：

《2026 大模型综合排行榜：GPT、Claude、Gemini、DeepSeek、Qwen 到底该选谁？》

文章结构：

1. 为什么现有 LLM 榜单都不够用
2. 什么叫“真实使用价值”
3. 数据来源和权重方法
4. 综合使用价值榜
5. AI Coding 榜
6. 中文能力榜
7. 性价比榜
8. 多模态/Agent 榜
9. 反直觉发现
10. 如何根据场景选模型
11. 后续会做成持续更新网页

成功标准：

- 所有排名可追溯到 source_url
- 方法论公开透明
- 明确标注限制和置信度
- 输出适合公众号/X/即刻传播的图表

### Phase 3：Static Website MVP

目标：做一个可访问、可筛选、可分享的网页排行榜。

建议技术：

- Astro / Next.js / Vite static site 三选一
- 数据仍从 YAML/CSV 生成 JSON
- 静态部署到 GitHub Pages / Cloudflare Pages

页面：

1. 首页：综合使用价值榜
2. 子榜页：Coding / 中文 / 性价比 / 多模态 / Agent / 开源
3. 模型详情页
4. 方法论页
5. 数据来源页
6. 更新日志页

成功标准：

- 可按 provider/type/场景筛选
- 每个分数可点击查看来源
- 每个模型有 model card
- 移动端可读
- SEO/GEO 友好

### Phase 4：Semi-Automated Updates

目标：每周/月半自动更新。

能力：

- 每个 source 有 ingestion script 或 manual checklist
- 运行脚本生成 diff
- 人工 review 后合并
- 自动生成月度变化报告

成功标准：

- 每月稳定发布一次 LLM Rank Update
- 新模型可在 24-72 小时内录入
- 历史趋势可追踪

### Phase 5：Model Selection Tool / API

目标：从排行榜变成模型选型工具。

能力：

- 用户选择场景：写作/编程/中文/Agent/低成本/多模态
- 用户设置权重
- 系统推荐模型组合
- 输出推荐理由
- 提供 JSON API

成功标准：

- 可以作为 Hermes Agent 模型路由依据
- 可以支持文章、网页、API 三端复用

---

## 12. 长期目标 PRD

### 12.1 产品名称

LLM Reality Rank

中文：大模型真实使用价值榜

### 12.2 产品愿景

成为中文 AI 高阶用户、开发者和创作者在选择 LLM 时最信任的独立参考系统。

它不只是告诉用户“谁排名第一”，而是回答：

- 为什么它适合你？
- 它在哪些场景强？
- 它在哪些场景不值得用？
- 它贵在哪里，便宜在哪里？
- 它的能力分来自哪些来源？
- 这个排名有多可信？
- 如果你要写代码/写中文/做 Agent/控制成本，应该怎么选？

### 12.3 目标用户

#### 核心用户 1：AI Coding 开发者

画像：

- 使用 Cursor / Claude Code / Codex / OpenCode / Hermes Agent
- 关心模型的真实工程能力
- 不满足于 HumanEval 这类旧 benchmark
- 关心 SWE-bench、Aider、工具调用、长上下文、成本

核心问题：

- 哪个模型最会修 bug？
- 哪个模型最适合 agentic coding？
- 哪个模型贵但值？哪个便宜但够用？
- Claude / GPT / Gemini / DeepSeek / Qwen 在 coding 上怎么选？

#### 核心用户 2：中文 AI 高阶用户/创作者

画像：

- 关注中文写作、总结、翻译、知识问答
- 需要公众号、X、小红书、研究笔记等内容生产
- 不想只看英文 benchmark

核心问题：

- 哪个模型中文表达最好？
- 哪个模型最懂中文语境？
- 哪个模型适合长文写作？
- 哪个模型适合把英文资料转成中文内容？

#### 核心用户 3：AI 产品/技术负责人

画像：

- 需要为产品/API/团队选择模型
- 关心成本、稳定性、速度、上下文、工具调用
- 需要向团队解释选型依据

核心问题：

- 现在 API 该接哪几个模型？
- 哪些模型适合 fallback？
- 哪些模型适合批处理？
- 哪些模型适合中国用户？

#### 扩展用户：研究爱好者/投资者/媒体

关注模型格局、开源 vs 闭源、中国 vs 海外、能力趋势和反直觉结论。

### 12.4 核心价值主张

1. 综合但不糊涂

不是简单平均，而是按场景分榜。

2. 透明可追溯

每个分数都能追溯到来源。

3. 面向真实使用

价格、速度、上下文、API、工具调用、中文能力同样重要。

4. 中文友好

引入 SuperCLUE、C-Eval、CMMLU、OpenCompass 等中文来源，不只看英文榜。

5. 开发者友好

重视 SWE-bench、Aider、LiveCodeBench、GAIA、Function Calling。

6. 可持续更新

目标是长期维护，不是一篇一次性文章。

### 12.5 产品形态

#### MVP 形态

- Markdown 数据文档
- CSV/YAML 数据源
- Python scoring pipeline
- 第一版长文

#### V1 形态

- 静态网页排行榜
- 总榜 + 子榜
- 模型详情页
- 方法论页
- 数据来源页

#### V2 形态

- 定期自动更新
- 历史趋势图
- 模型对比工具
- 权重自定义
- Newsletter/月报

#### V3 形态

- API
- 可嵌入 widget
- Hermes Agent 模型路由数据源
- 企业/团队选型报告生成器

### 12.6 核心功能需求

#### F1：来源管理

系统必须支持：

- source registry
- source trust
- contamination risk
- update frequency
- ingestion method
- source_url
- source license/terms note

验收：

- 每个 source 都有唯一 source_id
- raw data 不能引用不存在的 source_id
- 每个 source 都能解释它测什么、不测什么

#### F2：模型归一化

系统必须支持：

- canonical_id
- aliases
- api_model_ids
- provider_slug
- model_family
- model_variant
- version
- release_date
- match_confidence

验收：

- GPT-4o 和 GPT-4o mini 不会合并
- Claude Sonnet 和 Opus 不会合并
- Gemini Pro 和 Flash 不会合并
- DeepSeek V 和 R 系列不会合并
- unknown version 会降低 confidence

#### F3：原始数据录入

系统必须支持：

- source_id
- metric_name
- metric_type
- model_name_raw
- canonical_id
- rank_raw
- score_raw
- score_unit
- date_observed
- source_url
- notes

验收：

- 每条 raw row 可追溯
- 每条 raw row 可验证来源
- 缺少 score/rank 的行不会进入计算

#### F4：标准化评分

系统必须支持：

- accuracy/pass_rate 直接归一化
- Elo 分组标准化
- rank 分组标准化
- price inverse scoring
- speed percentile
- latency inverse percentile
- context log scale

验收：

- 所有 normalized scores 在 0-100
- 不同 metric_type 有明确转换方法
- 每个转换方法有测试

#### F5：场景聚合

系统必须支持：

- Overall
- Coding
- Chinese
- Value for Money
- Multimodal
- Agent
- Open-weight
- Long Context

验收：

- 每个子榜有独立权重
- 主榜和子榜不会混用不相关指标
- 缺失维度降低 confidence，而不是强行补 0

#### F6：置信度

系统必须支持：

- source_count
- scenario_count
- source_quality
- freshness
- match_confidence
- missing_dimensions
- vendor_report_penalty

验收：

- High / Medium / Low confidence 明确输出
- Low confidence 模型可以显示但必须标注
- 正式主榜应默认过滤 insufficient_data

#### F7：输出层

系统必须输出：

- normalized_scores.csv
- model_scores.csv
- model_scores.md
- first-draft-leaderboard.md
- site-ready JSON
- model detail JSON

验收：

- Markdown 可直接用于文章草稿
- JSON 可直接用于静态网页
- CSV 可人工审阅

#### F8：网页排行榜

系统必须支持：

- 总榜
- 子榜 tabs
- provider filter
- model type filter
- confidence filter
- cost/speed/context columns
- source evidence drilldown
- model detail page

验收：

- 用户能在 10 秒内找到“我该用哪个模型”
- 每个分数能看到来源
- 移动端可读

### 12.7 非功能需求

#### 透明性

- 所有权重公开
- 所有来源公开
- 所有不确定性公开

#### 可复现性

- 本地运行脚本可生成同样输出
- 数据版本可通过 git 追踪

#### 可维护性

- 新增 source 不应改核心逻辑
- 新增 model 只需更新 models.yaml
- 新增 metric_type 需要测试

#### 可信度

- 严禁未经标注的厂商自报混入第三方分数
- 严禁版本不明模型进入正式主榜高置信区
- 严禁把 smoke test output 当正式榜单

#### SEO/GEO

- 页面标题和结构要适合搜索引擎和生成式搜索引用
- 方法论页面要清晰解释排名逻辑
- 每个模型页要有结构化信息

### 12.8 里程碑

#### M0：Foundation Done（当前接近完成）

状态：基本完成。

完成标准：

- repo 创建
- docs 完成
- sources/models/raw_rankings 建立
- validate/normalize/aggregate 初版可运行
- 测试通过

#### M1：Internal Alpha Leaderboard

目标时间：下一阶段

完成标准：

- 录入至少 5 个 P0 source
- 录入至少 100 条 numeric rows
- 覆盖至少 25 个模型
- 生成第一版内部榜单
- 明确所有 Low confidence 项

#### M2：Public Methodology Article

完成标准：

- 写出第一篇方法论长文
- 输出总榜 + 3-5 个子榜
- 所有排名可追溯
- 明确说明局限

#### M3：Website MVP

完成标准：

- 静态网页上线
- 支持总榜和子榜
- 支持基础筛选
- 支持模型详情页
- 数据由 repo 生成

#### M4：Monthly Update System

完成标准：

- 每月更新流程固定
- 自动生成变化报告
- 历史快照可查
- 支持新增模型和新增 source

#### M5：Model Selection Platform

完成标准：

- 用户自定义权重
- 输出推荐模型组合
- 提供 API/JSON
- 可反哺 Hermes Agent 模型路由

---

## 13. 数据采集操作规范

### 13.1 采集前

1. 先确认 source 是否在 sources.yaml。
2. 如果不在，先添加 source。
3. 确认 metric_type 是否已有处理逻辑。
4. 确认 model 是否在 models.yaml。
5. 不确定模型版本时，不要猜，使用 @unknown 并写 notes。

### 13.2 采集时

每条 raw row 必须填：

- source_id
- source_name
- source_priority
- category_primary
- metric_name
- metric_type
- model_name_raw
- canonical_id
- provider
- rank_raw 或 score_raw
- score_unit
- score_higher_is_better
- date_observed
- source_url
- evaluation_independence
- source_trust
- contamination_risk
- freshness_weight
- notes

### 13.3 采集后

运行：

```bash
python3 scripts/llm-reality-rank/validate_data.py
python3 scripts/llm-reality-rank/normalize_scores.py
python3 scripts/llm-reality-rank/aggregate_scores.py
pytest tests/llm-reality-rank -q
```

检查：

- normalized rows 数量是否符合预期
- skipped rows 是否只是 TODO 或无分数来源
- model_scores 是否有异常高分
- Low confidence 是否合理

---

## 14. 质量红线

以下事项不要做：

1. 不要把当前 smoke-test 排名当正式结果。
2. 不要把厂商自报当第三方分数。
3. 不要把 GPT-4o 和 GPT-4o mini 合并。
4. 不要把 Claude Sonnet 和 Opus 合并。
5. 不要把 Gemini Pro 和 Flash 合并。
6. 不要把 DeepSeek V 系列和 R 系列合并。
7. 不要在模型版本不明时强行写 release_date。
8. 不要让只有一个来源的模型进入正式主榜高置信区。
9. 不要用简单平均替代场景权重。
10. 不要忽略中文榜和 AI Coding 榜；这是项目差异化关键。
11. 不要改动用户 credential 或 live config。
12. 不要在没有验证的情况下 push。

---

## 15. 推荐接手顺序

如果你只有一天时间，按这个顺序做：

1. 更新 README 与当前脚本状态同步。
2. 加 GitHub Actions CI。
3. 修正 Elo normalization，不要 clamp 到 100。
4. 正式录入 LMArena Top 20。
5. 正式录入 Artificial Analysis Top 20。
6. 跑 pipeline，检查输出。
7. 提交 PR 或直接 push main（按维护者要求）。

如果你有三天时间，继续：

8. 录入 Aider Top 20。
9. 录入 LiveBench Top 20。
10. 录入 SWE-bench Verified Top 20。
11. 复核模型 canonical_id。
12. 输出 internal alpha leaderboard。

如果你有一周时间，继续：

13. 加 source evidence 输出。
14. 加 confidence/missing dimensions。
15. 写第一篇方法论长文草稿。
16. 设计网站 MVP 信息架构。

---

## 16. 当前已知技术债

1. README 项目结构没有同步最新脚本。
2. normalize_scores.py 对 Elo 的处理过于粗糙。
3. aggregate_scores.py 对缺失维度的处理还只是 alpha 逻辑。
4. confidence_proxy 只是简化版。
5. raw_rankings.csv 还没有正式数据，只是 TODO + seed rows。
6. models.yaml 中多个模型 version unknown。
7. outputs 生成文件未纳入 snapshot/versioning 策略。
8. 没有 CI。
9. 没有 requirements.txt/pyproject.toml。
10. 没有 source-specific ingestion scripts。
11. 没有静态网页。
12. 没有正式文章。

---

## 17. Git 工作流

当前是直接 main 开发。建议后续改为 feature branch 或 PR：

```bash
git checkout -b feat/<short-name>
# work
python3 scripts/llm-reality-rank/validate_data.py
pytest tests/llm-reality-rank -q
git add .
git commit -m "feat: <description>"
git push -u origin feat/<short-name>
gh pr create
```

如果用户要求快速推进，也可以直接 main，但必须先跑验证。

---

## 18. 给接手同事/Agent 的最终提醒

这个项目的关键不是“把榜单爬下来”，而是建立可信方法论。

请始终记住：

- 数据可追溯比排名好看更重要。
- 版本清晰比覆盖面大更重要。
- 置信度标注比装作确定更重要。
- 中文能力和 AI Coding 是差异化重点。
- 不要只看考试分，要看真实使用价值。

当前最重要的下一步：

把 P0 来源中的 LMArena、Artificial Analysis、Aider、LiveBench、SWE-bench Verified 五个来源正式录入至少 Top 20，并修正 Elo/rank/price/speed 的 normalization 逻辑。

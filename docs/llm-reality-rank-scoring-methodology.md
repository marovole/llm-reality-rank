# LLM Reality Rank 评分方法论

更新时间：2026-05-03

项目名：LLM Reality Rank / 大模型真实使用价值榜

核心口号：不是只看考试分，而是看真实使用价值。

目标：聚合主流 LLM 排行榜、Benchmark、价格速度数据和真实使用信号，生成一个可解释、可追溯、可持续更新的综合评价体系。

---

## 1. 基本原则

### 1.1 不追求“绝对最强模型”

LLM 没有单一绝对排名。模型价值取决于场景：

- 普通用户看对话体验、中文能力、价格、可访问性。
- 开发者看代码能力、工具调用、上下文、速度、API 稳定性。
- 研究者看推理、数学、多模态、鲁棒性、抗污染评测。
- 企业看成本、稳定性、安全、合规、生态支持。

因此主榜名称建议使用：

综合使用价值榜

而不是：

最强模型榜

### 1.2 区分五类分数

Reality Value Index 不直接平均所有 Benchmark，而是分五类：

1. Capability Score：能力分
2. Specialty Score：专项分
3. Practicality Score：实用分
4. Ecosystem Score：生态分
5. Confidence Score：置信分

最终总分：

Reality Value Index = Scenario Score × Confidence Modifier

其中：

Scenario Score = 各维度按场景权重加权后的 0-100 分

Confidence Modifier = 0.85-1.05 之间的置信修正因子

### 1.3 所有分数必须可追溯

每个模型每个维度都要能追溯到：

- 来源榜单
- 原始指标
- 抓取/记录日期
- 模型原始名称
- 模型归一化名称
- 是否厂商自报
- 是否第三方复现
- 是否经过时间衰减

### 1.4 厂商自报数据降权

厂商官方 Benchmark 可以收录，但不能和第三方独立评测同权。

建议规则：

- 第三方独立评测：100% 权重
- 平台半独立评测：80-90% 权重
- 厂商官方自报：50-70% 权重
- 未注明来源的营销图表：不进入正式分数，只做备注

### 1.5 新鲜度必须进入评分

LLM 变化太快，180 天前的排名可能已经失效。

建议时间衰减：

- 0-30 天：1.00
- 31-90 天：0.90
- 91-180 天：0.75
- 181-365 天：0.50
- 365 天以上：默认不进入主榜，只保留历史档案

---

## 2. 分数总览

### 2.1 Capability Score：能力分

衡量模型的通用智能和基础能力。

来源示例：

- LMArena / Chatbot Arena
- LiveBench
- Stanford HELM
- OpenCompass
- Artificial Analysis Intelligence Index
- HLE
- ARC-AGI

子维度：

- General Knowledge：通用知识
- Conversation Quality：对话质量
- Reasoning：推理
- Math：数学
- Instruction Following：指令跟随
- Robustness：鲁棒性

### 2.2 Specialty Score：专项分

衡量模型在具体任务上的能力。

主要专项：

- Coding
- Chinese
- Multimodal
- Agent / Tool Use
- Long Context
- Document Understanding
- Open-weight / Local Deployment

来源示例：

- SWE-bench Verified
- Aider Leaderboards
- LiveCodeBench
- SuperCLUE
- C-Eval
- CMMLU
- MMMU
- MathVista
- GAIA
- Berkeley Function Calling
- WebArena
- OSWorld

### 2.3 Practicality Score：实用分

衡量模型在真实使用中的成本、速度、上下文、稳定性。

来源示例：

- Artificial Analysis
- OpenRouter pricing/rankings
- 官方 API pricing
- OpenRouter/API availability
- 实测 tokens/s

子维度：

- Price Efficiency：价格效率
- Output Speed：输出速度
- Latency：延迟
- Context Window：上下文长度
- Structured Output：JSON/schema 支持
- Function Calling：工具调用支持
- Vision/Audio Support：多模态 API 支持
- Reliability：稳定性/可用性

### 2.4 Ecosystem Score：生态分

衡量模型是否被真实生态采用。

来源示例：

- OpenRouter Rankings
- Cursor / Claude Code / Codex / OpenCode 支持情况
- 是否有主流 SDK
- 是否有 OpenAI-compatible API
- 是否支持本地部署工具链
- Hugging Face 下载/点赞/社区活跃度

子维度：

- API Availability：API 可用性
- Tooling Support：工具链支持
- Developer Adoption：开发者采用
- Community Activity：社区活跃
- Deployment Flexibility：部署灵活性

### 2.5 Confidence Score：置信分

衡量这个模型分数有多可信。

影响因素：

- 独立来源数量
- 来源可信度
- 数据新鲜度
- 是否多个来源结论一致
- 是否存在大量缺失维度
- 是否只有厂商自报
- 模型名称/版本是否明确

置信等级：

- High：多个独立来源，更新时间近，模型版本明确。
- Medium：来源数量中等，部分维度缺失或更新时间一般。
- Low：来源少、厂商自报多、模型版本不清、数据过旧。

---

## 3. 标准化方法

不同榜单指标不一样，不能直接平均。

### 3.1 原始指标类型

常见 metric_type：

- Elo
- win_rate
- accuracy
- pass_rate
- resolved_rate
- aggregate_score
- rank
- price_per_1m_tokens
- tokens_per_second
- latency
- context_length
- usage_rank

### 3.2 统一转为 0-100 分

#### Elo / Arena 分数

推荐：转为 percentile rank，而不是直接 min-max。

原因：Elo 差距不总是线性反映实用差距。

方法：

score_normalized = percentile_rank(model_elo among current models) × 100

#### Accuracy / Pass Rate

如果原始值就是百分比：

score_normalized = raw_percentage

如果不同 benchmark 难度差异大，先在该 benchmark 内做 percentile，再进入合成。

#### Rank

如果只有排名没有分数：

score_normalized = 100 × (N - rank) / (N - 1)

限制：

只有 rank 的来源不应高权重，因为丢失了差距信息。

#### Price

价格越低越好，但不能让极弱免费模型刷高性价比分。

建议先计算：

price_efficiency = capability_score / log10(cost_per_1m_output_tokens + 1)

再在候选模型内标准化到 0-100。

也可以拆成：

- input_price_score
- output_price_score
- cached_input_score
- batch_api_score

#### Speed

输出速度建议用 tokens/s。

score_normalized = percentile_rank(tokens_per_second) × 100

延迟 latency 越低越好：

latency_score = inverse_percentile_rank(latency) × 100

#### Context Window

上下文长度有边际递减，不能线性加分。

建议使用 log scale：

context_score = min(100, 100 × log2(context_tokens / 8k) / log2(1m / 8k))

解释：

- 8k 是基础线
- 1M 约视为满分
- 128k 到 1M 有加分，但边际递减

### 3.3 缺失值处理

如果某模型缺失某来源，不直接记 0。

规则：

- 维度缺失：该维度按已有来源平均，但降低 confidence。
- 关键维度缺失：该子榜不进入排名，或标注 Low Confidence。
- 数据过旧：时间衰减，而不是直接删除。
- 厂商自报：降权，而不是直接删除。

---

## 4. 来源权重

### 4.1 来源可信度系数

source_trust_weight：

- high: 1.00
- medium-high: 0.85
- medium: 0.70
- low-medium: 0.55
- low: 0.40

### 4.2 污染风险系数

contamination_risk_weight：

- low: 1.00
- low-medium: 0.90
- medium: 0.75
- medium-high: 0.60
- high: 0.40

### 4.3 数据来源类型系数

evaluation_independence_weight：

- independent_third_party: 1.00
- platform_or_community: 0.85
- benchmark_author_reported: 0.80
- vendor_reported: 0.60
- unknown: 0.50

### 4.4 最终来源权重

source_effective_weight = base_weight × source_trust_weight × contamination_risk_weight × evaluation_independence_weight × freshness_weight

---

## 5. 主榜权重：综合使用价值榜

建议第一版权重：

- 通用能力：20%
- 推理/数学：15%
- 编程能力：15%
- 中文能力：15%
- 多模态/文档理解：10%
- Agent/工具调用：10%
- 成本/速度/上下文：10%
- 生态/可用性：5%

解释：

这个权重偏向中文高阶用户/开发者/创作者，不是纯学术榜，也不是纯 API 价格榜。

### 5.1 主榜公式

Overall_RVI =
  0.20 × General
+ 0.15 × Reasoning_Math
+ 0.15 × Coding
+ 0.15 × Chinese
+ 0.10 × Multimodal_Doc
+ 0.10 × Agent_ToolUse
+ 0.10 × Practicality
+ 0.05 × Ecosystem

Final_Score = Overall_RVI × Confidence_Modifier

### 5.2 Confidence Modifier

- High: 1.00-1.05
- Medium: 0.95-1.00
- Low: 0.85-0.95

建议第一版保守处理：

- High: 1.00
- Medium: 0.95
- Low: 0.88

不建议让置信度大幅加分，主要用于惩罚不确定性。

---

## 6. 子榜权重

### 6.1 AI Coding 榜

- SWE-bench Verified：30%
- Aider Leaderboards：25%
- LiveCodeBench：20%
- BigCodeBench / EvalPlus：10%
- Agent 工具调用/终端任务：10%
- Coding 成本效率：5%

解释：

AI Coding 榜应更重视真实改代码和 issue 修复，而不是 HumanEval 这类旧题。

### 6.2 中文能力榜

- SuperCLUE：25%
- C-Eval：20%
- CMMLU：20%
- OpenCompass 中文相关维度：20%
- 中文人工/自建评测：10%
- 中国语境可用性：5%

解释：

中文榜不只看考试，还要覆盖中文表达、中文知识、中国语境和实际可用性。

### 6.3 性价比榜

- 综合能力分：35%
- 输出价格：20%
- 输入价格：10%
- 缓存/批处理价格：10%
- 输出速度：10%
- 上下文长度：5%
- API 可用性/稳定性：10%

限制：

低能力模型即使便宜，也不能进入高性价比榜前列。建议设置最低能力门槛：综合能力分 >= 60。

### 6.4 多模态榜

- MMMU / MMMU-Pro：30%
- MathVista：20%
- OpenCompass Open VLM：20%
- OCRBench / 文档理解：15%
- 视频理解：10%
- 多模态 API 可用性：5%

### 6.5 Agent 能力榜

- GAIA：25%
- Berkeley Function Calling：20%
- WebArena：15%
- OSWorld：15%
- Terminal-Bench / τ-bench：15%
- 长上下文/工具调用稳定性：10%

### 6.6 开源/开放权重模型榜

- Open LLM Leaderboard：20%
- OpenCompass：20%
- LiveBench：15%
- Coding：15%
- 中文能力：10%
- 部署成本/推理效率：10%
- 社区生态：10%

### 6.7 长上下文榜

- 实际长上下文召回/needle 类评测：30%
- LongBench / RULER / NoLiMa 等：30%
- 上下文窗口长度：15%
- 长上下文价格：10%
- 长文稳定性/幻觉控制：10%
- API 可用性：5%

注：长上下文榜需要后续补充专门来源，第一版可先列为扩展榜。

---

## 7. 模型资格规则

### 7.1 主榜入选条件

一个模型进入综合主榜，需要满足：

- 模型版本明确
- 至少有 3 个独立来源
- 至少覆盖 3 个核心维度
- 有公开可访问方式或 API
- 数据更新时间不超过 180 天，或有足够理由保留

### 7.2 子榜入选条件

子榜可以放宽，但必须标注置信度。

例如：

- 中文榜：至少 2 个中文来源
- Coding 榜：至少 2 个 coding 来源
- 多模态榜：必须明确是 VLM/多模态模型
- 开源榜：必须有可获取权重或明确开放许可

### 7.3 排除规则

以下模型不进入正式主榜：

- 名称不清、版本不明
- 只有厂商营销图，没有可验证来源
- 无法公开使用或获取
- 只在单一封闭 benchmark 出现
- 明显过时且无历史意义

---

## 8. 置信度算法

### 8.1 置信度输入

confidence_raw =
  source_count_score
+ source_quality_score
+ freshness_score
+ coverage_score
+ consistency_score
- ambiguity_penalty
- vendor_report_penalty

### 8.2 简化第一版规则

第一版可以先不用复杂公式，直接规则化：

High Confidence：

- >= 5 个来源
- 至少 3 个 high trust 来源
- 核心维度覆盖 >= 5 个
- 最近 90 天内有数据
- 模型版本明确

Medium Confidence：

- 3-4 个来源
- 至少 1 个 high trust 来源
- 核心维度覆盖 >= 3 个
- 最近 180 天内有数据
- 模型版本基本明确

Low Confidence：

- < 3 个来源
- 维度缺失严重
- 多数为厂商自报
- 模型版本模糊
- 数据超过 180 天

---

## 9. 时间衰减

freshness_weight：

- 0-30 天：1.00
- 31-90 天：0.90
- 91-180 天：0.75
- 181-365 天：0.50
- 365 天以上：0.25 或不进入主榜

如果某来源本身更新频率很低但仍有学术价值，例如 HELM，可在 notes 中标注并降低而非删除。

---

## 10. 输出格式

### 10.1 榜单表格字段

- Rank
- Model
- Provider
- Type: closed / open-weight / open-source / local
- Overall RVI
- Confidence
- General
- Reasoning
- Coding
- Chinese
- Multimodal
- Agent
- Practicality
- Ecosystem
- Price Tier
- Speed Tier
- Context Window
- Best For
- Watch Out
- Last Updated

### 10.2 模型卡片字段

- 模型名称
- 厂商
- 版本/发布日期
- 模型类型
- 推荐用途
- 不推荐用途
- 总分
- 子维度雷达
- 主要优势
- 主要短板
- 数据来源
- 价格
- 上下文
- API/产品入口
- 替代模型

### 10.3 来源卡片字段

- 来源名称
- URL
- 组织
- 测评类型
- 指标类型
- 更新频率
- 可信度
- 污染风险
- 进入哪些子榜
- 权重说明
- 已知局限

---

## 11. 第一版手工评分建议

第一版不用追求完全自动化。建议流程：

1. 从 P0 来源收集 Top 20-50 模型。
2. 建立模型名称归一化表。
3. 每个来源只录入主指标和排名。
4. 用 percentile rank 标准化。
5. 对每个子榜分别计算。
6. 手工检查异常值。
7. 输出总榜 + 子榜 + 置信度。
8. 在文章中公开方法论和局限性。

### 11.1 异常检查

需要人工复核的情况：

- 某模型总榜很高，但所有主流榜都很低。
- 某模型只因价格极低冲到性价比第一。
- 某模型版本明显混淆。
- 某模型在中文榜高，但没有中文来源支持。
- 某模型多模态分高，但实际 API 不支持 vision。
- 同一模型在不同来源名称不同，导致重复计入。

---

## 12. 已知局限

1. Benchmark 可能被训练污染。
2. 人类偏好榜受回答风格影响。
3. 价格和速度会频繁变化。
4. 不同平台同名模型可能版本不同。
5. 中国大陆可用性难以客观量化。
6. 私有模型缺乏完全透明评测。
7. Agent 能力高度依赖 scaffold，不完全是 base model 能力。
8. 多模态能力在不同输入类型之间差异很大。
9. 开源模型本地部署体验受硬件和量化影响。
10. 综合权重本身是价值判断，应公开说明。

---

## 13. 推荐文章表达

为了减少争议，文章里建议这样写：

“这个榜单不是判断谁拥有最高智商，而是回答一个更实际的问题：如果你今天要选择一个模型来写作、编程、研究、处理中文内容、做 Agent 或控制成本，哪个模型最值得用？”

“我们把模型评价拆成能力、专项、实用、生态和置信五个层次。考试分只是其中一部分，价格、速度、上下文、工具调用、中文能力和真实开发者采用同样重要。”

---

## 14. 下一步

1. 完成 model-normalization.md。
2. 建立 sources.yaml 或 sources.csv。
3. 建立 models.yaml。
4. 手工录入 P0 来源 Top 模型。
5. 计算第一版 RVI。
6. 写第一篇方法论长文。
7. 设计静态网页榜单。

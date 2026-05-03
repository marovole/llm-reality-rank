# LLM Reality Rank 模型名称归一化规则

更新时间：2026-05-03

目标：解决不同排行榜、API 平台、厂商文档中模型名称不一致的问题，确保 LLM Reality Rank 不会把同一个模型拆成多个模型，也不会把不同版本误合并。

---

## 1. 为什么需要模型归一化

LLM 榜单聚合最大的坑之一是模型命名混乱。

常见问题：

1. 同一模型在不同榜单名字不同。
   - Claude 3.5 Sonnet
   - claude-3-5-sonnet-20241022
   - Claude Sonnet 3.5 New

2. 同一品牌下不同版本被混在一起。
   - GPT-4o
   - GPT-4o mini
   - GPT-4.1
   - GPT-4.1 mini

3. 同名模型在不同平台可能不是同一版本。
   - DeepSeek Chat
   - DeepSeek V3
   - deepseek-chat
   - DeepSeek-V3-0324

4. 厂商产品名和 API model id 不一致。
   - Gemini Advanced
   - Gemini 2.5 Pro
   - gemini-2.5-pro-preview

5. 开源模型有 base/instruct/chat/quantized/merged 变体。
   - Qwen3-72B
   - Qwen3-72B-Instruct
   - Qwen3-72B-AWQ
   - Qwen3-72B-GGUF

6. 榜单只写系列名，没有明确版本。
   - Claude
   - GPT-4
   - Gemini Pro

如果不处理，会导致综合分严重失真。

---

## 2. 归一化目标

每个模型在系统中应有一个稳定的 canonical_id。

canonical_id 格式：

provider_slug/model_family/model_variant@version_or_date

示例：

- openai/gpt-4o@2024-08-06
- openai/gpt-4.1@2025-04-14
- anthropic/claude-3.5-sonnet@2024-10-22
- anthropic/claude-opus-4.5@2025-11-24
- google/gemini-2.5-pro@2025-06
- deepseek/deepseek-v3@2025-03-24
- qwen/qwen3-max@unknown
- meta/llama-3.1-405b-instruct@2024-07-23

如果版本不明：

- 使用 @unknown
- confidence 降级
- 不进入需要精确版本的主榜，除非来源足够多且上下文能确认

---

## 3. 标准字段

### 3.1 模型主表字段

每个模型记录建议包含：

- canonical_id
- display_name
- provider
- provider_slug
- model_family
- model_variant
- version
- release_date
- api_model_ids
- aliases
- model_type
- access_type
- license_type
- parameter_count
- context_window
- modality
- supports_tools
- supports_structured_output
- supports_vision
- supports_audio
- supports_video
- supports_image_generation
- default_platforms
- notes

### 3.2 字段说明

canonical_id:
唯一标识符。聚合、去重、计算都用它。

display_name:
面向用户展示的名称，例如 Claude 3.5 Sonnet (2024-10-22)。

provider:
厂商或组织，例如 OpenAI、Anthropic、Google、DeepSeek、Alibaba Qwen。

provider_slug:
小写短标识，例如 openai、anthropic、google、deepseek、qwen。

model_family:
模型系列，例如 gpt-4o、claude-3.5、gemini-2.5、qwen3、llama-3.1。

model_variant:
具体变体，例如 sonnet、opus、pro、flash、mini、instruct、base、reasoning。

version:
版本号、发布日期、API suffix 或厂商明确版本。

release_date:
发布日期。未知则 null。

api_model_ids:
不同平台 API id 列表。

aliases:
各排行榜中可能出现的名称。

model_type:
- closed
- open_weight
- open_source
- local_only
- hosted_open_weight

access_type:
- api
- web_app
- local
- api_and_local
- unavailable

license_type:
- proprietary
- open_weight_custom
- apache_2
- mit
- llama_license
- unknown

modality:
- text
- text_vision
- text_vision_audio
- text_vision_audio_video
- image_generation
- multimodal_generation

---

## 4. 名称解析流程

### 4.1 输入

来自来源榜单的原始模型名：

- model_name_raw
- source_id
- source_url
- date_observed
- metadata if available

### 4.2 解析步骤

1. 清洗字符串
   - trim 空格
   - 统一大小写用于匹配，但保留原始名
   - 去除无意义后缀，如 “API”, “Chatbot”, “Preview” 但不要丢失版本信息

2. 匹配精确 API model id
   - 如果 raw name 等于已知 api_model_id，直接映射 canonical_id

3. 匹配 alias
   - 查 models.yaml aliases

4. 提取 provider
   - OpenAI / Anthropic / Google / DeepSeek / Qwen / Meta / Mistral / xAI / Moonshot / MiniMax / Zhipu / Baidu / Tencent 等

5. 提取 family
   - GPT-4o, GPT-4.1, Claude 3.5, Gemini 2.5, DeepSeek V3, Qwen3, Llama 3.1 等

6. 提取 variant
   - mini, nano, pro, flash, sonnet, opus, haiku, instruct, reasoning, preview, turbo

7. 提取 version/date
   - 20241022
   - 2024-10-22
   - 0324
   - 2025-03-24
   - latest / preview / experimental

8. 判断是否需要人工确认
   - 只写 GPT-4：需要人工确认
   - 只写 Claude：需要人工确认
   - 只写 Gemini Pro：需要人工确认
   - 含 latest：需要记录 date_observed 并降低置信度

### 4.3 输出

- canonical_id
- match_type:
  - exact_api_id
  - exact_alias
  - fuzzy_alias
  - rule_based
  - manual
  - unresolved
- match_confidence:
  - high
  - medium
  - low
- normalization_notes

---

## 5. 合并与拆分规则

### 5.1 可以合并的情况

以下可以合并到同一个 canonical_id：

- 大小写不同
- 空格/连字符不同
- 同一 API id 的展示名不同
- 同一发布日期版本的别名不同
- 同一模型的网页产品名和 API 名能明确对应

示例：

- claude-3-5-sonnet-20241022
- Claude 3.5 Sonnet (New)
- Claude 3.5 Sonnet 2024-10-22

都可以映射到：

anthropic/claude-3.5-sonnet@2024-10-22

### 5.2 必须拆分的情况

以下不能合并：

- mini / full / pro / flash / lite 不同
- base / instruct / chat 不同
- preview / stable 不同，除非确认 identical
- 不同日期 API suffix
- thinking/reasoning 版本和 non-thinking 版本
- 量化版本和原始权重版本，如果榜单测的是本地推理性能
- 不同参数规模

示例：

- GPT-4o ≠ GPT-4o mini
- Claude 3.5 Sonnet 2024-06 ≠ Claude 3.5 Sonnet 2024-10
- Gemini 2.5 Pro ≠ Gemini 2.5 Flash
- Qwen3-72B-Base ≠ Qwen3-72B-Instruct
- DeepSeek V3 ≠ DeepSeek R1

### 5.3 暂时合并但标注的情况

有些榜单只写模糊名，但上下文能推断大概版本。

例如某榜单在 2025-04 记录 “Claude 3.7 Sonnet”，且当时只有一个公开版本。

处理：

- 可映射到 canonical_id
- match_confidence = medium
- normalization_notes 说明推断依据
- confidence 降低

---

## 6. Provider slug 规范

建议第一版 provider_slug：

- openai
- anthropic
- google
- xai
- deepseek
- qwen
- meta
- mistral
- moonshot
- minimax
- zhipu
- baidu
- tencent
- stepfun
- 01ai
- cohere
- ai21
- reka
- perplexity
- nvidia
- microsoft
- amazon
- alibaba
- unknown

注意：

Qwen 可用 qwen 作为模型品牌 slug，provider 可显示 Alibaba Qwen。

---

## 7. 常见模型系列规范

### 7.1 OpenAI

provider_slug: openai

常见 family/variant：

- gpt-4o
- gpt-4o-mini
- gpt-4.1
- gpt-4.1-mini
- gpt-4.1-nano
- gpt-5
- gpt-5-mini
- gpt-5-nano
- o1
- o1-mini
- o3
- o3-mini
- o4-mini

规则：

- GPT 系列和 o 系列不要混合。
- mini/nano 必须拆分。
- API 日期 suffix 优先作为 version。
- ChatGPT 产品名不能直接当模型名，除非来源明确底层模型。

### 7.2 Anthropic

provider_slug: anthropic

常见 family/variant：

- claude-3-opus
- claude-3-sonnet
- claude-3-haiku
- claude-3.5-sonnet
- claude-3.5-haiku
- claude-3.7-sonnet
- claude-opus-4
- claude-sonnet-4
- claude-opus-4.5
- claude-sonnet-4.5

规则：

- Opus / Sonnet / Haiku 必须拆分。
- 同名 Sonnet 不同日期必须拆分。
- Thinking 模式如果作为同一 API 参数，不单独建模型；如果榜单作为独立模型评估，可加 mode 字段。

### 7.3 Google Gemini

provider_slug: google

常见 family/variant：

- gemini-1.5-pro
- gemini-1.5-flash
- gemini-2.0-flash
- gemini-2.5-pro
- gemini-2.5-flash
- gemini-3-pro
- gemini-3-flash

规则：

- Pro / Flash / Flash-Lite 必须拆分。
- Preview / Experimental 版本要保留 version 或 notes。
- Gemini Advanced 是产品名，不是模型名。

### 7.4 DeepSeek

provider_slug: deepseek

常见 family/variant：

- deepseek-v3
- deepseek-v3.1
- deepseek-v4
- deepseek-r1
- deepseek-r1-distill
- deepseek-chat
- deepseek-reasoner

规则：

- V 系列 chat 模型和 R 系列 reasoning 模型必须拆分。
- deepseek-chat 需要根据日期映射到底层 V3/V4。
- deepseek-reasoner 需要根据日期映射到底层 R1/R 系列。
- Distill 模型必须注明基座和参数规模。

### 7.5 Qwen

provider_slug: qwen
provider display: Alibaba Qwen

常见 family/variant：

- qwen2.5
- qwen2.5-coder
- qwen2.5-vl
- qwen3
- qwen3-coder
- qwen3-max
- qwen3-omni

规则：

- Base / Instruct / Coder / VL / Omni 必须拆分。
- 参数规模必须进入 variant 或 metadata。
- API 商业模型和开源权重模型不要混合。

### 7.6 Meta Llama

provider_slug: meta

常见 family/variant：

- llama-3
- llama-3.1
- llama-3.2
- llama-3.3
- llama-4

规则：

- 参数规模必须明确：8B/70B/405B 等。
- Base / Instruct 必须拆分。
- Vision 版本必须拆分。
- Quantized GGUF/AWQ 版本只有在本地推理榜单中单独记录。

### 7.7 Mistral

provider_slug: mistral

常见 family/variant：

- mistral-large
- mistral-small
- mistral-medium
- mixtral
- codestral
- ministral

规则：

- Large/Small/Medium 必须拆分。
- Codestral 进入 coding 模型系列。
- Open-weight 与 hosted API 需要标注 access_type。

### 7.8 xAI

provider_slug: xai

常见 family/variant：

- grok-2
- grok-3
- grok-3-mini
- grok-4
- grok-code

规则：

- Grok 正式版、mini、code 版本拆分。
- X 产品体验和 API 模型需区分。

### 7.9 Moonshot / Kimi

provider_slug: moonshot

常见 family/variant：

- kimi-k1
- kimi-k2
- kimi-k2-thinking
- moonshot-v1

规则：

- Kimi 产品名与 Moonshot API id 需要映射。
- thinking 版本是否拆分取决于榜单是否独立评估。

### 7.10 MiniMax

provider_slug: minimax

常见 family/variant：

- minimax-m1
- abab
- minimax-text

规则：

- 海螺/产品名和 API 模型名分开。
- 多模态/语音/视频模型不与文本模型合并。

### 7.11 Zhipu / GLM

provider_slug: zhipu

常见 family/variant：

- glm-4
- glm-4-plus
- glm-4.5
- glm-z1
- cogvlm

规则：

- GLM 文本、推理、多模态模型拆分。
- 开源权重模型和 API 商业模型拆分。

---

## 8. 模型类型规则

### 8.1 model_type

closed:
闭源模型，只能通过 API 或产品使用。

open_weight:
权重开放，但许可证可能有限制，不一定 OSI open-source。

open_source:
权重和代码/许可证符合较宽松开源使用。

local_only:
主要本地运行，无主流官方 API。

hosted_open_weight:
开放权重模型，但当前记录的是某平台托管版本。

### 8.2 access_type

api:
可通过 API 使用。

web_app:
只能通过网页/应用使用。

local:
可本地部署。

api_and_local:
既有 API 也可本地部署。

unavailable:
已不可用或只在论文中出现。

---

## 9. 多模态能力规则

modality 建议枚举：

- text
- text_vision
- text_audio
- text_vision_audio
- text_vision_video
- text_vision_audio_video
- image_generation
- video_generation
- multimodal_generation

注意：

- 能理解图片 ≠ 能生成图片。
- 能处理音频输入 ≠ 能生成语音。
- 能处理视频帧 ≠ 原生视频理解。
- 多模态能力在 API 和网页产品中可能不同。

字段建议：

- supports_vision: true/false/unknown
- supports_audio_input: true/false/unknown
- supports_audio_output: true/false/unknown
- supports_video_input: true/false/unknown
- supports_image_generation: true/false/unknown
- supports_image_editing: true/false/unknown

---

## 10. 工具调用能力规则

字段建议：

- supports_function_calling
- supports_parallel_tool_calls
- supports_structured_output
- supports_json_schema
- supports_code_execution
- supports_web_search
- supports_computer_use

注意：

- 原生支持 function calling 和通过 prompt 模拟 JSON 不是一回事。
- 平台提供 web_search 不等于 base model 自带搜索能力。
- Computer Use 通常是模型 + scaffold + 环境能力，不要完全归因到 base model。

---

## 11. 上下文窗口规则

字段建议：

- context_window_tokens
- max_output_tokens
- effective_context_notes
- long_context_benchmark_sources

注意：

- 标称 context window 不等于有效长上下文能力。
- 1M context 如果召回差，不能在长上下文榜满分。
- 上下文、价格、速度要按具体 API 版本记录。

---

## 12. 模型名称归一化表格式

建议使用 YAML 或 CSV。

### 12.1 YAML 示例

```yaml
- canonical_id: anthropic/claude-3.5-sonnet@2024-10-22
  display_name: Claude 3.5 Sonnet (2024-10-22)
  provider: Anthropic
  provider_slug: anthropic
  model_family: claude-3.5
  model_variant: sonnet
  version: 2024-10-22
  release_date: 2024-10-22
  model_type: closed
  access_type: api
  license_type: proprietary
  context_window: 200000
  modality: text_vision
  supports_tools: true
  supports_structured_output: true
  api_model_ids:
    - claude-3-5-sonnet-20241022
  aliases:
    - Claude 3.5 Sonnet New
    - Claude 3.5 Sonnet (New)
    - claude-3.5-sonnet
  notes: Do not merge with 2024-06 Claude 3.5 Sonnet.
```

### 12.2 CSV 字段

```csv
canonical_id,display_name,provider,provider_slug,model_family,model_variant,version,release_date,model_type,access_type,license_type,context_window,modality,supports_tools,supports_structured_output,api_model_ids,aliases,notes
```

---

## 13. 归一化决策记录

每次人工合并/拆分都应记录：

- date
- raw_name
- source_id
- decision
- canonical_id
- match_confidence
- reason
- reviewer

示例：

```yaml
- date: 2026-05-03
  raw_name: Claude 3.5 Sonnet New
  source_id: lmarena_chatbot_arena
  decision: mapped
  canonical_id: anthropic/claude-3.5-sonnet@2024-10-22
  match_confidence: high
  reason: Arena label refers to Oct 2024 Sonnet refresh.
  reviewer: marovole
```

---

## 14. 第一版模型清单建议

第一版建议只收主流模型，每个厂商 1-3 个代表模型。

### 闭源/API 模型

OpenAI:
- GPT-4o
- GPT-4.1
- GPT-4.1 mini
- o3 / o4-mini / GPT-5 系列，按实际榜单数据确认

Anthropic:
- Claude Sonnet 系列
- Claude Opus 系列
- Claude Haiku 系列

Google:
- Gemini Pro
- Gemini Flash

xAI:
- Grok 主力模型
- Grok mini / code 模型，如有数据

DeepSeek:
- DeepSeek V 系列 chat 模型
- DeepSeek R 系列 reasoning 模型

Qwen:
- Qwen Max
- Qwen Coder
- Qwen 开放权重主力

Moonshot/Kimi:
- Kimi K2 / Kimi Thinking 类模型

Mistral:
- Mistral Large
- Codestral

MiniMax / Zhipu / Baidu / Tencent:
- 仅收进入主流榜单且数据足够的代表模型

### 开放权重模型

- Qwen3 系列
- DeepSeek 开放权重系列
- Llama 3.x / 4 系列
- Mistral / Mixtral 系列
- GLM 开源系列
- Yi / InternLM / MiniCPM 等视数据质量收录

### 多模态模型

- GPT-4o / GPT-4.1 vision-capable variants
- Gemini Pro / Flash 多模态版本
- Claude vision-capable variants
- Qwen-VL / Qwen-Omni
- InternVL
- LLaVA / open VLM models

---

## 15. 第一版人工审核 checklist

在计算前检查：

1. 是否有重复模型？
2. 是否把 mini 和 full 合并了？
3. 是否把 base 和 instruct 合并了？
4. 是否把 preview 和 stable 合并了？
5. 是否把网页产品名误当模型名？
6. 是否模型版本日期缺失？
7. 是否 API id 能对应到 canonical_id？
8. 是否有模型只在一个来源出现？
9. 是否有模型数据过旧？
10. 是否有厂商自报数据被当成第三方数据？

---

## 16. 未解决问题

第一版需要保守处理以下问题：

1. 同一模型不同平台部署是否表现一致？
2. API 模型 silent update 如何记录？
3. Thinking mode 是否作为独立模型？
4. Web app 模型和 API 模型是否合并？
5. 开源模型的量化版本是否影响榜单？
6. Agent scaffold 对模型能力的贡献如何分离？
7. 中国大陆可访问性是否作为模型字段还是平台字段？

建议：

第一版先以“公开榜单中的模型名 + 手工确认 canonical_id”为准，不追求完全自动化。所有不确定映射都标注 medium/low confidence。

---

## 17. 下一步

1. 建立 models.yaml。
2. 建立 aliases.yaml 或在 models.yaml 内维护 aliases。
3. 建立 normalization-decisions.yaml。
4. 从 P0 来源抽取 Top 模型。
5. 对 raw model names 做第一轮人工归一化。
6. 计算子榜和主榜。

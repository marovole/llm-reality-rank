# LLM Reality Rank 来源登记表

更新时间：2026-05-03

定位：为“LLM Reality Rank / 大模型真实使用价值榜”收录主流 LLM 排行榜、Benchmark 和实用性数据源。第一版目标是支持“长文 + 静态网页”两个交付形态。

核心原则：

1. 不把任何单一榜单视为最终真相。
2. 区分“能力分”“专项分”“实用分”“生态分”“置信分”。
3. 厂商自报数据可收录，但要降权并标注。
4. 主榜强调真实使用价值，子榜强调场景适配。
5. 所有来源必须保留 URL、评测对象、指标类型、更新时间和局限性说明。

---

## P0：第一版必须收录

### 1. LMArena / Chatbot Arena

- source_id: lmarena_chatbot_arena
- name: LMArena / Chatbot Arena Leaderboard
- url: https://lmarena.ai/leaderboard/
- backup_url: https://huggingface.co/spaces/lmarena-ai/arena-leaderboard
- organization: LMSYS / LMArena
- category: general, preference, conversation
- metric_type: Elo, human preference, win rate
- source_trust: high
- contamination_risk: low-medium
- recommended_weight: high for general/chat; medium for overall
- update_frequency: frequent
- best_for: 通用对话、人类偏好、回答体验
- use_in:
  - 综合使用价值榜
  - 通用对话榜
  - 写作/用户体验榜
- notes: 影响力极高，适合衡量真实用户偏好；但偏主观，容易受回答风格影响，不等于严格能力上限。

### 2. Artificial Analysis LLM Leaderboard

- source_id: artificial_analysis_llm
- name: Artificial Analysis LLM Leaderboard / Intelligence Index
- url: https://artificialanalysis.ai/leaderboards/models
- organization: Artificial Analysis
- category: general, cost_speed, api, practical
- metric_type: intelligence index, price, latency, speed, context
- source_trust: high
- contamination_risk: low-medium
- recommended_weight: high for practicality; medium-high for overall
- update_frequency: frequent
- best_for: API 选型、价格、速度、上下文、综合实用指标
- use_in:
  - 综合使用价值榜
  - 性价比榜
  - API 模型榜
  - 速度榜
  - 成本效率榜
- notes: 很适合作为 Reality Value Index 的 Practicality Multiplier 来源。

### 3. LiveBench

- source_id: livebench
- name: LiveBench
- url: https://livebench.ai/
- organization: LiveBench team
- category: general, reasoning, math, coding, anti_contamination
- metric_type: benchmark score, task accuracy
- source_trust: high
- contamination_risk: low
- recommended_weight: high
- update_frequency: frequent
- best_for: 动态、抗污染的综合能力评估
- use_in:
  - 综合能力榜
  - 推理榜
  - 数学榜
  - 编程参考
- notes: 动态更新有助于降低 benchmark contamination，适合成为 P0 客观能力源。

### 4. OpenCompass LLM Leaderboard

- source_id: opencompass_llm
- name: OpenCompass LLM Leaderboard
- url: https://rank.opencompass.org.cn/leaderboard-llm-v2
- backup_url: https://opencompass.org.cn/leaderboard-llm
- organization: OpenCompass / Shanghai AI Lab ecosystem
- category: general, chinese, reasoning, coding, open_models
- metric_type: benchmark aggregate, task score
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for Chinese/general; medium-high for overall
- update_frequency: frequent
- best_for: 中英综合能力、中国模型覆盖、开源模型评测
- use_in:
  - 综合使用价值榜
  - 中文能力榜
  - 开源模型榜
  - 中国模型榜
- notes: 对中文和中国模型覆盖优于许多英文榜单。

### 5. Hugging Face Open LLM Leaderboard

- source_id: hf_open_llm_leaderboard
- name: Hugging Face Open LLM Leaderboard
- url: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
- organization: Hugging Face
- category: open_models, general
- metric_type: benchmark aggregate
- source_trust: high
- contamination_risk: medium-high
- recommended_weight: medium for open models; low-medium for overall
- update_frequency: frequent
- best_for: 开放权重模型横向比较
- use_in:
  - 开源/开放权重模型榜
  - 本地部署榜
  - 小模型榜
- notes: 旧版曾被刷榜/污染质疑。适合用作开源模型来源之一，不应单独决定总分。

### 6. Stanford HELM / HELM Lite

- source_id: stanford_helm
- name: Stanford HELM / HELM Lite
- url: https://crfm.stanford.edu/helm/
- lite_url: https://crfm.stanford.edu/helm/lite/latest/
- organization: Stanford CRFM
- category: general, safety, robustness, fairness, academic
- metric_type: holistic benchmark metrics
- source_trust: high
- contamination_risk: medium
- recommended_weight: medium-high for methodology; medium for overall
- update_frequency: periodic
- best_for: 学术公信力、鲁棒性、安全、公平、校准等维度
- use_in:
  - 综合能力榜
  - 安全/鲁棒性参考
  - 方法论背书
- notes: 更新速度未必最快，但学术权威性强。

### 7. SWE-bench Verified

- source_id: swe_bench_verified
- name: SWE-bench Verified
- url: https://www.swebench.com/
- organization: SWE-bench
- category: coding, agentic_coding, software_engineering
- metric_type: resolved issue rate, pass rate
- source_trust: high
- contamination_risk: medium
- recommended_weight: very high for coding; medium for overall
- update_frequency: frequent
- best_for: 真实 GitHub issue 修复能力
- use_in:
  - AI Coding 榜
  - Agent Coding 榜
  - 真实工程能力榜
- notes: 优先使用 Verified，不要和普通 SWE-bench 混合计分。

### 8. Aider LLM Leaderboards

- source_id: aider_leaderboards
- name: Aider LLM Leaderboards
- url: https://aider.chat/docs/leaderboards/
- organization: Aider
- category: coding, code_editing, cost
- metric_type: pass rate, cost, code editing benchmark
- source_trust: high
- contamination_risk: low-medium
- recommended_weight: very high for AI Coding; medium for overall
- update_frequency: frequent
- best_for: 真实代码编辑、多语言改代码、coding cost
- use_in:
  - AI Coding 榜
  - 代码编辑榜
  - 性价比 Coding 榜
- notes: 与 AI Coding 真实使用高度相关，建议高权重。

### 9. LiveCodeBench

- source_id: livecodebench
- name: LiveCodeBench
- url: https://livecodebench.github.io/leaderboard.html
- organization: LiveCodeBench
- category: coding, algorithms, anti_contamination
- metric_type: pass rate, benchmark score
- source_trust: high
- contamination_risk: low-medium
- recommended_weight: high for coding; medium for overall
- update_frequency: frequent
- best_for: 动态编程能力、算法题、代码推理
- use_in:
  - 编程能力榜
  - 算法代码榜
  - 推理+代码榜
- notes: 比 HumanEval/MBPP 更新、更难、更抗污染。

### 10. SuperCLUE

- source_id: superclue
- name: SuperCLUE
- url: https://superclueai.com/
- github_url: https://github.com/CLUEbenchmark/SuperCLUE
- organization: CLUEbenchmark / SuperCLUE
- category: chinese, general, reasoning
- metric_type: benchmark aggregate, task score
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for Chinese; medium for overall
- update_frequency: periodic
- best_for: 中文通用大模型综合评测
- use_in:
  - 中文能力榜
  - 中国模型榜
  - 综合使用价值榜中文维度
- notes: 中文榜单核心来源之一。

### 11. C-Eval

- source_id: ceval
- name: C-Eval
- url: https://cevalbenchmark.com/static/leaderboard.html
- organization: C-Eval team
- category: chinese, exams, knowledge
- metric_type: accuracy, exam benchmark score
- source_trust: high
- contamination_risk: medium-high
- recommended_weight: medium-high for Chinese; low-medium for overall
- update_frequency: periodic
- best_for: 中文考试、知识理解
- use_in:
  - 中文知识榜
  - 中文能力榜
- notes: 经典中文评测。当前站点可能有证书问题，抓取时可能需要使用镜像/GitHub/忽略 SSL。

### 12. CMMLU

- source_id: cmmlu
- name: CMMLU
- url: https://github.com/haonan-li/CMMLU
- organization: CMMLU authors
- category: chinese, knowledge, mmlu_style
- metric_type: accuracy
- source_trust: high
- contamination_risk: medium-high
- recommended_weight: medium-high for Chinese; low-medium for overall
- update_frequency: periodic
- best_for: 中文多任务语言理解
- use_in:
  - 中文能力榜
  - 中文知识理解榜
- notes: 需区分官方自报和第三方复现。

### 13. MMMU

- source_id: mmmu
- name: MMMU
- url: https://mmmu-benchmark.github.io/
- organization: MMMU authors
- category: multimodal, vision, reasoning
- metric_type: accuracy
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for multimodal; low-medium for overall
- update_frequency: periodic
- best_for: 多学科多模态理解与视觉推理
- use_in:
  - 多模态榜
  - 图文理解榜
  - 视觉推理榜
- notes: 多模态理解重要 benchmark。

### 14. MathVista

- source_id: mathvista
- name: MathVista
- url: https://mathvista.github.io/
- organization: MathVista authors
- category: multimodal, math, visual_reasoning
- metric_type: accuracy
- source_trust: high
- contamination_risk: medium
- recommended_weight: medium-high for multimodal reasoning; low for overall
- update_frequency: periodic
- best_for: 视觉数学推理
- use_in:
  - 多模态推理榜
  - 数学视觉榜
- notes: 适合作为多模态子维度。

### 15. GAIA Benchmark

- source_id: gaia
- name: GAIA Benchmark Leaderboard
- url: https://gaia-benchmark-leaderboard.hf.space/
- backup_url: https://huggingface.co/spaces/gaia-benchmark/leaderboard
- organization: GAIA benchmark authors
- category: agent, tool_use, research_assistant
- metric_type: task success rate
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for Agent; low-medium for overall
- update_frequency: periodic
- best_for: 多步推理、搜索、工具使用、研究助手能力
- use_in:
  - Agent 能力榜
  - 研究助手榜
  - 工具使用榜
- notes: 非常适合衡量“LLM 作为助手/Agent”的真实任务能力。

### 16. Berkeley Function Calling Leaderboard / Gorilla

- source_id: berkeley_function_calling
- name: Berkeley Function Calling Leaderboard / Gorilla
- url: https://gorilla.cs.berkeley.edu/leaderboard.html
- blog_url: https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html
- organization: UC Berkeley Gorilla
- category: agent, function_calling, tool_use
- metric_type: accuracy, AST/subtree/executable evaluation
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for Agent; low-medium for overall
- update_frequency: periodic
- best_for: 函数调用、API 调用、工具使用
- use_in:
  - Agent 工具调用榜
  - Function Calling 榜
- notes: 对 Hermes/Codex/Claude Code 等工具型 Agent 选型很关键。

### 17. OpenRouter Rankings

- source_id: openrouter_rankings
- name: OpenRouter Rankings
- url: https://openrouter.ai/rankings
- organization: OpenRouter
- category: adoption, api, ecosystem, usage
- metric_type: usage ranking, traffic/popularity signal
- source_trust: medium-high
- contamination_risk: low for usage, not applicable for ability
- recommended_weight: medium for ecosystem; low for ability
- update_frequency: frequent
- best_for: 真实市场选择、API 使用热度、生态采用
- use_in:
  - 实际使用热度
  - API 生态榜
  - 实用性 multiplier
- notes: 不是能力榜，不能当能力分；适合作为 adoption / popularity / availability 信号。

---

## P1：第一版可收录，但低权重或用于子榜

### 18. Vellum LLM Leaderboard

- source_id: vellum_llm_leaderboard
- name: Vellum LLM Leaderboard
- url: https://www.vellum.ai/llm-leaderboard
- organization: Vellum
- category: general, application_development
- metric_type: model comparison, benchmark aggregate
- source_trust: medium-high
- contamination_risk: medium
- recommended_weight: low-medium
- use_in: 应用开发者榜、综合使用价值辅助来源
- notes: 更适合作为应用层选型参考，不宜高权重。

### 19. Scale SWE-bench Leaderboard

- source_id: scale_swe_bench
- name: Scale AI SWE-bench Leaderboard
- url: https://scale.com/leaderboard/swe-bench
- organization: Scale AI
- category: coding, agentic_coding
- metric_type: SWE-bench score
- source_trust: high
- contamination_risk: medium
- recommended_weight: medium-high for coding
- use_in: AI Coding 榜、Agent Coding 榜
- notes: 抓取时需要处理 308 redirect。

### 20. BigCodeBench

- source_id: bigcodebench
- name: BigCodeBench
- url: https://bigcode-bench.github.io/
- organization: BigCodeBench authors
- category: coding
- metric_type: pass rate, benchmark score
- source_trust: high
- contamination_risk: medium
- recommended_weight: medium-high for coding
- use_in: 编程能力榜、开源模型 Coding 榜
- notes: 比 HumanEval 更现代，覆盖更复杂任务。

### 21. EvalPlus

- source_id: evalplus
- name: EvalPlus Leaderboard
- url: https://evalplus.github.io/leaderboard.html
- organization: EvalPlus authors
- category: coding
- metric_type: HumanEval+ / MBPP+ pass rate
- source_trust: high
- contamination_risk: medium-high
- recommended_weight: medium for coding basics
- use_in: 编程基础能力榜
- notes: 传统代码 benchmark 改进版，但 HumanEval 系列仍偏旧。

### 22. Humanity's Last Exam / HLE

- source_id: humanitys_last_exam
- name: Humanity's Last Exam
- url: https://scale.com/research/humanitys-last-exam
- organization: Scale AI / CAIS and collaborators
- category: reasoning, expert_knowledge, hard_benchmark
- metric_type: accuracy
- source_trust: high
- contamination_risk: low-medium
- recommended_weight: medium for reasoning; low-medium for overall
- use_in: 高难度推理榜、专家任务榜
- notes: 高传播性、高难度，但不等于日常使用价值。

### 23. ARC-AGI / ARC Prize

- source_id: arc_agi
- name: ARC-AGI / ARC Prize Leaderboard
- url: https://arcprize.org/leaderboard
- related_url: https://agi.safe.ai/
- organization: ARC Prize / related AGI eval community
- category: reasoning, abstraction, agi_signal
- metric_type: task success, accuracy
- source_trust: high
- contamination_risk: low
- recommended_weight: medium for reasoning; low for overall
- use_in: 推理能力榜、AGI 风向标
- notes: 不适合作为普通使用价值主权重。

### 24. BAAI Open Chinese LLM Leaderboard

- source_id: baai_open_cn_llm
- name: BAAI Open Chinese LLM Leaderboard
- url: https://huggingface.co/spaces/BAAI/open_cn_llm_leaderboard
- organization: BAAI
- category: chinese, open_models
- metric_type: benchmark aggregate
- source_trust: medium-high
- contamination_risk: medium
- recommended_weight: medium-high for Chinese open models
- use_in: 中文开源模型榜、中国模型榜
- notes: 适合补充中文开放权重模型表现。

### 25. Open Multilingual LLM Leaderboard

- source_id: open_multilingual_llm
- name: Open Multilingual LLM Leaderboard
- url: https://huggingface.co/spaces/PetruZetta/open_multilingual_llm_leaderboard
- alternate_url: https://huggingface.co/spaces/uonlp/open_multilingual_llm_leaderboard
- organization: community / UONLP variants
- category: multilingual
- metric_type: multilingual benchmark aggregate
- source_trust: medium
- contamination_risk: medium
- recommended_weight: medium for multilingual
- use_in: 多语言榜、全球化使用榜
- notes: 中文榜优先使用 SuperCLUE / C-Eval / CMMLU / OpenCompass。

### 26. OpenCompass Open VLM Leaderboard

- source_id: opencompass_open_vlm
- name: OpenCompass Open VLM Leaderboard
- url: https://huggingface.co/spaces/opencompass/open_vlm_leaderboard
- organization: OpenCompass
- category: multimodal, open_vlm
- metric_type: VLM benchmark aggregate
- source_trust: high
- contamination_risk: medium
- recommended_weight: medium-high for multimodal open models
- use_in: 多模态榜、开源 VLM 榜
- notes: OpenCompass 体系的多模态补充。

### 27. OCRBench / MultimodalOCR

- source_id: ocrbench_multimodalocr
- name: OCRBench / MultimodalOCR
- url: https://github.com/Yuliang-Liu/MultimodalOCR
- organization: MultimodalOCR authors
- category: multimodal, ocr, document_understanding
- metric_type: OCR/document benchmark score
- source_trust: medium-high
- contamination_risk: medium
- recommended_weight: high for document understanding; medium for multimodal
- use_in: 文档理解榜、多模态榜、办公实用榜
- notes: 很贴近日常真实使用，适合增强 Reality Rank 差异化。

### 28. WebArena

- source_id: webarena
- name: WebArena
- url: https://webarena.dev/
- organization: WebArena authors
- category: agent, web_agent
- metric_type: task success rate
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for web agent; low for overall
- use_in: Agent 榜、Web Agent 榜
- notes: 衡量网页环境任务完成能力。

### 29. OSWorld

- source_id: osworld
- name: OSWorld
- url: https://os-world.github.io/
- organization: OSWorld authors
- category: agent, computer_use, multimodal_agent
- metric_type: task success rate
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for computer use; low for overall
- use_in: Agent 榜、Computer Use 榜、多模态 Agent 榜
- notes: 衡量真实计算机环境中的 open-ended task 能力。

### 30. MTEB Leaderboard

- source_id: mteb
- name: MTEB Leaderboard
- url: https://huggingface.co/spaces/mteb/leaderboard
- standalone_url: https://mteb-leaderboard.hf.space/
- organization: MTEB / Hugging Face community
- category: embedding, retrieval, rag
- metric_type: embedding benchmark aggregate
- source_trust: high
- contamination_risk: medium
- recommended_weight: high for embedding; not included in LLM generation overall
- use_in: Embedding 模型榜、RAG 组件榜、Agent 基础设施榜
- notes: 不是生成式 LLM 主榜来源，但对 RAG/Agent 系统选型非常重要。

---

## P2：观察/后续扩展

### 31. Terminal-Bench

- source_id: terminal_bench
- name: Terminal-Bench
- url: https://terminal-bench.com/
- category: agent, terminal, coding_agent
- recommended_weight: high for CLI Agent once data ingestion is stable
- notes: 终端环境真实任务 benchmark，和 Hermes/Codex/Claude Code 高相关；当前抓取可能有 TLS 兼容问题。

### 32. SimpleBench

- source_id: simplebench
- name: SimpleBench
- url: https://huggingface.co/spaces/simple-bench/simple-bench
- category: reasoning, common_sense, robustness
- recommended_weight: medium for common sense
- notes: HF Space 访问可能受限；适合作为“模型为什么会犯简单错”的传播素材。

### 33. ZebraLogic

- source_id: zebralogic
- name: ZebraLogic
- url: https://huggingface.co/spaces/allenai/ZebraLogic
- category: reasoning, logic
- recommended_weight: medium for logic reasoning
- notes: 逻辑推理子指标。

### 34. SEA-HELM

- source_id: sea_helm
- name: SEA-HELM
- url: https://leaderboard.sea-lion.ai/
- category: multilingual, southeast_asia
- recommended_weight: medium for multilingual regional coverage
- notes: 第一版可列入观察，全球化扩展时有价值。

### 35. OpenCompass Open VLM Video Leaderboard

- source_id: opencompass_video_vlm
- name: OpenCompass Open VLM Video Leaderboard
- url: https://huggingface.co/spaces/opencompass/openvlm_video_leaderboard
- category: multimodal, video
- recommended_weight: medium for video understanding
- notes: 视频理解后续扩展来源。

### 36. Video-MME

- source_id: video_mme
- name: Video-MME
- url: https://video-mme.github.io/
- category: multimodal, video
- recommended_weight: medium for video understanding
- notes: 需确认最新项目页和数据入口。

### 37. AlpacaEval

- source_id: alpacaeval
- name: AlpacaEval
- url: https://tatsu-lab.github.io/alpaca_eval/
- category: preference, instruction_following
- recommended_weight: low-medium
- notes: 自动偏好评测，可能受评审模型偏差影响。

### 38. RewardBench

- source_id: rewardbench
- name: RewardBench
- url: https://huggingface.co/spaces/allenai/reward-bench
- category: reward_model, alignment
- recommended_weight: low for main LLM rank
- notes: 主要用于奖励模型/偏好模型，不是通用 LLM 主榜核心来源。

### 39. WildBench

- source_id: wildbench
- name: WildBench
- url: https://huggingface.co/spaces/allenai/WildBench
- category: general, real_user_tasks, open_ended
- recommended_weight: low-medium
- notes: 真实开放任务辅助来源。

### 40. τ-bench / Tool-use Benchmarks

- source_id: tau_bench_tool_use
- name: τ-bench / Tool-use Benchmarks
- url: TBD
- category: agent, tool_use
- recommended_weight: medium-high for Agent once canonical source is confirmed
- notes: 需要后续确认权威入口。

---

## 建议的来源分类权重

### 综合使用价值榜

- 通用/偏好能力：LMArena, LiveBench, HELM, OpenCompass
- 推理/知识能力：LiveBench, HLE, ARC-AGI, HELM
- 编程能力：SWE-bench Verified, Aider, LiveCodeBench
- 中文能力：SuperCLUE, C-Eval, CMMLU, OpenCompass
- 多模态能力：MMMU, MathVista, OpenCompass VLM, OCRBench
- 实用性：Artificial Analysis, OpenRouter, pricing/context/speed
- Agent 能力：GAIA, Berkeley Function Calling, WebArena, OSWorld

### 数据层级

1. 原始分：保留来源原始指标。
2. 标准化分：转为 0-100。
3. 场景权重分：按子榜权重合成。
4. 置信度：来源数量、来源可信度、更新日期、是否第三方评测。
5. 时间衰减：越旧权重越低。

### 推荐数据表字段

- source_id
- source_name
- url
- organization
- category
- metric_type
- source_trust
- contamination_risk
- update_frequency
- recommended_weight
- model_name_raw
- model_name_normalized
- model_provider
- model_version
- score_raw
- score_normalized
- rank_raw
- date_observed
- date_published
- notes
- ingestion_method: manual, scrape, api, csv, hf_space
- license_or_terms_note

---

## 第一版执行建议

第一版先不要追求自动抓取所有来源。推荐顺序：

1. 手工结构化 P0 来源。
2. 每个来源先收 Top 20-50 模型。
3. 建立模型名称归一化表，解决 GPT/Claude/Gemini/Qwen/DeepSeek 同名不同版本问题。
4. 做 5 个子榜：综合、Coding、中文、性价比、多模态/Agent。
5. 发布第一篇方法论长文。
6. 再开发静态网页。
7. 最后做半自动更新。

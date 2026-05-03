# LLM Reality Rank

LLM Reality Rank（大模型真实使用价值榜）是一个面向中文高阶 AI 用户、开发者和创作者的 LLM 综合评价项目。

核心口号：不是只看考试分，而是看真实使用价值。

项目聚合主流 LLM 排行榜、专项 benchmark、价格速度数据和真实使用信号，形成一个可解释、可追溯、可持续更新的综合评价体系。当前仓库已经包含可运行的数据管线、reviewed alpha 快照、静态 API、文章导出和 Astro 静态站点。

## 定位

LLM Reality Rank 优先回答这些问题：

- 今天最值得普通用户使用的模型是谁？
- AI Coding 场景应该选 GPT、Claude、Gemini、DeepSeek、Qwen 还是其他模型？
- 中文写作、中文知识和中国语境下哪个模型更稳？
- 哪些模型不是绝对最强，但性价比极高？
- 哪些模型适合 Agent、工具调用、长任务和真实工作流？
- 开源/开放权重模型在实际使用中已经到什么位置？

## 当前状态

当前是 M5 alpha platform 阶段，已经包含：

- 来源登记、模型归一化和评分方法论文档
- machine-readable `sources.yaml` / `models.yaml` / `raw_rankings.csv`
- safe ingestion framework（fixture 默认、bounded live-safe 可选）
- validate / normalize / aggregate scoring pipeline
- reviewed alpha snapshot：`snapshots/llm-reality-rank/2026-05-alpha/`
- static API JSON：`site/public/api/v1/` 和 `outputs/llm-reality-rank/api/v1/`
- article-ready Markdown exports 和公开方法论草稿
- Astro + Cloudflare Pages 静态站点，包含首页、榜单、模型证据、方法论、快照页和模型选择器
- Python pytest、站点内容/交互检查、Astro check/build 和 GitHub Actions CI

## Alpha 数据 caveats

`2026-05-alpha` 是 reviewed alpha seed snapshot，不是完整或最终排名：

- 当前只覆盖少量已人工复核、可追溯的种子数据。
- 缺失维度会显式暴露，不会用未复核数据补齐或插值。
- 分数依赖外部 benchmark 与来源当时状态，不代表绝对真相。
- 引用时建议写作“基于 reviewed alpha snapshot 的有限证据”，不要写成全网最终榜单。

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

## 项目结构

```text
data/llm-reality-rank/
  sources.yaml
  models.yaml
  raw_rankings.csv

docs/
  llm-reality-rank-source-registry.md
  llm-reality-rank-scoring-methodology.md
  llm-reality-rank-model-normalization.md
  public-methodology-article-2026-05-alpha.md

scripts/llm-reality-rank/
  ingest_sources.py
  validate_data.py
  normalize_scores.py
  aggregate_scores.py
  export_reviewed_snapshot.py
  export_article_assets.py

outputs/llm-reality-rank/
  api/v1/*.json                     # generated static API source
  article-exports/<snapshot-id>/     # generated article tables
  normalized_scores.csv              # generated
  model_scores.csv                   # generated
  model_scores.md                    # generated
  first-draft-leaderboard.md         # generated

snapshots/llm-reality-rank/
  2026-05-alpha/*.json               # reviewed immutable alpha snapshot

site/
  package.json
  astro.config.mjs
  _headers
  src/
  public/api/v1/*.json

tests/llm-reality-rank/
  test_*.py

.github/workflows/
  ci.yml
```

Most generated files under `outputs/llm-reality-rank/` are ignored by git. Reviewed snapshots and published static API files are tracked when promoted.

## Setup

Python scripts require Python 3 and the dependencies in `requirements.txt`:

```bash
python3 -m pip install -r requirements.txt
```

The site requires Node compatible with `site/package.json` (`>=20.3.0 <21` or `>=22`):

```bash
npm --prefix site install
```

## Data pipeline commands

Validate source/model/raw data:

```bash
python3 scripts/llm-reality-rank/validate_data.py
```

Run the scoring pipeline:

```bash
python3 scripts/llm-reality-rank/normalize_scores.py
python3 scripts/llm-reality-rank/aggregate_scores.py
```

The pipeline writes generated CSV/Markdown outputs to `outputs/llm-reality-rank/`.

## Safe ingestion commands

List available ingestion targets:

```bash
python3 scripts/llm-reality-rank/ingest_sources.py list
```

Run fixture-based ingestion:

```bash
python3 scripts/llm-reality-rank/ingest_sources.py ingest aider --mode fixture --fixture path/to/fixture.json --output-csv outputs/llm-reality-rank/ingested-aider.csv
```

Run bounded live-safe ingestion when a target supports public fetching:

```bash
python3 scripts/llm-reality-rank/ingest_sources.py ingest artificial_analysis --mode live-safe --output-csv outputs/llm-reality-rank/ingested-artificial-analysis.csv
```

Live-safe mode is intentionally conservative: it uses public HTTP(S), timeouts, size limits, and returns `manual_required` instead of scraping around blocked or unsupported pages.

## Snapshot, API, and article exports

Promote generated pipeline outputs to an immutable reviewed snapshot and static API JSON:

```bash
python3 scripts/llm-reality-rank/export_reviewed_snapshot.py --snapshot-id 2026-05-alpha
```

This writes:

- `snapshots/llm-reality-rank/<snapshot-id>/*.json`
- `outputs/llm-reality-rank/api/v1/*.json`

Export article-ready tables and the public methodology article draft:

```bash
python3 scripts/llm-reality-rank/export_article_assets.py --snapshot-id 2026-05-alpha
```

This writes:

- `outputs/llm-reality-rank/article-exports/<snapshot-id>/*.md`
- `docs/public-methodology-article-2026-05-alpha.md`

Use `--skip-article` if you only want table exports.

## Site commands

Run site checks:

```bash
npm --prefix site test
npm --prefix site run check
```

Start local development:

```bash
npm --prefix site run dev
```

Build and preview the static site:

```bash
npm --prefix site run build
npm --prefix site run preview
```

The site build runs `site/scripts/copy-api-assets.mjs` before Astro build, copying static API JSON from `outputs/llm-reality-rank/api/v1/` into `site/public/api/v1/`.

## Cloudflare Pages notes

The Astro site is configured for static output in `site/astro.config.mjs`:

- `output: 'static'`
- site URL: `https://llm-reality-rank.pages.dev`
- trailing slash pages with directory-style output

Recommended Cloudflare Pages settings:

- Root directory: `site`
- Build command: `npm run build`
- Build output directory: `dist`
- Node version: use Node 20.3+ or 22+

If building from the repository root instead, use `npm --prefix site run build` and publish `site/dist`. The `site/_headers` file sets JSON content type/cache headers for `/api/v1/*.json` and `X-Content-Type-Options: nosniff`.

## Verification

Python validators and tests:

```bash
python3 scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
```

Site validators:

```bash
npm --prefix site test
npm --prefix site run check
npm --prefix site run build
```

GitHub Actions currently runs Python data validation and pytest on push and pull request.

## Key source references

Complete source and methodology references:

```text
docs/llm-reality-rank-source-registry.md
docs/llm-reality-rank-scoring-methodology.md
docs/llm-reality-rank-model-normalization.md
data/llm-reality-rank/sources.yaml
```

The source registry includes P0 sources such as LMArena / Chatbot Arena, Artificial Analysis, LiveBench, OpenCompass, Hugging Face Open LLM Leaderboard, Stanford HELM, SWE-bench Verified, Aider, LiveCodeBench, SuperCLUE, C-Eval, CMMLU, MMMU, MathVista, GAIA, Berkeley Function Calling / Gorilla, and OpenRouter.

## License

MIT

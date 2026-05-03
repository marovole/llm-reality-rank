# LLM Reality Rank Scoring Pipeline Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Build the first local, reproducible data pipeline that validates LLM Reality Rank YAML/CSV inputs and computes draft normalized scores from manually collected leaderboard rows.

**Architecture:** Keep the first version intentionally simple: machine-readable data lives under `data/llm-reality-rank/`, scripts live under `scripts/llm-reality-rank/`, and generated outputs live under `outputs/llm-reality-rank/`. The pipeline validates source/model references, normalizes raw metrics into 0-100 scores, applies source/freshness/trust multipliers, aggregates by scenario, and exports CSV/Markdown tables for article and static-site use.

**Tech Stack:** Python 3.13 stdlib + PyYAML. Optional later: pandas, duckdb, pytest, static-site framework.

---

## Current Files

- `docs/llm-reality-rank-source-registry.md`
- `docs/llm-reality-rank-scoring-methodology.md`
- `docs/llm-reality-rank-model-normalization.md`
- `data/llm-reality-rank/sources.yaml`
- `data/llm-reality-rank/models.yaml`
- `data/llm-reality-rank/raw_rankings.csv`

---

## Task 1: Create Directory Skeleton

**Objective:** Create stable directories for scripts, tests, and generated outputs.

**Files:**
- Create: `scripts/llm-reality-rank/.gitkeep`
- Create: `outputs/llm-reality-rank/.gitkeep`
- Create: `tests/llm-reality-rank/.gitkeep`

**Step 1: Create directories**

Run:

```bash
mkdir -p scripts/llm-reality-rank outputs/llm-reality-rank tests/llm-reality-rank
touch scripts/llm-reality-rank/.gitkeep outputs/llm-reality-rank/.gitkeep tests/llm-reality-rank/.gitkeep
```

**Step 2: Verify**

Run:

```bash
find scripts/llm-reality-rank outputs/llm-reality-rank tests/llm-reality-rank -maxdepth 1 -type f -name .gitkeep
```

Expected: three `.gitkeep` paths.

---

## Task 2: Write Data Validation Script

**Objective:** Validate that `sources.yaml`, `models.yaml`, and `raw_rankings.csv` are structurally valid and cross-reference each other.

**Files:**
- Create: `scripts/llm-reality-rank/validate_data.py`

**Step 1: Implement validator**

Create `scripts/llm-reality-rank/validate_data.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "llm-reality-rank"

REQUIRED_SOURCE_FIELDS = {"source_id", "priority", "name", "urls", "categories", "metric_types", "source_trust", "contamination_risk"}
REQUIRED_MODEL_FIELDS = {"canonical_id", "display_name", "provider", "provider_slug", "model_family", "model_variant", "version", "model_type", "access_type"}
REQUIRED_RANKING_FIELDS = {
    "source_id", "source_name", "source_priority", "category_primary", "metric_name", "metric_type",
    "model_name_raw", "canonical_id", "provider", "rank_raw", "score_raw", "score_unit",
    "score_higher_is_better", "date_published", "date_observed", "source_url",
    "evaluation_independence", "source_trust", "contamination_risk", "freshness_weight", "notes",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fail(errors: list[str]) -> None:
    if errors:
        print("VALIDATION FAILED")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    print("VALIDATION PASSED")


def main() -> None:
    errors: list[str] = []
    sources_doc = load_yaml(DATA / "sources.yaml")
    models_doc = load_yaml(DATA / "models.yaml")

    sources = sources_doc.get("sources", [])
    models = models_doc.get("models", [])

    source_ids = set()
    for idx, s in enumerate(sources, 1):
        missing = REQUIRED_SOURCE_FIELDS - set(s)
        if missing:
            errors.append(f"source #{idx} missing fields: {sorted(missing)}")
        sid = s.get("source_id")
        if sid in source_ids:
            errors.append(f"duplicate source_id: {sid}")
        source_ids.add(sid)

    model_ids = set()
    for idx, m in enumerate(models, 1):
        missing = REQUIRED_MODEL_FIELDS - set(m)
        if missing:
            errors.append(f"model #{idx} missing fields: {sorted(missing)}")
        cid = m.get("canonical_id")
        if cid in model_ids:
            errors.append(f"duplicate canonical_id: {cid}")
        model_ids.add(cid)

    with (DATA / "raw_rankings.csv").open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = REQUIRED_RANKING_FIELDS - header
        if missing:
            errors.append(f"raw_rankings.csv missing columns: {sorted(missing)}")
        for row_num, row in enumerate(reader, 2):
            sid = row.get("source_id")
            cid = row.get("canonical_id")
            if sid and sid not in source_ids:
                errors.append(f"row {row_num}: unknown source_id {sid}")
            if cid and cid not in model_ids:
                errors.append(f"row {row_num}: unknown canonical_id {cid}")
            higher = row.get("score_higher_is_better", "").lower()
            if higher not in {"true", "false", ""}:
                errors.append(f"row {row_num}: score_higher_is_better must be true/false/empty")

    fail(errors)


if __name__ == "__main__":
    main()
```

**Step 2: Run validator**

Run:

```bash
python3 scripts/llm-reality-rank/validate_data.py
```

Expected: `VALIDATION PASSED`.

---

## Task 3: Write Normalization Script

**Objective:** Convert raw ranking rows with numeric scores or ranks into normalized 0-100 rows.

**Files:**
- Create: `scripts/llm-reality-rank/normalize_scores.py`
- Create: `outputs/llm-reality-rank/normalized_scores.csv`

**Step 1: Implement minimal normalization**

Rules:

- If `score_raw` exists and metric type is accuracy/pass_rate/benchmark_score/aggregate_score, use numeric score directly if 0-100.
- If only `rank_raw` exists, convert rank within same `source_id + metric_name` group.
- Empty TODO rows should be skipped but reported.

**Step 2: Run script**

Run:

```bash
python3 scripts/llm-reality-rank/normalize_scores.py
```

Expected:

- Creates `outputs/llm-reality-rank/normalized_scores.csv`
- Prints skipped TODO rows count.

---

## Task 4: Add Source Weight Calculation

**Objective:** Apply source trust, contamination risk, evaluation independence, and freshness multipliers.

**Files:**
- Modify: `scripts/llm-reality-rank/normalize_scores.py`

**Weight maps:**

```python
SOURCE_TRUST = {
    "high": 1.00,
    "medium_high": 0.85,
    "medium": 0.70,
    "low_medium": 0.55,
    "low": 0.40,
}

CONTAMINATION_RISK = {
    "low": 1.00,
    "low_medium": 0.90,
    "medium": 0.75,
    "medium_high": 0.60,
    "high": 0.40,
    "low_for_usage_not_applicable_for_ability": 1.00,
}

INDEPENDENCE = {
    "independent_third_party": 1.00,
    "platform_or_community": 0.85,
    "benchmark_author_reported": 0.80,
    "vendor_reported": 0.60,
    "unknown": 0.50,
}
```

**Expected output columns:**

- source_id
- metric_name
- canonical_id
- score_raw
- score_normalized
- source_effective_weight
- score_weighted
- category_primary

---

## Task 5: Write Scenario Aggregation Script

**Objective:** Aggregate normalized scores into draft sub-scores and an overall score.

**Files:**
- Create: `scripts/llm-reality-rank/aggregate_scores.py`
- Create: `outputs/llm-reality-rank/model_scores.csv`
- Create: `outputs/llm-reality-rank/model_scores.md`

**First-pass category mapping:**

- general -> General
- reasoning/math -> Reasoning_Math
- coding -> Coding
- chinese -> Chinese
- multimodal -> Multimodal_Doc
- agent -> Agent_ToolUse
- practical/cost_speed/api -> Practicality
- ecosystem/adoption/usage -> Ecosystem

**Overall weights:**

- General: 0.20
- Reasoning_Math: 0.15
- Coding: 0.15
- Chinese: 0.15
- Multimodal_Doc: 0.10
- Agent_ToolUse: 0.10
- Practicality: 0.10
- Ecosystem: 0.05

**Step 1: Implement weighted average by canonical_id and category.**

**Step 2: Export CSV and Markdown table.**

**Step 3: Run aggregation.**

Run:

```bash
python3 scripts/llm-reality-rank/aggregate_scores.py
```

Expected:

- Creates CSV and Markdown outputs.
- Skips models with no numeric rows.

---

## Task 6: Add Seed Numeric Sample Rows

**Objective:** Replace a small subset of TODO rows with real numeric values after manual lookup, enough to test the pipeline end-to-end.

**Files:**
- Modify: `data/llm-reality-rank/raw_rankings.csv`

**Step 1: Pick 3 sources**

Suggested first sources:

- Artificial Analysis
- Aider
- LMArena

**Step 2: Add 3-5 models per source**

At minimum include:

- GPT-4o
- Claude 3.5 Sonnet
- Gemini 2.5 Pro
- DeepSeek V3
- Qwen3-Max if available

**Step 3: Run full pipeline**

```bash
python3 scripts/llm-reality-rank/validate_data.py
python3 scripts/llm-reality-rank/normalize_scores.py
python3 scripts/llm-reality-rank/aggregate_scores.py
```

Expected: all pass and produce non-empty `model_scores.csv`.

---

## Task 7: Create First Public-Facing Draft Table

**Objective:** Generate a Markdown table suitable for article drafting.

**Files:**
- Create: `outputs/llm-reality-rank/first-draft-leaderboard.md`

**Content:**

- title
- generation date
- caution banner: “draft, incomplete data”
- top models table
- methodology links
- known missing sources

---

## Task 8: Review and Commit

**Objective:** Verify all generated files and commit.

**Step 1: Validate YAML and CSV**

```bash
python3 scripts/llm-reality-rank/validate_data.py
```

**Step 2: Check generated outputs**

```bash
ls -lh outputs/llm-reality-rank/
head -20 outputs/llm-reality-rank/model_scores.md
```

**Step 3: Commit**

```bash
git add docs/ data/ scripts/ outputs/ tests/
git commit -m "feat: add LLM Reality Rank data pipeline"
```

If this directory is not a git repository, skip commit and report file paths.

---

## Stop Conditions

Stop and ask for user input if:

- A source blocks scraping and requires login/manual export.
- A model name cannot be safely normalized.
- A benchmark uses incompatible metrics that cannot be converted without a policy decision.
- Real numeric data conflicts across sources in a way that changes the methodology.

---

## Verification Checklist

- [ ] `sources.yaml` parses with PyYAML.
- [ ] `models.yaml` parses with PyYAML.
- [ ] `raw_rankings.csv` header matches expected schema.
- [ ] Every `source_id` in raw rankings exists in `sources.yaml`.
- [ ] Every `canonical_id` in raw rankings exists in `models.yaml`.
- [ ] Normalized scores are between 0 and 100.
- [ ] Source weights are non-zero and explainable.
- [ ] Aggregated scores are reproducible.
- [ ] Markdown output is readable in terminal and article drafts.

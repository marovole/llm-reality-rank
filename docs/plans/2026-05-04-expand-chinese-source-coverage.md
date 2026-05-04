# Expand Source Coverage: Chinese Benchmarks (SuperCLUE / C-Eval / OpenCompass) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Triple `raw_rankings.csv` row count by adding three Chinese-language P0 benchmarks (SuperCLUE, C-Eval, OpenCompass) as fixture-mode ingestion targets, then publish a refreshed reviewed snapshot `2026-05-beta`.

**Architecture:** Extend the existing `TARGETS` registry in `scripts/llm-reality-rank/ingest_sources.py` with three new fixture-only entries. Each source gets (1) a TARGETS dict block, (2) a TDD pytest verifying canonicalized fixture parsing, (3) a committed canonical fixture file under `data/llm-reality-rank/fixtures/`, (4) appended rows in `raw_rankings.csv`. Then re-run validate → normalize → aggregate → export_reviewed_snapshot to produce snapshot `2026-05-beta` and refreshed static API JSON. Site build is verified at the end; no site code changes are expected because the leaderboard pages read snapshot JSON dynamically.

**Tech Stack:** Python 3 (pytest, stdlib only), existing pipeline scripts under `scripts/llm-reality-rank/`, Astro site build for verification.

**Pre-flight assumptions:**
- Working tree is clean and on `main` (or a dedicated worktree for this plan).
- `python3 -m pip install -r requirements.txt` already done.
- `npm --prefix site install` already done.
- The reviewer (you) will hand-verify each fixture against the public source URL on the day of execution and edit canonical IDs as needed before commit. Fixture rows below are **seed values** — adjust scores/dates if you find drift.

---

## Task 1: Register SuperCLUE TARGET (failing test first)

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py:44-127` (TARGETS dict)
- Modify: `tests/llm-reality-rank/test_ingest_sources.py:18-28` (CLI list test)

**Step 1: Add a failing test that asserts SuperCLUE appears in the CLI `list` output**

Append to `tests/llm-reality-rank/test_ingest_sources.py` (a new test, do not modify the existing `test_cli_list_exposes_first_batch_targets`):

```python
def test_cli_list_exposes_superclue_target(capsys):
    module = load_module()
    exit_code = module.main(["list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "superclue" in captured
    assert "SuperCLUE" in captured
```

**Step 2: Run the test to verify it fails**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_superclue_target -v`
Expected: `FAILED` with `assert "superclue" in captured` failing.

**Step 3: Add SuperCLUE entry to TARGETS dict**

Insert into the `TARGETS = { ... }` block in `scripts/llm-reality-rank/ingest_sources.py` (alphabetical order, after `lmarena` is fine):

```python
    "superclue": {
        "source_id": "superclue",
        "source_name": "SuperCLUE",
        "source_priority": "P0",
        "category_primary": "chinese",
        "metric_name": "superclue_total",
        "metric_type": "aggregate_score",
        "score_unit": "score",
        "score_higher_is_better": "true",
        "source_url": "https://superclueai.com/",
        "evaluation_independence": "platform_or_community",
        "source_trust": "high",
        "contamination_risk": "medium",
        "freshness_weight": "1.0",
    },
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_superclue_target -v`
Expected: `PASSED`

**Step 5: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): register SuperCLUE as fixture-mode target"
```

---

## Task 2: SuperCLUE fixture parsing test + canonical fixture file

**Files:**
- Create: `data/llm-reality-rank/fixtures/superclue-2026-05-03.json`
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (append new test)

**Step 1: Write a failing test for SuperCLUE fixture parsing**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_superclue_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "superclue.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "GPT-5.5",
                    "canonical_id": "openai/gpt-5.5@unknown",
                    "provider": "OpenAI",
                    "rank_raw": "1",
                    "score_raw": "82.4",
                    "date_published": "2026-04-15",
                    "date_observed": "2026-05-03",
                    "source_url": "https://superclueai.com/",
                    "notes": "canonicalization_status=canonicalized",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = module.ingest_target("superclue", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "superclue"
    assert row["category_primary"] == "chinese"
    assert row["metric_name"] == "superclue_total"
    assert row["model_name_raw"] == "GPT-5.5"
    assert row["canonical_id"] == "openai/gpt-5.5@unknown"
    assert row["score_raw"] == "82.4"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_superclue_fixture_parser_outputs_traceable_rows_without_network -v`
Expected: `PASSED` immediately (the generic `parse_structured_fixture` already handles new TARGETS entries). If it fails, inspect the error — the existing parser is generic and Task 1 should already be sufficient.

> If it passes on first run with no code change, that's expected and correct. Proceed.

**Step 3: Create canonical fixture file**

Write `data/llm-reality-rank/fixtures/superclue-2026-05-03.json` with reviewed rows. Use **the actual current SuperCLUE leaderboard at observation time**. Seed template (you must verify each row against `https://superclueai.com/` and edit before commit):

```json
[
  {
    "model_name_raw": "GPT-5.5",
    "canonical_id": "openai/gpt-5.5@unknown",
    "provider": "OpenAI",
    "rank_raw": "1",
    "score_raw": "82.4",
    "date_published": "2026-04-15",
    "date_observed": "2026-05-03",
    "source_url": "https://superclueai.com/",
    "notes": "Reviewed alpha seed observed from SuperCLUE public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "rank_raw": "2",
    "score_raw": "80.1",
    "date_published": "2026-04-15",
    "date_observed": "2026-05-03",
    "source_url": "https://superclueai.com/",
    "notes": "Reviewed alpha seed observed from SuperCLUE public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Gemini 3.1 Pro",
    "canonical_id": "google/gemini-3.1-pro@unknown",
    "provider": "Google",
    "rank_raw": "3",
    "score_raw": "78.9",
    "date_published": "2026-04-15",
    "date_observed": "2026-05-03",
    "source_url": "https://superclueai.com/",
    "notes": "Reviewed alpha seed observed from SuperCLUE public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3.5@unknown",
    "provider": "DeepSeek",
    "rank_raw": "4",
    "score_raw": "76.2",
    "date_published": "2026-04-15",
    "date_observed": "2026-05-03",
    "source_url": "https://superclueai.com/",
    "notes": "Reviewed alpha seed observed from SuperCLUE public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Qwen3-Max",
    "canonical_id": "alibaba/qwen3-max@unknown",
    "provider": "Alibaba",
    "rank_raw": "5",
    "score_raw": "74.8",
    "date_published": "2026-04-15",
    "date_observed": "2026-05-03",
    "source_url": "https://superclueai.com/",
    "notes": "Reviewed alpha seed observed from SuperCLUE public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 4: Verify each `canonical_id` exists in `data/llm-reality-rank/models.yaml`**

Run: `grep -E "openai/gpt-5.5|anthropic/claude-opus-4.7|google/gemini-3.1-pro|deepseek/deepseek-v3.5|alibaba/qwen3-max" data/llm-reality-rank/models.yaml`
Expected: Each canonical_id appears at least once. If any is missing, **stop and add the model to `models.yaml`** before continuing — the validator will reject unknown canonical IDs.

**Step 5: Smoke-test the fixture via the CLI**

Run:
```bash
python3 scripts/llm-reality-rank/ingest_sources.py ingest superclue \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/superclue-2026-05-03.json \
  --output-csv outputs/llm-reality-rank/ingested-superclue.csv
```
Expected: JSON output with `"status": "ok"`, 5 rows in `outputs/llm-reality-rank/ingested-superclue.csv`.

**Step 6: Commit**

```bash
git add data/llm-reality-rank/fixtures/superclue-2026-05-03.json tests/llm-reality-rank/test_ingest_sources.py
git commit -m "data(superclue): add reviewed alpha seed fixture"
```

---

## Task 3: Register C-Eval TARGET

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py` (TARGETS dict)
- Modify: `tests/llm-reality-rank/test_ingest_sources.py`

**Step 1: Add failing test**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_cli_list_exposes_ceval_target(capsys):
    module = load_module()
    module.main(["list"])
    captured = capsys.readouterr().out
    assert "ceval" in captured
    assert "C-Eval" in captured
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_ceval_target -v`
Expected: `FAILED`.

**Step 3: Add C-Eval entry to TARGETS dict**

Insert into `TARGETS = { ... }`:

```python
    "ceval": {
        "source_id": "ceval",
        "source_name": "C-Eval",
        "source_priority": "P0",
        "category_primary": "chinese",
        "metric_name": "ceval_overall",
        "metric_type": "benchmark_score",
        "score_unit": "percent_correct",
        "score_higher_is_better": "true",
        "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
        "evaluation_independence": "independent_third_party",
        "source_trust": "high",
        "contamination_risk": "medium",
        "freshness_weight": "0.8",
    },
```

> `freshness_weight: 0.8` because C-Eval refresh cadence is slower than SuperCLUE; reflects lower temporal confidence in the aggregator.

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_ceval_target -v`
Expected: `PASSED`.

**Step 5: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): register C-Eval as fixture-mode target"
```

---

## Task 4: C-Eval fixture parsing test + fixture file

**Files:**
- Create: `data/llm-reality-rank/fixtures/ceval-2026-05-03.json`
- Modify: `tests/llm-reality-rank/test_ingest_sources.py`

**Step 1: Write fixture-parser test**

Append:

```python
def test_ceval_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "ceval.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Qwen3-Max",
                    "canonical_id": "alibaba/qwen3-max@unknown",
                    "provider": "Alibaba",
                    "rank_raw": "1",
                    "score_raw": "89.7",
                    "date_published": "2026-03-20",
                    "date_observed": "2026-05-03",
                    "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
                    "notes": "canonicalization_status=canonicalized",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("ceval", mode="fixture", fixture_path=fixture)
    assert result.status == "ok"
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "ceval"
    assert row["category_primary"] == "chinese"
    assert row["metric_name"] == "ceval_overall"
    assert row["score_raw"] == "89.7"
```

**Step 2: Run — expected PASS** (generic parser handles it).

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_ceval_fixture_parser_outputs_traceable_rows_without_network -v`
Expected: `PASSED`.

**Step 3: Create canonical fixture file**

Write `data/llm-reality-rank/fixtures/ceval-2026-05-03.json` after verifying entries against `https://cevalbenchmark.com/static/leaderboard.html`. Seed (verify and edit):

```json
[
  {
    "model_name_raw": "Qwen3-Max",
    "canonical_id": "alibaba/qwen3-max@unknown",
    "provider": "Alibaba",
    "rank_raw": "1",
    "score_raw": "89.7",
    "date_published": "2026-03-20",
    "date_observed": "2026-05-03",
    "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
    "notes": "Reviewed alpha seed observed from C-Eval public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "GPT-5.5",
    "canonical_id": "openai/gpt-5.5@unknown",
    "provider": "OpenAI",
    "rank_raw": "2",
    "score_raw": "88.9",
    "date_published": "2026-03-20",
    "date_observed": "2026-05-03",
    "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
    "notes": "Reviewed alpha seed observed from C-Eval public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3.5@unknown",
    "provider": "DeepSeek",
    "rank_raw": "3",
    "score_raw": "87.3",
    "date_published": "2026-03-20",
    "date_observed": "2026-05-03",
    "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
    "notes": "Reviewed alpha seed observed from C-Eval public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "rank_raw": "4",
    "score_raw": "85.6",
    "date_published": "2026-03-20",
    "date_observed": "2026-05-03",
    "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
    "notes": "Reviewed alpha seed observed from C-Eval public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 4: Verify canonical_ids exist in models.yaml** (same procedure as Task 2 Step 4).

**Step 5: Smoke-test via CLI**

```bash
python3 scripts/llm-reality-rank/ingest_sources.py ingest ceval \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/ceval-2026-05-03.json \
  --output-csv outputs/llm-reality-rank/ingested-ceval.csv
```
Expected: 4 rows, `"status": "ok"`.

**Step 6: Commit**

```bash
git add data/llm-reality-rank/fixtures/ceval-2026-05-03.json tests/llm-reality-rank/test_ingest_sources.py
git commit -m "data(ceval): add reviewed alpha seed fixture"
```

---

## Task 5: Register OpenCompass TARGET

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py`
- Modify: `tests/llm-reality-rank/test_ingest_sources.py`

**Step 1: Add failing test**

Append:

```python
def test_cli_list_exposes_opencompass_target(capsys):
    module = load_module()
    module.main(["list"])
    captured = capsys.readouterr().out
    assert "opencompass" in captured
    assert "OpenCompass" in captured
```

**Step 2: Run — expected FAIL.**

`.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_opencompass_target -v`

**Step 3: Add OpenCompass to TARGETS**

```python
    "opencompass": {
        "source_id": "opencompass_llm",
        "source_name": "OpenCompass LLM Leaderboard",
        "source_priority": "P0",
        "category_primary": "chinese",
        "metric_name": "opencompass_overall",
        "metric_type": "aggregate_score",
        "score_unit": "score",
        "score_higher_is_better": "true",
        "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
        "evaluation_independence": "platform_or_community",
        "source_trust": "high",
        "contamination_risk": "medium",
        "freshness_weight": "0.9",
    },
```

**Step 4: Run — expected PASS.**

**Step 5: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): register OpenCompass as fixture-mode target"
```

---

## Task 6: OpenCompass fixture parsing test + fixture file

**Files:**
- Create: `data/llm-reality-rank/fixtures/opencompass-2026-05-03.json`
- Modify: `tests/llm-reality-rank/test_ingest_sources.py`

**Step 1: Append parser test**

```python
def test_opencompass_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "opencompass.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "DeepSeek V3.5",
                    "canonical_id": "deepseek/deepseek-v3.5@unknown",
                    "provider": "DeepSeek",
                    "rank_raw": "1",
                    "score_raw": "75.6",
                    "date_published": "2026-04-01",
                    "date_observed": "2026-05-03",
                    "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
                    "notes": "canonicalization_status=canonicalized",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("opencompass", mode="fixture", fixture_path=fixture)
    assert result.status == "ok"
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "opencompass_llm"
    assert row["category_primary"] == "chinese"
```

**Step 2: Run — expected PASS.**

**Step 3: Create canonical fixture**

Write `data/llm-reality-rank/fixtures/opencompass-2026-05-03.json` after verifying against the source. Seed:

```json
[
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3.5@unknown",
    "provider": "DeepSeek",
    "rank_raw": "1",
    "score_raw": "75.6",
    "date_published": "2026-04-01",
    "date_observed": "2026-05-03",
    "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
    "notes": "Reviewed alpha seed observed from OpenCompass public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Qwen3-Max",
    "canonical_id": "alibaba/qwen3-max@unknown",
    "provider": "Alibaba",
    "rank_raw": "2",
    "score_raw": "74.2",
    "date_published": "2026-04-01",
    "date_observed": "2026-05-03",
    "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
    "notes": "Reviewed alpha seed observed from OpenCompass public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "GPT-5.5",
    "canonical_id": "openai/gpt-5.5@unknown",
    "provider": "OpenAI",
    "rank_raw": "3",
    "score_raw": "73.5",
    "date_published": "2026-04-01",
    "date_observed": "2026-05-03",
    "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
    "notes": "Reviewed alpha seed observed from OpenCompass public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "rank_raw": "4",
    "score_raw": "72.1",
    "date_published": "2026-04-01",
    "date_observed": "2026-05-03",
    "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
    "notes": "Reviewed alpha seed observed from OpenCompass public leaderboard on 2026-05-03; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 4: Verify canonical_ids in models.yaml.**

**Step 5: Smoke-test via CLI** (analogous command).

**Step 6: Commit**

```bash
git add data/llm-reality-rank/fixtures/opencompass-2026-05-03.json tests/llm-reality-rank/test_ingest_sources.py
git commit -m "data(opencompass): add reviewed alpha seed fixture"
```

---

## Task 7: Append produced rows into raw_rankings.csv

**Files:**
- Modify: `data/llm-reality-rank/raw_rankings.csv`

**Step 1: Concatenate the three ingested CSVs into raw_rankings.csv**

Run:

```bash
python3 -c "
import csv
from pathlib import Path

raw = Path('data/llm-reality-rank/raw_rankings.csv')
with raw.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    existing = list(reader)

new_rows = []
for src in ['superclue', 'ceval', 'opencompass']:
    p = Path(f'outputs/llm-reality-rank/ingested-{src}.csv')
    with p.open('r', encoding='utf-8') as f:
        new_rows.extend(list(csv.DictReader(f)))

with raw.open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(existing + new_rows)

print(f'wrote {len(existing) + len(new_rows)} total rows')
"
```

Expected output: `wrote 24 total rows` (11 existing + 13 new).

**Step 2: Verify validate_data passes**

Run: `python3 scripts/llm-reality-rank/validate_data.py`
Expected: exit code 0, no errors. If validator complains about unknown canonical IDs, **stop** and add the missing models to `data/llm-reality-rank/models.yaml`, then re-run.

**Step 3: Commit**

```bash
git add data/llm-reality-rank/raw_rankings.csv
git commit -m "data: append SuperCLUE / C-Eval / OpenCompass alpha seed rows"
```

---

## Task 8: Re-run scoring pipeline

**Files:**
- Modify (auto-generated): `outputs/llm-reality-rank/normalized_scores.csv`, `model_scores.csv`, `model_scores.md`, `first-draft-leaderboard.md`

**Step 1: Run normalization**

Run: `python3 scripts/llm-reality-rank/normalize_scores.py`
Expected: writes `outputs/llm-reality-rank/normalized_scores.csv` with rows for all 24 raw rankings.

**Step 2: Run aggregation**

Run: `python3 scripts/llm-reality-rank/aggregate_scores.py`
Expected: writes `outputs/llm-reality-rank/model_scores.csv`, `model_scores.md`, `first-draft-leaderboard.md`. Inspect the new leaderboard and confirm Chinese benchmark columns now appear.

**Step 3: Spot-check the markdown leaderboard**

Read: `outputs/llm-reality-rank/first-draft-leaderboard.md`
Expected: includes a Chinese-category column, models like Qwen3-Max and DeepSeek V3.5 appear with non-empty scores.

> No commit yet — these outputs are gitignored. Snapshot promotion happens in Task 9.

---

## Task 9: Promote new reviewed snapshot 2026-05-beta

**Files:**
- Create: `snapshots/llm-reality-rank/2026-05-beta/*.json`
- Modify: `outputs/llm-reality-rank/api/v1/*.json` (gets re-copied into site at build)
- Modify: `site/public/api/v1/*.json` (refreshed by build)

**Step 1: Run snapshot exporter**

Run: `python3 scripts/llm-reality-rank/export_reviewed_snapshot.py --snapshot-id 2026-05-beta`
Expected: `snapshots/llm-reality-rank/2026-05-beta/` populated with leaderboard.json, models.json, scores.json, scenarios.json, source-evidence.json, sources.json, snapshots.json, manifest.json, selector-data.json. Also refreshes `outputs/llm-reality-rank/api/v1/*.json`.

**Step 2: Spot-check snapshot leaderboard**

Run: `python3 -c "import json; d=json.load(open('snapshots/llm-reality-rank/2026-05-beta/leaderboard.json')); print('snapshot_id:', d.get('snapshot_id')); rows = d.get('rows') or d.get('entries') or d.get('models') or []; print('rows:', len(rows))"`
Expected: snapshot_id `2026-05-beta`, rows count > 0. **If rows == 0, this is the latent bug from `2026-05-alpha` — do not proceed; investigate `export_reviewed_snapshot.py` first.**

**Step 3: Run pytest full suite**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank -q`
Expected: all green.

**Step 4: Commit**

```bash
git add snapshots/llm-reality-rank/2026-05-beta/ outputs/llm-reality-rank/api/v1/
git commit -m "feat: publish reviewed alpha snapshot 2026-05-beta with Chinese benchmarks"
```

---

## Task 10: Verify site build still passes

**Files:**
- Modify (auto): `site/public/api/v1/*.json`

**Step 1: Build the site**

Run: `npm --prefix site run build`
Expected: success. The pre-build script copies `outputs/llm-reality-rank/api/v1/` into `site/public/api/v1/`.

**Step 2: Run site checks**

Run: `npm --prefix site test && npm --prefix site run check`
Expected: both pass. If a content/interaction test references the old snapshot ID `2026-05-alpha`, update it.

**Step 3: Spot-check rendered pages locally**

Run: `npm --prefix site run preview` (in background or new terminal). Open `http://localhost:4321/leaderboard/` and `http://localhost:4321/leaderboard/chinese/` (if scenario route supports it). Confirm Chinese-category models render.

**Step 4: Commit any site config or test updates**

```bash
git add site/
git commit -m "test(site): refresh checks against 2026-05-beta snapshot"
```

> If no site changes were needed, skip this commit.

---

## Task 11: Update README and methodology article

**Files:**
- Modify: `README.md`
- Modify or create: `docs/public-methodology-article-2026-05-beta.md`

**Step 1: Update README data scope claim**

In `README.md`, find the "当前状态" section and update the snapshot reference:

```diff
- - reviewed alpha snapshot：`snapshots/llm-reality-rank/2026-05-alpha/`
+ - reviewed alpha snapshots：`snapshots/llm-reality-rank/2026-05-alpha/` 与 `2026-05-beta/`
+   （beta 加入 SuperCLUE / C-Eval / OpenCompass 中文基准）
```

In the "Alpha 数据 caveats" section, update the snapshot id reference accordingly.

**Step 2: Regenerate methodology article**

Run: `python3 scripts/llm-reality-rank/export_article_assets.py --snapshot-id 2026-05-beta`
Expected: writes `docs/public-methodology-article-2026-05-beta.md` and tables under `outputs/llm-reality-rank/article-exports/2026-05-beta/`.

**Step 3: Commit**

```bash
git add README.md docs/public-methodology-article-2026-05-beta.md
git commit -m "docs: update README and methodology article for 2026-05-beta snapshot"
```

---

## Task 12: End-to-end verification

**Step 1: Clean run of the full validation chain**

Run in order:
```bash
python3 scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
npm --prefix site test
npm --prefix site run check
npm --prefix site run build
```
Expected: all pass.

**Step 2: Confirm git status is clean**

Run: `git status`
Expected: nothing to commit.

**Step 3: Push branch (only if working in a worktree/branch, not main)**

```bash
git push -u origin <branch-name>
```

> Plan complete. The next sprint candidate is publishing to Cloudflare Pages (P1), or adding MMMU + Berkeley Function Calling for the multimodal/agent dimension.

---

## Risks & guardrails

- **Canonical-ID drift:** Fixture rows reference canonical IDs that must exist in `models.yaml`. Always run `validate_data.py` after editing fixtures; do not commit until it's green.
- **Score drift between observation and commit:** Each fixture is dated `date_observed: 2026-05-03`. If the actual observation is done on a different day, **edit the fixture file's `date_observed` field across all rows** before commit. Notes strings should match.
- **Latent snapshot bug:** Task 9 Step 2 explicitly checks for the `rows: 0` issue spotted in the existing `2026-05-alpha`. If that bug is reproduced in beta, halt and root-cause `export_reviewed_snapshot.py` before continuing.
- **Source HTML changes:** This plan deliberately stays in fixture mode. Live-safe parser commitments are out of scope here and should be a separate plan.
- **Don't ingest unverified data:** If you cannot manually confirm a row from the public source on the day of execution, omit that row rather than guess.

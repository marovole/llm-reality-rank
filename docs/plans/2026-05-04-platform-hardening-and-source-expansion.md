# Platform Hardening & Source Expansion Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the five highest-ROI gaps identified in the 2026-05-beta status review — version-track plans, harden CI to cover the site, triple English-language P0 source coverage (LMArena / HF Open LLM / LiveCodeBench), expand Practicality with Artificial Analysis price/speed/context, and break out of fixture-only mode by shipping a real live-safe parser for LiveBench — culminating in a `2026-05-gamma` reviewed snapshot.

**Architecture:** Five sequential workstreams, all following the existing `validate → normalize → aggregate → export_reviewed_snapshot → export_article_assets` pipeline. New sources are added as fixture-mode `TARGETS` entries (the proven pattern from `docs/plans/2026-05-04-expand-chinese-source-coverage.md`); the LiveBench live-safe parser extends `ingest_sources.py` with one CSV-aware code path that promotes the existing `manual_required` fallback to a real ingestion. CI gains a Node job that runs site tests + astro check + build behind the existing Python validate+pytest job. No site source code changes are expected — leaderboard pages already read snapshot JSON dynamically.

**Tech Stack:** Python 3.12 (pytest, stdlib only), existing scripts under `scripts/llm-reality-rank/`, Astro 5.18 + Node 22 site build, GitHub Actions CI.

**Pre-flight assumptions:**
- Working tree is clean and on `main` (or a dedicated worktree for this plan).
- `python3 -m pip install -r requirements.txt` already done; `.venv/bin/python` available.
- `npm --prefix site install` already done.
- The reviewer (you) will hand-verify each fixture against the public source URL on the day of execution and edit canonical IDs/scores as needed before commit. Fixture rows below are **seed values** — adjust scores/dates if you find drift.
- Today's date is 2026-05-04. All `date_observed` values default to that.

---

## Workstream A — Housekeeping & CI Hardening

### Task A1: Track the planning directory in git

**Files:**
- Create: `docs/plans/.gitkeep` (only if `docs/plans/` would otherwise be empty after this commit)
- Tracked-by-this-commit: `docs/plans/2026-05-04-expand-chinese-source-coverage.md` and `docs/plans/2026-05-04-platform-hardening-and-source-expansion.md`

**Step 1: Verify the current untracked state**

Run: `git status --short docs/plans/`
Expected output includes the two `.md` files as `??` (untracked).

**Step 2: Stage and commit the plans**

```bash
git add docs/plans/2026-05-04-expand-chinese-source-coverage.md docs/plans/2026-05-04-platform-hardening-and-source-expansion.md
git commit -m "docs(plans): track Chinese-source expansion + platform-hardening plans"
```

**Step 3: Verify**

Run: `git status --short docs/plans/`
Expected: empty output (no untracked plan files).

---

### Task A2: Add a failing CI test that asserts a Node job runs site checks

**Files:**
- Create: `tests/llm-reality-rank/test_ci_workflow.py`

**Step 1: Write the failing test**

Create `tests/llm-reality-rank/test_ci_workflow.py`:

```python
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def read_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_workflow_runs_site_tests_and_build():
    text = read_workflow()
    assert "npm --prefix site install" in text or "npm ci --prefix site" in text or "working-directory: site" in text, (
        "CI must install site npm dependencies"
    )
    assert "npm --prefix site test" in text or re.search(r"working-directory: site\s+run: npm test", text), (
        "CI must run site tests (npm --prefix site test)"
    )
    assert "npm --prefix site run check" in text or re.search(r"working-directory: site\s+run: npm run check", text), (
        "CI must run astro check (npm --prefix site run check)"
    )
    assert "npm --prefix site run build" in text or re.search(r"working-directory: site\s+run: npm run build", text), (
        "CI must run site build (npm --prefix site run build)"
    )


def test_workflow_uses_supported_node_version():
    text = read_workflow()
    assert "actions/setup-node@" in text, "CI must use actions/setup-node"
    match = re.search(r"node-version:\s*['\"]?(\d+)", text)
    assert match, "CI must pin a node-version"
    major = int(match.group(1))
    assert major >= 22, f"site/package.json requires Node >=20.3 <21 || >=22; got {major}"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ci_workflow.py -v`
Expected: 2 FAILED (assertions about site test/check/build/setup-node missing).

**Step 3: Commit the failing test**

```bash
git add tests/llm-reality-rank/test_ci_workflow.py
git commit -m "test(ci): add failing assertion that CI runs site test/check/build"
```

---

### Task A3: Extend CI workflow to run site tests, astro check, and build

**Files:**
- Modify: `.github/workflows/ci.yml`

**Step 1: Replace the workflow with the extended version**

Overwrite `.github/workflows/ci.yml` with:

```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  validate-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Python dependencies
        run: python -m pip install -r requirements.txt

      - name: Validate data
        run: python scripts/llm-reality-rank/validate_data.py

      - name: Run Python tests
        run: python -m pytest tests/llm-reality-rank -q

  site:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '22'

      - name: Install site dependencies
        run: npm --prefix site ci

      - name: Run site content/behavior checks
        run: npm --prefix site test

      - name: Run astro check
        run: npm --prefix site run check

      - name: Build site
        run: npm --prefix site run build
```

**Step 2: Run the test to verify it now passes**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ci_workflow.py -v`
Expected: 2 PASSED.

**Step 3: Run the full Python test suite to confirm no regressions**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank -q`
Expected: all green.

**Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add site job for npm test, astro check, and build on Node 22"
```

---

## Workstream B — English-Language P0 Source Expansion

> Each task in this workstream follows the same TDD-driven pattern that produced the `2026-05-beta` snapshot:
> 1. CLI list test → register `TARGETS` entry → fixture parser test → commit fixture file → append rows to `raw_rankings.csv`.
>
> Reference shape: `data/llm-reality-rank/fixtures/superclue-2026-05-03.json` and the matching test in `tests/llm-reality-rank/test_ingest_sources.py` (`test_superclue_fixture_parser_outputs_traceable_rows_without_network`).

### Task B1: Unblock LMArena fixture-mode ingestion (failing test first)

LMArena is already in `TARGETS` but `parse_structured_fixture` (`scripts/llm-reality-rank/ingest_sources.py:325-330`) short-circuits to `manual_required` for the `lmarena` target. The existing test `test_lmarena_fixture_fails_closed_to_manual_required_status` enforces that. We will narrow the safety wall: pickle fixtures stay rejected (already covered by `test_lmarena_pickle_fixture_fails_closed_without_execution`), but a hand-curated JSON fixture is allowed.

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py:324-330`
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (rewrite `test_lmarena_fixture_fails_closed_to_manual_required_status`)
- Add: a new test that asserts a JSON fixture parses successfully

**Step 1: Add a failing test for the JSON-fixture happy path**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_lmarena_json_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "lmarena.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "GPT-5.5",
                    "canonical_id": "openai/gpt-5.5-high@unknown",
                    "provider": "OpenAI",
                    "rank_raw": "1",
                    "score_raw": "1502",
                    "date_published": "2026-05-01",
                    "date_observed": "2026-05-04",
                    "source_url": "https://lmarena.ai/leaderboard/",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("lmarena", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    assert result.used_network is False
    assert len(result.rows) == 1
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "lmarena_chatbot_arena"
    assert row["score_raw"] == "1502"
```

Make sure `import json` is already at the top of the test file (it is — verify with `head -5 tests/llm-reality-rank/test_ingest_sources.py`).

**Step 2: Update the existing pickle-fail-closed test to keep its scope on pickle only**

Find `test_lmarena_fixture_fails_closed_to_manual_required_status` in `tests/llm-reality-rank/test_ingest_sources.py` and rename + retarget it:

```python
def test_lmarena_csv_fixture_still_requires_manual_review(tmp_path):
    """LMArena CSV fixtures stay manual_required because Elo provenance must be hand-verified.

    JSON fixtures are allowed (see test_lmarena_json_fixture_parser_*) because they require
    explicit per-field curation, but CSV passthrough remains gated.
    """
    module = load_module()
    fixture_path = tmp_path / "lmarena.csv"
    fixture_path.write_text("model_name_raw,canonical_id,score_raw\nGPT-5.5,openai/gpt-5.5-high@unknown,1502\n", encoding="utf-8")
    result = module.ingest_target("lmarena", mode="fixture", fixture_path=fixture_path)
    assert result.status == "manual_required"
    assert result.used_network is False
```

(`test_lmarena_pickle_fixture_fails_closed_without_execution` is left untouched — pickle stays rejected.)

**Step 3: Run tests to verify the new test fails and the others still pass**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py -v -k lmarena`
Expected: `test_lmarena_json_fixture_parser_*` FAILS; pickle test PASSES; CSV test PASSES (current code already returns manual_required for any LMArena fixture).

**Step 4: Modify `parse_structured_fixture` to allow JSON LMArena fixtures**

In `scripts/llm-reality-rank/ingest_sources.py:324-330`, replace:

```python
def parse_structured_fixture(target: str, fixture_path: Path) -> IngestionResult:
    if target == "lmarena":
        return manual_required(
            target,
            "LMArena fixture ingestion is manual_required: safe structured parser is not configured and unsafe pickle/anti-bot paths are prohibited.",
            used_network=False,
        )
```

with:

```python
def parse_structured_fixture(target: str, fixture_path: Path) -> IngestionResult:
    if target == "lmarena" and fixture_path.suffix.lower() != ".json":
        return manual_required(
            target,
            "LMArena fixture ingestion accepts only hand-curated JSON fixtures; CSV/pickle paths require manual review.",
            used_network=False,
        )
```

**Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py -v -k lmarena`
Expected: all 3 lmarena tests PASS.

**Step 6: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): allow hand-curated JSON fixtures for LMArena"
```

---

### Task B2: Commit the LMArena fixture file

**Files:**
- Create: `data/llm-reality-rank/fixtures/lmarena-2026-05-04.json`

**Step 1: Hand-verify the LMArena leaderboard against `https://lmarena.ai/leaderboard/`**

Manually open the URL. Record top 6 models by Arena Elo. Update the seed values below if drift is found.

**Step 2: Write the fixture**

Create `data/llm-reality-rank/fixtures/lmarena-2026-05-04.json`:

```json
[
  {
    "model_name_raw": "GPT-5.5 (high)",
    "canonical_id": "openai/gpt-5.5-high@unknown",
    "provider": "OpenAI",
    "rank_raw": "1",
    "score_raw": "1502",
    "date_published": "2026-05-01",
    "date_observed": "2026-05-04",
    "source_url": "https://lmarena.ai/leaderboard/",
    "notes": "Reviewed alpha seed observed from LMArena public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "rank_raw": "2",
    "score_raw": "1488",
    "date_published": "2026-05-01",
    "date_observed": "2026-05-04",
    "source_url": "https://lmarena.ai/leaderboard/",
    "notes": "Reviewed alpha seed observed from LMArena public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Gemini 3.1 Pro Preview",
    "canonical_id": "google/gemini-3.1-pro-preview@unknown",
    "provider": "Google",
    "rank_raw": "3",
    "score_raw": "1481",
    "date_published": "2026-05-01",
    "date_observed": "2026-05-04",
    "source_url": "https://lmarena.ai/leaderboard/",
    "notes": "Reviewed alpha seed observed from LMArena public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3@2025-03-24",
    "provider": "DeepSeek",
    "rank_raw": "4",
    "score_raw": "1462",
    "date_published": "2026-05-01",
    "date_observed": "2026-05-04",
    "source_url": "https://lmarena.ai/leaderboard/",
    "notes": "Reviewed alpha seed observed from LMArena public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Qwen3-Max",
    "canonical_id": "qwen/qwen3-max@unknown",
    "provider": "Alibaba",
    "rank_raw": "5",
    "score_raw": "1444",
    "date_published": "2026-05-01",
    "date_observed": "2026-05-04",
    "source_url": "https://lmarena.ai/leaderboard/",
    "notes": "Reviewed alpha seed observed from LMArena public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 3: Smoke-test the fixture path**

Run:
```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest lmarena --mode fixture --fixture data/llm-reality-rank/fixtures/lmarena-2026-05-04.json
```
Expected: JSON output with `"status": "ok"`, `"row_count": 5`, all `canonical_id` present.

**Step 4: Commit**

```bash
git add data/llm-reality-rank/fixtures/lmarena-2026-05-04.json
git commit -m "data(lmarena): add reviewed alpha seed fixture"
```

---

### Task B3: Append LMArena rows to `raw_rankings.csv`

**Files:**
- Modify: `data/llm-reality-rank/raw_rankings.csv` (append)

**Step 1: Generate the rows via the ingest CLI**

Run:
```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest lmarena \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/lmarena-2026-05-04.json \
  --output-csv outputs/llm-reality-rank/ingested-lmarena.csv
```
Expected: prints `"status": "ok"`; writes 5 rows to the output CSV.

**Step 2: Append the data rows (skip the header) to `raw_rankings.csv`**

Run:
```bash
tail -n +2 outputs/llm-reality-rank/ingested-lmarena.csv >> data/llm-reality-rank/raw_rankings.csv
```

**Step 3: Validate**

Run: `.venv/bin/python scripts/llm-reality-rank/validate_data.py`
Expected: `VALIDATION PASSED`.

Run: `.venv/bin/python -m pytest tests/llm-reality-rank -q`
Expected: all green.

**Step 4: Commit**

```bash
git add data/llm-reality-rank/raw_rankings.csv
git commit -m "data(lmarena): append reviewed alpha seed rows"
```

---

### Task B4: Register HF Open LLM Leaderboard as a fixture-mode target (failing test first)

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py` (TARGETS dict, alphabetical position after `artificial_analysis`)
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (add CLI list test)

**Step 1: Add a failing CLI list test**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_cli_list_exposes_hf_open_llm_target(capsys):
    module = load_module()
    exit_code = module.main(["list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "hf_open_llm" in captured
    assert "Hugging Face" in captured
```

**Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_hf_open_llm_target -v`
Expected: FAILED.

**Step 3: Add the TARGETS entry**

Insert into the `TARGETS = { ... }` block in `scripts/llm-reality-rank/ingest_sources.py` (after the `artificial_analysis` entry, before `lmarena`):

```python
    "hf_open_llm": {
        "source_id": "hf_open_llm_leaderboard",
        "source_name": "Hugging Face Open LLM Leaderboard",
        "source_priority": "P0",
        "category_primary": "general",
        "metric_name": "open_llm_average",
        "metric_type": "benchmark_aggregate",
        "score_unit": "score",
        "score_higher_is_better": "true",
        "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
        "evaluation_independence": "platform_or_community",
        "source_trust": "high",
        "contamination_risk": "medium",
        "freshness_weight": "0.9",
    },
```

**Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py -v -k hf_open_llm`
Expected: PASSED.

**Step 5: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): register Hugging Face Open LLM Leaderboard as fixture-mode target"
```

---

### Task B5: HF Open LLM fixture parser test + canonical fixture file

**Files:**
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (add fixture parser test)
- Create: `data/llm-reality-rank/fixtures/hf-open-llm-2026-05-04.json`

**Step 1: Add a failing fixture parser test**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_hf_open_llm_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "hf-open-llm.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Qwen3-Max",
                    "canonical_id": "qwen/qwen3-max@unknown",
                    "provider": "Alibaba",
                    "rank_raw": "1",
                    "score_raw": "78.4",
                    "date_published": "2026-04-20",
                    "date_observed": "2026-05-04",
                    "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("hf_open_llm", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "hf_open_llm_leaderboard"
    assert row["score_raw"] == "78.4"
```

**Step 2: Run to verify pass (the parser is generic — it should already work)**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_hf_open_llm_fixture_parser_outputs_traceable_rows_without_network -v`
Expected: PASSED.

**Step 3: Hand-verify scores against the public leaderboard, then create the canonical fixture**

Open `https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard` and record top entries. Update seed values if needed.

Create `data/llm-reality-rank/fixtures/hf-open-llm-2026-05-04.json`:

```json
[
  {
    "model_name_raw": "Qwen3-Max",
    "canonical_id": "qwen/qwen3-max@unknown",
    "provider": "Alibaba",
    "rank_raw": "1",
    "score_raw": "78.4",
    "date_published": "2026-04-20",
    "date_observed": "2026-05-04",
    "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
    "notes": "Reviewed alpha seed observed from HF Open LLM Leaderboard public space on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3@2025-03-24",
    "provider": "DeepSeek",
    "rank_raw": "2",
    "score_raw": "76.1",
    "date_published": "2026-04-20",
    "date_observed": "2026-05-04",
    "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
    "notes": "Reviewed alpha seed observed from HF Open LLM Leaderboard public space on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Llama 4 Maverick",
    "canonical_id": "meta/llama-4-maverick@unknown",
    "provider": "Meta",
    "rank_raw": "3",
    "score_raw": "73.8",
    "date_published": "2026-04-20",
    "date_observed": "2026-05-04",
    "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
    "notes": "Reviewed alpha seed observed from HF Open LLM Leaderboard public space on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Mistral Large 3",
    "canonical_id": "mistral/mistral-large-3@unknown",
    "provider": "Mistral",
    "rank_raw": "4",
    "score_raw": "70.2",
    "date_published": "2026-04-20",
    "date_observed": "2026-05-04",
    "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
    "notes": "Reviewed alpha seed observed from HF Open LLM Leaderboard public space on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 4: Smoke-test and commit**

```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest hf_open_llm \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/hf-open-llm-2026-05-04.json
```
Expected: `"status": "ok"`, `"row_count": 4`.

```bash
git add data/llm-reality-rank/fixtures/hf-open-llm-2026-05-04.json tests/llm-reality-rank/test_ingest_sources.py
git commit -m "data(hf_open_llm): add reviewed alpha seed fixture and parser test"
```

---

### Task B6: Append HF Open LLM rows to `raw_rankings.csv`

**Files:**
- Modify: `data/llm-reality-rank/raw_rankings.csv` (append)

**Step 1-4: Same shape as Task B3, substituting `hf_open_llm` and the HF fixture path.**

```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest hf_open_llm \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/hf-open-llm-2026-05-04.json \
  --output-csv outputs/llm-reality-rank/ingested-hf-open-llm.csv
tail -n +2 outputs/llm-reality-rank/ingested-hf-open-llm.csv >> data/llm-reality-rank/raw_rankings.csv
.venv/bin/python scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
```

Expected: validation passes, all tests green.

```bash
git add data/llm-reality-rank/raw_rankings.csv
git commit -m "data(hf_open_llm): append reviewed alpha seed rows"
```

---

### Task B7: Register LiveCodeBench as a fixture-mode target (failing test first)

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py` (TARGETS dict, after `livebench`)
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (add CLI list test)

**Step 1: Add a failing CLI list test**

```python
def test_cli_list_exposes_livecodebench_target(capsys):
    module = load_module()
    exit_code = module.main(["list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "livecodebench" in captured
    assert "LiveCodeBench" in captured
```

**Step 2: Verify failure**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_cli_list_exposes_livecodebench_target -v`
Expected: FAILED.

**Step 3: Add TARGETS entry**

```python
    "livecodebench": {
        "source_id": "livecodebench",
        "source_name": "LiveCodeBench",
        "source_priority": "P0",
        "category_primary": "coding",
        "metric_name": "lcb_pass1",
        "metric_type": "pass_rate",
        "score_unit": "percent",
        "score_higher_is_better": "true",
        "source_url": "https://livecodebench.github.io/leaderboard.html",
        "evaluation_independence": "independent_third_party",
        "source_trust": "high",
        "contamination_risk": "low",
        "freshness_weight": "1.0",
    },
```

**Step 4: Run, then commit**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py -v -k livecodebench`
Expected: PASSED.

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): register LiveCodeBench as fixture-mode target"
```

---

### Task B8: LiveCodeBench fixture + raw rows

**Files:**
- Create: `data/llm-reality-rank/fixtures/livecodebench-2026-05-04.json`
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (parser test)
- Modify: `data/llm-reality-rank/raw_rankings.csv` (append)

**Step 1: Add a parser test mirroring B5's HF test**

```python
def test_livecodebench_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "livecodebench.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Claude Opus 4.7",
                    "canonical_id": "anthropic/claude-opus-4.7@unknown",
                    "provider": "Anthropic",
                    "rank_raw": "1",
                    "score_raw": "84.2",
                    "date_published": "2026-04-25",
                    "date_observed": "2026-05-04",
                    "source_url": "https://livecodebench.github.io/leaderboard.html",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("livecodebench", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "livecodebench"
    assert row["score_raw"] == "84.2"
```

Run: expected PASS (generic parser).

**Step 2: Hand-verify against `https://livecodebench.github.io/leaderboard.html`, then create the fixture**

Create `data/llm-reality-rank/fixtures/livecodebench-2026-05-04.json`:

```json
[
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "rank_raw": "1",
    "score_raw": "84.2",
    "date_published": "2026-04-25",
    "date_observed": "2026-05-04",
    "source_url": "https://livecodebench.github.io/leaderboard.html",
    "notes": "Reviewed alpha seed observed from LiveCodeBench public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "GPT-5.5 (high)",
    "canonical_id": "openai/gpt-5.5-high@unknown",
    "provider": "OpenAI",
    "rank_raw": "2",
    "score_raw": "82.7",
    "date_published": "2026-04-25",
    "date_observed": "2026-05-04",
    "source_url": "https://livecodebench.github.io/leaderboard.html",
    "notes": "Reviewed alpha seed observed from LiveCodeBench public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Gemini 3.1 Pro Preview",
    "canonical_id": "google/gemini-3.1-pro-preview@unknown",
    "provider": "Google",
    "rank_raw": "3",
    "score_raw": "79.4",
    "date_published": "2026-04-25",
    "date_observed": "2026-05-04",
    "source_url": "https://livecodebench.github.io/leaderboard.html",
    "notes": "Reviewed alpha seed observed from LiveCodeBench public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3@2025-03-24",
    "provider": "DeepSeek",
    "rank_raw": "4",
    "score_raw": "76.1",
    "date_published": "2026-04-25",
    "date_observed": "2026-05-04",
    "source_url": "https://livecodebench.github.io/leaderboard.html",
    "notes": "Reviewed alpha seed observed from LiveCodeBench public leaderboard on 2026-05-04; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 3: Append to raw rankings**

```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest livecodebench \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/livecodebench-2026-05-04.json \
  --output-csv outputs/llm-reality-rank/ingested-livecodebench.csv
tail -n +2 outputs/llm-reality-rank/ingested-livecodebench.csv >> data/llm-reality-rank/raw_rankings.csv
.venv/bin/python scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
```

Expected: green throughout.

**Step 4: Commit**

```bash
git add data/llm-reality-rank/fixtures/livecodebench-2026-05-04.json tests/llm-reality-rank/test_ingest_sources.py data/llm-reality-rank/raw_rankings.csv
git commit -m "data(livecodebench): add reviewed alpha seed fixture, parser test, and rows"
```

---

## Workstream C — Practicality Coverage via Artificial Analysis Multi-Metric Ingestion

> Currently `artificial_analysis` only contributes `intelligence_index`. Artificial Analysis publishes `price`, `latency`, `speed`, and `context` series too — these are exactly the lower-is-better / higher-is-better dimensions the normalize step already handles. Each becomes its own `metric_name`, sharing the same `source_id` and the existing `category_primary: practical`. We will ingest them via fixture rows in a single new fixture file with explicit `metric_name` / `metric_type` overrides per row.

### Task C1: Confirm fixture parser respects per-row `metric_name` overrides

**Files:**
- Modify: `tests/llm-reality-rank/test_ingest_sources.py` (new test)

**Step 1: Add a test asserting per-row metric_name overrides flow through**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_fixture_per_row_metric_name_overrides_target_default(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "aa-multi.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "GPT-5.5",
                    "canonical_id": "openai/gpt-5.5-high@unknown",
                    "provider": "OpenAI",
                    "score_raw": "0.50",
                    "metric_name": "aa_price_per_million_tokens_blended",
                    "metric_type": "price",
                    "score_higher_is_better": "false",
                    "source_url": "https://artificialanalysis.ai/leaderboards/models",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("artificial_analysis", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    [row] = result.rows
    assert row["metric_name"] == "aa_price_per_million_tokens_blended"
    assert row["metric_type"] == "price"
    assert row["score_higher_is_better"] == "false"
```

**Step 2: Run to check current behaviour**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_fixture_per_row_metric_name_overrides_target_default -v`

If FAIL: `proposed_row` only honours fields in `RAW_ROW_FIELDS` from `meta` (TARGETS) and from `fixture_value` aliases. `metric_name` and `metric_type` are not in `FIELD_ALIASES`, so the per-row override is dropped. Proceed to Step 3 to fix.

If PASS: skip to Step 5 (commit).

**Step 3: Extend `proposed_row` to honour per-row metric overrides**

In `scripts/llm-reality-rank/ingest_sources.py`, modify `proposed_row` (around line 299-321). Add the override block before `return row`:

```python
    for override_field in ("metric_name", "metric_type", "score_higher_is_better", "score_unit", "category_primary"):
        override_value = fixture_value(fixture_row, override_field)
        if not override_value and isinstance(fixture_row.get(override_field), str):
            override_value = str(fixture_row[override_field]).strip()
        if override_value:
            row[override_field] = override_value
```

Also update `FIELD_ALIASES` to recognise these new aliases — find the dict (line 167-200) and add:

```python
    "metric_name": ["metric_name", "Metric Name"],
    "metric_type": ["metric_type", "Metric Type"],
    "score_higher_is_better": ["score_higher_is_better"],
    "score_unit": ["score_unit", "unit"],
    "category_primary": ["category_primary"],
```

**Step 4: Re-run the test**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_fixture_per_row_metric_name_overrides_target_default -v`
Expected: PASSED.

Run the full suite: `.venv/bin/python -m pytest tests/llm-reality-rank -q`
Expected: all green.

**Step 5: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py tests/llm-reality-rank/test_ingest_sources.py
git commit -m "feat(ingest): allow per-row metric_name/metric_type overrides in fixtures"
```

---

### Task C2: Commit Artificial Analysis price/speed/context fixture and append rows

**Files:**
- Create: `data/llm-reality-rank/fixtures/artificial-analysis-practicality-2026-05-04.json`
- Modify: `data/llm-reality-rank/raw_rankings.csv` (append)

**Step 1: Hand-verify Artificial Analysis price/speed/context table values, then create the fixture**

Create `data/llm-reality-rank/fixtures/artificial-analysis-practicality-2026-05-04.json`:

```json
[
  {
    "model_name_raw": "GPT-5.5",
    "canonical_id": "openai/gpt-5.5-high@unknown",
    "provider": "OpenAI",
    "score_raw": "12.50",
    "metric_name": "aa_price_per_million_tokens_blended",
    "metric_type": "price",
    "score_unit": "usd_per_million_tokens",
    "score_higher_is_better": "false",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA price; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "score_raw": "30.00",
    "metric_name": "aa_price_per_million_tokens_blended",
    "metric_type": "price",
    "score_unit": "usd_per_million_tokens",
    "score_higher_is_better": "false",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA price; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Gemini 3.1 Pro Preview",
    "canonical_id": "google/gemini-3.1-pro-preview@unknown",
    "provider": "Google",
    "score_raw": "5.00",
    "metric_name": "aa_price_per_million_tokens_blended",
    "metric_type": "price",
    "score_unit": "usd_per_million_tokens",
    "score_higher_is_better": "false",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA price; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3@2025-03-24",
    "provider": "DeepSeek",
    "score_raw": "0.85",
    "metric_name": "aa_price_per_million_tokens_blended",
    "metric_type": "price",
    "score_unit": "usd_per_million_tokens",
    "score_higher_is_better": "false",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA price; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "GPT-5.5",
    "canonical_id": "openai/gpt-5.5-high@unknown",
    "provider": "OpenAI",
    "score_raw": "120",
    "metric_name": "aa_output_tokens_per_second",
    "metric_type": "speed",
    "score_unit": "tokens_per_second",
    "score_higher_is_better": "true",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA speed; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Claude Opus 4.7",
    "canonical_id": "anthropic/claude-opus-4.7@unknown",
    "provider": "Anthropic",
    "score_raw": "55",
    "metric_name": "aa_output_tokens_per_second",
    "metric_type": "speed",
    "score_unit": "tokens_per_second",
    "score_higher_is_better": "true",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA speed; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "Gemini 3.1 Pro Preview",
    "canonical_id": "google/gemini-3.1-pro-preview@unknown",
    "provider": "Google",
    "score_raw": "210",
    "metric_name": "aa_output_tokens_per_second",
    "metric_type": "speed",
    "score_unit": "tokens_per_second",
    "score_higher_is_better": "true",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA speed; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  },
  {
    "model_name_raw": "DeepSeek V3.5",
    "canonical_id": "deepseek/deepseek-v3@2025-03-24",
    "provider": "DeepSeek",
    "score_raw": "85",
    "metric_name": "aa_output_tokens_per_second",
    "metric_type": "speed",
    "score_unit": "tokens_per_second",
    "score_higher_is_better": "true",
    "category_primary": "practical",
    "date_published": "2026-04-30",
    "date_observed": "2026-05-04",
    "source_url": "https://artificialanalysis.ai/leaderboards/models",
    "notes": "Reviewed alpha seed AA speed; canonicalization_status=canonicalized; alpha snapshot seed, not comprehensive."
  }
]
```

**Step 2: Smoke-test fixture parsing**

```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest artificial_analysis \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/artificial-analysis-practicality-2026-05-04.json
```
Expected: `"status": "ok"`, `"row_count": 8`. Inspect output JSON to confirm `metric_name` and `metric_type` differ across rows.

**Step 3: Append rows**

```bash
.venv/bin/python scripts/llm-reality-rank/ingest_sources.py ingest artificial_analysis \
  --mode fixture \
  --fixture data/llm-reality-rank/fixtures/artificial-analysis-practicality-2026-05-04.json \
  --output-csv outputs/llm-reality-rank/ingested-artificial-analysis-practicality.csv
tail -n +2 outputs/llm-reality-rank/ingested-artificial-analysis-practicality.csv >> data/llm-reality-rank/raw_rankings.csv
.venv/bin/python scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
```

Expected: validation passes, all tests green.

**Step 4: Commit**

```bash
git add data/llm-reality-rank/fixtures/artificial-analysis-practicality-2026-05-04.json data/llm-reality-rank/raw_rankings.csv
git commit -m "data(artificial_analysis): add Practicality price/speed seed rows"
```

---

## Workstream D — Live-Safe Parser for LiveBench

> LiveBench publishes a public CSV at the URL already used in `raw_rankings.csv:notes`: `https://raw.githubusercontent.com/LiveBench/LiveBench.github.io/main/public/table_2026_01_08.csv`. This is the safest possible "live" target — it is plain CSV from GitHub raw, no anti-bot, no JS, no auth. We promote `ingest_live_safe` from a uniform `manual_required` fallback into a real parser for this one target. The parser computes `global_average` as the mean of task columns and emits the same rowshape `proposed_row` produces for fixtures.

### Task D1: Add a failing test for the LiveBench live-safe parser

**Files:**
- Modify: `tests/llm-reality-rank/test_ingest_sources.py`

**Step 1: Add a test that bypasses real network by stubbing `bounded_live_fetch`**

Append to `tests/llm-reality-rank/test_ingest_sources.py`:

```python
def test_livebench_live_safe_parses_github_csv(monkeypatch):
    module = load_module()
    fake_csv = (
        "model,reasoning_average,coding_average,math_average,language_average\n"
        "gpt-5.5-high,82.0,80.0,79.0,76.0\n"
        "claude-opus-4-7,84.0,78.0,80.0,82.0\n"
    ).encode("utf-8")

    def fake_fetch(url, *, timeout=10):
        assert "LiveBench" in url or "livebench" in url.lower()
        return fake_csv

    monkeypatch.setattr(module, "bounded_live_fetch", fake_fetch)

    result = module.ingest_target("livebench", mode="live-safe")
    assert result.status == "ok"
    assert result.used_network is True
    assert len(result.rows) == 2
    scores = {row["model_name_raw"]: float(row["score_raw"]) for row in result.rows}
    assert scores["gpt-5.5-high"] == 79.25
    assert scores["claude-opus-4-7"] == 81.0
    for row in result.rows:
        assert row["source_id"] == "livebench"
        assert row["metric_name"] == "global_average"
        assert row["score_higher_is_better"] == "true"
```

**Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_livebench_live_safe_parses_github_csv -v`
Expected: FAILED with `result.status == "manual_required"`.

**Step 3: Commit the failing test**

```bash
git add tests/llm-reality-rank/test_ingest_sources.py
git commit -m "test(ingest): add failing live-safe LiveBench CSV parser assertion"
```

---

### Task D2: Implement the LiveBench live-safe parser

**Files:**
- Modify: `scripts/llm-reality-rank/ingest_sources.py:60-74` (TARGETS["livebench"]) — add `live_csv_url`
- Modify: `scripts/llm-reality-rank/ingest_sources.py:379-391` (`ingest_live_safe`)

**Step 1: Add a `live_csv_url` field to the `livebench` TARGETS entry**

Replace the `livebench` block at lines 60-74:

```python
    "livebench": {
        "source_id": "livebench",
        "source_name": "LiveBench",
        "source_priority": "P0",
        "category_primary": "general",
        "metric_name": "global_average",
        "metric_type": "benchmark_score",
        "score_unit": "score",
        "score_higher_is_better": "true",
        "source_url": "https://livebench.ai/",
        "live_csv_url": "https://raw.githubusercontent.com/LiveBench/LiveBench.github.io/main/public/table_2026_01_08.csv",
        "evaluation_independence": "independent_third_party",
        "source_trust": "high",
        "contamination_risk": "low",
        "freshness_weight": "1.0",
    },
```

**Step 2: Replace `ingest_live_safe` with a parser-aware version**

Replace the current `ingest_live_safe` (lines 379-391) with:

```python
def ingest_live_safe(target: str) -> IngestionResult:
    meta = TARGETS[target]
    csv_url = meta.get("live_csv_url")
    fetch_url = csv_url or meta["source_url"]
    try:
        content = bounded_live_fetch(fetch_url)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return manual_required(target, f"bounded public request failed safely: {exc}", used_network=True)
    if looks_like_pickle(content):
        return manual_required(target, "live response appears to be pickle data; unsafe deserialization refused.", used_network=True)
    if csv_url and target == "livebench":
        return parse_livebench_csv(content, source_url=csv_url)
    return manual_required(
        target,
        "bounded public request completed, but no committed safe structured parser is configured for this live response.",
        used_network=True,
    )


def parse_livebench_csv(content: bytes, *, source_url: str) -> IngestionResult:
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(text.splitlines())
    rows: list[dict[str, str]] = []
    today = date.today().isoformat()
    for raw in reader:
        model_name = (raw.get("model") or "").strip()
        if not model_name:
            continue
        task_values: list[float] = []
        for key, value in raw.items():
            if key == "model" or value is None:
                continue
            try:
                task_values.append(float(str(value).strip()))
            except ValueError:
                continue
        if not task_values:
            continue
        score = round(sum(task_values) / len(task_values), 6)
        fixture_row = {
            "model_name_raw": model_name,
            "canonical_id": "",
            "provider": "",
            "rank_raw": "",
            "score_raw": str(score),
            "date_published": "",
            "date_observed": today,
            "source_url": source_url,
            "notes": "Live-safe LiveBench CSV ingestion; canonical_id requires human review before promotion.",
        }
        rows.append(proposed_row("livebench", fixture_row, source_url=source_url))
    return IngestionResult(
        target="livebench",
        status="ok" if rows else "manual_required",
        message=f"Parsed {len(rows)} LiveBench rows from live-safe CSV.",
        rows=rows,
        used_network=True,
        source_url=source_url,
    )
```

**Step 3: Run the test to verify it passes**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py::test_livebench_live_safe_parses_github_csv -v`
Expected: PASSED.

Run full suite: `.venv/bin/python -m pytest tests/llm-reality-rank -q`
Expected: all green.

**Step 4: Commit**

```bash
git add scripts/llm-reality-rank/ingest_sources.py
git commit -m "feat(ingest): add live-safe LiveBench CSV parser via GitHub raw URL"
```

---

### Task D3: Add a smoke-test guard against future LiveBench CSV column drift

**Files:**
- Modify: `tests/llm-reality-rank/test_ingest_sources.py`

**Step 1: Add a regression test for empty/malformed CSV handling**

Append:

```python
def test_livebench_live_safe_handles_empty_csv(monkeypatch):
    module = load_module()
    monkeypatch.setattr(module, "bounded_live_fetch", lambda url, *, timeout=10: b"model\n")
    result = module.ingest_target("livebench", mode="live-safe")
    assert result.status == "manual_required"
    assert result.used_network is True
    assert len(result.rows) == 0


def test_livebench_live_safe_skips_rows_with_no_numeric_values(monkeypatch):
    module = load_module()
    csv_text = (
        "model,col_a,col_b\n"
        "good-model,80,75\n"
        "bad-model,n/a,n/a\n"
    ).encode("utf-8")
    monkeypatch.setattr(module, "bounded_live_fetch", lambda url, *, timeout=10: csv_text)
    result = module.ingest_target("livebench", mode="live-safe")
    assert result.status == "ok"
    assert {row["model_name_raw"] for row in result.rows} == {"good-model"}
```

**Step 2: Run, expect PASS**

Run: `.venv/bin/python -m pytest tests/llm-reality-rank/test_ingest_sources.py -v -k livebench`
Expected: 3 PASSED (D1's test plus the two new ones).

**Step 3: Commit**

```bash
git add tests/llm-reality-rank/test_ingest_sources.py
git commit -m "test(ingest): cover LiveBench live-safe edge cases (empty + non-numeric rows)"
```

---

## Workstream E — Reviewed Snapshot 2026-05-gamma

### Task E1: Run the full pipeline

**Files:**
- Touched (generated): `outputs/llm-reality-rank/normalized_scores.csv`, `outputs/llm-reality-rank/model_scores.csv`, `outputs/llm-reality-rank/model_scores.md`, `outputs/llm-reality-rank/first-draft-leaderboard.md`

**Step 1: Validate, then run normalize → aggregate**

```bash
.venv/bin/python scripts/llm-reality-rank/validate_data.py
.venv/bin/python scripts/llm-reality-rank/normalize_scores.py
.venv/bin/python scripts/llm-reality-rank/aggregate_scores.py
```

Expected:
- Validation prints `VALIDATION PASSED`.
- normalize prints "Wrote N normalized rows" with `N` significantly larger than the 24 rows pre-plan (target: 24 + 5 LMArena + 4 HF + 4 LiveCodeBench + 8 AA-practicality = 45).
- aggregate prints model count.

**Step 2: Sanity-check that no row was silently dropped**

Run: `wc -l data/llm-reality-rank/raw_rankings.csv`
Expected: 46 lines (1 header + 45 data rows). If less, find the missing rows in the workstream B/C output CSVs.

---

### Task E2: Promote to `2026-05-gamma` reviewed snapshot

**Files:**
- Created: `snapshots/llm-reality-rank/2026-05-gamma/*.json`
- Updated: `outputs/llm-reality-rank/api/v1/*.json`
- Updated: `site/public/api/v1/*.json` (via `prebuild` copy)

**Step 1: Export the reviewed snapshot**

```bash
.venv/bin/python scripts/llm-reality-rank/export_reviewed_snapshot.py --snapshot-id 2026-05-gamma
```

Expected: writes `snapshots/llm-reality-rank/2026-05-gamma/{manifest,leaderboard,scores,models,sources,scenarios,snapshots,source-evidence,selector-data}.json` and refreshes `outputs/llm-reality-rank/api/v1/*.json`.

**Step 2: Confirm manifest includes the new sources**

Run: `python3 -c "import json; m = json.load(open('snapshots/llm-reality-rank/2026-05-gamma/manifest.json')); print(sorted(s['source_id'] for s in m['included_sources']))"`
Expected: list contains `lmarena_chatbot_arena`, `hf_open_llm_leaderboard`, `livecodebench`, `superclue`, `ceval`, `opencompass_llm`, `livebench`, `aider_leaderboards`, `swe_bench_verified`, `artificial_analysis_llm` (10 sources).

**Step 3: Build the site to refresh `site/public/api/v1` and run all checks**

```bash
npm --prefix site run build
npm --prefix site test
npm --prefix site run check
```

Expected: build succeeds, all content/responsive/selector/evidence checks pass.

**Step 4: Commit**

```bash
git add snapshots/llm-reality-rank/2026-05-gamma site/public/api/v1 outputs/llm-reality-rank/api/v1
git commit -m "feat: publish reviewed alpha snapshot 2026-05-gamma with English P0 expansion + Practicality"
```

---

### Task E3: Refresh README, methodology article, and HANDOFF status block

**Files:**
- Modify: `README.md` (sources list line 264; current state lines 28-29; technical state in `## 当前状态`)
- Modify: `docs/HANDOFF.md` (line 22-29 "当前状态" block + line 1188 onward technical-debt list)
- Generated: `docs/public-methodology-article-2026-05-gamma.md`

**Step 1: Generate the article assets for the new snapshot**

```bash
.venv/bin/python scripts/llm-reality-rank/export_article_assets.py --snapshot-id 2026-05-gamma
```

Expected: writes `outputs/llm-reality-rank/article-exports/2026-05-gamma/*.md` and `docs/public-methodology-article-2026-05-gamma.md`.

**Step 2: Update README**

In `README.md` line 28-29, change:
```
- reviewed alpha snapshots：`snapshots/llm-reality-rank/2026-05-alpha/` 与 `2026-05-beta/`
  （beta 加入 SuperCLUE / C-Eval / OpenCompass 中文基准）
```
to:
```
- reviewed alpha snapshots：`2026-05-alpha/`、`2026-05-beta/` 与 `2026-05-gamma/`
  （beta 加入 SuperCLUE / C-Eval / OpenCompass；gamma 加入 LMArena / HF Open LLM /
  LiveCodeBench 与 Artificial Analysis 价格/速度维度，并启用 LiveBench live-safe 抓取）
```

**Step 3: Update HANDOFF status block**

In `docs/HANDOFF.md` lines around the `## 3. 当前仓库状态` block, update "当前还没有完成" — strike items now done:
- ✅ CI/CD（site job 已加入）
- 🟡 自动化抓取/定时更新（LiveBench live-safe 落地，其余仍 fixture）
- ✅ 静态网页（已有 MVP）

In the `## 16. 当前已知技术债` block, mark resolved items:
- 1. README 项目结构 — done
- 2. Elo normalization — done in current `normalize_scores.py`
- 8. 没有 CI — done
- 10. 没有 source-specific ingestion scripts — partial: LiveBench live-safe done

**Step 4: Validate, commit**

```bash
.venv/bin/python scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
npm --prefix site test
git add README.md docs/HANDOFF.md docs/public-methodology-article-2026-05-gamma.md outputs/llm-reality-rank/article-exports/2026-05-gamma
git commit -m "docs: update README, HANDOFF, and methodology article for 2026-05-gamma snapshot"
```

---

### Task E4: Final regression sweep

**Step 1: Re-run everything end-to-end**

```bash
.venv/bin/python scripts/llm-reality-rank/validate_data.py
.venv/bin/python -m pytest tests/llm-reality-rank -q
npm --prefix site ci
npm --prefix site test
npm --prefix site run check
npm --prefix site run build
```

Expected: every step exits 0.

**Step 2: Confirm git status is clean**

Run: `git status`
Expected: `nothing to commit, working tree clean`.

---

## Acceptance Criteria

This plan is complete when:

1. `git log --oneline` shows commits for: A1–A3, B1–B8, C1–C2, D1–D3, E1–E4 (~20 commits).
2. `data/llm-reality-rank/raw_rankings.csv` has **45 data rows** across **10 distinct `source_id` values**.
3. `snapshots/llm-reality-rank/2026-05-gamma/manifest.json` lists 10 included sources and >= 10 model rows in `model_scores`.
4. CI on `main` runs both Python and site jobs; both green.
5. `.venv/bin/python -m pytest tests/llm-reality-rank -q` passes locally.
6. `npm --prefix site test && npm --prefix site run check && npm --prefix site run build` pass locally.
7. `README.md`, `docs/HANDOFF.md`, and the methodology article reflect the gamma snapshot.

---

## Out of Scope (Not in This Plan)

- LMArena CSV / pickle / scrape ingestion (still gated; only hand-curated JSON allowed).
- LiveCodeBench / HF Open LLM live-safe parsers (fixture-only; their pages are JS-rendered).
- Adding CMMLU / MMMU / MathVista / GAIA / OpenRouter — separate plan.
- Site UI changes — current pages already render new sources dynamically from JSON.
- Confidence scoring rebalance — current thresholds are intentionally retained to preserve existing test expectations.

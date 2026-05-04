#!/usr/bin/env python3
"""
Safe source ingestion framework for LLM Reality Rank.

This module provides a secure, traceable way to ingest LLM benchmark data
from various sources while maintaining data integrity and auditability.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# ============================================================================
# CONSTANTS
# ============================================================================

ROOT = Path(__file__).resolve().parents[2]

USER_AGENT = "llm-reality-rank-ingestion/0.1 (+https://github.com/) safe-public-fetch"
DEFAULT_TIMEOUT_SECONDS = 10

# Raw ranking fields in order
RAW_ROW_FIELDS = [
    "source_id",
    "source_name",
    "source_priority",
    "category_primary",
    "metric_name",
    "metric_type",
    "model_name_raw",
    "canonical_id",
    "provider",
    "rank_raw",
    "score_raw",
    "score_unit",
    "score_higher_is_better",
    "date_published",
    "date_observed",
    "source_url",
    "evaluation_independence",
    "source_trust",
    "contamination_risk",
    "freshness_weight",
    "notes",
]

# Field aliases for flexible fixture parsing
FIELD_ALIASES = {
    "model_name_raw": [
        "model_name_raw", "model_name", "model", "name",
        "Model", "Model name", "Model Name",
    ],
    "canonical_id": [
        "canonical_id", "canonical_model_id",
        "Canonical ID", "Canonical model ID",
    ],
    "provider": ["provider", "Provider", "organization", "Organization"],
    "rank_raw": ["rank_raw", "rank", "Rank", "overall_rank"],
    "score_raw": [
        "score_raw", "score", "Score", "Percent correct",
        "percent_correct", "global_average", "resolved", "resolved_rate",
        "intelligence_index",
    ],
    "date_published": ["date_published", "published_at", "Date published"],
    "date_observed": ["date_observed", "Date observed", "observed_at"],
    "source_url": ["source_url", "Source URL", "url"],
    "notes": ["notes", "Notes"],
    "metric_name": ["metric_name", "Metric Name"],
    "metric_type": ["metric_type", "Metric Type"],
    "score_higher_is_better": ["score_higher_is_better"],
    "score_unit": ["score_unit", "unit"],
    "category_primary": ["category_primary"],
}

# Ingestion target configurations
TARGETS = {
    "aider": {
        "source_id": "aider_leaderboards",
        "source_name": "Aider LLM Leaderboards",
        "source_priority": "P0",
        "category_primary": "coding",
        "metric_name": "polyglot_score",
        "metric_type": "pass_rate",
        "score_unit": "percent_correct",
        "score_higher_is_better": "true",
        "source_url": "https://aider.chat/docs/leaderboards/",
        "evaluation_independence": "platform_or_community",
        "source_trust": "high",
        "contamination_risk": "low_medium",
        "freshness_weight": "1.0",
    },
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
    "swe_bench_verified": {
        "source_id": "swe_bench_verified",
        "source_name": "SWE-bench Verified",
        "source_priority": "P0",
        "category_primary": "coding",
        "metric_name": "resolved_rate",
        "metric_type": "resolved_issue_rate",
        "score_unit": "percent",
        "score_higher_is_better": "true",
        "source_url": "https://www.swebench.com/",
        "evaluation_independence": "independent_third_party",
        "source_trust": "high",
        "contamination_risk": "medium",
        "freshness_weight": "1.0",
    },
    "artificial_analysis": {
        "source_id": "artificial_analysis_llm",
        "source_name": "Artificial Analysis LLM Leaderboard / Intelligence Index",
        "source_priority": "P0",
        "category_primary": "practical",
        "metric_name": "intelligence_index",
        "metric_type": "aggregate_score",
        "score_unit": "index",
        "score_higher_is_better": "true",
        "source_url": "https://artificialanalysis.ai/leaderboards/models",
        "evaluation_independence": "platform_or_community",
        "source_trust": "high",
        "contamination_risk": "low_medium",
        "freshness_weight": "1.0",
    },
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
    "lmarena": {
        "source_id": "lmarena_chatbot_arena",
        "source_name": "LMArena / Chatbot Arena Leaderboard",
        "source_priority": "P0",
        "category_primary": "general",
        "metric_name": "arena_elo",
        "metric_type": "elo",
        "score_unit": "elo",
        "score_higher_is_better": "true",
        "source_url": "https://lmarena.ai/leaderboard/",
        "evaluation_independence": "independent_third_party",
        "source_trust": "high",
        "contamination_risk": "low_medium",
        "freshness_weight": "1.0",
    },
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
}


# ============================================================================
# EXCEPTIONS
# ============================================================================

class UnsafeSourceError(Exception):
    """Raised when a source is deemed unsafe for automatic ingestion."""
    pass


# ============================================================================
# DATA CLASSES
# ============================================================================

class IngestionResult:
    """Result of an ingestion operation."""

    def __init__(
        self,
        target: str,
        status: str,
        message: str,
        rows: list[dict[str, str]] | None = None,
        used_network: bool = False,
        source_url: str = "",
    ) -> None:
        self.target = target
        self.status = status
        self.message = message
        self.rows = rows or []
        self.used_network = used_network
        self.source_url = source_url

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "status": self.status,
            "message": self.message,
            "row_count": len(self.rows),
            "used_network": self.used_network,
            "source_url": self.source_url,
            "rows": self.rows,
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def target_names() -> list[str]:
    """Return sorted list of available ingestion targets."""
    return sorted(TARGETS)


def bounded_live_fetch(url: str, *, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> bytes:
    """Fetch content from URL with safety checks."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported URL scheme for safe fetch: {parsed.scheme}")
    
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def is_pickle_path(path: Path) -> bool:
    """Check if path has pickle file extension."""
    return path.suffix.lower() in {".pkl", ".pickle"}


def looks_like_pickle(content: bytes) -> bool:
    """Check if content appears to be pickle data."""
    return content.startswith(b"\x80") or b"pickle" in content[:200].lower()


def first_value(row: dict[str, str], aliases: list[str]) -> str:
    """Get first non-empty value from row using field aliases."""
    for alias in aliases:
        value = row.get(alias, "")
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def fixture_value(row: dict[str, str], field: str) -> str:
    """Get value from fixture row with alias support."""
    return first_value(row, FIELD_ALIASES.get(field, [field]))


def canonicalization_note(canonical_id: str) -> str:
    """Generate canonicalization status note."""
    if canonical_id:
        return f"canonicalization_status=canonicalized; canonical_id={canonical_id}"
    return "canonicalization_status=unresolved; canonical_id unavailable in fixture row"


def build_row_notes(fixture_row: dict[str, str], canonical_id: str) -> str:
    """Build notes field for a row."""
    notes = fixture_value(fixture_row, "notes")
    status = canonicalization_note(canonical_id)
    
    if notes:
        return f"{status}; {notes}"
    return f"Fixture ingestion row; proposed only and requires human review before promotion.; {status}"


def apply_field_overrides(row: dict[str, str], fixture_row: dict[str, str]) -> None:
    """Apply per-row field overrides from fixture."""
    override_fields = (
        "metric_name", "metric_type", "score_higher_is_better",
        "score_unit", "category_primary"
    )
    
    for field in override_fields:
        override_value = fixture_value(fixture_row, field)
        if not override_value and isinstance(fixture_row.get(field), str):
            override_value = str(fixture_row[field]).strip()
        if override_value:
            row[field] = override_value


def create_base_row(target: str) -> dict[str, str]:
    """Create base row with target metadata."""
    meta = TARGETS[target]
    return {field: str(meta.get(field, "")) for field in RAW_ROW_FIELDS}


def build_proposed_row(target: str, fixture_row: dict[str, str], *, source_url: str) -> dict[str, str]:
    """Build a proposed row from fixture data."""
    row = create_base_row(target)
    
    canonical_id = fixture_value(fixture_row, "canonical_id")
    row_source_url = fixture_value(fixture_row, "source_url") or source_url
    
    row.update({
        "model_name_raw": fixture_value(fixture_row, "model_name_raw"),
        "canonical_id": canonical_id,
        "provider": fixture_value(fixture_row, "provider"),
        "rank_raw": fixture_value(fixture_row, "rank_raw"),
        "score_raw": fixture_value(fixture_row, "score_raw"),
        "date_published": fixture_value(fixture_row, "date_published"),
        "date_observed": fixture_value(fixture_row, "date_observed") or date.today().isoformat(),
        "source_url": row_source_url,
        "notes": build_row_notes(fixture_row, canonical_id),
    })
    
    apply_field_overrides(row, fixture_row)
    return row


# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_json_fixture(path: Path) -> list[dict[str, str]]:
    """Parse JSON fixture file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    defaults = {}
    
    if isinstance(payload, dict):
        defaults = {
            str(k): "" if v is None else str(v)
            for k, v in payload.items()
            if k != "rows" and not isinstance(v, (list, dict))
        }
        payload = payload.get("rows", [])
    
    if not isinstance(payload, list):
        raise ValueError("JSON fixture must contain a list of row objects")
    
    return [
        defaults | {str(k): "" if v is None else str(v) for k, v in row.items()}
        for row in payload
    ]


def parse_csv_fixture(path: Path) -> list[dict[str, str]]:
    """Parse CSV fixture file."""
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_fixture_rows(path: Path) -> list[dict[str, str]]:
    """Parse fixture rows from file (JSON or CSV)."""
    if is_pickle_path(path):
        raise UnsafeSourceError("pickle fixture is unsafe and will not be executed")
    
    if path.suffix.lower() == ".json":
        return parse_json_fixture(path)
    
    return parse_csv_fixture(path)


def calculate_livebench_score(raw: dict[str, str]) -> float | None:
    """Calculate average score from LiveBench CSV row."""
    task_values: list[float] = []
    
    for key, value in raw.items():
        if key == "model" or value is None:
            continue
        try:
            task_values.append(float(str(value).strip()))
        except ValueError:
            continue
    
    if not task_values:
        return None
    
    return round(sum(task_values) / len(task_values), 6)


def build_livebench_fixture_row(raw: dict[str, str], today: str, source_url: str) -> dict[str, str]:
    """Build fixture row from LiveBench CSV data."""
    model_name = (raw.get("model") or "").strip()
    if not model_name:
        return {}
    
    score = calculate_livebench_score(raw)
    if score is None:
        return {}
    
    return {
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


def parse_livebench_csv(content: bytes, *, source_url: str) -> IngestionResult:
    """Parse LiveBench CSV content."""
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(text.splitlines())
    rows: list[dict[str, str]] = []
    today = date.today().isoformat()
    
    for raw in reader:
        fixture_row = build_livebench_fixture_row(raw, today, source_url)
        if fixture_row:
            rows.append(build_proposed_row("livebench", fixture_row, source_url=source_url))
    
    status = "ok" if rows else "manual_required"
    message = f"Parsed {len(rows)} LiveBench rows from live-safe CSV."
    
    return IngestionResult(
        target="livebench",
        status=status,
        message=message,
        rows=rows,
        used_network=True,
        source_url=source_url,
    )


# ============================================================================
# INGESTION FUNCTIONS
# ============================================================================

def create_manual_result(target: str, message: str, *, used_network: bool) -> IngestionResult:
    """Create a manual review required result."""
    return IngestionResult(
        target=target,
        status="manual_required",
        message=message,
        rows=[],
        used_network=used_network,
        source_url=TARGETS[target]["source_url"],
    )


def parse_structured_fixture(target: str, fixture_path: Path) -> IngestionResult:
    """Parse structured fixture file for a target."""
    if target == "lmarena" and fixture_path.suffix.lower() != ".json":
        return create_manual_result(
            target,
            "LMArena fixture ingestion accepts only hand-curated JSON fixtures; CSV/pickle paths require manual review.",
            used_network=False,
        )
    
    try:
        fixture_rows = parse_fixture_rows(fixture_path)
    except UnsafeSourceError as exc:
        return create_manual_result(target, str(exc), used_network=False)
    
    source_url = f"fixture://{fixture_path.name}"
    rows = [build_proposed_row(target, row, source_url=source_url) for row in fixture_rows]
    
    return IngestionResult(
        target=target,
        status="ok",
        message=f"Parsed {len(rows)} fixture rows without network access.",
        rows=rows,
        used_network=False,
        source_url=source_url,
    )


def ingest_live_safe(target: str) -> IngestionResult:
    """Ingest data from live source with safety checks."""
    meta = TARGETS[target]
    csv_url = meta.get("live_csv_url")
    fetch_url = csv_url or meta["source_url"]
    
    try:
        content = bounded_live_fetch(fetch_url)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return create_manual_result(target, f"bounded public request failed safely: {exc}", used_network=True)
    
    if looks_like_pickle(content):
        return create_manual_result(
            target,
            "live response appears to be pickle data; unsafe deserialization refused.",
            used_network=True,
        )
    
    if csv_url and target == "livebench":
        return parse_livebench_csv(content, source_url=csv_url)
    
    return create_manual_result(
        target,
        "bounded public request completed, but no committed safe structured parser is configured for this live response.",
        used_network=True,
    )


def ingest_target(target: str, *, mode: str = "fixture", fixture_path: Path | None = None) -> IngestionResult:
    """Ingest data for a target."""
    if target not in TARGETS:
        raise ValueError(f"unknown ingestion target: {target}")
    
    if mode == "fixture":
        if fixture_path is None:
            return create_manual_result(target, "fixture mode requires an explicit --fixture path", used_network=False)
        return parse_structured_fixture(target, fixture_path)
    
    if target == "lmarena":
        return create_manual_result(
            target,
            "LMArena safe structured current data is not configured; remote pickle execution and anti-bot bypass are prohibited.",
            used_network=False,
        )
    
    return ingest_live_safe(target)


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def write_rows(path: Path, rows: Iterable[dict[str, str]]) -> None:
    """Write rows to CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RAW_ROW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(description="Safe source ingestion framework for LLM Reality Rank.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    subparsers.add_parser("list", help="List available ingestion targets.")
    
    ingest = subparsers.add_parser("ingest", help="Ingest a source target in fixture or bounded live-safe mode.")
    ingest.add_argument("target", choices=target_names())
    ingest.add_argument("--mode", choices=["fixture", "live-safe"], default="fixture")
    ingest.add_argument("--fixture", type=Path)
    ingest.add_argument("--output-csv", type=Path)
    
    return parser


def list_targets() -> int:
    """List available ingestion targets."""
    for target in target_names():
        meta = TARGETS[target]
        print(f"{target}\t{meta['source_id']}\t{meta['source_name']}")
    return 0


def ingest_command(args) -> int:
    """Execute ingest command."""
    result = ingest_target(args.target, mode=args.mode, fixture_path=args.fixture)
    
    if args.output_csv and result.rows:
        write_rows(args.output_csv, result.rows)
    
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.status in {"ok", "manual_required"} else 1


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    args = build_parser().parse_args(argv)
    
    if args.command == "list":
        return list_targets()
    
    return ingest_command(args)


if __name__ == "__main__":
    sys.exit(main())

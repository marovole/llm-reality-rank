#!/usr/bin/env python3
"""
Normalize raw scores to 0-100 scale with source weighting.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable

# ============================================================================
# CONSTANTS
# ============================================================================

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "llm-reality-rank"
OUTPUTS = ROOT / "outputs" / "llm-reality-rank"

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

OUTPUT_FIELDS = [
    "source_id", "metric_name", "category_primary", "canonical_id",
    "provider", "model_name_raw", "rank_raw", "score_raw",
    "score_normalized", "source_effective_weight", "score_weighted",
    "source_url", "date_observed", "notes",
]

DIRECT_SCORE_TYPES = {
    "accuracy", "aggregate_score", "benchmark_aggregate", "benchmark_score",
    "holistic_benchmark_metrics", "pass_rate", "percentage",
    "resolved_issue_rate", "score", "task_success_rate",
}

GROUP_HIGHER_IS_BETTER_TYPES = {
    "context", "context_length", "context_window", "elo", "speed",
    "throughput", "tokens_per_second",
}

GROUP_LOWER_IS_BETTER_TYPES = {"cost", "latency", "price"}


# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_float(value: str | None) -> float | None:
    """Parse string value to float."""
    if value is None:
        return None
    value = value.strip().replace("%", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_rows(path: Path) -> list[dict[str, str]]:
    """Load CSV rows from file."""
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ============================================================================
# SCORE CALCULATION
# ============================================================================

def clamp_score(value: float) -> float:
    """Clamp score to 0-100 range."""
    return max(0.0, min(100.0, value))


def get_metric_type(row: dict[str, str]) -> str:
    """Get normalized metric type from row."""
    return row.get("metric_type", "").strip().lower()


def is_higher_better(row: dict[str, str]) -> bool:
    """Check if higher score is better."""
    return row.get("score_higher_is_better", "true").strip().lower() != "false"


def should_group_normalize(row: dict[str, str], raw_score: float) -> bool:
    """Determine if score needs group normalization."""
    metric = get_metric_type(row)
    
    if metric in GROUP_HIGHER_IS_BETTER_TYPES or metric in GROUP_LOWER_IS_BETTER_TYPES:
        return True
    if metric in DIRECT_SCORE_TYPES:
        return raw_score > 100
    if 0 <= raw_score <= 100:
        return False
    
    return True


def normalize_min_max(value: float, values: list[float], *, lower_is_better: bool) -> float:
    """Normalize value using min-max scaling."""
    low = min(values)
    high = max(values)
    
    if high == low:
        return 100.0
    
    if lower_is_better:
        normalized = 100.0 * (high - value) / (high - low)
    else:
        normalized = 100.0 * (value - low) / (high - low)
    
    return clamp_score(normalized)


def normalize_rank(raw_rank: float, ranks: list[float]) -> float:
    """Normalize rank to 0-100 scale."""
    if len(ranks) <= 1:
        return 100.0
    
    best_rank = min(ranks)
    worst_rank = max(ranks)
    
    if worst_rank == best_rank:
        return 100.0
    
    normalized = 100.0 * (worst_rank - raw_rank) / (worst_rank - best_rank)
    return clamp_score(normalized)


def normalize_row_score(
    row: dict[str, str],
    group_size: int,
    group_score_values: list[float] | None = None,
    group_rank_values: list[float] | None = None,
) -> float | None:
    """Normalize a single score value."""
    raw_score = parse_float(row.get("score_raw"))

    if raw_score is not None:
        if should_group_normalize(row, raw_score):
            values = group_score_values or [raw_score]
            metric = get_metric_type(row)
            lower_is_better = metric in GROUP_LOWER_IS_BETTER_TYPES or not is_higher_better(row)
            return round(normalize_min_max(raw_score, values, lower_is_better=lower_is_better), 6)

        if 0 <= raw_score <= 1:
            return round(raw_score * 100, 6)

        return round(clamp_score(raw_score), 6)

    raw_rank = parse_float(row.get("rank_raw"))
    if raw_rank is None:
        return None

    if group_size <= 1:
        return 100.0

    ranks = group_rank_values or [raw_rank]
    return round(normalize_rank(raw_rank, ranks), 6)


def source_effective_weight(row: dict[str, str]) -> float:
    """Calculate effective source weight."""
    trust = SOURCE_TRUST.get(row.get("source_trust", "medium"), SOURCE_TRUST["medium"])
    contamination = CONTAMINATION_RISK.get(
        row.get("contamination_risk", "medium"), CONTAMINATION_RISK["medium"]
    )
    independence = INDEPENDENCE.get(
        row.get("evaluation_independence", "unknown"), INDEPENDENCE["unknown"]
    )
    freshness = parse_float(row.get("freshness_weight")) or 1.0

    return round(trust * contamination * independence * freshness, 6)


# ============================================================================
# GROUPING FUNCTIONS
# ============================================================================

def group_key(row: dict[str, str]) -> tuple[str, str]:
    """Get grouping key for a row."""
    return (row.get("source_id", ""), row.get("metric_name", ""))


def calculate_group_sizes(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], int]:
    """Calculate size of each source/metric group."""
    groups: dict[tuple[str, str], int] = defaultdict(int)
    
    for row in rows:
        if parse_float(row.get("score_raw")) is not None or parse_float(row.get("rank_raw")) is not None:
            groups[group_key(row)] += 1
    
    return groups


def collect_group_values(
    rows: Iterable[dict[str, str]],
    field_name: str,
) -> dict[tuple[str, str], list[float]]:
    """Collect values grouped by source/metric."""
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    
    for row in rows:
        value = parse_float(row.get(field_name))
        if value is not None:
            groups[group_key(row)].append(value)
    
    return groups


# ============================================================================
# NORMALIZATION
# ============================================================================

def create_normalized_row(
    row: dict[str, str],
    normalized_score: float,
    weight: float,
) -> dict[str, str]:
    """Create normalized output row."""
    output = {field: row.get(field, "") for field in OUTPUT_FIELDS}
    output["score_normalized"] = f"{normalized_score:.6f}"
    output["source_effective_weight"] = f"{weight:.6f}"
    output["score_weighted"] = f"{normalized_score * weight:.6f}"
    return output


def normalize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """Normalize all rows."""
    sizes = calculate_group_sizes(rows)
    score_values = collect_group_values(rows, "score_raw")
    rank_values = collect_group_values(rows, "rank_raw")
    
    normalized_rows: list[dict[str, str]] = []
    skipped = 0
    
    for row in rows:
        key = group_key(row)
        normalized_score = normalize_row_score(
            row,
            sizes.get(key, 1),
            score_values.get(key),
            rank_values.get(key),
        )
        
        if normalized_score is None:
            skipped += 1
            continue
        
        weight = source_effective_weight(row)
        normalized_rows.append(create_normalized_row(row, normalized_score, weight))
    
    return normalized_rows, skipped


# ============================================================================
# OUTPUT
# ============================================================================

def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    """Write rows to CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Main entry point."""
    rows = load_rows(DATA / "raw_rankings.csv")
    normalized_rows, skipped = normalize_rows(rows)
    
    out = OUTPUTS / "normalized_scores.csv"
    write_rows(out, normalized_rows)
    
    print(f"Wrote {len(normalized_rows)} normalized rows to {out}")
    print(f"Skipped {skipped} rows without numeric score/rank")


if __name__ == "__main__":
    main()

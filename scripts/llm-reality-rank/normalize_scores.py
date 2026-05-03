#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Iterable

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
    "source_id",
    "metric_name",
    "category_primary",
    "canonical_id",
    "provider",
    "model_name_raw",
    "rank_raw",
    "score_raw",
    "score_normalized",
    "source_effective_weight",
    "score_weighted",
    "source_url",
    "date_observed",
    "notes",
]

DIRECT_SCORE_TYPES = {
    "accuracy",
    "aggregate_score",
    "benchmark_aggregate",
    "benchmark_score",
    "holistic_benchmark_metrics",
    "pass_rate",
    "percentage",
    "resolved_issue_rate",
    "score",
    "task_success_rate",
}

GROUP_HIGHER_IS_BETTER_TYPES = {
    "context",
    "context_length",
    "context_window",
    "elo",
    "speed",
    "throughput",
    "tokens_per_second",
}

GROUP_LOWER_IS_BETTER_TYPES = {
    "cost",
    "latency",
    "price",
}

def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip().replace("%", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, value))


def metric_type(row: dict[str, str]) -> str:
    return row.get("metric_type", "").strip().lower()


def higher_is_better(row: dict[str, str]) -> bool:
    return row.get("score_higher_is_better", "true").strip().lower() != "false"


def should_group_normalize_score(row: dict[str, str], raw_score: float) -> bool:
    kind = metric_type(row)
    if kind in GROUP_HIGHER_IS_BETTER_TYPES or kind in GROUP_LOWER_IS_BETTER_TYPES:
        return True
    if kind in DIRECT_SCORE_TYPES:
        return raw_score > 100
    if 0 <= raw_score <= 100:
        return False
    return True


def min_max_score(value: float, values: list[float], *, lower_is_better: bool) -> float:
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
    raw_score = parse_float(row.get("score_raw"))
    if raw_score is not None:
        if should_group_normalize_score(row, raw_score):
            values = group_score_values or [raw_score]
            lower_is_better = metric_type(row) in GROUP_LOWER_IS_BETTER_TYPES or not higher_is_better(row)
            return round(min_max_score(raw_score, values, lower_is_better=lower_is_better), 6)
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
    trust = SOURCE_TRUST.get(row.get("source_trust", "medium"), SOURCE_TRUST["medium"])
    contamination = CONTAMINATION_RISK.get(
        row.get("contamination_risk", "medium"), CONTAMINATION_RISK["medium"]
    )
    independence = INDEPENDENCE.get(
        row.get("evaluation_independence", "unknown"), INDEPENDENCE["unknown"]
    )
    freshness = parse_float(row.get("freshness_weight"))
    if freshness is None:
        freshness = 1.0
    return round(trust * contamination * independence * freshness, 6)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def group_sizes(rows: Iterable[dict[str, str]]) -> dict[tuple[str, str], int]:
    groups: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        if parse_float(row.get("score_raw")) is not None or parse_float(row.get("rank_raw")) is not None:
            groups[(row.get("source_id", ""), row.get("metric_name", ""))] += 1
    return groups


def group_values(
    rows: Iterable[dict[str, str]],
    field_name: str,
) -> dict[tuple[str, str], list[float]]:
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        value = parse_float(row.get(field_name))
        if value is not None:
            groups[(row.get("source_id", ""), row.get("metric_name", ""))].append(value)
    return groups


def normalize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    sizes = group_sizes(rows)
    score_values = group_values(rows, "score_raw")
    rank_values = group_values(rows, "rank_raw")
    normalized_rows: list[dict[str, str]] = []
    skipped = 0

    for row in rows:
        key = (row.get("source_id", ""), row.get("metric_name", ""))
        score_normalized = normalize_row_score(
            row,
            sizes.get(key, 1),
            score_values.get(key),
            rank_values.get(key),
        )
        if score_normalized is None:
            skipped += 1
            continue

        weight = source_effective_weight(row)
        output = {field: row.get(field, "") for field in OUTPUT_FIELDS}
        output["score_normalized"] = f"{score_normalized:.6f}"
        output["source_effective_weight"] = f"{weight:.6f}"
        output["score_weighted"] = f"{score_normalized * weight:.6f}"
        normalized_rows.append(output)

    return normalized_rows, skipped


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = load_rows(DATA / "raw_rankings.csv")
    normalized_rows, skipped = normalize_rows(rows)
    out = OUTPUTS / "normalized_scores.csv"
    write_rows(out, normalized_rows)
    print(f"Wrote {len(normalized_rows)} normalized rows to {out}")
    print(f"Skipped {skipped} rows without numeric score/rank")


if __name__ == "__main__":
    main()

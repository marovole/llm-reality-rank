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


def normalize_row_score(row: dict[str, str], group_size: int) -> float | None:
    raw_score = parse_float(row.get("score_raw"))
    if raw_score is not None:
        if 0 <= raw_score <= 1:
            return round(raw_score * 100, 6)
        return round(clamp_score(raw_score), 6)

    raw_rank = parse_float(row.get("rank_raw"))
    if raw_rank is None:
        return None

    if group_size <= 1:
        return 100.0

    rank = int(raw_rank)
    higher_is_better = row.get("score_higher_is_better", "true").strip().lower() != "false"
    if higher_is_better:
        normalized = 100.0 * (rank - 1) / (group_size - 1)
    else:
        normalized = 100.0 * (group_size - rank) / (group_size - 1)
    return round(clamp_score(normalized), 6)


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


def normalize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    sizes = group_sizes(rows)
    normalized_rows: list[dict[str, str]] = []
    skipped = 0

    for row in rows:
        key = (row.get("source_id", ""), row.get("metric_name", ""))
        score_normalized = normalize_row_score(row, sizes.get(key, 1))
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

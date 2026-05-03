#!/usr/bin/env python3
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "llm-reality-rank"
OUTPUTS = ROOT / "outputs" / "llm-reality-rank"
NORMALIZED = OUTPUTS / "normalized_scores.csv"

SCENARIO_WEIGHTS = {
    "General": 0.20,
    "Reasoning_Math": 0.15,
    "Coding": 0.15,
    "Chinese": 0.15,
    "Multimodal_Doc": 0.10,
    "Agent_ToolUse": 0.10,
    "Practicality": 0.10,
    "Ecosystem": 0.05,
}

OUTPUT_FIELDS = [
    "rank",
    "canonical_id",
    "provider",
    "overall_score",
    "confidence_proxy",
    "General",
    "Reasoning_Math",
    "Coding",
    "Chinese",
    "Multimodal_Doc",
    "Agent_ToolUse",
    "Practicality",
    "Ecosystem",
    "source_count",
]


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def category_to_scenario(category: str) -> str:
    normalized = (category or "").strip().lower()
    if normalized in {"general", "preference", "conversation"}:
        return "General"
    if normalized in {"reasoning", "math"}:
        return "Reasoning_Math"
    if normalized in {"coding", "algorithms", "agentic_coding"}:
        return "Coding"
    if normalized in {"chinese", "exams", "knowledge"}:
        return "Chinese"
    if normalized in {"multimodal", "vision", "ocr", "document_understanding", "video"}:
        return "Multimodal_Doc"
    if normalized in {"agent", "tool_use", "function_calling", "web_agent", "computer_use"}:
        return "Agent_ToolUse"
    if normalized in {"practical", "cost_speed", "api"}:
        return "Practicality"
    if normalized in {"ecosystem", "adoption", "usage"}:
        return "Ecosystem"
    return "General"


def weighted_average(rows: list[dict[str, str]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        score = parse_float(row.get("score_normalized"))
        weight = parse_float(row.get("source_effective_weight"))
        if score is None:
            continue
        if weight is None or weight <= 0:
            weight = 1.0
        numerator += score * weight
        denominator += weight
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def overall_score(scenario_scores: dict[str, float]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for scenario, score in scenario_scores.items():
        weight = SCENARIO_WEIGHTS.get(scenario)
        if weight is None:
            continue
        numerator += score * weight
        denominator += weight
    if denominator == 0:
        return None
    return round(numerator / denominator, 6)


def confidence_proxy(source_count: int, scenario_count: int) -> str:
    if source_count >= 5 and scenario_count >= 4:
        return "High"
    if source_count >= 3 and scenario_count >= 2:
        return "Medium"
    return "Low"


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_model_scenario: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    providers: dict[str, str] = {}
    source_ids: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        canonical_id = row.get("canonical_id", "")
        if not canonical_id:
            continue
        scenario = category_to_scenario(row.get("category_primary", ""))
        by_model_scenario[(canonical_id, scenario)].append(row)
        providers[canonical_id] = row.get("provider", "")
        source_ids[canonical_id].add(row.get("source_id", ""))

    scenario_scores_by_model: dict[str, dict[str, float]] = defaultdict(dict)
    for (canonical_id, scenario), scenario_rows in by_model_scenario.items():
        avg = weighted_average(scenario_rows)
        if avg is not None:
            scenario_scores_by_model[canonical_id][scenario] = avg

    output: list[dict[str, str]] = []
    for canonical_id, scenario_scores in scenario_scores_by_model.items():
        overall = overall_score(scenario_scores)
        if overall is None:
            continue
        source_count = len({sid for sid in source_ids[canonical_id] if sid})
        scenario_count = len(scenario_scores)
        row = {
            "rank": "",
            "canonical_id": canonical_id,
            "provider": providers.get(canonical_id, ""),
            "overall_score": f"{overall:.6f}",
            "confidence_proxy": confidence_proxy(source_count, scenario_count),
            "source_count": str(source_count),
        }
        for scenario in SCENARIO_WEIGHTS:
            score = scenario_scores.get(scenario)
            row[scenario] = "" if score is None else f"{score:.6f}"
        output.append(row)

    output.sort(key=lambda r: float(r["overall_score"]), reverse=True)
    for idx, row in enumerate(output, 1):
        row["rank"] = str(idx)
    return output


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, str]], title: str = "LLM Reality Rank Draft Scores") -> None:
    lines = [
        f"# {title}",
        "",
        f"Generated: {date.today().isoformat()}",
        "",
        "> Draft output. Scores are only as complete as the currently ingested raw ranking rows.",
        "",
        "| Rank | Model | Provider | Overall | Confidence | Sources |",
        "|---:|---|---|---:|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['rank']} | `{row['canonical_id']}` | {row['provider']} | {float(row['overall_score']):.2f} | {row['confidence_proxy']} | {row['source_count']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows(NORMALIZED)
    aggregated = aggregate(rows)
    csv_out = OUTPUTS / "model_scores.csv"
    md_out = OUTPUTS / "model_scores.md"
    draft_out = OUTPUTS / "first-draft-leaderboard.md"
    write_csv(csv_out, aggregated)
    write_markdown(md_out, aggregated)
    write_markdown(draft_out, aggregated, title="LLM Reality Rank First Draft Leaderboard")
    print(f"Wrote {len(aggregated)} model scores to {csv_out}")
    print(f"Wrote Markdown table to {md_out}")
    print(f"Wrote first draft leaderboard to {draft_out}")


if __name__ == "__main__":
    main()

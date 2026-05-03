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
    "confidence_score",
    "confidence_label",
    "eligibility_status",
    "eligibility_reason",
    "publication_status",
    "review_status",
    "official_status",
    "uncertainty_flags",
    "missing_dimensions",
    "General",
    "Reasoning_Math",
    "Coding",
    "Chinese",
    "Multimodal_Doc",
    "Agent_ToolUse",
    "Practicality",
    "Ecosystem",
    "scenario_count",
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


def contains_uncertain_note(rows: list[dict[str, str]], markers: set[str]) -> bool:
    for row in rows:
        note = row.get("notes", "").lower()
        if any(marker in note for marker in markers):
            return True
    return False


def average_source_quality(rows: list[dict[str, str]]) -> float:
    weights = [parse_float(row.get("source_effective_weight")) for row in rows]
    valid_weights = [weight for weight in weights if weight is not None and weight > 0]
    if not valid_weights:
        return 0.5
    return min(1.0, sum(valid_weights) / len(valid_weights))


def confidence_score(
    source_count: int,
    scenario_count: int,
    source_quality: float,
    *,
    has_unresolved_canonicalization: bool = False,
    has_placeholder_data: bool = False,
) -> float:
    source_component = min(source_count / 5, 1.0) * 35
    scenario_component = min(scenario_count / len(SCENARIO_WEIGHTS), 1.0) * 35
    quality_component = max(0.0, min(source_quality, 1.0)) * 30
    penalty = 0.0
    if has_unresolved_canonicalization:
        penalty += 20.0
    if has_placeholder_data:
        penalty += 20.0
    return round(max(0.0, min(100.0, source_component + scenario_component + quality_component - penalty)), 6)


def confidence_label(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def eligibility_status(
    source_count: int,
    scenario_count: int,
    *,
    has_unresolved_canonicalization: bool = False,
    has_placeholder_data: bool = False,
) -> str:
    if has_unresolved_canonicalization or has_placeholder_data:
        return "ineligible"
    if source_count >= 5 and scenario_count >= 4:
        return "eligible"
    if source_count >= 2 and scenario_count >= 2:
        return "provisional"
    return "ineligible"


def eligibility_reason(
    status: str,
    source_count: int,
    scenario_count: int,
    *,
    has_unresolved_canonicalization: bool = False,
    has_placeholder_data: bool = False,
) -> str:
    reasons: list[str] = []
    if status == "eligible":
        return "meets_source_and_scenario_thresholds_for_review"
    if source_count < 5:
        reasons.append("insufficient_sources_for_review")
    if scenario_count < 4:
        reasons.append("insufficient_scenarios_for_review")
    if has_unresolved_canonicalization:
        reasons.append("unresolved_canonicalization")
    if has_placeholder_data:
        reasons.append("placeholder_or_todo_data")
    return ";".join(reasons)


def uncertainty_flags(
    source_count: int,
    scenario_count: int,
    missing_dimensions: list[str],
    source_quality: float,
    *,
    has_unresolved_canonicalization: bool = False,
    has_placeholder_data: bool = False,
) -> list[str]:
    flags = ["draft_unreviewed", "not_official"]
    if source_count < 5:
        flags.append("insufficient_sources")
    if scenario_count < 4:
        flags.append("insufficient_scenarios")
    if missing_dimensions:
        flags.append("missing_dimensions")
    if source_quality < 0.6:
        flags.append("low_source_quality")
    if has_unresolved_canonicalization:
        flags.append("unresolved_canonicalization")
    if has_placeholder_data:
        flags.append("placeholder_or_todo_data")
    return flags


def load_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_model_scenario: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    providers: dict[str, str] = {}
    source_ids: dict[str, set[str]] = defaultdict(set)
    rows_by_model: dict[str, list[dict[str, str]]] = defaultdict(list)

    for row in rows:
        canonical_id = row.get("canonical_id", "")
        if not canonical_id:
            continue
        scenario = category_to_scenario(row.get("category_primary", ""))
        by_model_scenario[(canonical_id, scenario)].append(row)
        providers[canonical_id] = row.get("provider", "")
        source_ids[canonical_id].add(row.get("source_id", ""))
        rows_by_model[canonical_id].append(row)

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
        model_rows = rows_by_model[canonical_id]
        missing_dimensions = [scenario for scenario in SCENARIO_WEIGHTS if scenario not in scenario_scores]
        source_quality = average_source_quality(model_rows)
        has_unresolved_canonicalization = contains_uncertain_note(
            model_rows, {"unresolved", "canonicalization_status=unresolved"}
        )
        has_placeholder_data = contains_uncertain_note(model_rows, {"todo", "placeholder", "smoke-test"})
        score = confidence_score(
            source_count,
            scenario_count,
            source_quality,
            has_unresolved_canonicalization=has_unresolved_canonicalization,
            has_placeholder_data=has_placeholder_data,
        )
        label = confidence_label(score)
        eligibility = eligibility_status(
            source_count,
            scenario_count,
            has_unresolved_canonicalization=has_unresolved_canonicalization,
            has_placeholder_data=has_placeholder_data,
        )
        flags = uncertainty_flags(
            source_count,
            scenario_count,
            missing_dimensions,
            source_quality,
            has_unresolved_canonicalization=has_unresolved_canonicalization,
            has_placeholder_data=has_placeholder_data,
        )
        row = {
            "rank": "",
            "canonical_id": canonical_id,
            "provider": providers.get(canonical_id, ""),
            "overall_score": f"{overall:.6f}",
            "confidence_proxy": label,
            "confidence_score": f"{score:.6f}",
            "confidence_label": label,
            "eligibility_status": eligibility,
            "eligibility_reason": eligibility_reason(
                eligibility,
                source_count,
                scenario_count,
                has_unresolved_canonicalization=has_unresolved_canonicalization,
                has_placeholder_data=has_placeholder_data,
            ),
            "publication_status": "unpublished",
            "review_status": "draft_unreviewed",
            "official_status": "not_official",
            "uncertainty_flags": ";".join(flags),
            "missing_dimensions": ";".join(missing_dimensions),
            "scenario_count": str(scenario_count),
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
        "> Draft/unreviewed generated output: this is not an official ranking. Generated rows remain unpublished and not official until promoted to a reviewed snapshot.",
        "",
        "| Rank | Model | Provider | Overall | Confidence | Eligibility | Status | Sources |",
        "|---:|---|---|---:|---|---|---|---:|",
    ]
    for row in rows:
        status = f"{row['review_status']} / {row['publication_status']} / {row['official_status']}"
        lines.append(
            f"| {row['rank']} | `{row['canonical_id']}` | {row['provider']} | {float(row['overall_score']):.2f} | {row['confidence_label']} ({float(row['confidence_score']):.1f}) | {row['eligibility_status']} | {status} | {row['source_count']} |"
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

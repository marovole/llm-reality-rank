#!/usr/bin/env python3
"""
Aggregate normalized scores into model-level scenario scores and overall rankings.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

# ============================================================================
# CONSTANTS
# ============================================================================

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
    "rank", "canonical_id", "provider", "overall_score", "confidence_proxy",
    "confidence_score", "confidence_label", "eligibility_status", "eligibility_reason",
    "publication_status", "review_status", "official_status", "uncertainty_flags",
    "missing_dimensions", "General", "Reasoning_Math", "Coding", "Chinese",
    "Multimodal_Doc", "Agent_ToolUse", "Practicality", "Ecosystem",
    "scenario_count", "source_count",
]

UNCERTAINTY_MARKERS = {"unresolved", "canonicalization_status=unresolved"}
PLACEHOLDER_MARKERS = {"todo", "placeholder", "smoke-test"}


# ============================================================================
# PARSING FUNCTIONS
# ============================================================================

def parse_float(value: str | None) -> float | None:
    """Parse string value to float, returning None if invalid."""
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
    """Map category to scenario dimension."""
    normalized = (category or "").strip().lower()
    
    category_map = {
        "general": "General",
        "preference": "General",
        "conversation": "General",
        "reasoning": "Reasoning_Math",
        "math": "Reasoning_Math",
        "coding": "Coding",
        "algorithms": "Coding",
        "agentic_coding": "Coding",
        "chinese": "Chinese",
        "exams": "Chinese",
        "knowledge": "Chinese",
        "multimodal": "Multimodal_Doc",
        "vision": "Multimodal_Doc",
        "ocr": "Multimodal_Doc",
        "document_understanding": "Multimodal_Doc",
        "video": "Multimodal_Doc",
        "agent": "Agent_ToolUse",
        "tool_use": "Agent_ToolUse",
        "function_calling": "Agent_ToolUse",
        "web_agent": "Agent_ToolUse",
        "computer_use": "Agent_ToolUse",
        "practical": "Practicality",
        "cost_speed": "Practicality",
        "api": "Practicality",
        "ecosystem": "Ecosystem",
        "adoption": "Ecosystem",
        "usage": "Ecosystem",
    }
    
    return category_map.get(normalized, "General")


def load_rows(path: Path) -> list[dict[str, str]]:
    """Load CSV rows from file."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ============================================================================
# CALCULATION FUNCTIONS
# ============================================================================

def weighted_average(rows: list[dict[str, str]]) -> float | None:
    """Calculate weighted average of normalized scores."""
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
    """Calculate overall score from scenario scores."""
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


def average_source_quality(rows: list[dict[str, str]]) -> float:
    """Calculate average source quality from weights."""
    weights = [parse_float(row.get("source_effective_weight")) for row in rows]
    valid_weights = [weight for weight in weights if weight is not None and weight > 0]
    
    if not valid_weights:
        return 0.5
    
    return min(1.0, sum(valid_weights) / len(valid_weights))


def contains_markers(rows: list[dict[str, str]], markers: set[str]) -> bool:
    """Check if any row contains markers in notes."""
    for row in rows:
        note = row.get("notes", "").lower()
        if any(marker in note for marker in markers):
            return True
    return False


def calculate_confidence_metrics(model_data: dict[str, Any]) -> dict[str, Any]:
    """Calculate confidence metrics for a model."""
    return {
        "source_count": len(model_data["source_ids"]),
        "scenario_count": len(model_data["scenario_scores"]),
        "source_quality": average_source_quality(model_data["rows"]),
        "has_unresolved_canonicalization": contains_markers(model_data["rows"], UNCERTAINTY_MARKERS),
        "has_placeholder_data": contains_markers(model_data["rows"], PLACEHOLDER_MARKERS),
    }


def confidence_score(metrics: dict[str, Any]) -> float:
    """Calculate confidence score from metrics."""
    source_component = min(metrics["source_count"] / 5, 1.0) * 35
    scenario_component = min(metrics["scenario_count"] / len(SCENARIO_WEIGHTS), 1.0) * 35
    quality_component = max(0.0, min(metrics["source_quality"], 1.0)) * 30
    
    penalty = 0.0
    if metrics["has_unresolved_canonicalization"]:
        penalty += 20.0
    if metrics["has_placeholder_data"]:
        penalty += 20.0
    
    return round(max(0.0, min(100.0, source_component + scenario_component + quality_component - penalty)), 6)


def confidence_label(score: float) -> str:
    """Get confidence label from score."""
    if score >= 75:
        return "High"
    if score >= 45:
        return "Medium"
    return "Low"


def confidence_proxy(source_count: int, scenario_count: int) -> str:
    """Get confidence proxy label."""
    if source_count >= 5 and scenario_count >= 4:
        return "High"
    if source_count >= 3 and scenario_count >= 2:
        return "Medium"
    return "Low"


def eligibility_status(metrics: dict[str, Any]) -> str:
    """Determine eligibility status."""
    if metrics["has_unresolved_canonicalization"] or metrics["has_placeholder_data"]:
        return "ineligible"
    if metrics["source_count"] >= 5 and metrics["scenario_count"] >= 4:
        return "eligible"
    if metrics["source_count"] >= 2 and metrics["scenario_count"] >= 2:
        return "provisional"
    return "ineligible"


def eligibility_reason(status: str, metrics: dict[str, Any]) -> str:
    """Generate eligibility reason text."""
    if status == "eligible":
        return "meets_source_and_scenario_thresholds_for_review"
    
    reasons: list[str] = []
    if metrics["source_count"] < 5:
        reasons.append("insufficient_sources_for_review")
    if metrics["scenario_count"] < 4:
        reasons.append("insufficient_scenarios_for_review")
    if metrics["has_unresolved_canonicalization"]:
        reasons.append("unresolved_canonicalization")
    if metrics["has_placeholder_data"]:
        reasons.append("placeholder_or_todo_data")
    
    return ";".join(reasons)


def uncertainty_flags(metrics: dict[str, Any], missing_dimensions: list[str]) -> list[str]:
    """Generate uncertainty flags."""
    flags = ["draft_unreviewed", "not_official"]
    
    if metrics["source_count"] < 5:
        flags.append("insufficient_sources")
    if metrics["scenario_count"] < 4:
        flags.append("insufficient_scenarios")
    if missing_dimensions:
        flags.append("missing_dimensions")
    if metrics["source_quality"] < 0.6:
        flags.append("low_source_quality")
    if metrics["has_unresolved_canonicalization"]:
        flags.append("unresolved_canonicalization")
    if metrics["has_placeholder_data"]:
        flags.append("placeholder_or_todo_data")
    
    return flags


def get_missing_dimensions(scenario_scores: dict[str, float]) -> list[str]:
    """Get list of missing scenario dimensions."""
    return [scenario for scenario in SCENARIO_WEIGHTS if scenario not in scenario_scores]


# ============================================================================
# AGGREGATION FUNCTIONS
# ============================================================================

def group_rows_by_model_scenario(rows: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    """Group rows by model and scenario."""
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    
    for row in rows:
        canonical_id = row.get("canonical_id", "")
        if not canonical_id:
            continue
        scenario = category_to_scenario(row.get("category_primary", ""))
        groups[(canonical_id, scenario)].append(row)
    
    return groups


def collect_model_data(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    """Collect and aggregate data for each model."""
    by_model_scenario = group_rows_by_model_scenario(rows)
    
    model_data: dict[str, dict[str, Any]] = {}
    
    for (canonical_id, scenario), scenario_rows in by_model_scenario.items():
        avg = weighted_average(scenario_rows)
        if avg is None:
            continue
        
        if canonical_id not in model_data:
            provider = scenario_rows[0].get("provider", "") if scenario_rows else ""
            model_data[canonical_id] = {
                "canonical_id": canonical_id,
                "provider": provider,
                "scenario_scores": {},
                "source_ids": set(),
                "rows": [],
            }
        
        model_data[canonical_id]["scenario_scores"][scenario] = avg
        model_data[canonical_id]["rows"].extend(scenario_rows)
    
    # Collect source IDs
    for row in rows:
        canonical_id = row.get("canonical_id", "")
        source_id = row.get("source_id", "")
        if canonical_id and source_id and canonical_id in model_data:
            model_data[canonical_id]["source_ids"].add(source_id)
    
    return model_data


def build_output_row(model_data: dict[str, Any]) -> dict[str, str] | None:
    """Build output row from model data."""
    overall = overall_score(model_data["scenario_scores"])
    if overall is None:
        return None
    
    metrics = calculate_confidence_metrics(model_data)
    missing_dimensions = get_missing_dimensions(model_data["scenario_scores"])
    score = confidence_score(metrics)
    label = confidence_label(score)
    eligibility = eligibility_status(metrics)
    
    row = {
        "rank": "",
        "canonical_id": model_data["canonical_id"],
        "provider": model_data["provider"],
        "overall_score": f"{overall:.6f}",
        "confidence_proxy": confidence_proxy(metrics["source_count"], metrics["scenario_count"]),
        "confidence_score": f"{score:.6f}",
        "confidence_label": label,
        "eligibility_status": eligibility,
        "eligibility_reason": eligibility_reason(eligibility, metrics),
        "publication_status": "unpublished",
        "review_status": "draft_unreviewed",
        "official_status": "not_official",
        "uncertainty_flags": ";".join(uncertainty_flags(metrics, missing_dimensions)),
        "missing_dimensions": ";".join(missing_dimensions),
        "scenario_count": str(metrics["scenario_count"]),
        "source_count": str(metrics["source_count"]),
    }
    
    for scenario in SCENARIO_WEIGHTS:
        scenario_score = model_data["scenario_scores"].get(scenario)
        row[scenario] = "" if scenario_score is None else f"{scenario_score:.6f}"
    
    return row


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Aggregate normalized rows into model scores."""
    model_data_map = collect_model_data(rows)
    
    output: list[dict[str, str]] = []
    for model_data in model_data_map.values():
        row = build_output_row(model_data)
        if row:
            output.append(row)
    
    output.sort(key=lambda r: float(r["overall_score"]), reverse=True)
    
    for idx, row in enumerate(output, 1):
        row["rank"] = str(idx)
    
    return output


# ============================================================================
# OUTPUT FUNCTIONS
# ============================================================================

def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write rows to CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def format_markdown_row(row: dict[str, str]) -> str:
    """Format a single row for markdown table."""
    status = f"{row['review_status']} / {row['publication_status']} / {row['official_status']}"
    return (
        f"| {row['rank']} | `{row['canonical_id']}` | {row['provider']} | "
        f"{float(row['overall_score']):.2f} | {row['confidence_label']} ({float(row['confidence_score']):.1f}) | "
        f"{row['eligibility_status']} | {status} | {row['source_count']} |"
    )


def write_markdown(path: Path, rows: list[dict[str, str]], title: str = "LLM Reality Rank Draft Scores") -> None:
    """Write rows to markdown file."""
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
    
    lines.extend(format_markdown_row(row) for row in rows)
    
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    """Main entry point."""
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

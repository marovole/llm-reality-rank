#!/usr/bin/env python3
"""
Validate data integrity for LLM Reality Rank.

Validates sources, models, and rankings data for consistency and completeness.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

# ============================================================================
# CONSTANTS
# ============================================================================

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "llm-reality-rank"

REQUIRED_SOURCE_FIELDS = {
    "source_id", "priority", "name", "urls", "categories",
    "metric_types", "source_trust", "contamination_risk",
}

REQUIRED_MODEL_FIELDS = {
    "canonical_id", "display_name", "provider", "provider_slug",
    "model_family", "model_variant", "version", "model_type", "access_type",
}

REQUIRED_RANKING_FIELDS = {
    "source_id", "source_name", "source_priority", "category_primary",
    "metric_name", "metric_type", "model_name_raw", "canonical_id",
    "provider", "rank_raw", "score_raw", "score_unit",
    "score_higher_is_better", "date_published", "date_observed",
    "source_url", "evaluation_independence", "source_trust",
    "contamination_risk", "freshness_weight", "notes",
}

CORE_REQUIRED_RANKING_VALUES = {
    "source_id", "source_name", "source_priority", "category_primary",
    "metric_name", "metric_type", "model_name_raw", "provider",
    "date_observed", "source_url", "evaluation_independence",
    "source_trust", "contamination_risk", "notes",
}

VALID_BOOLEAN_VALUES = {"true", "false", ""}


# ============================================================================
# DATA LOADING
# ============================================================================

def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    """Load CSV rows from file."""
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_sources(sources: list[dict]) -> list[str]:
    """Validate sources data."""
    errors: list[str] = []
    source_ids: set[str] = set()
    
    for idx, source in enumerate(sources, 1):
        missing = REQUIRED_SOURCE_FIELDS - set(source)
        if missing:
            errors.append(f"source #{idx} missing fields: {sorted(missing)}")
        
        source_id = source.get("source_id")
        if source_id in source_ids:
            errors.append(f"duplicate source_id: {source_id}")
        if source_id:
            source_ids.add(source_id)
    
    return errors, source_ids


def validate_models(models: list[dict]) -> list[str]:
    """Validate models data."""
    errors: list[str] = []
    model_ids: set[str] = set()
    
    for idx, model in enumerate(models, 1):
        missing = REQUIRED_MODEL_FIELDS - set(model)
        if missing:
            errors.append(f"model #{idx} missing fields: {sorted(missing)}")
        
        canonical_id = model.get("canonical_id")
        if canonical_id in model_ids:
            errors.append(f"duplicate canonical_id: {canonical_id}")
        if canonical_id:
            model_ids.add(canonical_id)
    
    return errors, model_ids


def validate_ranking_header(header: set[str]) -> list[str]:
    """Validate ranking CSV header."""
    missing = REQUIRED_RANKING_FIELDS - header
    if missing:
        return [f"raw_rankings.csv missing columns: {sorted(missing)}"]
    return []


def validate_ranking_row(
    row: dict[str, str],
    row_num: int,
    source_ids: set[str],
    model_ids: set[str],
) -> list[str]:
    """Validate a single ranking row."""
    errors: list[str] = []
    
    source_id = row.get("source_id")
    canonical_id = row.get("canonical_id")
    
    # Check required values
    missing_values = [
        field for field in sorted(CORE_REQUIRED_RANKING_VALUES)
        if not row.get(field, "").strip()
    ]
    if missing_values:
        errors.append(f"row {row_num}: missing required values: {missing_values}")
    
    # Check source_id exists
    if source_id and source_id not in source_ids:
        errors.append(f"row {row_num}: unknown source_id {source_id}")
    
    # Check canonical_id exists
    if canonical_id and canonical_id not in model_ids:
        errors.append(f"row {row_num}: unknown canonical_id {canonical_id}")
    
    # Check boolean value
    higher = row.get("score_higher_is_better", "").lower()
    if higher not in VALID_BOOLEAN_VALUES:
        errors.append(f"row {row_num}: score_higher_is_better must be true/false/empty")
    
    return errors


def validate_rankings(
    rows: list[dict[str, str]],
    source_ids: set[str],
    model_ids: set[str],
) -> list[str]:
    """Validate all ranking rows."""
    errors: list[str] = []
    
    for row_num, row in enumerate(rows, 2):
        errors.extend(validate_ranking_row(row, row_num, source_ids, model_ids))
    
    return errors


# ============================================================================
# MAIN
# ============================================================================

def print_results(errors: list[str]) -> None:
    """Print validation results."""
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    
    print("VALIDATION PASSED")


def main() -> None:
    """Main entry point."""
    errors: list[str] = []
    
    # Load data
    sources_doc = load_yaml(DATA / "sources.yaml")
    models_doc = load_yaml(DATA / "models.yaml")
    
    sources = sources_doc.get("sources", [])
    models = models_doc.get("models", [])
    
    # Validate sources and models
    source_errors, source_ids = validate_sources(sources)
    errors.extend(source_errors)
    
    model_errors, model_ids = validate_models(models)
    errors.extend(model_errors)
    
    # Validate rankings
    ranking_rows = load_csv_rows(DATA / "raw_rankings.csv")
    header = set(ranking_rows[0].keys()) if ranking_rows else set()
    errors.extend(validate_ranking_header(header))
    errors.extend(validate_rankings(ranking_rows, source_ids, model_ids))
    
    print_results(errors)


if __name__ == "__main__":
    main()

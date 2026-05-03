#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "llm-reality-rank"

REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "priority",
    "name",
    "urls",
    "categories",
    "metric_types",
    "source_trust",
    "contamination_risk",
}

REQUIRED_MODEL_FIELDS = {
    "canonical_id",
    "display_name",
    "provider",
    "provider_slug",
    "model_family",
    "model_variant",
    "version",
    "model_type",
    "access_type",
}

REQUIRED_RANKING_FIELDS = {
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
}

CORE_REQUIRED_RANKING_VALUES = {
    "source_id",
    "source_name",
    "source_priority",
    "category_primary",
    "metric_name",
    "metric_type",
    "model_name_raw",
    "provider",
    "date_observed",
    "source_url",
    "evaluation_independence",
    "source_trust",
    "contamination_risk",
    "notes",
}


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fail(errors: list[str]) -> None:
    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    print("VALIDATION PASSED")


def main() -> None:
    errors: list[str] = []

    sources_doc = load_yaml(DATA / "sources.yaml")
    models_doc = load_yaml(DATA / "models.yaml")

    sources = sources_doc.get("sources", [])
    models = models_doc.get("models", [])

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

    with (DATA / "raw_rankings.csv").open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = REQUIRED_RANKING_FIELDS - header
        if missing:
            errors.append(f"raw_rankings.csv missing columns: {sorted(missing)}")

        for row_num, row in enumerate(reader, 2):
            source_id = row.get("source_id")
            canonical_id = row.get("canonical_id")

            missing_values = [
                field
                for field in sorted(CORE_REQUIRED_RANKING_VALUES)
                if not row.get(field, "").strip()
            ]
            if missing_values:
                errors.append(f"row {row_num}: missing required values: {missing_values}")

            if source_id and source_id not in source_ids:
                errors.append(f"row {row_num}: unknown source_id {source_id}")
            if canonical_id and canonical_id not in model_ids:
                errors.append(f"row {row_num}: unknown canonical_id {canonical_id}")

            higher = row.get("score_higher_is_better", "").lower()
            if higher not in {"true", "false", ""}:
                errors.append(f"row {row_num}: score_higher_is_better must be true/false/empty")

    fail(errors)


if __name__ == "__main__":
    main()

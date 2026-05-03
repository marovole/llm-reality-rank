#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "llm-reality-rank"
OUTPUTS = ROOT / "outputs" / "llm-reality-rank"
SNAPSHOTS = ROOT / "snapshots" / "llm-reality-rank"
API = OUTPUTS / "api" / "v1"

SCENARIO_DIMENSIONS = [
    ("General", "General capability", "通用能力"),
    ("Reasoning_Math", "Reasoning and math", "推理/数学"),
    ("Coding", "Coding", "编程能力"),
    ("Chinese", "Chinese capability", "中文能力"),
    ("Multimodal_Doc", "Multimodal and document understanding", "多模态/文档理解"),
    ("Agent_ToolUse", "Agent and tool use", "Agent/工具调用"),
    ("Practicality", "Practicality", "成本/速度/上下文"),
    ("Ecosystem", "Ecosystem", "生态/可用性"),
]

PRESETS = [
    {
        "id": "coding",
        "display_name": "Coding / AI 编程",
        "description": "Prioritizes coding benchmarks, reasoning, and practical API usability.",
        "weights": {"Coding": 0.50, "Reasoning_Math": 0.20, "Practicality": 0.20, "General": 0.10},
    },
    {
        "id": "chinese_writing",
        "display_name": "Chinese writing / 中文写作",
        "description": "Prioritizes Chinese capability, general quality, and ecosystem availability.",
        "weights": {"Chinese": 0.50, "General": 0.25, "Ecosystem": 0.15, "Practicality": 0.10},
    },
    {
        "id": "agent_workflows",
        "display_name": "Agent workflows / Agent 工作流",
        "description": "Prioritizes tool use, coding, reasoning, and long-task practicality.",
        "weights": {"Agent_ToolUse": 0.40, "Coding": 0.20, "Reasoning_Math": 0.20, "Practicality": 0.20},
    },
    {
        "id": "budget_api",
        "display_name": "Budget/API value / 预算 API 选型",
        "description": "Prioritizes cost, latency, context, ecosystem, and adequate general capability.",
        "weights": {"Practicality": 0.45, "Ecosystem": 0.20, "General": 0.20, "Coding": 0.15},
    },
    {
        "id": "multimodal",
        "display_name": "Multimodal / 多模态",
        "description": "Prioritizes multimodal/document performance plus general and reasoning ability.",
        "weights": {"Multimodal_Doc": 0.50, "General": 0.20, "Reasoning_Math": 0.15, "Practicality": 0.15},
    },
    {
        "id": "open_weight",
        "display_name": "Open-weight usage / 开放权重",
        "description": "Prioritizes deployable/open-weight models with coding, Chinese, and practical strength.",
        "weights": {"Ecosystem": 0.25, "Practicality": 0.25, "Coding": 0.20, "Chinese": 0.15, "General": 0.15},
        "filters": {"model_type": ["open_weight", "open_source", "hosted_open_weight", "local_only"]},
    },
]

BLOCKING_NOTE_MARKERS = ("todo", "placeholder", "smoke-test", "smoke test", "unresolved", "unsupported")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def note_has_blocker(note: str) -> str | None:
    lowered = (note or "").lower()
    for marker in BLOCKING_NOTE_MARKERS:
        if marker in lowered:
            return marker
    return None


def source_primary_url(source: dict[str, Any]) -> str:
    urls = source.get("urls") or {}
    if isinstance(urls, dict):
        for value in urls.values():
            if value:
                return str(value)
    return ""


def validate_promotion_inputs(
    raw_rows: list[dict[str, str]],
    normalized_rows: list[dict[str, str]],
    score_rows: list[dict[str, str]],
    sources: list[dict[str, Any]],
    models: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    source_ids = {source.get("source_id") for source in sources if source.get("source_id")}
    model_ids = {model.get("canonical_id") for model in models if model.get("canonical_id")}

    if not raw_rows:
        errors.append("raw_rankings has no rows to promote")
    if not normalized_rows:
        errors.append("normalized_scores has no rows to promote")
    if not score_rows:
        errors.append("model_scores has no rows to promote")

    for row_num, row in enumerate(raw_rows, 2):
        source_id = row.get("source_id", "").strip()
        canonical_id = row.get("canonical_id", "").strip()
        note = row.get("notes", "")
        blocker = note_has_blocker(note)
        if blocker:
            errors.append(f"raw row {row_num}: blocking marker '{blocker}' in notes: {note}")
        if not source_id or source_id not in source_ids:
            errors.append(f"raw row {row_num}: source_id does not resolve: {source_id or '<missing>'}")
        if not canonical_id or canonical_id not in model_ids:
            errors.append(f"raw row {row_num}: canonical_id does not resolve: {canonical_id or '<missing>'}")
        if parse_float(row.get("score_raw")) is None and parse_float(row.get("rank_raw")) is None:
            errors.append(f"raw row {row_num}: missing numeric score_raw or rank_raw")
        if not row.get("source_url", "").strip() or row.get("source_url", "").strip().upper() == "TBD":
            errors.append(f"raw row {row_num}: missing supported source_url")
        if not row.get("date_observed", "").strip():
            errors.append(f"raw row {row_num}: missing date_observed")

    for row_num, row in enumerate(normalized_rows, 2):
        blocker = note_has_blocker(row.get("notes", ""))
        if blocker:
            errors.append(f"normalized row {row_num}: blocking marker '{blocker}' in notes")
        if parse_float(row.get("score_normalized")) is None:
            errors.append(f"normalized row {row_num}: missing score_normalized")
        if row.get("source_id") not in source_ids:
            errors.append(f"normalized row {row_num}: source_id does not resolve: {row.get('source_id')}")
        if row.get("canonical_id") not in model_ids:
            errors.append(f"normalized row {row_num}: canonical_id does not resolve: {row.get('canonical_id')}")

    for row_num, row in enumerate(score_rows, 2):
        if row.get("canonical_id") not in model_ids:
            errors.append(f"score row {row_num}: canonical_id does not resolve: {row.get('canonical_id')}")
        if parse_float(row.get("overall_score")) is None:
            errors.append(f"score row {row_num}: missing overall_score")

    for source in sources:
        source_id = source.get("source_id", "<missing>")
        primary_url = source_primary_url(source)
        if source_id in {row.get("source_id") for row in raw_rows}:
            if not primary_url or primary_url.upper() == "TBD":
                errors.append(f"source {source_id}: missing supported registered URL")
            blocker = note_has_blocker(str(source.get("notes", "")))
            if blocker:
                errors.append(f"source {source_id}: blocking marker '{blocker}' in source notes")

    return errors


def evidence_id(snapshot_id: str, row: dict[str, str], index: int) -> str:
    content = "|".join(
        [
            snapshot_id,
            str(index),
            row.get("source_id", ""),
            row.get("metric_name", ""),
            row.get("canonical_id", ""),
            row.get("score_raw", ""),
            row.get("rank_raw", ""),
            row.get("date_observed", ""),
        ]
    )
    return "ev_" + hashlib.sha1(content.encode("utf-8")).hexdigest()[:16]


def build_source_evidence(snapshot_id: str, normalized_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for index, row in enumerate(normalized_rows, 1):
        evidence.append(
            {
                "evidence_id": evidence_id(snapshot_id, row, index),
                "snapshot_id": snapshot_id,
                "source_id": row.get("source_id", ""),
                "canonical_id": row.get("canonical_id", ""),
                "metric_name": row.get("metric_name", ""),
                "category_primary": row.get("category_primary", ""),
                "model_name_raw": row.get("model_name_raw", ""),
                "rank_raw": parse_float(row.get("rank_raw")),
                "score_raw": parse_float(row.get("score_raw")),
                "score_normalized": parse_float(row.get("score_normalized")),
                "source_effective_weight": parse_float(row.get("source_effective_weight")),
                "date_observed": row.get("date_observed", ""),
                "source_url": row.get("source_url", ""),
                "notes": row.get("notes", ""),
            }
        )
    return evidence


def included_sources(raw_rows: list[dict[str, str]], sources_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    source_ids = sorted({row.get("source_id", "") for row in raw_rows if row.get("source_id", "")})
    included: list[dict[str, Any]] = []
    for source_id in source_ids:
        source = sources_by_id.get(source_id, {})
        urls = source.get("urls") or {}
        included.append(
            {
                "source_id": source_id,
                "name": source.get("name", source_id),
                "priority": source.get("priority", ""),
                "categories": source.get("categories", []),
                "metric_types": source.get("metric_types", []),
                "urls": urls,
                "source_url": source_primary_url(source),
                "notes": source.get("notes", ""),
            }
        )
    return included


def build_snapshot_manifest(
    *,
    snapshot_id: str,
    generated_at: str,
    raw_rows: list[dict[str, str]],
    normalized_rows: list[dict[str, str]],
    score_rows: list[dict[str, str]],
    sources_doc: dict[str, Any],
    models_doc: dict[str, Any],
) -> dict[str, Any]:
    sources = sources_doc.get("sources", [])
    models = models_doc.get("models", [])
    sources_by_id = {source.get("source_id"): source for source in sources}
    observed_dates = sorted({row.get("date_observed", "") for row in raw_rows if row.get("date_observed", "")})
    return {
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "reviewed_at": generated_at,
        "release_stage": "alpha" if "alpha" in snapshot_id.lower() else "snapshot",
        "review_status": "reviewed",
        "publication_status": "published",
        "official_status": "reviewed_snapshot_not_absolute_truth",
        "methodology_version": sources_doc.get("metadata", {}).get(
            "methodology_doc", "docs/llm-reality-rank-scoring-methodology.md"
        ),
        "limitations": [
            "Alpha snapshot: intentionally small reviewed seed dataset for downstream content and site integration; it is not comprehensive or final.",
            "Reviewed snapshot data is traceable but remains benchmark-dependent and should not be treated as absolute truth.",
            "Sparse or missing dimensions are exposed explicitly rather than imputed.",
        ],
        "included_sources": included_sources(raw_rows, sources_by_id),
        "row_counts": {
            "raw_rankings": len(raw_rows),
            "normalized_scores": len(normalized_rows),
            "model_scores": len(score_rows),
            "models": len(models),
            "sources": len(sources),
        },
        "freshness": {
            "date_observed_min": observed_dates[0] if observed_dates else "",
            "date_observed_max": observed_dates[-1] if observed_dates else "",
            "observed_dates": observed_dates,
        },
        "artifacts": {
            "manifest": "manifest.json",
            "leaderboard": "leaderboard.json",
            "source_evidence": "source-evidence.json",
            "models": "models.json",
            "sources": "sources.json",
            "scores": "scores.json",
            "scenarios": "scenarios.json",
            "snapshots": "snapshots.json",
            "selector_data": "selector-data.json",
        },
    }


def build_models_api(models: list[dict[str, Any]], scored_model_ids: set[str]) -> dict[str, Any]:
    records = []
    for model in models:
        canonical_id = model.get("canonical_id", "")
        if canonical_id not in scored_model_ids:
            continue
        records.append(
            {
                "canonical_id": canonical_id,
                "display_name": model.get("display_name", canonical_id),
                "provider": model.get("provider", ""),
                "provider_slug": model.get("provider_slug", ""),
                "model_family": model.get("model_family", ""),
                "model_variant": model.get("model_variant", ""),
                "version": model.get("version", ""),
                "model_type": model.get("model_type", ""),
                "access_type": model.get("access_type", ""),
                "open_weight": model.get("model_type") in {"open_weight", "open_source", "hosted_open_weight"},
                "availability": {
                    "access_type": model.get("access_type", ""),
                    "api_model_ids": model.get("api_model_ids", []),
                },
                "aliases": model.get("aliases", []),
                "source_names": model.get("aliases", []),
                "notes": model.get("notes", ""),
                "status": "active",
            }
        )
    records.sort(key=lambda record: record["canonical_id"])
    return {"models": records}


def build_sources_api(sources: list[dict[str, Any]], used_source_ids: set[str], raw_rows: list[dict[str, str]]) -> dict[str, Any]:
    last_observed: dict[str, str] = {}
    for row in raw_rows:
        source_id = row.get("source_id", "")
        observed = row.get("date_observed", "")
        if observed and observed > last_observed.get(source_id, ""):
            last_observed[source_id] = observed

    records = []
    for source in sources:
        source_id = source.get("source_id", "")
        if source_id not in used_source_ids:
            continue
        records.append(
            {
                "source_id": source_id,
                "name": source.get("name", source_id),
                "priority": source.get("priority", ""),
                "categories": source.get("categories", []),
                "dimensions": source.get("categories", []),
                "metric_types": source.get("metric_types", []),
                "urls": source.get("urls", {}),
                "source_url": source_primary_url(source),
                "organization": source.get("organization", ""),
                "source_trust": source.get("source_trust", ""),
                "contamination_risk": source.get("contamination_risk", ""),
                "evaluation_independence": source.get("evaluation_independence", ""),
                "last_observed": last_observed.get(source_id, ""),
                "notes": source.get("notes", ""),
                "status": "active",
            }
        )
    records.sort(key=lambda record: record["source_id"])
    return {"sources": records}


def build_scenarios_api() -> dict[str, Any]:
    return {
        "dimensions": [
            {"id": key, "display_name": display, "label_zh": label_zh}
            for key, display, label_zh in SCENARIO_DIMENSIONS
        ],
        "presets": PRESETS,
    }


def build_scores_api(
    snapshot_id: str,
    score_rows: list[dict[str, str]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence_by_model: dict[str, list[dict[str, Any]]] = {}
    for item in evidence:
        evidence_by_model.setdefault(item["canonical_id"], []).append(item)

    scores = []
    dimension_ids = [dimension[0] for dimension in SCENARIO_DIMENSIONS]
    for row in score_rows:
        canonical_id = row.get("canonical_id", "")
        dimension_scores = {
            dimension: parse_float(row.get(dimension))
            for dimension in dimension_ids
            if parse_float(row.get(dimension)) is not None
        }
        model_evidence = evidence_by_model.get(canonical_id, [])
        source_refs = [
            {
                "evidence_id": item["evidence_id"],
                "source_id": item["source_id"],
                "metric_name": item["metric_name"],
                "dimension": item["category_primary"],
                "date_observed": item["date_observed"],
                "url": item["source_url"],
                "notes": item["notes"],
            }
            for item in model_evidence
        ]
        scores.append(
            {
                "score_id": f"{snapshot_id}:{canonical_id}",
                "snapshot_id": snapshot_id,
                "canonical_id": canonical_id,
                "rank": int(row.get("rank") or 0),
                "overall_score": parse_float(row.get("overall_score")),
                "dimension_scores": dimension_scores,
                "missing_dimensions": split_semicolon(row.get("missing_dimensions")),
                "confidence": {
                    "score": parse_float(row.get("confidence_score")),
                    "label": row.get("confidence_label", ""),
                    "proxy": row.get("confidence_proxy", ""),
                },
                "eligibility": {
                    "status": row.get("eligibility_status", ""),
                    "reason": row.get("eligibility_reason", ""),
                },
                "publication_status": "published",
                "review_status": "reviewed",
                "official_status": "reviewed_snapshot_not_absolute_truth",
                "uncertainty_flags": split_semicolon(row.get("uncertainty_flags")),
                "source_coverage": {
                    "source_count": int(row.get("source_count") or len({item["source_id"] for item in model_evidence})),
                    "scenario_count": int(row.get("scenario_count") or len(dimension_scores)),
                    "evidence_count": len(model_evidence),
                },
                "source_refs": source_refs,
            }
        )
    scores.sort(key=lambda score: (score["rank"], score["canonical_id"]))
    return {"scores": scores}


def build_snapshots_api(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_snapshot_id": manifest["snapshot_id"],
        "snapshots": [
            {
                "snapshot_id": manifest["snapshot_id"],
                "date": manifest["generated_at"][:10],
                "generated_at": manifest["generated_at"],
                "review_status": manifest["review_status"],
                "publication_status": manifest["publication_status"],
                "current": True,
                "latest": True,
                "freshness": manifest["freshness"],
                "artifacts": manifest["artifacts"],
                "limitations": manifest["limitations"],
            }
        ],
    }


def build_api_manifest(snapshot_id: str, generated_at: str) -> dict[str, Any]:
    return {
        "api_version": "v1",
        "generated_at": generated_at,
        "current_snapshot_id": snapshot_id,
        "endpoints": {
            "manifest": "/api/v1/manifest.json",
            "models": "/api/v1/models.json",
            "scores": "/api/v1/scores.json",
            "source_evidence": "/api/v1/source-evidence.json",
            "sources": "/api/v1/sources.json",
            "scenarios": "/api/v1/scenarios.json",
            "snapshots": "/api/v1/snapshots.json",
            "selector_data": "/api/v1/selector-data.json",
        },
        "disclaimer": "Reviewed snapshot data is traceable and client-ready, but it is not official truth; confidence, missing dimensions, and limitations must be shown with rankings.",
    }


def build_selector_data(
    snapshot_id: str,
    models_api: dict[str, Any],
    scores_api: dict[str, Any],
    scenarios_api: dict[str, Any],
) -> dict[str, Any]:
    models_by_id = {model["canonical_id"]: model for model in models_api["models"]}
    selector_models = []
    for score in scores_api["scores"]:
        model = models_by_id.get(score["canonical_id"], {})
        selector_models.append(
            {
                "canonical_id": score["canonical_id"],
                "display_name": model.get("display_name", score["canonical_id"]),
                "provider": model.get("provider", ""),
                "model_type": model.get("model_type", ""),
                "access_type": model.get("access_type", ""),
                "snapshot_id": snapshot_id,
                "scores": {
                    "overall_score": score["overall_score"],
                    "dimensions": score["dimension_scores"],
                },
                "confidence": score["confidence"],
                "missing_dimensions": score["missing_dimensions"],
                "source_ids": sorted({source_ref["source_id"] for source_ref in score["source_refs"]}),
                "source_refs": score["source_refs"],
            }
        )
    return {
        "snapshot_id": snapshot_id,
        "dimensions": scenarios_api["dimensions"],
        "presets": scenarios_api["presets"],
        "models": selector_models,
    }


def write_snapshot_and_api(
    snapshot_dir: Path,
    api_root: Path,
    manifest: dict[str, Any],
    leaderboard: dict[str, Any],
    evidence: list[dict[str, Any]],
    models_api: dict[str, Any],
    scores_api: dict[str, Any],
    sources_api: dict[str, Any],
    scenarios_api: dict[str, Any],
    snapshots_api: dict[str, Any],
    api_manifest: dict[str, Any],
    selector_data: dict[str, Any],
) -> None:
    if snapshot_dir.exists() and any(snapshot_dir.iterdir()):
        raise FileExistsError(f"snapshot directory already exists and is immutable: {snapshot_dir}")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    write_json(snapshot_dir / "manifest.json", manifest)
    write_json(snapshot_dir / "leaderboard.json", leaderboard)
    write_json(snapshot_dir / "source-evidence.json", {"source_evidence": evidence})
    write_json(snapshot_dir / "models.json", models_api)
    write_json(snapshot_dir / "scores.json", scores_api)
    write_json(snapshot_dir / "sources.json", sources_api)
    write_json(snapshot_dir / "scenarios.json", scenarios_api)
    write_json(snapshot_dir / "snapshots.json", snapshots_api)
    write_json(snapshot_dir / "selector-data.json", selector_data)

    write_json(api_root / "manifest.json", api_manifest)
    write_json(api_root / "models.json", models_api)
    write_json(api_root / "scores.json", scores_api)
    write_json(api_root / "source-evidence.json", {"source_evidence": evidence})
    write_json(api_root / "sources.json", sources_api)
    write_json(api_root / "scenarios.json", scenarios_api)
    write_json(api_root / "snapshots.json", snapshots_api)
    write_json(api_root / "selector-data.json", selector_data)


def promote_reviewed_snapshot(
    *,
    snapshot_id: str,
    raw_rankings_path: Path,
    normalized_scores_path: Path,
    model_scores_path: Path,
    sources_path: Path,
    models_path: Path,
    snapshot_root: Path = SNAPSHOTS,
    api_root: Path = API,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sources_doc = load_yaml(sources_path)
    models_doc = load_yaml(models_path)
    raw_rows = load_csv(raw_rankings_path)
    normalized_rows = load_csv(normalized_scores_path)
    score_rows = load_csv(model_scores_path)
    sources = sources_doc.get("sources", [])
    models = models_doc.get("models", [])

    errors = validate_promotion_inputs(raw_rows, normalized_rows, score_rows, sources, models)
    if errors:
        return {"ok": False, "errors": errors, "snapshot_dir": None, "api_root": None}

    snapshot_dir = snapshot_root / snapshot_id
    manifest = build_snapshot_manifest(
        snapshot_id=snapshot_id,
        generated_at=generated_at,
        raw_rows=raw_rows,
        normalized_rows=normalized_rows,
        score_rows=score_rows,
        sources_doc=sources_doc,
        models_doc=models_doc,
    )
    evidence = build_source_evidence(snapshot_id, normalized_rows)
    scored_model_ids = {row.get("canonical_id", "") for row in score_rows if row.get("canonical_id", "")}
    used_source_ids = {row.get("source_id", "") for row in normalized_rows if row.get("source_id", "")}
    models_api = build_models_api(models, scored_model_ids)
    sources_api = build_sources_api(sources, used_source_ids, raw_rows)
    scenarios_api = build_scenarios_api()
    scores_api = build_scores_api(snapshot_id, score_rows, evidence)
    snapshots_api = build_snapshots_api(manifest)
    api_manifest = build_api_manifest(snapshot_id, generated_at)
    selector_data = build_selector_data(snapshot_id, models_api, scores_api, scenarios_api)
    leaderboard = {
        "snapshot_id": snapshot_id,
        "generated_at": generated_at,
        "review_status": "reviewed",
        "scores": scores_api["scores"],
    }

    try:
        write_snapshot_and_api(
            snapshot_dir,
            api_root,
            manifest,
            leaderboard,
            evidence,
            models_api,
            scores_api,
            sources_api,
            scenarios_api,
            snapshots_api,
            api_manifest,
            selector_data,
        )
    except FileExistsError as exc:
        return {"ok": False, "errors": [str(exc)], "snapshot_dir": None, "api_root": None}

    return {"ok": True, "errors": [], "snapshot_dir": snapshot_dir, "api_root": api_root}


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote reviewed LLM Reality Rank data to immutable snapshot and static API JSON.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--raw-rankings", type=Path, default=DATA / "raw_rankings.csv")
    parser.add_argument("--normalized-scores", type=Path, default=OUTPUTS / "normalized_scores.csv")
    parser.add_argument("--model-scores", type=Path, default=OUTPUTS / "model_scores.csv")
    parser.add_argument("--sources", type=Path, default=DATA / "sources.yaml")
    parser.add_argument("--models", type=Path, default=DATA / "models.yaml")
    parser.add_argument("--snapshot-root", type=Path, default=SNAPSHOTS)
    parser.add_argument("--api-root", type=Path, default=API)
    args = parser.parse_args()

    result = promote_reviewed_snapshot(
        snapshot_id=args.snapshot_id,
        raw_rankings_path=args.raw_rankings,
        normalized_scores_path=args.normalized_scores,
        model_scores_path=args.model_scores,
        sources_path=args.sources,
        models_path=args.models,
        snapshot_root=args.snapshot_root,
        api_root=args.api_root,
    )
    if not result["ok"]:
        print("SNAPSHOT PROMOTION FAILED")
        for error in result["errors"]:
            print(f"- {error}")
        return 1

    print(f"SNAPSHOT PROMOTION PASSED: {result['snapshot_dir']}")
    print(f"STATIC API WRITTEN: {result['api_root']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

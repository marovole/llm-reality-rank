import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm-reality-rank" / "export_reviewed_snapshot.py"


def load_module():
    spec = importlib.util.spec_from_file_location("export_reviewed_snapshot", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_snapshot_manifest_contains_required_review_metadata(tmp_path):
    module = load_module()
    paths = write_fixture_dataset(tmp_path)

    result = module.promote_reviewed_snapshot(
        snapshot_id="2026-05-alpha",
        raw_rankings_path=paths["raw"],
        normalized_scores_path=paths["normalized"],
        model_scores_path=paths["scores"],
        sources_path=paths["sources"],
        models_path=paths["models"],
        snapshot_root=tmp_path / "snapshots",
        api_root=tmp_path / "api" / "v1",
        generated_at="2026-05-03T00:00:00Z",
    )

    manifest = read_json(result["snapshot_dir"] / "manifest.json")

    assert manifest["snapshot_id"] == "2026-05-alpha"
    assert manifest["release_stage"] == "alpha"
    assert manifest["review_status"] == "reviewed"
    assert manifest["publication_status"] == "published"
    assert manifest["generated_at"] == "2026-05-03T00:00:00Z"
    assert manifest["methodology_version"]
    assert manifest["row_counts"] == {
        "raw_rankings": 4,
        "normalized_scores": 4,
        "model_scores": 2,
        "models": 3,
        "sources": 5,
    }
    assert {source["source_id"] for source in manifest["included_sources"]} == {
        "aider_leaderboards",
        "artificial_analysis_llm",
        "livebench",
        "superclue",
    }
    assert all(source["urls"] for source in manifest["included_sources"])
    assert manifest["artifacts"]["source_evidence"] == "source-evidence.json"
    assert any("alpha" in limitation.lower() for limitation in manifest["limitations"])


def test_promotion_fails_for_todo_smoke_unresolved_or_unsupported_data(tmp_path):
    module = load_module()
    paths = write_fixture_dataset(tmp_path, bad_notes=[
        "TODO fill latest score",
        "smoke-test fixture row",
        "canonicalization_status=unresolved",
        "unsupported source evidence",
    ])

    result = module.promote_reviewed_snapshot(
        snapshot_id="bad-snapshot",
        raw_rankings_path=paths["raw"],
        normalized_scores_path=paths["normalized"],
        model_scores_path=paths["scores"],
        sources_path=paths["sources"],
        models_path=paths["models"],
        snapshot_root=tmp_path / "snapshots",
        api_root=tmp_path / "api" / "v1",
        generated_at="2026-05-03T00:00:00Z",
    )

    assert result["ok"] is False
    assert result["snapshot_dir"] is None
    diagnostics = "\n".join(result["errors"])
    assert "TODO" in diagnostics
    assert "smoke-test" in diagnostics
    assert "unresolved" in diagnostics
    assert "unsupported" in diagnostics
    assert not (tmp_path / "snapshots" / "bad-snapshot").exists()


def test_static_api_json_has_valid_schemas_and_cross_references(tmp_path):
    module = load_module()
    paths = write_fixture_dataset(tmp_path)

    result = module.promote_reviewed_snapshot(
        snapshot_id="2026-05-alpha",
        raw_rankings_path=paths["raw"],
        normalized_scores_path=paths["normalized"],
        model_scores_path=paths["scores"],
        sources_path=paths["sources"],
        models_path=paths["models"],
        snapshot_root=tmp_path / "snapshots",
        api_root=tmp_path / "api" / "v1",
        generated_at="2026-05-03T00:00:00Z",
    )

    api_root = result["api_root"]
    manifest = read_json(api_root / "manifest.json")
    models = read_json(api_root / "models.json")["models"]
    scores = read_json(api_root / "scores.json")["scores"]
    sources = read_json(api_root / "sources.json")["sources"]
    scenarios = read_json(api_root / "scenarios.json")
    snapshots = read_json(api_root / "snapshots.json")["snapshots"]

    model_ids = {model["canonical_id"] for model in models}
    source_ids = {source["source_id"] for source in sources}
    snapshot_ids = {snapshot["snapshot_id"] for snapshot in snapshots}
    dimension_ids = {dimension["id"] for dimension in scenarios["dimensions"]}

    assert manifest["api_version"] == "v1"
    assert manifest["current_snapshot_id"] in snapshot_ids
    assert manifest["endpoints"]["models"] == "/api/v1/models.json"
    assert "not official truth" in manifest["disclaimer"]
    assert len(model_ids) == len(models)
    assert "alpha/unused@2026-05" not in model_ids
    assert "unused_source" not in source_ids

    for score in scores:
        assert score["snapshot_id"] in snapshot_ids
        assert score["canonical_id"] in model_ids
        assert set(score["dimension_scores"]).issubset(dimension_ids)
        assert set(score["missing_dimensions"]).issubset(dimension_ids)
        assert score["confidence"]["label"] in {"High", "Medium", "Low"}
        assert score["source_coverage"]["source_count"] >= 1
        assert score["source_refs"]
        for source_ref in score["source_refs"]:
            assert source_ref["source_id"] in source_ids
            assert source_ref["url"].startswith("https://")
            assert source_ref["date_observed"] == "2026-05-03"

    for preset in scenarios["presets"]:
        assert set(preset["weights"]).issubset(dimension_ids)
        assert all(weight >= 0 for weight in preset["weights"].values())


def test_selector_data_contains_dimensions_presets_and_models(tmp_path):
    module = load_module()
    paths = write_fixture_dataset(tmp_path)

    result = module.promote_reviewed_snapshot(
        snapshot_id="2026-05-alpha",
        raw_rankings_path=paths["raw"],
        normalized_scores_path=paths["normalized"],
        model_scores_path=paths["scores"],
        sources_path=paths["sources"],
        models_path=paths["models"],
        snapshot_root=tmp_path / "snapshots",
        api_root=tmp_path / "api" / "v1",
        generated_at="2026-05-03T00:00:00Z",
    )

    selector_data = read_json(result["api_root"] / "selector-data.json")

    assert {dimension["id"] for dimension in selector_data["dimensions"]} >= {
        "General",
        "Coding",
        "Chinese",
        "Practicality",
    }
    assert {preset["id"] for preset in selector_data["presets"]} >= {
        "coding",
        "chinese_writing",
        "agent_workflows",
        "budget_api",
        "multimodal",
        "open_weight",
    }
    assert {model["canonical_id"] for model in selector_data["models"]} == {
        "alpha/model-a@2026-05",
        "alpha/model-b@2026-05",
    }
    assert selector_data["models"][0]["scores"]["overall_score"] is not None
    assert selector_data["models"][0]["confidence"]["label"]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_fixture_dataset(tmp_path: Path, bad_notes: list[str] | None = None) -> dict[str, Path]:
    sources = tmp_path / "sources.yaml"
    models = tmp_path / "models.yaml"
    raw = tmp_path / "raw_rankings.csv"
    normalized = tmp_path / "normalized_scores.csv"
    scores = tmp_path / "model_scores.csv"

    sources.write_text(
        """metadata:
  methodology_doc: docs/llm-reality-rank-scoring-methodology.md
sources:
  - source_id: livebench
    priority: P0
    name: LiveBench
    urls: {primary: "https://livebench.ai/"}
    categories: [general]
    metric_types: [benchmark_score]
    source_trust: high
    contamination_risk: low
    evaluation_independence: independent_third_party
    notes: Reviewed fixture source.
  - source_id: aider_leaderboards
    priority: P0
    name: Aider LLM Leaderboards
    urls: {primary: "https://aider.chat/docs/leaderboards/"}
    categories: [coding]
    metric_types: [pass_rate]
    source_trust: high
    contamination_risk: low_medium
    evaluation_independence: platform_or_community
    notes: Reviewed fixture source.
  - source_id: superclue
    priority: P0
    name: SuperCLUE
    urls: {primary: "https://superclueai.com/"}
    categories: [chinese]
    metric_types: [benchmark_score]
    source_trust: high
    contamination_risk: medium
    evaluation_independence: independent_third_party
    notes: Reviewed fixture source.
  - source_id: artificial_analysis_llm
    priority: P0
    name: Artificial Analysis LLM Leaderboard
    urls: {primary: "https://artificialanalysis.ai/leaderboards/models"}
    categories: [practical]
    metric_types: [aggregate_score]
    source_trust: high
    contamination_risk: low_medium
    evaluation_independence: platform_or_community
    notes: Reviewed fixture source.
  - source_id: unused_source
    priority: P2
    name: Unused Draft Source
    urls: {primary: "TBD"}
    categories: [general]
    metric_types: [accuracy]
    source_trust: medium
    contamination_risk: medium
    evaluation_independence: unknown
    notes: Draft placeholder source that must not enter public API.
""",
        encoding="utf-8",
    )
    models.write_text(
        """metadata:
  normalization_doc: docs/llm-reality-rank-model-normalization.md
models:
  - canonical_id: alpha/model-a@2026-05
    display_name: Alpha Model A
    provider: Alpha
    provider_slug: alpha
    model_family: alpha
    model_variant: a
    version: "2026-05"
    model_type: closed
    access_type: api
    aliases: [Alpha A]
    notes: Reviewed alpha fixture.
  - canonical_id: alpha/model-b@2026-05
    display_name: Alpha Model B
    provider: Alpha
    provider_slug: alpha
    model_family: alpha
    model_variant: b
    version: "2026-05"
    model_type: open_weight
    access_type: api_and_local
    aliases: [Alpha B]
    notes: Reviewed alpha fixture.
  - canonical_id: alpha/unused@2026-05
    display_name: Unused Draft Model
    provider: Alpha
    provider_slug: alpha
    model_family: alpha
    model_variant: unused
    version: "2026-05"
    model_type: closed
    access_type: api
    aliases: [Alpha Unused]
    notes: Draft placeholder model that must not enter public API.
""",
        encoding="utf-8",
    )

    notes = bad_notes or [
        "Reviewed source evidence row.",
        "Reviewed source evidence row.",
        "Reviewed source evidence row.",
        "Reviewed source evidence row.",
    ]
    raw.write_text(
        "\n".join(
            [
                "source_id,source_name,source_priority,category_primary,metric_name,metric_type,model_name_raw,canonical_id,provider,rank_raw,score_raw,score_unit,score_higher_is_better,date_published,date_observed,source_url,evaluation_independence,source_trust,contamination_risk,freshness_weight,notes",
                f"livebench,LiveBench,P0,general,global_average,benchmark_score,Alpha Model A,alpha/model-a@2026-05,Alpha,,88,points,true,,2026-05-03,https://livebench.ai/,independent_third_party,high,low,1.0,{notes[0]}",
                f"aider_leaderboards,Aider LLM Leaderboards,P0,coding,polyglot_score,pass_rate,Alpha Model A,alpha/model-a@2026-05,Alpha,,91,percent,true,,2026-05-03,https://aider.chat/docs/leaderboards/,platform_or_community,high,low_medium,1.0,{notes[1]}",
                f"superclue,SuperCLUE,P0,chinese,overall_score,benchmark_score,Alpha Model B,alpha/model-b@2026-05,Alpha,,84,points,true,,2026-05-03,https://superclueai.com/,independent_third_party,high,medium,1.0,{notes[2]}",
                f"artificial_analysis_llm,Artificial Analysis LLM Leaderboard,P0,practical,intelligence_index,aggregate_score,Alpha Model B,alpha/model-b@2026-05,Alpha,,72,index,true,,2026-05-03,https://artificialanalysis.ai/leaderboards/models,platform_or_community,high,low_medium,1.0,{notes[3]}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    normalized.write_text(
        "\n".join(
            [
                "source_id,metric_name,category_primary,canonical_id,provider,model_name_raw,rank_raw,score_raw,score_normalized,source_effective_weight,score_weighted,source_url,date_observed,notes",
                f"livebench,global_average,general,alpha/model-a@2026-05,Alpha,Alpha Model A,,88,88.000000,1.000000,88.000000,https://livebench.ai/,2026-05-03,{notes[0]}",
                f"aider_leaderboards,polyglot_score,coding,alpha/model-a@2026-05,Alpha,Alpha Model A,,91,91.000000,0.850000,77.350000,https://aider.chat/docs/leaderboards/,2026-05-03,{notes[1]}",
                f"superclue,overall_score,chinese,alpha/model-b@2026-05,Alpha,Alpha Model B,,84,84.000000,0.750000,63.000000,https://superclueai.com/,2026-05-03,{notes[2]}",
                f"artificial_analysis_llm,intelligence_index,practical,alpha/model-b@2026-05,Alpha,Alpha Model B,,72,72.000000,0.850000,61.200000,https://artificialanalysis.ai/leaderboards/models,2026-05-03,{notes[3]}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    scores.write_text(
        "\n".join(
            [
                "rank,canonical_id,provider,overall_score,confidence_proxy,confidence_score,confidence_label,eligibility_status,eligibility_reason,publication_status,review_status,official_status,uncertainty_flags,missing_dimensions,General,Reasoning_Math,Coding,Chinese,Multimodal_Doc,Agent_ToolUse,Practicality,Ecosystem,scenario_count,source_count",
                "1,alpha/model-a@2026-05,Alpha,89.285714,Medium,58.750000,Medium,provisional,insufficient_sources_for_review;insufficient_scenarios_for_review,unpublished,draft_unreviewed,not_official,missing_dimensions,Chinese;Practicality,88.000000,,91.000000,,,,,,2,2",
                "2,alpha/model-b@2026-05,Alpha,78.000000,Medium,56.875000,Medium,provisional,insufficient_sources_for_review;insufficient_scenarios_for_review,unpublished,draft_unreviewed,not_official,missing_dimensions,General;Coding,,,84.000000,,,72.000000,,2,2",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "sources": sources,
        "models": models,
        "raw": raw,
        "normalized": normalized,
        "scores": scores,
    }

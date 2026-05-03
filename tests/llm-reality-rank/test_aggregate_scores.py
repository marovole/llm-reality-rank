import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm-reality-rank" / "aggregate_scores.py"


def load_module():
    spec = importlib.util.spec_from_file_location("aggregate_scores", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_category_to_scenario_maps_known_categories():
    module = load_module()

    assert module.category_to_scenario("general") == "General"
    assert module.category_to_scenario("math") == "Reasoning_Math"
    assert module.category_to_scenario("coding") == "Coding"
    assert module.category_to_scenario("chinese") == "Chinese"
    assert module.category_to_scenario("document_understanding") == "Multimodal_Doc"
    assert module.category_to_scenario("function_calling") == "Agent_ToolUse"
    assert module.category_to_scenario("cost_speed") == "Practicality"
    assert module.category_to_scenario("usage") == "Ecosystem"


def test_weighted_average_uses_source_weights():
    module = load_module()
    rows = [
        {"score_normalized": "100", "source_effective_weight": "1.0"},
        {"score_normalized": "50", "source_effective_weight": "0.5"},
    ]

    assert module.weighted_average(rows) == 83.333333


def test_overall_score_uses_available_scenario_weights_renormalized():
    module = load_module()
    scenario_scores = {"General": 80.0, "Coding": 100.0}

    assert module.overall_score(scenario_scores) == 88.571429


def test_aggregate_maps_categories_to_scenario_columns():
    module = load_module()
    rows = [
        normalized_row("model-a", "general", "80"),
        normalized_row("model-a", "math", "90"),
        normalized_row("model-a", "coding", "70"),
        normalized_row("model-a", "chinese", "60"),
        normalized_row("model-a", "document_understanding", "50"),
        normalized_row("model-a", "function_calling", "40"),
        normalized_row("model-a", "cost_speed", "30"),
        normalized_row("model-a", "usage", "20"),
    ]

    [aggregated] = module.aggregate(rows)

    assert aggregated["General"] == "80.000000"
    assert aggregated["Reasoning_Math"] == "90.000000"
    assert aggregated["Coding"] == "70.000000"
    assert aggregated["Chinese"] == "60.000000"
    assert aggregated["Multimodal_Doc"] == "50.000000"
    assert aggregated["Agent_ToolUse"] == "40.000000"
    assert aggregated["Practicality"] == "30.000000"
    assert aggregated["Ecosystem"] == "20.000000"


def test_aggregate_leaves_missing_scenario_dimensions_empty():
    module = load_module()
    rows = [
        normalized_row("sparse-model", "coding", "91"),
        normalized_row("sparse-model", "chinese", "82"),
    ]

    [aggregated] = module.aggregate(rows)

    assert aggregated["Coding"] == "91.000000"
    assert aggregated["Chinese"] == "82.000000"
    assert aggregated["General"] == ""
    assert aggregated["Reasoning_Math"] == ""
    assert aggregated["Multimodal_Doc"] == ""
    assert aggregated["Agent_ToolUse"] == ""
    assert aggregated["Practicality"] == ""
    assert aggregated["Ecosystem"] == ""


def test_sparse_models_are_not_silently_official():
    module = load_module()
    rows = [normalized_row("sparse-model", "coding", "91")]

    [aggregated] = module.aggregate(rows)

    assert aggregated["eligibility_status"] == "ineligible"
    assert aggregated["publication_status"] == "unpublished"
    assert aggregated["review_status"] == "draft_unreviewed"
    assert aggregated["official_status"] == "not_official"
    assert "insufficient_sources" in aggregated["uncertainty_flags"]
    assert "insufficient_scenarios" in aggregated["uncertainty_flags"]


def test_high_coverage_has_higher_confidence_than_sparse_coverage():
    module = load_module()
    sparse_rows = [normalized_row("sparse-model", "coding", "71", source_id="sparse_source")]
    high_coverage_rows = [
        normalized_row("covered-model", "general", "80", source_id="source_general"),
        normalized_row("covered-model", "math", "82", source_id="source_math"),
        normalized_row("covered-model", "coding", "84", source_id="source_coding"),
        normalized_row("covered-model", "chinese", "86", source_id="source_chinese"),
        normalized_row("covered-model", "function_calling", "88", source_id="source_agent"),
    ]

    rows_by_model = {row["canonical_id"]: row for row in module.aggregate(sparse_rows + high_coverage_rows)}

    assert rows_by_model["covered-model"]["eligibility_status"] == "eligible"
    assert rows_by_model["covered-model"]["confidence_label"] == "High"
    assert float(rows_by_model["covered-model"]["confidence_score"]) > float(
        rows_by_model["sparse-model"]["confidence_score"]
    )


def test_missing_dimensions_are_exposed_without_fabricating_scores():
    module = load_module()
    rows = [
        normalized_row("sparse-model", "coding", "91"),
        normalized_row("sparse-model", "chinese", "82"),
    ]

    [aggregated] = module.aggregate(rows)

    assert aggregated["General"] == ""
    assert aggregated["missing_dimensions"] == (
        "General;Reasoning_Math;Multimodal_Doc;Agent_ToolUse;Practicality;Ecosystem"
    )
    assert "missing_dimensions" in aggregated["uncertainty_flags"]


def test_markdown_output_declares_draft_unreviewed_not_official(tmp_path):
    module = load_module()
    row = {
        "rank": "1",
        "canonical_id": "model-a",
        "provider": "Provider",
        "overall_score": "90.000000",
        "confidence_score": "92.000000",
        "confidence_label": "High",
        "confidence_proxy": "High",
        "source_count": "5",
        "eligibility_status": "eligible",
        "publication_status": "unpublished",
        "review_status": "draft_unreviewed",
        "official_status": "not_official",
        "missing_dimensions": "",
        "uncertainty_flags": "",
    }

    out = tmp_path / "scores.md"
    module.write_markdown(out, [row])

    text = out.read_text(encoding="utf-8")
    assert "Draft/unreviewed generated output" in text
    assert "not an official ranking" in text
    assert "| Rank | Model | Provider | Overall | Confidence | Eligibility | Status | Sources |" in text
    assert "draft_unreviewed / unpublished / not_official" in text


def normalized_row(
    canonical_id: str,
    category: str,
    score: str,
    *,
    source_id: str | None = None,
    weight: str = "1.0",
) -> dict[str, str]:
    return {
        "canonical_id": canonical_id,
        "provider": "Provider",
        "category_primary": category,
        "score_normalized": score,
        "source_effective_weight": weight,
        "source_id": source_id or f"{category}_source",
    }

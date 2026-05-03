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

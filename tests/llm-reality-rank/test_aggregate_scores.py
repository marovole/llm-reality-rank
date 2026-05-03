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
    assert module.category_to_scenario("coding") == "Coding"
    assert module.category_to_scenario("chinese") == "Chinese"
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

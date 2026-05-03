import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm-reality-rank" / "normalize_scores.py"


def load_module():
    spec = importlib.util.spec_from_file_location("normalize_scores", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_normalize_direct_percentage_score():
    module = load_module()
    row = {
        "score_raw": "87.5",
        "rank_raw": "",
        "score_higher_is_better": "true",
        "metric_type": "accuracy",
    }

    assert module.normalize_row_score(row, group_size=5) == 87.5


def test_normalize_rank_with_higher_rank_better():
    module = load_module()
    row = {
        "score_raw": "",
        "rank_raw": "1",
        "score_higher_is_better": "false",
        "metric_type": "usage_ranking",
    }

    assert module.normalize_row_score(row, group_size=5) == 100.0


def test_source_effective_weight_multiplies_policy_factors():
    module = load_module()
    row = {
        "source_trust": "high",
        "contamination_risk": "medium",
        "evaluation_independence": "platform_or_community",
        "freshness_weight": "0.9",
    }

    assert module.source_effective_weight(row) == 0.57375

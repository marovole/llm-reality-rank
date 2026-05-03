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


def test_normalize_elo_scores_within_source_metric_group():
    module = load_module()
    rows = [
        base_row(model="model-a", score_raw="1488", metric_type="elo"),
        base_row(model="model-b", score_raw="1493", metric_type="elo"),
        base_row(model="model-c", score_raw="1491", metric_type="elo"),
    ]

    normalized, skipped = module.normalize_rows(rows)

    assert skipped == 0
    scores = {row["canonical_id"]: row["score_normalized"] for row in normalized}
    assert scores == {
        "model-a": "0.000000",
        "model-b": "100.000000",
        "model-c": "60.000000",
    }


def test_normalize_equal_elo_scores_to_100_within_group():
    module = load_module()
    rows = [
        base_row(model="model-a", score_raw="1488", metric_type="elo"),
        base_row(model="model-b", score_raw="1488", metric_type="elo"),
    ]

    normalized, skipped = module.normalize_rows(rows)

    assert skipped == 0
    assert [row["score_normalized"] for row in normalized] == ["100.000000", "100.000000"]


def test_normalize_rank_only_source_as_inverse_rank_percentile():
    module = load_module()
    rows = [
        base_row(model="model-a", rank_raw="1", metric_type="usage_ranking"),
        base_row(model="model-b", rank_raw="3", metric_type="usage_ranking"),
        base_row(model="model-c", rank_raw="5", metric_type="usage_ranking"),
    ]

    normalized, skipped = module.normalize_rows(rows)

    assert skipped == 0
    scores = {row["canonical_id"]: row["score_normalized"] for row in normalized}
    assert scores == {
        "model-a": "100.000000",
        "model-b": "50.000000",
        "model-c": "0.000000",
    }


def test_normalize_price_and_latency_as_lower_is_better_within_group():
    module = load_module()
    rows = [
        base_row(model="cheap", score_raw="0.5", metric_type="price"),
        base_row(model="middle", score_raw="1.0", metric_type="price"),
        base_row(model="expensive", score_raw="2.0", metric_type="price"),
        base_row(
            source_id="latency_source",
            metric_name="latency_ms",
            model="fast",
            score_raw="100",
            metric_type="latency",
        ),
        base_row(
            source_id="latency_source",
            metric_name="latency_ms",
            model="slow",
            score_raw="300",
            metric_type="latency",
        ),
    ]

    normalized, skipped = module.normalize_rows(rows)

    assert skipped == 0
    scores = {row["canonical_id"]: row["score_normalized"] for row in normalized}
    assert scores["cheap"] == "100.000000"
    assert scores["middle"] == "66.666667"
    assert scores["expensive"] == "0.000000"
    assert scores["fast"] == "100.000000"
    assert scores["slow"] == "0.000000"


def test_normalize_speed_and_large_context_as_higher_is_better_within_group():
    module = load_module()
    rows = [
        base_row(model="slow", score_raw="25", metric_type="speed"),
        base_row(model="fast", score_raw="75", metric_type="speed"),
        base_row(
            source_id="context_source",
            metric_name="context_tokens",
            model="short-context",
            score_raw="32000",
            metric_type="context_window",
        ),
        base_row(
            source_id="context_source",
            metric_name="context_tokens",
            model="long-context",
            score_raw="128000",
            metric_type="context_window",
        ),
    ]

    normalized, skipped = module.normalize_rows(rows)

    assert skipped == 0
    scores = {row["canonical_id"]: row["score_normalized"] for row in normalized}
    assert scores["slow"] == "0.000000"
    assert scores["fast"] == "100.000000"
    assert scores["short-context"] == "0.000000"
    assert scores["long-context"] == "100.000000"


def base_row(
    *,
    source_id: str = "source",
    metric_name: str = "metric",
    model: str,
    rank_raw: str = "",
    score_raw: str = "",
    metric_type: str,
) -> dict[str, str]:
    return {
        "source_id": source_id,
        "metric_name": metric_name,
        "category_primary": "general",
        "canonical_id": model,
        "provider": "Provider",
        "model_name_raw": model,
        "rank_raw": rank_raw,
        "score_raw": score_raw,
        "metric_type": metric_type,
        "score_higher_is_better": "true",
        "source_trust": "high",
        "contamination_risk": "low",
        "evaluation_independence": "independent_third_party",
        "freshness_weight": "1.0",
        "source_url": "https://example.com",
        "date_observed": "2026-05-03",
        "notes": "",
    }

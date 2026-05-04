import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm-reality-rank" / "ingest_sources.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ingest_sources", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cli_list_exposes_first_batch_targets(capsys):
    module = load_module()

    exit_code = module.main(["list"])
    output = capsys.readouterr().out

    assert exit_code == 0
    for target in ["aider", "livebench", "swe_bench_verified", "artificial_analysis", "lmarena"]:
        assert target in output


def test_cli_list_exposes_superclue_target(capsys):
    module = load_module()
    exit_code = module.main(["list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "superclue" in captured
    assert "SuperCLUE" in captured


def test_cli_list_exposes_ceval_target(capsys):
    module = load_module()
    module.main(["list"])
    captured = capsys.readouterr().out
    assert "ceval" in captured
    assert "C-Eval" in captured


def test_cli_list_exposes_opencompass_target(capsys):
    module = load_module()
    module.main(["list"])
    captured = capsys.readouterr().out
    assert "opencompass" in captured
    assert "OpenCompass" in captured


def test_ceval_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "ceval.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Qwen3-Max",
                    "canonical_id": "qwen/qwen3-max@unknown",
                    "provider": "Alibaba",
                    "rank_raw": "1",
                    "score_raw": "89.7",
                    "date_published": "2026-03-20",
                    "date_observed": "2026-05-03",
                    "source_url": "https://cevalbenchmark.com/static/leaderboard.html",
                    "notes": "canonicalization_status=canonicalized",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("ceval", mode="fixture", fixture_path=fixture)
    assert result.status == "ok"
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "ceval"
    assert row["category_primary"] == "chinese"
    assert row["metric_name"] == "ceval_overall"
    assert row["score_raw"] == "89.7"


def test_superclue_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "superclue.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "GPT-5.5",
                    "canonical_id": "openai/gpt-5.5-high@unknown",
                    "provider": "OpenAI",
                    "rank_raw": "1",
                    "score_raw": "82.4",
                    "date_published": "2026-04-15",
                    "date_observed": "2026-05-03",
                    "source_url": "https://superclueai.com/",
                    "notes": "canonicalization_status=canonicalized",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = module.ingest_target("superclue", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "superclue"
    assert row["category_primary"] == "chinese"
    assert row["metric_name"] == "superclue_total"
    assert row["model_name_raw"] == "GPT-5.5"
    assert row["canonical_id"] == "openai/gpt-5.5-high@unknown"
    assert row["score_raw"] == "82.4"


def test_opencompass_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "opencompass.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "DeepSeek V3.5",
                    "canonical_id": "deepseek/deepseek-v3@2025-03-24",
                    "provider": "DeepSeek",
                    "rank_raw": "1",
                    "score_raw": "75.6",
                    "date_published": "2026-04-01",
                    "date_observed": "2026-05-03",
                    "source_url": "https://rank.opencompass.org.cn/leaderboard-llm-v2",
                    "notes": "canonicalization_status=canonicalized",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("opencompass", mode="fixture", fixture_path=fixture)
    assert result.status == "ok"
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "opencompass_llm"
    assert row["category_primary"] == "chinese"


def test_fixture_mode_parses_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "aider.csv"
    fixture.write_text(
        "model_name_raw,canonical_id,provider,rank_raw,score_raw\n"
        "o3 (high),openai/o3@unknown,OpenAI,1,81.3\n",
        encoding="utf-8",
    )

    result = module.ingest_target("aider", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    assert result.rows[0]["source_id"] == "aider_leaderboards"
    assert result.rows[0]["metric_name"] == "polyglot_score"
    assert result.rows[0]["source_url"] == "fixture://aider.csv"
    assert result.rows[0]["notes"].startswith("Fixture ingestion row")


def test_aider_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "aider_polyglot.csv"
    fixture.write_text(
        "Model,Rank,Percent correct,Provider,Canonical ID,Date observed,Source URL,Notes\n"
        "o3 (high),6,81.3,OpenAI,openai/o3@unknown,2026-05-03,https://aider.chat/docs/leaderboards/,Visible polyglot row.\n",
        encoding="utf-8",
    )

    result = module.ingest_target("aider", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "aider_leaderboards"
    assert row["category_primary"] == "coding"
    assert row["metric_name"] == "polyglot_score"
    assert row["metric_type"] == "pass_rate"
    assert row["model_name_raw"] == "o3 (high)"
    assert row["canonical_id"] == "openai/o3@unknown"
    assert row["provider"] == "OpenAI"
    assert row["rank_raw"] == "6"
    assert row["score_raw"] == "81.3"
    assert row["source_url"] == "https://aider.chat/docs/leaderboards/"
    assert "canonicalized" in row["notes"].lower()


def test_livebench_json_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "livebench.json"
    fixture.write_text(
        json.dumps(
            {
                "date_observed": "2026-05-03",
                "source_url": "https://livebench.ai/",
                "rows": [
                    {
                        "model": "Gemini 2.5 Pro",
                        "rank": 1,
                        "global_average": 72.5,
                        "provider": "Google",
                        "canonical_id": "google/gemini-2.5-pro@unknown",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = module.ingest_target("livebench", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "livebench"
    assert row["metric_name"] == "global_average"
    assert row["metric_type"] == "benchmark_score"
    assert row["model_name_raw"] == "Gemini 2.5 Pro"
    assert row["rank_raw"] == "1"
    assert row["score_raw"] == "72.5"
    assert row["score_unit"] == "score"
    assert row["source_url"] == "https://livebench.ai/"
    assert "canonicalized" in row["notes"].lower()


def test_swe_bench_verified_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture = tmp_path / "swe_bench_verified.csv"
    fixture.write_text(
        "name,resolved,rank,provider,canonical_id,date_observed,source_url\n"
        "Claude 3.5 Sonnet,49.0,2,Anthropic,anthropic/claude-3.5-sonnet@2024-10-22,2026-05-03,https://www.swebench.com/\n",
        encoding="utf-8",
    )

    result = module.ingest_target("swe_bench_verified", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "swe_bench_verified"
    assert row["category_primary"] == "coding"
    assert row["metric_name"] == "resolved_rate"
    assert row["metric_type"] == "resolved_issue_rate"
    assert row["model_name_raw"] == "Claude 3.5 Sonnet"
    assert row["rank_raw"] == "2"
    assert row["score_raw"] == "49.0"
    assert row["score_unit"] == "percent"
    assert row["source_url"] == "https://www.swebench.com/"
    assert "canonicalized" in row["notes"].lower()


def test_artificial_analysis_unresolved_fixture_row_keeps_explicit_status(tmp_path):
    module = load_module()
    fixture = tmp_path / "artificial_analysis.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name": "Unmapped Model X",
                    "rank": 9,
                    "intelligence_index": 42,
                    "provider": "Unknown Provider",
                    "date_observed": "2026-05-03",
                    "source_url": "https://artificialanalysis.ai/leaderboards/models",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = module.ingest_target("artificial_analysis", mode="fixture", fixture_path=fixture)

    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row, canonical_required=False)
    assert row["source_id"] == "artificial_analysis_llm"
    assert row["category_primary"] == "practical"
    assert row["metric_name"] == "intelligence_index"
    assert row["metric_type"] == "aggregate_score"
    assert row["model_name_raw"] == "Unmapped Model X"
    assert row["canonical_id"] == ""
    assert row["rank_raw"] == "9"
    assert row["score_raw"] == "42"
    assert "canonicalization_status=unresolved" in row["notes"]


def test_lmarena_csv_fixture_still_requires_manual_review(tmp_path):
    """LMArena CSV fixtures stay manual_required because Elo provenance must be hand-verified.

    JSON fixtures are allowed (see test_lmarena_json_fixture_parser_*) because they require
    explicit per-field curation, but CSV passthrough remains gated.
    """
    module = load_module()
    fixture_path = tmp_path / "lmarena.csv"
    fixture_path.write_text("model_name_raw,canonical_id,score_raw\nGPT-5.5,openai/gpt-5.5-high@unknown,1502\n", encoding="utf-8")
    result = module.ingest_target("lmarena", mode="fixture", fixture_path=fixture_path)
    assert result.status == "manual_required"
    assert result.used_network is False


def test_lmarena_pickle_fixture_fails_closed_without_execution(tmp_path):
    module = load_module()
    marker = tmp_path / "executed"
    fixture = tmp_path / "leaderboard.pkl"
    fixture.write_bytes(b"cos\nsystem\n(S'touch " + str(marker).encode("utf-8") + b"'\ntR.")

    result = module.ingest_target("lmarena", mode="fixture", fixture_path=fixture)

    assert result.status == "manual_required"
    assert result.used_network is False
    assert result.rows == []
    assert "pickle" in result.message.lower()
    assert not marker.exists()


def assert_required_traceability(row: dict[str, str], *, canonical_required: bool = True) -> None:
    required = [
        "source_id",
        "source_name",
        "source_priority",
        "category_primary",
        "metric_name",
        "metric_type",
        "model_name_raw",
        "provider",
        "score_unit",
        "score_higher_is_better",
        "date_observed",
        "source_url",
        "evaluation_independence",
        "source_trust",
        "contamination_risk",
        "freshness_weight",
        "notes",
    ]
    for field in required:
        assert row[field], field
    assert row["rank_raw"] or row["score_raw"]
    if canonical_required:
        assert row["canonical_id"]
    else:
        assert "canonicalization_status=unresolved" in row["notes"]


def test_cli_fixture_json_reports_status_and_rows(tmp_path, capsys):
    module = load_module()
    fixture = tmp_path / "livebench.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Gemini 2.5 Pro",
                    "canonical_id": "google/gemini-2.5-pro@unknown",
                    "provider": "Google",
                    "rank_raw": 1,
                    "score_raw": 72.5,
                }
            ]
        ),
        encoding="utf-8",
    )

    exit_code = module.main(["ingest", "livebench", "--mode", "fixture", "--fixture", str(fixture)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["target"] == "livebench"
    assert payload["used_network"] is False
    assert payload["row_count"] == 1
    assert payload["rows"][0]["source_id"] == "livebench"


def test_validation_rejects_missing_core_raw_ranking_values(tmp_path, capsys):
    validate = load_validate_module()
    data_dir = tmp_path / "data"
    write_registry_files(data_dir)
    with (data_dir / "raw_rankings.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(validate.REQUIRED_RANKING_FIELDS))
        writer.writeheader()
        row = {field: "value" for field in validate.REQUIRED_RANKING_FIELDS}
        row.update(
            {
                "source_id": "known_source",
                "canonical_id": "known/model@1",
                "metric_name": "",
                "model_name_raw": "",
                "date_observed": "",
                "source_url": "",
                "notes": "",
                "rank_raw": "",
                "score_raw": "",
                "score_higher_is_better": "true",
            }
        )
        writer.writerow(row)

    validate.DATA = data_dir
    try:
        validate.main()
    except SystemExit as exc:
        exit_code = int(exc.code)
    else:
        exit_code = 0
    output = capsys.readouterr().out

    assert exit_code == 1
    for field in ["metric_name", "model_name_raw", "date_observed", "source_url", "notes"]:
        assert field in output


def load_validate_module():
    script = ROOT / "scripts" / "llm-reality-rank" / "validate_data.py"
    spec = importlib.util.spec_from_file_location("validate_data_for_ingest_test", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_registry_files(data_dir: Path) -> None:
    data_dir.mkdir(parents=True)
    (data_dir / "sources.yaml").write_text(
        """
sources:
  - source_id: known_source
    priority: P0
    name: Known Source
    urls:
      primary: https://example.com/source
    categories: [general]
    metric_types: [accuracy]
    source_trust: high
    contamination_risk: low
""".lstrip(),
        encoding="utf-8",
    )
    (data_dir / "models.yaml").write_text(
        """
models:
  - canonical_id: known/model@1
    display_name: Known Model
    provider: Known Provider
    provider_slug: known
    model_family: known
    model_variant: full
    version: "1"
    model_type: closed
    access_type: api
""".lstrip(),
        encoding="utf-8",
    )


def test_lmarena_json_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "lmarena.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "GPT-5.5",
                    "canonical_id": "openai/gpt-5.5-high@unknown",
                    "provider": "OpenAI",
                    "rank_raw": "1",
                    "score_raw": "1502",
                    "date_published": "2026-05-01",
                    "date_observed": "2026-05-04",
                    "source_url": "https://lmarena.ai/leaderboard/",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("lmarena", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    assert result.used_network is False
    assert len(result.rows) == 1
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "lmarena_chatbot_arena"
    assert row["score_raw"] == "1502"


def test_cli_list_exposes_hf_open_llm_target(capsys):
    module = load_module()
    exit_code = module.main(["list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "hf_open_llm" in captured
    assert "Hugging Face" in captured


def test_hf_open_llm_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "hf-open-llm.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Qwen3-Max",
                    "canonical_id": "qwen/qwen3-max@unknown",
                    "provider": "Alibaba",
                    "rank_raw": "1",
                    "score_raw": "78.4",
                    "date_published": "2026-04-20",
                    "date_observed": "2026-05-04",
                    "source_url": "https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("hf_open_llm", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    assert result.used_network is False
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "hf_open_llm_leaderboard"
    assert row["score_raw"] == "78.4"


def test_cli_list_exposes_livecodebench_target(capsys):
    module = load_module()
    exit_code = module.main(["list"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "livecodebench" in captured
    assert "LiveCodeBench" in captured


def test_livecodebench_fixture_parser_outputs_traceable_rows_without_network(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "livecodebench.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "Claude Opus 4.7",
                    "canonical_id": "anthropic/claude-opus-4.7@unknown",
                    "provider": "Anthropic",
                    "rank_raw": "1",
                    "score_raw": "84.2",
                    "date_published": "2026-04-25",
                    "date_observed": "2026-05-04",
                    "source_url": "https://livecodebench.github.io/leaderboard.html",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("livecodebench", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    [row] = result.rows
    assert_required_traceability(row)
    assert row["source_id"] == "livecodebench"
    assert row["score_raw"] == "84.2"


def test_fixture_per_row_metric_name_overrides_target_default(tmp_path):
    module = load_module()
    fixture_path = tmp_path / "aa-multi.json"
    fixture_path.write_text(
        json.dumps(
            [
                {
                    "model_name_raw": "GPT-5.5",
                    "canonical_id": "openai/gpt-5.5-high@unknown",
                    "provider": "OpenAI",
                    "score_raw": "0.50",
                    "metric_name": "aa_price_per_million_tokens_blended",
                    "metric_type": "price",
                    "score_higher_is_better": "false",
                    "source_url": "https://artificialanalysis.ai/leaderboards/models",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = module.ingest_target("artificial_analysis", mode="fixture", fixture_path=fixture_path)
    assert result.status == "ok"
    [row] = result.rows
    assert row["metric_name"] == "aa_price_per_million_tokens_blended"
    assert row["metric_type"] == "price"
    assert row["score_higher_is_better"] == "false"


def test_livebench_live_safe_parses_github_csv(monkeypatch):
    module = load_module()
    fake_csv = (
        "model,reasoning_average,coding_average,math_average,language_average\n"
        "gpt-5.5-high,82.0,80.0,79.0,76.0\n"
        "claude-opus-4-7,84.0,78.0,80.0,82.0\n"
    ).encode("utf-8")

    def fake_fetch(url, *, timeout=10):
        assert "LiveBench" in url or "livebench" in url.lower()
        return fake_csv

    monkeypatch.setattr(module, "bounded_live_fetch", fake_fetch)

    result = module.ingest_target("livebench", mode="live-safe")
    assert result.status == "ok"
    assert result.used_network is True
    assert len(result.rows) == 2
    scores = {row["model_name_raw"]: float(row["score_raw"]) for row in result.rows}
    assert scores["gpt-5.5-high"] == 79.25
    assert scores["claude-opus-4-7"] == 81.0
    for row in result.rows:
        assert row["source_id"] == "livebench"
        assert row["metric_name"] == "global_average"
        assert row["score_higher_is_better"] == "true"

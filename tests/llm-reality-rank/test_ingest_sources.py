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

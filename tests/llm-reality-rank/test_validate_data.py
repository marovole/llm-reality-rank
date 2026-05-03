import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm-reality-rank" / "validate_data.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_data", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_minimal_dataset(data_dir: Path, *, source_id: str, canonical_id: str) -> None:
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
    with (data_dir / "raw_rankings.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(module_required_ranking_fields()))
        writer.writeheader()
        writer.writerow(
            {
                "source_id": source_id,
                "source_name": "Known Source",
                "source_priority": "P0",
                "category_primary": "general",
                "metric_name": "accuracy",
                "metric_type": "accuracy",
                "model_name_raw": "Known Model",
                "canonical_id": canonical_id,
                "provider": "Known Provider",
                "rank_raw": "",
                "score_raw": "88",
                "score_unit": "percent",
                "score_higher_is_better": "true",
                "date_published": "",
                "date_observed": "2026-05-03",
                "source_url": "https://example.com/source",
                "evaluation_independence": "independent_third_party",
                "source_trust": "high",
                "contamination_risk": "low",
                "freshness_weight": "1.0",
                "notes": "Fixture row.",
            }
        )


def module_required_ranking_fields() -> set[str]:
    module = load_module()
    return module.REQUIRED_RANKING_FIELDS


def run_validation(data_dir: Path, capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    module = load_module()
    module.DATA = data_dir
    with pytest.raises(SystemExit) as exc:
        module.main()
    return int(exc.value.code), capsys.readouterr().out


def test_validation_rejects_unknown_source_id(tmp_path, capsys):
    data_dir = tmp_path / "data"
    write_minimal_dataset(data_dir, source_id="unknown_source", canonical_id="known/model@1")

    exit_code, output = run_validation(data_dir, capsys)

    assert exit_code == 1
    assert "unknown source_id unknown_source" in output


def test_validation_rejects_unknown_canonical_id(tmp_path, capsys):
    data_dir = tmp_path / "data"
    write_minimal_dataset(data_dir, source_id="known_source", canonical_id="unknown/model@1")

    exit_code, output = run_validation(data_dir, capsys)

    assert exit_code == 1
    assert "unknown canonical_id unknown/model@1" in output

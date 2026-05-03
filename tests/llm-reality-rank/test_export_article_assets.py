import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "llm-reality-rank" / "export_article_assets.py"


def load_module():
    spec = importlib.util.spec_from_file_location("export_article_assets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_article_export_writes_overall_and_core_subranking_tables_from_reviewed_snapshot(tmp_path):
    module = load_module()
    snapshot_dir = tmp_path / "snapshots" / "2026-05-alpha"
    snapshot_dir.mkdir(parents=True)
    write_snapshot_fixture(snapshot_dir)

    result = module.export_article_assets(
        snapshot_id="2026-05-alpha",
        snapshot_root=tmp_path / "snapshots",
        output_root=tmp_path / "article-exports",
    )

    assert result["ok"] is True
    export_dir = result["output_dir"]
    expected_files = {
        "overall.md",
        "coding.md",
        "chinese.md",
        "value-api.md",
        "multimodal.md",
        "agent.md",
        "article-tables.json",
    }
    assert expected_files.issubset({path.name for path in result["artifacts"]})

    overall = (export_dir / "overall.md").read_text(encoding="utf-8")
    coding = (export_dir / "coding.md").read_text(encoding="utf-8")
    chinese = (export_dir / "chinese.md").read_text(encoding="utf-8")
    multimodal = (export_dir / "multimodal.md").read_text(encoding="utf-8")
    agent = (export_dir / "agent.md").read_text(encoding="utf-8")
    payload = json.loads((export_dir / "article-tables.json").read_text(encoding="utf-8"))

    assert "2026-05-alpha" in overall
    assert "不是正式综合排名" in overall
    assert "Confidence" in overall
    assert "Sources" in overall
    assert "Alpha Model A" in overall
    assert "Alpha Model A" in coding
    assert "Alpha Model B" in chinese
    assert "No reviewed snapshot rows" in multimodal
    assert "No reviewed snapshot rows" in agent
    assert payload["snapshot_id"] == "2026-05-alpha"
    assert {table["id"] for table in payload["tables"]} == {
        "overall",
        "coding",
        "chinese",
        "value-api",
        "multimodal",
        "agent",
    }


def test_methodology_article_contains_snapshot_links_caveats_and_no_official_claims(tmp_path):
    module = load_module()
    snapshot_dir = tmp_path / "snapshots" / "2026-05-alpha"
    snapshot_dir.mkdir(parents=True)
    write_snapshot_fixture(snapshot_dir)
    article_path = tmp_path / "docs" / "article.md"

    result = module.export_article_assets(
        snapshot_id="2026-05-alpha",
        snapshot_root=tmp_path / "snapshots",
        output_root=tmp_path / "article-exports",
        article_path=article_path,
    )

    article = article_path.read_text(encoding="utf-8")
    assert result["article_path"] == article_path
    assert "2026-05-alpha" in article
    assert "docs/llm-reality-rank-source-registry.md" in article
    assert "docs/llm-reality-rank-scoring-methodology.md" in article
    assert "snapshots/llm-reality-rank/2026-05-alpha/manifest.json" in article
    assert "outputs/llm-reality-rank/article-exports/2026-05-alpha/overall.md" in article
    assert "Alpha / 不完整覆盖" in article
    assert "不是正式综合排名" in article
    assert "置信度" in article
    assert "局限" in article
    assert "官方最终排名" not in article
    assert "烟测数据" not in article


def write_snapshot_fixture(snapshot_dir: Path) -> None:
    write_json(
        snapshot_dir / "manifest.json",
        {
            "snapshot_id": "2026-05-alpha",
            "generated_at": "2026-05-03T00:00:00Z",
            "review_status": "reviewed",
            "release_stage": "alpha",
            "methodology_version": "docs/llm-reality-rank-scoring-methodology.md",
            "limitations": [
                "Alpha snapshot: intentionally small reviewed seed dataset; it is not comprehensive or final.",
                "Sparse or missing dimensions are exposed explicitly rather than imputed.",
            ],
            "included_sources": [
                {
                    "source_id": "livebench",
                    "name": "LiveBench",
                    "source_url": "https://livebench.ai/",
                },
                {
                    "source_id": "aider_leaderboards",
                    "name": "Aider LLM Leaderboards",
                    "source_url": "https://aider.chat/docs/leaderboards/",
                },
            ],
            "row_counts": {"model_scores": 2, "raw_rankings": 3},
            "freshness": {"date_observed_min": "2026-05-03", "date_observed_max": "2026-05-03"},
        },
    )
    write_json(
        snapshot_dir / "models.json",
        {
            "models": [
                {
                    "canonical_id": "alpha/model-a@2026-05",
                    "display_name": "Alpha Model A",
                    "provider": "Alpha",
                    "model_type": "closed",
                    "version": "2026-05",
                    "notes": "Reviewed fixture model.",
                },
                {
                    "canonical_id": "alpha/model-b@2026-05",
                    "display_name": "Alpha Model B",
                    "provider": "Alpha",
                    "model_type": "closed",
                    "version": "2026-05",
                    "notes": "Reviewed fixture model.",
                },
            ]
        },
    )
    write_json(
        snapshot_dir / "scores.json",
        {
            "scores": [
                {
                    "canonical_id": "alpha/model-a@2026-05",
                    "rank": 1,
                    "overall_score": 80.0,
                    "dimension_scores": {"General": 80.0, "Coding": 90.0, "Practicality": 70.0},
                    "confidence": {"label": "Medium", "score": 50.0},
                    "eligibility": {"status": "provisional", "reason": "insufficient_scenarios"},
                    "missing_dimensions": ["Chinese", "Multimodal_Doc", "Agent_ToolUse"],
                    "source_coverage": {"source_count": 2, "scenario_count": 3, "evidence_count": 2},
                    "source_refs": [
                        {
                            "source_id": "livebench",
                            "metric_name": "global_average",
                            "date_observed": "2026-05-03",
                            "url": "https://livebench.ai/",
                            "notes": "Reviewed alpha seed, not comprehensive.",
                        }
                    ],
                },
                {
                    "canonical_id": "alpha/model-b@2026-05",
                    "rank": 2,
                    "overall_score": 75.0,
                    "dimension_scores": {"Chinese": 88.0, "Practicality": 60.0},
                    "confidence": {"label": "Low", "score": 35.0},
                    "eligibility": {"status": "ineligible", "reason": "insufficient_sources"},
                    "missing_dimensions": ["General", "Coding", "Multimodal_Doc", "Agent_ToolUse"],
                    "source_coverage": {"source_count": 1, "scenario_count": 2, "evidence_count": 1},
                    "source_refs": [
                        {
                            "source_id": "aider_leaderboards",
                            "metric_name": "polyglot_score",
                            "date_observed": "2026-05-03",
                            "url": "https://aider.chat/docs/leaderboards/",
                            "notes": "Reviewed alpha seed, not comprehensive.",
                        }
                    ],
                },
            ]
        },
    )


def write_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOTS = ROOT / "snapshots" / "llm-reality-rank"
ARTICLE_EXPORTS = ROOT / "outputs" / "llm-reality-rank" / "article-exports"
DEFAULT_ARTICLE = ROOT / "docs" / "public-methodology-article-2026-05-alpha.md"

TABLE_SPECS = [
    {
        "id": "overall",
        "filename": "overall.md",
        "title": "Overall reviewed alpha table / 综合 Alpha 表",
        "dimension": None,
        "description": "Uses reviewed snapshot overall_score. Alpha coverage is sparse; this is not a final official ranking.",
    },
    {
        "id": "coding",
        "filename": "coding.md",
        "title": "Coding reviewed alpha table / AI 编程 Alpha 表",
        "dimension": "Coding",
        "description": "Rows with reviewed Coding dimension data from the snapshot.",
    },
    {
        "id": "chinese",
        "filename": "chinese.md",
        "title": "Chinese reviewed alpha table / 中文能力 Alpha 表",
        "dimension": "Chinese",
        "description": "Rows with reviewed Chinese dimension data from the snapshot.",
    },
    {
        "id": "value-api",
        "filename": "value-api.md",
        "title": "Value/API reviewed alpha table / 性价比与 API Alpha 表",
        "dimension": "Practicality",
        "description": "Rows with reviewed Practicality data, currently centered on API/intelligence-index evidence when available.",
    },
    {
        "id": "multimodal",
        "filename": "multimodal.md",
        "title": "Multimodal reviewed alpha table / 多模态 Alpha 表",
        "dimension": "Multimodal_Doc",
        "description": "Rows with reviewed Multimodal_Doc dimension data from the snapshot.",
    },
    {
        "id": "agent",
        "filename": "agent.md",
        "title": "Agent reviewed alpha table / Agent Alpha 表",
        "dimension": "Agent_ToolUse",
        "description": "Rows with reviewed Agent_ToolUse dimension data from the snapshot.",
    },
]

DIMENSION_LABELS = {
    "General": "通用能力",
    "Reasoning_Math": "推理/数学",
    "Coding": "编程能力",
    "Chinese": "中文能力",
    "Multimodal_Doc": "多模态/文档理解",
    "Agent_ToolUse": "Agent/工具调用",
    "Practicality": "成本/速度/上下文",
    "Ecosystem": "生态/可用性",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def model_lookup(models_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {model["canonical_id"]: model for model in models_payload.get("models", [])}


def source_names(source_refs: list[dict[str, Any]]) -> str:
    names = sorted({ref.get("source_id", "") for ref in source_refs if ref.get("source_id")})
    return ", ".join(names) if names else "n/a"


def source_links(source_refs: list[dict[str, Any]]) -> list[str]:
    links = []
    seen = set()
    for ref in source_refs:
        source_id = ref.get("source_id", "")
        url = ref.get("url", "")
        if not source_id or not url or (source_id, url) in seen:
            continue
        links.append(f"[{source_id}]({url})")
        seen.add((source_id, url))
    return links


def format_score(score: float | int | None) -> str:
    if score is None:
        return "—"
    return f"{float(score):.2f}"


def rows_for_table(scores: list[dict[str, Any]], dimension: str | None) -> list[dict[str, Any]]:
    if dimension is None:
        return sorted(scores, key=lambda row: (row.get("rank", 999999), row.get("canonical_id", "")))
    rows = [row for row in scores if row.get("dimension_scores", {}).get(dimension) is not None]
    return sorted(rows, key=lambda row: float(row.get("dimension_scores", {}).get(dimension, 0)), reverse=True)


def table_records(
    scores: list[dict[str, Any]],
    models_by_id: dict[str, dict[str, Any]],
    dimension: str | None,
) -> list[dict[str, Any]]:
    records = []
    for position, score in enumerate(rows_for_table(scores, dimension), 1):
        canonical_id = score.get("canonical_id", "")
        model = models_by_id.get(canonical_id, {})
        dimension_scores = score.get("dimension_scores", {})
        value = score.get("overall_score") if dimension is None else dimension_scores.get(dimension)
        records.append(
            {
                "rank": position if dimension is not None else score.get("rank", position),
                "canonical_id": canonical_id,
                "display_name": model.get("display_name", canonical_id),
                "provider": model.get("provider", ""),
                "score": value,
                "overall_score": score.get("overall_score"),
                "confidence_label": score.get("confidence", {}).get("label", ""),
                "confidence_score": score.get("confidence", {}).get("score"),
                "eligibility_status": score.get("eligibility", {}).get("status", ""),
                "source_count": score.get("source_coverage", {}).get("source_count", 0),
                "scenario_count": score.get("source_coverage", {}).get("scenario_count", 0),
                "missing_dimensions": score.get("missing_dimensions", []),
                "source_refs": score.get("source_refs", []),
                "source_ids": sorted({ref.get("source_id", "") for ref in score.get("source_refs", []) if ref.get("source_id")}),
            }
        )
    return records


def markdown_table(
    *,
    snapshot_id: str,
    spec: dict[str, Any],
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
) -> str:
    dimension = spec["dimension"]
    score_label = "Overall" if dimension is None else f"{dimension} ({DIMENSION_LABELS.get(dimension, dimension)})"
    lines = [
        f"# {spec['title']}",
        "",
        f"Snapshot: `{snapshot_id}`",
        "",
        f"> Alpha / 不完整覆盖：本表只使用 reviewed snapshot `{snapshot_id}` 中已复核的数据。它不是正式综合排名，不代表全面、最终或官方结论。",
        "",
        f"Description: {spec['description']}",
        "",
        f"Generated from: `snapshots/llm-reality-rank/{snapshot_id}/scores.json` and `manifest.json`",
        "",
    ]
    if not records:
        lines.extend(
            [
                "No reviewed snapshot rows are available for this sub-ranking in the current alpha snapshot.",
                "",
                "This absence is intentional: missing dimensions are not imputed or filled from unreviewed data.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            f"| Rank | Model | Provider | {score_label} | Confidence | Eligibility | Coverage | Missing dimensions | Sources |",
            "|---:|---|---|---:|---|---|---|---|---|",
        ]
    )
    for record in records:
        missing = ", ".join(record["missing_dimensions"]) if record["missing_dimensions"] else "—"
        confidence = f"{record['confidence_label']} ({format_score(record['confidence_score'])})"
        coverage = f"{record['source_count']} sources / {record['scenario_count']} scenarios"
        sources = ", ".join(source_links(record["source_refs"])) or source_names(record["source_refs"])
        lines.append(
            "| {rank} | `{model}` | {provider} | {score} | {confidence} | {eligibility} | {coverage} | {missing} | {sources} |".format(
                rank=record["rank"],
                model=record["display_name"],
                provider=record["provider"],
                score=format_score(record["score"]),
                confidence=confidence,
                eligibility=record["eligibility_status"],
                coverage=coverage,
                missing=missing,
                sources=sources,
            )
        )
    lines.extend(
        [
            "",
            "Caveat: rows with Low confidence, ineligible status, or many missing dimensions should be treated as evidence excerpts, not settled recommendations.",
            "",
            "Included snapshot limitations:",
        ]
    )
    for limitation in manifest.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def build_article(
    *,
    snapshot_id: str,
    manifest: dict[str, Any],
    table_specs: list[dict[str, Any]],
    output_dir: Path,
) -> str:
    source_lines = []
    for source in manifest.get("included_sources", []):
        source_id = source.get("source_id", "")
        name = source.get("name", source_id)
        url = source.get("source_url", "")
        source_lines.append(f"- `{source_id}` — [{name}]({url})" if url else f"- `{source_id}` — {name}")

    table_lines = [
        f"- [{spec['title']}](../outputs/llm-reality-rank/article-exports/{snapshot_id}/{spec['filename']})"
        for spec in table_specs
    ]

    lines = [
        "# LLM Reality Rank 方法论公开草稿：先看真实使用价值，而不是只看考试分",
        "",
        f"> Snapshot: `{snapshot_id}` · Release stage: Alpha / 不完整覆盖 · Generated: {date.today().isoformat()}",
        "",
        f"这是一篇面向中文高阶 AI 用户、开发者和创作者的公开方法论草稿。它使用的表格和结论只来自 reviewed snapshot `{snapshot_id}`；当前快照是一个小规模 Alpha 种子，不是正式综合排名，也不是对所有主流模型的全面最终结论。",
        "",
        "## 这份榜单想解决什么问题",
        "",
        "LLM Reality Rank 不是再做一个“谁智商最高”的单一 benchmark 榜。我们更关心一个现实问题：当你今天要写作、编程、处理中文内容、做 Agent 工作流、控制 API 成本或选择可长期使用的模型时，哪些模型有可解释、可追溯的使用价值证据？",
        "",
        "因此，本项目把模型评价拆成能力、专项、实用、生态和置信度五个层次。考试分、偏好分、代码任务、中文任务、价格速度、上下文、工具调用和可用性都只是证据的一部分，不能单独被当成最终答案。",
        "",
        "## 当前 reviewed snapshot",
        "",
        f"- Snapshot manifest: [`snapshots/llm-reality-rank/{snapshot_id}/manifest.json`](../snapshots/llm-reality-rank/{snapshot_id}/manifest.json)",
        f"- Score records: [`snapshots/llm-reality-rank/{snapshot_id}/scores.json`](../snapshots/llm-reality-rank/{snapshot_id}/scores.json)",
        f"- Source evidence: [`snapshots/llm-reality-rank/{snapshot_id}/source-evidence.json`](../snapshots/llm-reality-rank/{snapshot_id}/source-evidence.json)",
        "- Source registry: [`docs/llm-reality-rank-source-registry.md`](llm-reality-rank-source-registry.md)",
        "- Scoring methodology: [`docs/llm-reality-rank-scoring-methodology.md`](llm-reality-rank-scoring-methodology.md)",
        "",
        "当前 Alpha 快照包含的已复核来源：",
        "",
        *source_lines,
        "",
        f"数据观察日期范围：`{manifest.get('freshness', {}).get('date_observed_min', '')}` 到 `{manifest.get('freshness', {}).get('date_observed_max', '')}`。行数：raw `{manifest.get('row_counts', {}).get('raw_rankings', 0)}`，model scores `{manifest.get('row_counts', {}).get('model_scores', 0)}`。",
        "",
        "## Article-ready exports",
        "",
        "下列表格由脚本可复现生成，来源均为同一个 reviewed snapshot：",
        "",
        *table_lines,
        "",
        "这些表格会保留模型名、分数、置信度、资格状态、覆盖来源数、缺失维度和来源链接。若某个子榜当前没有 reviewed 数据，表格会显式显示缺失状态，而不是用未复核数据补齐。",
        "",
        "## 分数如何理解",
        "",
        "综合分使用项目方法论中的场景维度：General、Reasoning/Math、Coding、Chinese、Multimodal/Doc、Agent/ToolUse、Practicality、Ecosystem。不同来源先被标准化到 0-100，再按来源可信度、污染风险、独立性和新鲜度加权。当前 Alpha 快照覆盖很稀疏，所以更适合展示管线和证据格式，而不适合被解读成完整主榜。",
        "",
        "## 置信度如何理解",
        "",
        "置信度不是模型能力分，而是“这条分数有多可信”的提示。它主要受来源数量、维度覆盖、来源质量、数据新鲜度和模型版本清晰度影响。当前 `2026-05-alpha` 中大量记录仍然是 Low 或 Medium confidence，并伴随 `insufficient_sources`、`insufficient_scenarios`、`missing_dimensions` 等标记；这些标记必须和任何排名表一起展示。",
        "",
        "## 为什么不声称这是正式排名",
        "",
        "当前快照是 Alpha / 不完整覆盖。它只包含少量已经人工复核、可追溯的种子数据，且缺少中文、多模态、Agent、生态等关键来源的完整覆盖。模型版本也可能存在 `unknown` 标签，需要在后续快照中继续复核。因此本文只能说“在当前 reviewed alpha evidence 中呈现的相对位置”，不能说“最终谁最强”。",
        "",
        "## 局限",
        "",
    ]
    for limitation in manifest.get("limitations", []):
        lines.append(f"- {limitation}")
    lines.extend(
        [
            "- Benchmark 可能被训练污染；偏好榜也会受回答风格影响。",
            "- 价格、速度、上下文和 API 可用性会频繁变化。",
            "- Agent 能力高度依赖 scaffold，不完全等同于 base model 能力。",
            "- 中文、多模态和开放权重模型覆盖在当前 Alpha 快照中仍明显不足。",
            "",
            "## 推荐引用方式",
            "",
            "推荐表述：`基于 LLM Reality Rank reviewed alpha snapshot 2026-05-alpha 的有限证据，某模型在已覆盖维度上显示出相对优势，但该快照不是完整或最终排名。`",
            "",
            "不推荐表述：把 Alpha 快照写成定稿名次、全网最强模型榜，或宣称低置信度模型已经被证明更强。",
            "",
        ]
    )
    return "\n".join(lines)


def export_article_assets(
    *,
    snapshot_id: str,
    snapshot_root: Path = SNAPSHOTS,
    output_root: Path = ARTICLE_EXPORTS,
    article_path: Path | None = DEFAULT_ARTICLE,
) -> dict[str, Any]:
    snapshot_dir = snapshot_root / snapshot_id
    if not snapshot_dir.exists():
        return {"ok": False, "errors": [f"snapshot directory not found: {snapshot_dir}"]}

    manifest = read_json(snapshot_dir / "manifest.json")
    if manifest.get("snapshot_id") != snapshot_id:
        return {"ok": False, "errors": [f"manifest snapshot_id mismatch: {manifest.get('snapshot_id')}"]}
    if manifest.get("review_status") != "reviewed":
        return {"ok": False, "errors": [f"snapshot is not reviewed: {manifest.get('review_status')}"]}

    scores = read_json(snapshot_dir / "scores.json").get("scores", [])
    models_by_id = model_lookup(read_json(snapshot_dir / "models.json"))
    output_dir = output_root / snapshot_id
    output_dir.mkdir(parents=True, exist_ok=True)

    tables = []
    artifacts = []
    for spec in TABLE_SPECS:
        records = table_records(scores, models_by_id, spec["dimension"])
        table_payload = {
            "id": spec["id"],
            "title": spec["title"],
            "dimension": spec["dimension"],
            "snapshot_id": snapshot_id,
            "records": records,
        }
        tables.append(table_payload)
        path = output_dir / spec["filename"]
        path.write_text(
            markdown_table(snapshot_id=snapshot_id, spec=spec, manifest=manifest, records=records),
            encoding="utf-8",
        )
        artifacts.append(path)

    json_path = output_dir / "article-tables.json"
    write_json(
        json_path,
        {
            "snapshot_id": snapshot_id,
            "generated_from": f"snapshots/llm-reality-rank/{snapshot_id}",
            "caveat": "Reviewed alpha snapshot only; not a comprehensive final or official ranking.",
            "tables": tables,
        },
    )
    artifacts.append(json_path)

    final_article_path = None
    if article_path is not None:
        article_path.parent.mkdir(parents=True, exist_ok=True)
        article_path.write_text(
            build_article(snapshot_id=snapshot_id, manifest=manifest, table_specs=TABLE_SPECS, output_dir=output_dir),
            encoding="utf-8",
        )
        final_article_path = article_path
        artifacts.append(article_path)

    return {"ok": True, "errors": [], "output_dir": output_dir, "artifacts": artifacts, "article_path": final_article_path}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export reproducible article-ready tables and a public methodology draft.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--snapshot-root", type=Path, default=SNAPSHOTS)
    parser.add_argument("--output-root", type=Path, default=ARTICLE_EXPORTS)
    parser.add_argument("--article-path", type=Path, default=DEFAULT_ARTICLE)
    parser.add_argument("--skip-article", action="store_true")
    args = parser.parse_args()

    result = export_article_assets(
        snapshot_id=args.snapshot_id,
        snapshot_root=args.snapshot_root,
        output_root=args.output_root,
        article_path=None if args.skip_article else args.article_path,
    )
    if not result["ok"]:
        print("ARTICLE EXPORT FAILED")
        for error in result["errors"]:
            print(f"- {error}")
        return 1

    print(f"ARTICLE EXPORT PASSED: {result['output_dir']}")
    for artifact in result["artifacts"]:
        print(f"- {artifact}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

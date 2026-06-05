from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def load_registry(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def group_index(inventory: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in inventory.iterrows():
        raw_groups = "" if pd.isna(row.get("groups", "")) else str(row.get("groups", ""))
        groups = set(raw_groups.split(";")) - {"", "nan", "None"}
        for group in sorted(groups):
            rows.append(
                {
                    "source": row["source"],
                    "label": row["label"],
                    "smiles": row["smiles"],
                    "group": group,
                }
            )
    return pd.DataFrame(rows)


def source_summary(inventory: pd.DataFrame, groups: pd.DataFrame, registry: dict[str, Any]) -> pd.DataFrame:
    source_meta = registry.get("sources", {})
    rows = []
    for source, frame in inventory.groupby("source"):
        meta = source_meta.get(str(source), {})
        source_groups = groups[groups["source"] == source]
        group_counts = source_groups["group"].value_counts()
        rows.append(
            {
                "source": source,
                "registered": bool(meta),
                "source_type": meta.get("source_type", "unregistered"),
                "authority_level": meta.get("authority_level", 0),
                "components": int(len(frame)),
                "functional_groups": int(group_counts.size),
                "top_functional_groups": ";".join(f"{name}:{int(count)}" for name, count in group_counts.head(8).items()),
                "role": meta.get("role", ""),
            }
        )
    return pd.DataFrame(rows).sort_values(["authority_level", "components"], ascending=[False, False])


def functional_group_coverage(groups: pd.DataFrame, registry: dict[str, Any]) -> pd.DataFrame:
    if groups.empty:
        return pd.DataFrame()
    pivot = groups.pivot_table(index="group", columns="source", values="smiles", aggfunc="count", fill_value=0)
    pivot["total"] = pivot.sum(axis=1)
    source_cols = [col for col in pivot.columns if col != "total"]
    pivot["sources_present"] = (pivot[source_cols] > 0).sum(axis=1)
    sparse = int(registry.get("audit", {}).get("sparse_group_threshold", 15))
    high_value = set(registry.get("functional_group_priorities", {}).get("sparse_high_value", []))
    pivot["priority"] = ["sparse_high_value" if group in high_value else "standard" for group in pivot.index]
    pivot["coverage_note"] = [
        "needs_literature_expansion" if (group in high_value and int(total) < sparse) else "covered"
        for group, total in zip(pivot.index, pivot["total"], strict=False)
    ]
    return pivot.reset_index().sort_values(["priority", "total"], ascending=[True, True])


def write_report(
    inventory: pd.DataFrame,
    summary: pd.DataFrame,
    coverage: pd.DataFrame,
    registry: dict[str, Any],
    report_path: Path,
    out_dir: Path,
) -> None:
    sparse = coverage[coverage["coverage_note"] == "needs_literature_expansion"] if not coverage.empty else pd.DataFrame()
    lines = [
        "# Candidate Source Registry And Functional Group Audit",
        "",
        "本文档回应 TODO 中“候选组分数据集：来源、按官能团分类、数据库组织”的要求。当前仍只处理单一小分子 SMILES / MoleCode，不做商品级复杂组分或聚合物超图表示。",
        "",
        "## Outputs",
        "",
        f"- Source registry: `trail/candidates/source_registry.yaml`",
        f"- Source summary: `{out_dir / 'candidate_source_summary.csv'}`",
        f"- Functional group coverage: `{out_dir / 'functional_group_source_coverage.csv'}`",
        f"- JSON summary: `{out_dir / 'candidate_source_audit_summary.json'}`",
        "",
        "## Inventory Summary",
        "",
        f"- Candidate components: {len(inventory)}",
        f"- Functional groups: {int(coverage['group'].nunique()) if not coverage.empty else 0}",
        f"- Registered sources: {len(registry.get('sources', {}))}",
        "",
        "## Source Summary",
        "",
        "| source | type | authority | components | groups | top groups |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['source']} | {row['source_type']} | {int(row['authority_level'])} | "
            f"{int(row['components'])} | {int(row['functional_groups'])} | {row['top_functional_groups']} |"
        )
    lines.extend(
        [
            "",
            "## Sparse High-Value Groups",
            "",
            "| group | total | sources present | note |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    if sparse.empty:
        lines.append("| none | 0 | 0 | all sparse high-value groups above threshold |")
    else:
        for _, row in sparse.sort_values("total").iterrows():
            lines.append(f"| {row['group']} | {int(row['total'])} | {int(row['sources_present'])} | {row['coverage_note']} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `library` 是当前最高权重来源，因为它直接来自本地 SMP 数据集和论文复现材料。",
            "- `generated` 用来补足热固性常见但数据稀疏的结构；它不是实验标签来源，必须继续通过 predictor/Harness/PiEvo。",
            "- `chembl` 提供新颖性和 OOD 探索，但 authority 较低，尤其需要过滤 drug-like 复杂结构。",
            "- 稀疏高价值官能团应优先从 SMP 论文或人工规则模板扩展，而不是盲目扩大 ChEMBL 数量。",
            "- 后续真实 LLM/RAG 生成出的候选应通过 generation record ledger 进入 `generation_record` 来源，而不是直接混入 library。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def audit_sources(inventory_path: Path, registry_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    inventory = pd.read_csv(inventory_path)
    registry = load_registry(registry_path)
    groups = group_index(inventory)
    summary = source_summary(inventory, groups, registry)
    coverage = functional_group_coverage(groups, registry)
    audit_summary = {
        "inventory_rows": int(len(inventory)),
        "registered_sources": int(len(registry.get("sources", {}))),
        "inventory_sources": inventory["source"].value_counts().to_dict(),
        "unregistered_inventory_sources": sorted(set(inventory["source"]) - set(registry.get("sources", {}))),
        "functional_groups": int(coverage["group"].nunique()) if not coverage.empty else 0,
        "sparse_high_value_groups_needing_expansion": (
            coverage.loc[coverage["coverage_note"] == "needs_literature_expansion", "group"].tolist() if not coverage.empty else []
        ),
    }
    return summary, coverage, audit_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit SMP candidate component sources and functional-group coverage.")
    parser.add_argument("--inventory", default="artifacts/trail/candidates_smoke/component_inventory.csv")
    parser.add_argument("--registry", default="trail/candidates/source_registry.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/candidates_source_audit")
    parser.add_argument("--report", default="reports/candidate_source_audit.md")
    args = parser.parse_args()

    inventory = pd.read_csv(args.inventory)
    registry = load_registry(Path(args.registry))
    groups = group_index(inventory)
    summary = source_summary(inventory, groups, registry)
    coverage = functional_group_coverage(groups, registry)
    audit_summary = {
        "inventory_rows": int(len(inventory)),
        "registered_sources": int(len(registry.get("sources", {}))),
        "inventory_sources": inventory["source"].value_counts().to_dict(),
        "unregistered_inventory_sources": sorted(set(inventory["source"]) - set(registry.get("sources", {}))),
        "functional_groups": int(coverage["group"].nunique()) if not coverage.empty else 0,
        "sparse_high_value_groups_needing_expansion": (
            coverage.loc[coverage["coverage_note"] == "needs_literature_expansion", "group"].tolist() if not coverage.empty else []
        ),
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "candidate_source_summary.csv", index=False)
    coverage.to_csv(out_dir / "functional_group_source_coverage.csv", index=False)
    (out_dir / "candidate_source_audit_summary.json").write_text(json.dumps(audit_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(inventory, summary, coverage, registry, Path(args.report), out_dir)


if __name__ == "__main__":
    main()

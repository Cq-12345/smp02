from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.audit_candidate_sources import functional_group_coverage, group_index, load_registry
from trail.candidates.build_component_inventory import candidate_row, write_outputs


def load_templates(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def expand_inventory(base_inventory: pd.DataFrame, template_doc: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source = str(template_doc.get("source", "literature_template"))
    seen = set(base_inventory["smiles"].astype(str)) if not base_inventory.empty else set()
    added: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for template in template_doc.get("templates", []):
        label = str(template.get("label", "template"))
        intended_group = str(template.get("intended_group", ""))
        smiles = str(template.get("smiles", ""))
        row = candidate_row(smiles, source, label)
        if row is None:
            rejected.append({**template, "reason": "invalid_or_out_of_scope_smiles"})
            continue
        groups = set(str(row.get("groups", "")).split(";")) - {""}
        if intended_group and intended_group not in groups:
            rejected.append({**template, "canonical_smiles": row["smiles"], "detected_groups": ";".join(sorted(groups)), "reason": "intended_group_not_detected"})
            continue
        if str(row["smiles"]) in seen:
            rejected.append({**template, "canonical_smiles": row["smiles"], "detected_groups": row["groups"], "reason": "duplicate_with_existing_inventory"})
            continue
        seen.add(str(row["smiles"]))
        row = dict(row)
        row["template_family"] = template.get("family", intended_group)
        row["template_intended_group"] = intended_group
        added.append(row)
    added_df = pd.DataFrame(added)
    rejected_df = pd.DataFrame(rejected)
    if added_df.empty:
        expanded = base_inventory.copy()
    else:
        for column in added_df.columns:
            if column not in base_inventory.columns:
                base_inventory[column] = ""
        for column in base_inventory.columns:
            if column not in added_df.columns:
                added_df[column] = ""
        expanded = pd.concat([base_inventory, added_df[base_inventory.columns]], ignore_index=True)
    return expanded, added_df, rejected_df


def high_value_counts(coverage: pd.DataFrame, registry: dict[str, Any]) -> pd.DataFrame:
    high_value = registry.get("functional_group_priorities", {}).get("sparse_high_value", [])
    if coverage.empty:
        return pd.DataFrame(columns=["group", "total", "coverage_note"])
    return coverage[coverage["group"].isin(high_value)].sort_values("group").copy()


def write_report(
    base_inventory: pd.DataFrame,
    expanded_inventory: pd.DataFrame,
    added: pd.DataFrame,
    rejected: pd.DataFrame,
    registry: dict[str, Any],
    report_path: Path,
    out_dir: Path,
) -> None:
    base_coverage = functional_group_coverage(group_index(base_inventory), registry)
    expanded_coverage = functional_group_coverage(group_index(expanded_inventory), registry)
    base_high = high_value_counts(base_coverage, registry)
    expanded_high = high_value_counts(expanded_coverage, registry)
    joined = base_high[["group", "total", "coverage_note"]].rename(columns={"total": "before_total", "coverage_note": "before_note"}).merge(
        expanded_high[["group", "total", "coverage_note"]].rename(columns={"total": "after_total", "coverage_note": "after_note"}),
        on="group",
        how="outer",
    )
    lines = [
        "# Sparse Functional Group Candidate Expansion",
        "",
        "本文档回应 TODO 中“候选组分数据集：来源、按官能团分类、数据库”的补强要求。本轮仍只使用单一小分子 SMILES / MoleCode，不进入商品级组分、聚合物或超图表示。",
        "",
        "## Outputs",
        "",
        f"- Template library: `trail/candidates/sparse_functional_group_templates.yaml`",
        f"- Expanded inventory: `{out_dir / 'component_inventory.csv'}`",
        f"- Added templates: `{out_dir / 'template_expansion_added.csv'}`",
        f"- Rejected templates: `{out_dir / 'template_expansion_rejected.csv'}`",
        f"- Summary: `{out_dir / 'template_expansion_summary.json'}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
        f"| base inventory rows | {len(base_inventory)} |",
        f"| expanded inventory rows | {len(expanded_inventory)} |",
        f"| added templates | {len(added)} |",
        f"| rejected templates | {len(rejected)} |",
        "",
        "## Sparse High-Value Coverage",
        "",
        "| group | before | after | before note | after note |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for _, row in joined.sort_values("group").iterrows():
        lines.append(
            f"| {row['group']} | {int(row['before_total'])} | {int(row['after_total'])} | "
            f"{row['before_note']} | {row['after_note']} |"
        )
    lines.extend(
        [
            "",
            "## Added Template Families",
            "",
            "| intended group | added rows |",
            "| --- | ---: |",
        ]
    )
    if added.empty:
        lines.append("| none | 0 |")
    else:
        for group, count in added["template_intended_group"].value_counts().sort_index().items():
            lines.append(f"| {group} | {int(count)} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `literature_template` 是低/中权威候选来源：它只表示热固性/SMP 常见小分子单体家族模板，不提供 Tg 标签。",
            "- 新增模板必须先通过 RDKit、允许元素、单片段、官能团检测和去重，随后仍需进入 predictor/Harness/PiEvo。",
            "- 本轮目标是修复候选空间的稀疏官能团覆盖，让后续 replacement、LLM/RAG 和 PiEvo 有更多可反应方向可探索。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_expansion(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    base_inventory = pd.read_csv(args.base_inventory)
    template_doc = load_templates(Path(args.templates))
    registry = load_registry(Path(args.registry))
    expanded, added, rejected = expand_inventory(base_inventory, template_doc)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_outputs(expanded, out_dir)
    added.to_csv(out_dir / "template_expansion_added.csv", index=False)
    rejected.to_csv(out_dir / "template_expansion_rejected.csv", index=False)
    coverage = functional_group_coverage(group_index(expanded), registry)
    sparse_remaining = (
        coverage.loc[coverage["coverage_note"] == "needs_literature_expansion", "group"].tolist()
        if not coverage.empty
        else []
    )
    summary = {
        "base_inventory_rows": int(len(base_inventory)),
        "expanded_inventory_rows": int(len(expanded)),
        "added_templates": int(len(added)),
        "rejected_templates": int(len(rejected)),
        "source_counts": expanded["source"].value_counts().to_dict(),
        "sparse_high_value_groups_needing_expansion": sparse_remaining,
    }
    (out_dir / "template_expansion_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(base_inventory, expanded, added, rejected, registry, Path(args.report), out_dir)
    return expanded, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand candidate inventory with curated sparse functional-group templates.")
    parser.add_argument("--base-inventory", default="artifacts/trail/candidates_smoke/component_inventory.csv")
    parser.add_argument("--templates", default="trail/candidates/sparse_functional_group_templates.yaml")
    parser.add_argument("--registry", default="trail/candidates/source_registry.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/candidates_expanded")
    parser.add_argument("--report", default="reports/sparse_candidate_template_expansion.md")
    args = parser.parse_args()
    run_expansion(args)


if __name__ == "__main__":
    main()

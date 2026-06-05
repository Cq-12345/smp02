from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from trail.generation.import_generation_records import import_generation_records  # noqa: E402


GENERATION_RECORD_COLUMNS = [
    "generation_id",
    "strategy",
    "stage",
    "target_tg_c",
    "target_window_c",
    "candidate_smiles",
    "candidate_ratios",
    "source_context",
    "generator_id",
    "generation_time",
    "prompt_id",
    "prompt_text",
    "prompt_hash",
    "rag_query",
    "rag_context_refs",
    "rag_context_digest",
    "principle_hypothesis",
    "functional_group_plan",
    "candidate_json",
    "compatibility_reasons",
    "predicted_tg_mean_c",
    "predicted_tg_sigma_c",
    "ood_penalty",
    "pievo_round",
    "selected_by_ids",
    "harness_failure_reason",
    "review_status",
    "notes",
]


def stable_id(prefix: str, *parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def selected_to_record(row: pd.Series, index: int, target_tg_c: float, target_window_c: float, generation_time: str) -> dict[str, Any]:
    smiles = f"{row['smiles_a']}|{row['smiles_b']}"
    ratios = f"{float(row['ratio_a']):.5f}:{float(row['ratio_b']):.5f}"
    prompt_text = (
        f"Enumerate rule-template SMP formulation candidates for target_tg_c={target_tg_c:g}, "
        f"target_window_c={target_window_c:g}; retain only compatible functional-group pairs and ratio-simplex records."
    )
    candidate_json = {
        "source_row_index": int(index),
        "smiles_a": str(row["smiles_a"]),
        "smiles_b": str(row["smiles_b"]),
        "groups_a": str(row.get("groups_a", "")),
        "groups_b": str(row.get("groups_b", "")),
        "ratio_a": float(row["ratio_a"]),
        "ratio_b": float(row["ratio_b"]),
        "source_target_distance_c": float(row.get("target_distance", abs(float(row["predicted_tg"]) - target_tg_c))),
        "in_target_range": bool(row.get("in_target_range", True)),
    }
    return {
        "generation_id": stable_id("rule_template", smiles, ratios, index),
        "strategy": "rule_template",
        "stage": "harnessed",
        "target_tg_c": float(target_tg_c),
        "target_window_c": float(target_window_c),
        "candidate_smiles": smiles,
        "candidate_ratios": ratios,
        "source_context": "selected_candidate_space_rule_template",
        "generator_id": "smp02.agent_discovery:rule_template_enumeration",
        "generation_time": generation_time,
        "prompt_id": "rule_template_candidate_space_v1",
        "prompt_text": prompt_text,
        "prompt_hash": prompt_hash(prompt_text),
        "rag_query": "",
        "rag_context_refs": "artifacts/reproduce/discovery/selected_candidates.csv|trail/harness/constraints.py",
        "rag_context_digest": "Rule-template candidate-space enumeration with functional-group compatibility and target-window filtering.",
        "principle_hypothesis": "Rule-template compatible functional-group enumeration can seed validated target-window formulations.",
        "functional_group_plan": f"{row.get('groups_a', '')} + {row.get('groups_b', '')}",
        "candidate_json": json.dumps(candidate_json, ensure_ascii=False, sort_keys=True),
        "compatibility_reasons": str(row["compatibility_reason"]),
        "predicted_tg_mean_c": float(row["predicted_tg"]),
        "predicted_tg_sigma_c": "",
        "ood_penalty": 0.0,
        "pievo_round": "",
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "Rule-template enumeration seed from selected candidate space; surrogate evidence only, not real DSC.",
    }


def build_records(selected_path: Path, target_tg_c: float, target_window_c: float, max_records: int, generation_time: str) -> pd.DataFrame:
    selected = pd.read_csv(selected_path)
    required = {"smiles_a", "smiles_b", "ratio_a", "ratio_b", "compatibility_reason", "predicted_tg"}
    missing = sorted(required - set(selected.columns))
    if missing:
        raise ValueError(f"Selected candidates file {selected_path} missing required columns: {missing}")
    selected = selected.copy()
    selected["target_distance_local"] = (selected["predicted_tg"].astype(float) - float(target_tg_c)).abs()
    selected = selected[selected["target_distance_local"] <= float(target_window_c)].sort_values("target_distance_local").head(int(max_records))
    rows = [
        selected_to_record(row, int(index), target_tg_c, target_window_c, generation_time)
        for index, row in selected.iterrows()
    ]
    return pd.DataFrame(rows, columns=GENERATION_RECORD_COLUMNS)


def write_report(records: pd.DataFrame, ledger: pd.DataFrame, summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Rule-template Generation Records",
        "",
        "本文档把枚举搜索空间中的近目标候选写成 `rule_template` generation records。它们不是新物理实验，而是规则/模板生成器的可审计基线种子。",
        "",
        "## 输出文件",
        "",
        f"- Input records: `{out_dir / 'rule_template_generation_records_input.csv'}`",
        f"- Ledger: `{out_dir / 'generation_record_ledger.csv'}`",
        f"- Summary: `{out_dir / 'generation_record_summary.json'}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- 这些 records 来自当前小分子 SMILES / MoleCode 搜索空间，不进入暂缓的商品级/聚合物超图表示。",
            "- importer 会重新检查 RDKit、ratio、target window 和 compatibility evidence；失败项不会进入训练标签。",
            "- 它们为 SFT 和 diffusion/flow 提供规则模板基线种子，后续生成器输出仍必须走同一 Harness/PiEvo/人工审核链路。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_import(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    input_records = build_records(Path(args.selected), args.target_tg_c, args.target_window_c, args.max_records, args.generation_time)
    input_path = out_dir / "rule_template_generation_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    input_records.to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    summary = summary | {
        "target_tg_c": float(args.target_tg_c),
        "target_window_c": float(args.target_window_c),
        "selected_candidates_path": str(args.selected),
        "input_records_path": str(input_path),
        "generation_record_ledger_path": str(ledger_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(input_records, ledger, summary, out_dir, Path(args.report))
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build rule-template generation records from selected candidate-space formulations.")
    parser.add_argument("--selected", default="artifacts/reproduce/discovery/selected_candidates.csv")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--max-records", type=int, default=50)
    parser.add_argument("--generation-time", default="2026-06-06")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/rule_template_records")
    parser.add_argument("--report", default="reports/rule_template_generation_records.md")
    args = parser.parse_args()
    run_import(args)


if __name__ == "__main__":
    main()

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


def stable_id(*parts: object) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"diffusion_flow_dry_run_{digest}"


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def load_seed_table(path: Path) -> pd.DataFrame:
    table = pd.read_csv(path)
    required = {
        "split",
        "generation_id",
        "strategy",
        "target_tg_c",
        "target_window_c",
        "candidate_smiles",
        "candidate_ratios",
        "predicted_tg_mean_c",
        "target_distance_c",
        "generation_reward",
        "compatibility_reasons",
        "source_ledger",
    }
    missing = sorted(required - set(table.columns))
    if missing:
        raise ValueError(f"Diffusion/flow seed table {path} missing required columns: {missing}")
    for column in [
        "target_tg_c",
        "target_window_c",
        "predicted_tg_mean_c",
        "predicted_tg_sigma_c",
        "target_distance_c",
        "generation_reward",
    ]:
        if column not in table.columns:
            table[column] = 0.0
        table[column] = table[column].map(as_float)
    return table


def split_rows(table: pd.DataFrame, split: str) -> pd.DataFrame:
    return table[table["split"].astype(str) == split].copy()


def select_seed_prototypes(
    train: pd.DataFrame,
    max_records: int,
    target_tg_c: float,
    target_condition_tolerance_c: float,
) -> pd.DataFrame:
    if train.empty:
        raise ValueError("Diffusion/flow seed table has no train split rows")
    candidates = train.copy()
    candidates["target_condition_delta_c"] = (candidates["target_tg_c"].astype(float) - float(target_tg_c)).abs()
    conditioned = candidates[candidates["target_condition_delta_c"] <= float(target_condition_tolerance_c)].copy()
    if conditioned.empty:
        conditioned = candidates
    conditioned["dry_run_target_distance_c"] = (conditioned["predicted_tg_mean_c"].astype(float) - float(target_tg_c)).abs()
    conditioned = conditioned.sort_values(
        ["target_condition_delta_c", "dry_run_target_distance_c", "generation_reward", "generation_id"],
        ascending=[True, True, False, True],
    )
    rows = []
    seen: set[tuple[str, str]] = set()
    for index, row in conditioned.iterrows():
        key = (str(row["candidate_smiles"]), str(row["candidate_ratios"]))
        if key in seen:
            continue
        seen.add(key)
        item = row.copy()
        item["source_seed_index"] = int(index)
        rows.append(item)
        if len(rows) >= int(max_records):
            break
    return pd.DataFrame(rows)


def record_from_seed(row: pd.Series, target_tg_c: float, target_window_c: float, generation_time: str) -> dict[str, Any]:
    prompt = "\n".join(
        [
            "Diffusion/flow dry-run candidate generation.",
            f"Target Tg condition: {target_tg_c:.1f} C",
            f"Target window: +/-{target_window_c:.1f} C",
            "Use a validated diffusion/flow seed-table prototype; preserve auditability and re-run Harness.",
            f"Source seed generation id: {row['generation_id']}",
            f"Source seed strategy: {row['strategy']}",
        ]
    )
    candidate_audit = {
        "dry_run_mode": "conditional_seed_replay_not_weight_update",
        "source_seed_generation_id": str(row["generation_id"]),
        "source_seed_strategy": str(row["strategy"]),
        "source_seed_split": str(row["split"]),
        "source_seed_index": int(row.get("source_seed_index", -1)),
        "source_ledger": str(row.get("source_ledger", "")),
        "source_target_tg_c": as_float(row.get("target_tg_c")),
        "target_condition_delta_c": as_float(row.get("target_condition_delta_c")),
        "source_target_distance_c": as_float(row.get("target_distance_c")),
        "source_generation_reward": as_float(row.get("generation_reward")),
    }
    return {
        "generation_id": stable_id(row["generation_id"], row["candidate_smiles"], row["candidate_ratios"], target_tg_c),
        "strategy": "diffusion_or_flow_matching",
        "stage": "harnessed",
        "target_tg_c": float(target_tg_c),
        "target_window_c": float(target_window_c),
        "candidate_smiles": str(row["candidate_smiles"]),
        "candidate_ratios": str(row["candidate_ratios"]),
        "source_context": "diffusion_flow_seed_table_dry_run",
        "generator_id": "diffusion_or_flow_matching:conditional_seed_replay_v1",
        "generation_time": generation_time,
        "prompt_id": "diffusion_flow_candidate_generator_dry_run_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": "",
        "rag_context_refs": str(row.get("source_ledger", "")),
        "rag_context_digest": "Validated diffusion/flow seed-table row replayed under a target Tg condition.",
        "principle_hypothesis": "Conditional diffusion/flow should learn the validated target-window formulation manifold before proposing off-manifold candidates.",
        "functional_group_plan": "",
        "candidate_json": json.dumps(candidate_audit, ensure_ascii=False, sort_keys=True),
        "compatibility_reasons": str(row.get("compatibility_reasons", "")),
        "predicted_tg_mean_c": as_float(row.get("predicted_tg_mean_c")),
        "predicted_tg_sigma_c": as_float(row.get("predicted_tg_sigma_c")),
        "ood_penalty": 0.0,
        "pievo_round": "",
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "Diffusion/flow dry-run replay of a validated seed-table row; not a neural diffusion or flow-matching weight update and not real DSC.",
    }


def build_records(
    seed_table: pd.DataFrame,
    max_records: int,
    target_tg_c: float,
    target_window_c: float,
    target_condition_tolerance_c: float,
    generation_time: str,
) -> pd.DataFrame:
    selected = select_seed_prototypes(
        split_rows(seed_table, "train"),
        max_records=max_records,
        target_tg_c=target_tg_c,
        target_condition_tolerance_c=target_condition_tolerance_c,
    )
    rows = [
        record_from_seed(row, target_tg_c, target_window_c, generation_time)
        for _, row in selected.iterrows()
    ]
    return pd.DataFrame(rows, columns=GENERATION_RECORD_COLUMNS)


def heldout_eval_table(seed_table: pd.DataFrame, generated_records: pd.DataFrame) -> pd.DataFrame:
    eval_rows = split_rows(seed_table, "eval")
    if eval_rows.empty:
        return pd.DataFrame(
            columns=[
                "eval_generation_id",
                "eval_candidate_smiles",
                "eval_candidate_ratios",
                "nearest_generated_id",
                "nearest_generated_distance_c",
                "exact_candidate_match",
            ]
        )
    generated = generated_records.copy()
    generated["target_distance_c"] = (
        generated["predicted_tg_mean_c"].astype(float) - generated["target_tg_c"].astype(float)
    ).abs()
    rows = []
    for _, row in eval_rows.iterrows():
        exact = generated[
            (generated["candidate_smiles"] == str(row["candidate_smiles"]))
            & (generated["candidate_ratios"] == str(row["candidate_ratios"]))
        ]
        if exact.empty:
            nearest = generated.sort_values("target_distance_c").iloc[0] if not generated.empty else pd.Series()
        else:
            nearest = exact.iloc[0]
        rows.append(
            {
                "eval_generation_id": str(row["generation_id"]),
                "eval_candidate_smiles": str(row["candidate_smiles"]),
                "eval_candidate_ratios": str(row["candidate_ratios"]),
                "nearest_generated_id": "" if nearest.empty else nearest["generation_id"],
                "nearest_generated_distance_c": None if nearest.empty else float(nearest["target_distance_c"]),
                "exact_candidate_match": bool(not exact.empty),
            }
        )
    return pd.DataFrame(rows)


def write_report(summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Diffusion/Flow Candidate Generator Dry Run",
        "",
        "本文档把已通过 readiness gate 的 diffusion/flow seed table 推进一步：用 train split 中的 validated seed prototypes 做一个可复现的 conditional seed replay dry-run，并重新写入 `diffusion_or_flow_matching` generation ledger。",
        "",
        "这不是神经扩散模型或 flow-matching 权重训练完成；它的作用是验证 diffusion/flow 生成器激活后的审计链、Harness 门禁和策略回流接口。",
        "",
        "## 输出文件",
        "",
        f"- Input records: `{out_dir / 'diffusion_flow_candidate_records_input.csv'}`",
        f"- Ledger: `{out_dir / 'generation_record_ledger.csv'}`",
        f"- Summary: `{out_dir / 'generation_record_summary.json'}`",
        f"- Heldout eval table: `{out_dir / 'heldout_eval_retrieval.csv'}`",
        f"- Report: `{report_path}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, dict) or isinstance(value, list):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- `diffusion_or_flow_matching` 的 dry-run 输出仍必须满足 generation record schema、RDKit、ratio、prediction、target 和 chemistry evidence。",
            "- dry-run 只复用 validated seed-table prototypes，因此可以验证链路，但不能证明模型已经学会连续配方流形或分布外生成。",
            "- 后续若真正训练 diffusion/flow 权重，应把模型输出写入同一 ledger，并和本 dry-run 的 Harness pass、target distance、重复率做对比。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_dry_run(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seed_table = load_seed_table(Path(args.seed_table))
    records = build_records(
        seed_table,
        max_records=args.max_records,
        target_tg_c=args.target_tg_c,
        target_window_c=args.target_window_c,
        target_condition_tolerance_c=args.target_condition_tolerance_c,
        generation_time=args.generation_time,
    )
    input_path = out_dir / "diffusion_flow_candidate_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    heldout_path = out_dir / "heldout_eval_retrieval.csv"
    records.to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    heldout = heldout_eval_table(seed_table, records)
    heldout.to_csv(heldout_path, index=False)
    summary = summary | {
        "generator_mode": "conditional_seed_replay_not_weight_update",
        "seed_table": str(args.seed_table),
        "train_seed_rows": int((seed_table["split"].astype(str) == "train").sum()),
        "eval_seed_rows": int((seed_table["split"].astype(str) == "eval").sum()),
        "generated_records": int(len(records)),
        "target_condition_tolerance_c": float(args.target_condition_tolerance_c),
        "heldout_exact_candidate_matches": int(heldout["exact_candidate_match"].sum()) if not heldout.empty else 0,
        "heldout_eval_rows": int(len(heldout)),
        "input_records_path": str(input_path),
        "generation_record_ledger_path": str(ledger_path),
        "heldout_eval_retrieval_path": str(heldout_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, out_dir, Path(args.report))
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an auditable diffusion/flow candidate-generator dry run.")
    parser.add_argument("--seed-table", default="artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv")
    parser.add_argument("--max-records", type=int, default=19)
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--target-condition-tolerance-c", type=float, default=10.0)
    parser.add_argument("--generation-time", default="2026-06-06")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/diffusion_flow_candidate_dry_run")
    parser.add_argument("--report", default="reports/diffusion_flow_candidate_generator_dry_run.md")
    args = parser.parse_args()
    run_dry_run(args)


if __name__ == "__main__":
    main()

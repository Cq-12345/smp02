from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_LEDGERS = [
    "artifacts/trail/generation/rule_template_records/generation_record_ledger.csv",
    "artifacts/trail/generation/prompt_records/generation_record_ledger.csv",
    "artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv",
    "artifacts/trail/generation/expanded_inventory_feedback_aware_llm_rag/generation_record_ledger.csv",
    "artifacts/trail/generation/original_replacement_records/generation_record_ledger.csv",
    "artifacts/trail/generation/feedback_guided_replacement_records/generation_record_ledger.csv",
    "artifacts/trail/generation/vae_latent_local_search_records/generation_record_ledger.csv",
    "artifacts/trail/generation/expanded_inventory_replacement_records/generation_record_ledger.csv",
    "artifacts/trail/generation/feedback_guided_replacement_target_records/target_190/generation_record_ledger.csv",
    "artifacts/trail/generation/feedback_guided_replacement_target_records/target_195/generation_record_ledger.csv",
    "artifacts/trail/generation/feedback_guided_replacement_target_records/target_200/generation_record_ledger.csv",
    "artifacts/trail/generation/feedback_guided_replacement_target_records/target_250/generation_record_ledger.csv",
]


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def stable_split(*parts: object, train_fraction: float = 0.85) -> str:
    text = "|".join(str(part) for part in parts)
    bucket = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "train" if bucket < train_fraction else "eval"


def load_ledgers(paths: list[Path]) -> pd.DataFrame:
    frames = []
    for path in paths:
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        frame["source_ledger"] = str(path)
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    for column in [
        "generation_id",
        "strategy",
        "stage",
        "target_tg_c",
        "target_window_c",
        "candidate_smiles",
        "candidate_ratios",
        "source_context",
        "compatibility_reasons",
        "predicted_tg_mean_c",
        "predicted_tg_sigma_c",
        "ood_penalty",
        "generation_reward",
        "target_distance_c",
        "harness_pass",
        "record_pass",
        "prompt_text",
        "rag_context_refs",
        "rag_context_digest",
        "principle_hypothesis",
        "functional_group_plan",
        "candidate_json",
        "review_status",
        "notes",
    ]:
        if column not in combined.columns:
            combined[column] = ""
    combined["harness_pass"] = combined["harness_pass"].map(parse_bool)
    combined["record_pass"] = combined["record_pass"].map(parse_bool)
    combined["generation_reward"] = combined["generation_reward"].map(lambda value: as_float(value, 0.0))
    combined["target_distance_c"] = combined["target_distance_c"].map(lambda value: as_float(value, 1e9))
    return combined


def successful_records(ledger: pd.DataFrame, min_reward: float) -> pd.DataFrame:
    if ledger.empty:
        return pd.DataFrame()
    success = ledger[
        ledger["harness_pass"]
        & ledger["record_pass"]
        & ledger["predicted_tg_mean_c"].notna()
        & (ledger["generation_reward"].astype(float) >= float(min_reward))
    ].copy()
    if success.empty:
        return success
    success = success.sort_values(["generation_reward", "target_distance_c"], ascending=[False, True])
    return success.drop_duplicates(subset=["candidate_smiles", "candidate_ratios", "target_tg_c", "strategy"], keep="first").reset_index(drop=True)


def candidate_payload(row: pd.Series) -> dict[str, Any]:
    payload = {
        "strategy": str(row["strategy"]),
        "stage": "harnessed",
        "target_tg_c": as_float(row["target_tg_c"]),
        "target_window_c": as_float(row["target_window_c"], 5.0),
        "candidate_smiles": str(row["candidate_smiles"]),
        "candidate_ratios": str(row["candidate_ratios"]),
        "compatibility_reasons": str(row.get("compatibility_reasons", "")),
        "principle_hypothesis": str(row.get("principle_hypothesis", "")),
        "functional_group_plan": str(row.get("functional_group_plan", "")),
        "predicted_tg_mean_c": as_float(row.get("predicted_tg_mean_c")),
        "predicted_tg_sigma_c": as_float(row.get("predicted_tg_sigma_c")),
        "ood_penalty": as_float(row.get("ood_penalty")),
        "review_status": "needs_review",
    }
    raw_json = str(row.get("candidate_json", "")).strip()
    if raw_json:
        try:
            payload["candidate_json"] = json.loads(raw_json)
        except Exception:
            payload["candidate_json"] = raw_json
    return payload


def sft_user_prompt(row: pd.Series) -> str:
    context_bits = [
        f"Target Tg: {as_float(row['target_tg_c']):.1f} C",
        f"Target window: +/-{as_float(row['target_window_c'], 5.0):.1f} C",
        "Representation: single small-molecule SMILES / MoleCode only.",
        "Return one auditable generation_record JSON. It must pass RDKit, ratio, prediction, target, and chemistry gates before recommendation.",
    ]
    if str(row.get("rag_context_refs", "")).strip():
        context_bits.append(f"RAG refs: {row['rag_context_refs']}")
    if str(row.get("rag_context_digest", "")).strip():
        context_bits.append(f"RAG digest: {row['rag_context_digest']}")
    if str(row.get("source_context", "")).strip():
        context_bits.append(f"Source context: {row['source_context']}")
    return "\n".join(context_bits)


def build_sft_examples(records: pd.DataFrame) -> list[dict[str, Any]]:
    examples = []
    for _, row in records.iterrows():
        split = stable_split(row["generation_id"], row["candidate_smiles"], row["candidate_ratios"])
        examples.append(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "You generate auditable SMP formulation hypotheses as JSON generation records. Do not bypass Harness or predictor validation.",
                    },
                    {"role": "user", "content": sft_user_prompt(row)},
                    {"role": "assistant", "content": json.dumps(candidate_payload(row), ensure_ascii=False, sort_keys=True)},
                ],
                "metadata": {
                    "generation_id": str(row["generation_id"]),
                    "strategy": str(row["strategy"]),
                    "source_ledger": str(row["source_ledger"]),
                    "target_distance_c": as_float(row["target_distance_c"]),
                    "generation_reward": as_float(row["generation_reward"]),
                    "split": split,
                },
            }
        )
    if len(examples) > 1 and all(example["metadata"]["split"] == "train" for example in examples):
        examples[-1]["metadata"]["split"] = "eval"
    return examples


def build_diffusion_flow_seed_table(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return pd.DataFrame(
            columns=[
                "split",
                "generation_id",
                "strategy",
                "target_tg_c",
                "target_window_c",
                "candidate_smiles",
                "candidate_ratios",
                "predicted_tg_mean_c",
                "predicted_tg_sigma_c",
                "target_distance_c",
                "generation_reward",
                "compatibility_reasons",
                "source_ledger",
            ]
        )
    rows = []
    for _, row in records.iterrows():
        rows.append(
            {
                "split": stable_split(row["generation_id"], row["candidate_smiles"], row["candidate_ratios"]),
                "generation_id": str(row["generation_id"]),
                "strategy": str(row["strategy"]),
                "target_tg_c": as_float(row["target_tg_c"]),
                "target_window_c": as_float(row["target_window_c"], 5.0),
                "candidate_smiles": str(row["candidate_smiles"]),
                "candidate_ratios": str(row["candidate_ratios"]),
                "predicted_tg_mean_c": as_float(row["predicted_tg_mean_c"]),
                "predicted_tg_sigma_c": as_float(row["predicted_tg_sigma_c"]),
                "target_distance_c": as_float(row["target_distance_c"]),
                "generation_reward": as_float(row["generation_reward"]),
                "compatibility_reasons": str(row.get("compatibility_reasons", "")),
                "source_ledger": str(row["source_ledger"]),
            }
        )
    table = pd.DataFrame(rows)
    if len(table) > 1 and (table["split"] == "eval").sum() == 0:
        table.loc[table.index[-1], "split"] = "eval"
    return table


def write_jsonl(path: Path, examples: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(example, ensure_ascii=False) for example in examples) + ("\n" if examples else ""), encoding="utf-8")


def readiness_summary(
    ledger: pd.DataFrame,
    records: pd.DataFrame,
    sft_examples: list[dict[str, Any]],
    seed_table: pd.DataFrame,
    args: argparse.Namespace,
) -> dict[str, Any]:
    train_examples = sum(1 for example in sft_examples if example["metadata"]["split"] == "train")
    eval_examples = sum(1 for example in sft_examples if example["metadata"]["split"] == "eval")
    strategy_counts = records["strategy"].value_counts().to_dict() if not records.empty else {}
    source_counts = records["source_ledger"].value_counts().to_dict() if not records.empty else {}
    sft_ready = len(sft_examples) >= int(args.min_sft_examples) and eval_examples > 0
    diffusion_flow_ready = len(seed_table) >= int(args.min_diffusion_flow_examples) and seed_table["split"].nunique() >= 2 if not seed_table.empty else False
    return {
        "input_ledgers": [str(path) for path in args.ledgers],
        "input_rows": int(len(ledger)),
        "harness_pass_rows": int(ledger["harness_pass"].sum()) if not ledger.empty and "harness_pass" in ledger else 0,
        "training_candidate_rows": int(len(records)),
        "min_reward": float(args.min_reward),
        "sft_examples": int(len(sft_examples)),
        "sft_train_examples": int(train_examples),
        "sft_eval_examples": int(eval_examples),
        "sft_ready": bool(sft_ready),
        "sft_min_examples": int(args.min_sft_examples),
        "diffusion_flow_seed_rows": int(len(seed_table)),
        "diffusion_flow_train_rows": int((seed_table["split"] == "train").sum()) if not seed_table.empty else 0,
        "diffusion_flow_eval_rows": int((seed_table["split"] == "eval").sum()) if not seed_table.empty else 0,
        "diffusion_flow_ready": bool(diffusion_flow_ready),
        "diffusion_flow_min_examples": int(args.min_diffusion_flow_examples),
        "strategy_counts": strategy_counts,
        "source_ledger_counts": source_counts,
        "next_data_needed_for_sft": max(int(args.min_sft_examples) - len(sft_examples), 0),
        "next_data_needed_for_diffusion_flow": max(int(args.min_diffusion_flow_examples) - len(seed_table), 0),
    }


def write_report(summary: dict[str, Any], report_path: Path, out_dir: Path) -> None:
    lines = [
        "# Generative Model Training Set Readiness",
        "",
        "本文档回应 TODO 中“LLM 微调 SFT、扩散生成、流匹配”的生成模型后续要求。当前仍只使用单一小分子 SMILES / MoleCode，不进入暂缓的商品级组分或聚合物超图表示。",
        "",
        "## Outputs",
        "",
        f"- SFT JSONL: `{out_dir / 'sft_generation_records.jsonl'}`",
        f"- Diffusion/flow seed table: `{out_dir / 'diffusion_flow_seed_table.csv'}`",
        f"- Summary: `{out_dir / 'generative_training_summary.json'}`",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key in [
        "input_rows",
        "harness_pass_rows",
        "training_candidate_rows",
        "sft_examples",
        "sft_train_examples",
        "sft_eval_examples",
        "sft_ready",
        "diffusion_flow_seed_rows",
        "diffusion_flow_train_rows",
        "diffusion_flow_eval_rows",
        "diffusion_flow_ready",
        "next_data_needed_for_sft",
        "next_data_needed_for_diffusion_flow",
    ]:
        lines.append(f"| {key} | {summary[key]} |")
    lines.extend(
        [
            "",
            "## Strategy Counts",
            "",
            "| strategy | records |",
            "| --- | ---: |",
        ]
    )
    for strategy, count in summary.get("strategy_counts", {}).items():
        lines.append(f"| {strategy} | {count} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- SFT JSONL 只使用已经通过 generation record/Harness 的 records；draft 或缺 predictor/chemistry evidence 的样本不会进入训练目标。",
            "- Diffusion/flow seed table 是未来条件生成模型的数据契约，记录目标 Tg、SMILES、比例、预测 Tg、reward 和 compatibility evidence；本轮不训练扩散/流匹配模型。",
            "- readiness gate 的作用是阻止在样本过少时训练一个看似可用但不可泛化的生成模型；若某个 gate 已通过，仍必须在训练后让新候选重新经过 predictor/Harness/PiEvo。",
            "- 未通过的 gate 继续要求更多通过 Harness 且最好被 observation ledger 验证的 records。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_training_sets(args: argparse.Namespace) -> dict[str, Any]:
    ledgers = load_ledgers(args.ledgers)
    records = successful_records(ledgers, args.min_reward)
    sft_examples = build_sft_examples(records)
    seed_table = build_diffusion_flow_seed_table(records)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "sft_generation_records.jsonl", sft_examples)
    seed_table.to_csv(out_dir / "diffusion_flow_seed_table.csv", index=False)
    summary = readiness_summary(ledgers, records, sft_examples, seed_table, args)
    (out_dir / "generative_training_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, Path(args.report), out_dir)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build auditable training corpora for future SFT and diffusion/flow SMP generators.")
    parser.add_argument("--ledgers", nargs="+", type=Path, default=[Path(path) for path in DEFAULT_LEDGERS])
    parser.add_argument("--min-reward", type=float, default=0.0)
    parser.add_argument("--min-sft-examples", type=int, default=20)
    parser.add_argument("--min-diffusion-flow-examples", type=int, default=100)
    parser.add_argument("--out-dir", default="artifacts/trail/generation/generative_training_sets")
    parser.add_argument("--report", default="reports/generative_training_set_readiness.md")
    args = parser.parse_args()
    build_training_sets(args)


if __name__ == "__main__":
    main()

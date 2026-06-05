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
    return f"sft_dry_run_{digest}"


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def load_sft_examples(path: Path) -> list[dict[str, Any]]:
    examples = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        item = json.loads(line)
        messages = item.get("messages", [])
        assistant = next((message for message in messages if message.get("role") == "assistant"), None)
        user = next((message for message in messages if message.get("role") == "user"), None)
        if assistant is None:
            raise ValueError(f"SFT example line {line_number} has no assistant message")
        payload = json.loads(str(assistant["content"]))
        metadata = dict(item.get("metadata", {}))
        metadata["line_number"] = line_number
        examples.append(
            {
                "payload": payload,
                "metadata": metadata,
                "user_prompt": "" if user is None else str(user.get("content", "")),
            }
        )
    return examples


def split_examples(examples: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [example for example in examples if str(example["metadata"].get("split", "")) == split]


def target_distance(payload: dict[str, Any]) -> float:
    predicted = as_float(payload.get("predicted_tg_mean_c"))
    target = as_float(payload.get("target_tg_c"))
    return abs(predicted - target)


def candidate_key(payload: dict[str, Any]) -> tuple[str, str]:
    return str(payload.get("candidate_smiles", "")), str(payload.get("candidate_ratios", ""))


def select_prototypes(train_examples: list[dict[str, Any]], max_records: int) -> list[dict[str, Any]]:
    ranked = sorted(
        train_examples,
        key=lambda example: (
            target_distance(example["payload"]),
            as_float(example["payload"].get("ood_penalty"), 0.0),
            str(example["metadata"].get("generation_id", "")),
        ),
    )
    selected = []
    seen: set[tuple[str, str]] = set()
    for example in ranked:
        key = candidate_key(example["payload"])
        if key in seen:
            continue
        seen.add(key)
        selected.append(example)
        if len(selected) >= int(max_records):
            break
    return selected


def extract_line(prompt: str, prefix: str) -> str:
    for line in prompt.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def record_from_prototype(example: dict[str, Any], target_tg_c: float, target_window_c: float, generation_time: str) -> dict[str, Any]:
    payload = dict(example["payload"])
    metadata = dict(example["metadata"])
    user_prompt = str(example.get("user_prompt", ""))
    smiles, ratios = candidate_key(payload)
    prompt = "\n".join(
        [
            "SFT dry-run candidate generation.",
            f"Target Tg: {target_tg_c:.1f} C",
            f"Target window: +/-{target_window_c:.1f} C",
            "Use a validated train-split generation_record prototype; preserve auditability and re-run Harness.",
            f"Source SFT generation id: {metadata.get('generation_id', '')}",
            f"Source strategy: {metadata.get('strategy', '')}",
        ]
    )
    candidate_audit = {
        "dry_run_mode": "prototype_replay_not_weight_update",
        "source_sft_generation_id": metadata.get("generation_id", ""),
        "source_strategy": metadata.get("strategy", ""),
        "source_ledger": metadata.get("source_ledger", ""),
        "source_line_number": metadata.get("line_number"),
        "source_target_distance_c": metadata.get("target_distance_c"),
        "source_generation_reward": metadata.get("generation_reward"),
        "source_candidate_json": payload.get("candidate_json", ""),
    }
    return {
        "generation_id": stable_id(smiles, ratios, metadata.get("generation_id", ""), metadata.get("line_number", "")),
        "strategy": "sft_candidate_generator",
        "stage": "harnessed",
        "target_tg_c": float(target_tg_c),
        "target_window_c": float(target_window_c),
        "candidate_smiles": smiles,
        "candidate_ratios": ratios,
        "source_context": "sft_generation_record_jsonl_dry_run",
        "generator_id": "sft_candidate_generator:prototype_replay_v1",
        "generation_time": generation_time,
        "prompt_id": "sft_candidate_generator_dry_run_v1",
        "prompt_text": prompt,
        "prompt_hash": prompt_hash(prompt),
        "rag_query": "",
        "rag_context_refs": extract_line(user_prompt, "RAG refs:"),
        "rag_context_digest": extract_line(user_prompt, "RAG digest:"),
        "principle_hypothesis": str(payload.get("principle_hypothesis", "")),
        "functional_group_plan": str(payload.get("functional_group_plan", "")),
        "candidate_json": json.dumps(candidate_audit, ensure_ascii=False, sort_keys=True),
        "compatibility_reasons": str(payload.get("compatibility_reasons", "")),
        "predicted_tg_mean_c": as_float(payload.get("predicted_tg_mean_c")),
        "predicted_tg_sigma_c": as_float(payload.get("predicted_tg_sigma_c")),
        "ood_penalty": as_float(payload.get("ood_penalty")),
        "pievo_round": "",
        "selected_by_ids": False,
        "harness_failure_reason": "",
        "review_status": "needs_review",
        "notes": "SFT dry-run replay of a validated train-split generation record; not a neural weight update or real DSC.",
    }


def build_records(examples: list[dict[str, Any]], max_records: int, target_tg_c: float, target_window_c: float, generation_time: str) -> pd.DataFrame:
    train_examples = split_examples(examples, "train")
    if not train_examples:
        raise ValueError("SFT JSONL has no train split examples")
    rows = [
        record_from_prototype(example, target_tg_c, target_window_c, generation_time)
        for example in select_prototypes(train_examples, max_records)
    ]
    return pd.DataFrame(rows, columns=GENERATION_RECORD_COLUMNS)


def heldout_eval_table(examples: list[dict[str, Any]], prototypes: pd.DataFrame) -> pd.DataFrame:
    eval_examples = split_examples(examples, "eval")
    if not eval_examples:
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
    rows = []
    generated = prototypes.copy()
    generated["target_distance_c"] = (generated["predicted_tg_mean_c"].astype(float) - generated["target_tg_c"].astype(float)).abs()
    for example in eval_examples:
        payload = example["payload"]
        eval_smiles, eval_ratios = candidate_key(payload)
        exact = generated[(generated["candidate_smiles"] == eval_smiles) & (generated["candidate_ratios"] == eval_ratios)]
        if exact.empty:
            nearest = generated.sort_values("target_distance_c").iloc[0] if not generated.empty else pd.Series()
        else:
            nearest = exact.iloc[0]
        rows.append(
            {
                "eval_generation_id": example["metadata"].get("generation_id", ""),
                "eval_candidate_smiles": eval_smiles,
                "eval_candidate_ratios": eval_ratios,
                "nearest_generated_id": "" if nearest.empty else nearest["generation_id"],
                "nearest_generated_distance_c": None if nearest.empty else float(nearest["target_distance_c"]),
                "exact_candidate_match": bool(not exact.empty),
            }
        )
    return pd.DataFrame(rows)


def write_report(summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# SFT Candidate Generator Dry Run",
        "",
        "本文档把已经通过 readiness gate 的 SFT JSONL 推进一步：用 train split 中的 validated generation records 做一个可复现的 prototype-replay dry-run，并重新写入 `sft_candidate_generator` generation ledger。",
        "",
        "这不是神经网络权重微调完成，也不是外部 LLM 输出；它的作用是验证 SFT 生成器激活后的审计链、Harness 门禁和策略回流接口。",
        "",
        "## 输出文件",
        "",
        f"- Input records: `{out_dir / 'sft_candidate_records_input.csv'}`",
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
            "- `sft_candidate_generator` 的输出仍然必须满足 generation record schema、RDKit、ratio、prediction、target 和 chemistry evidence。",
            "- dry-run 只复用 validated train-split prototypes，因此可以验证链路，但不能证明模型已经学会分布外生成。",
            "- 后续若真正训练 LLM/SFT 权重，应把模型输出写入同一 ledger，并和本 dry-run 的 Harness pass、target distance、重复率做对比。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_dry_run(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    examples = load_sft_examples(Path(args.sft_jsonl))
    records = build_records(
        examples,
        max_records=args.max_records,
        target_tg_c=args.target_tg_c,
        target_window_c=args.target_window_c,
        generation_time=args.generation_time,
    )
    input_path = out_dir / "sft_candidate_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    records.to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    heldout = heldout_eval_table(examples, records)
    heldout.to_csv(out_dir / "heldout_eval_retrieval.csv", index=False)
    summary = summary | {
        "generator_mode": "prototype_replay_not_weight_update",
        "sft_jsonl": str(args.sft_jsonl),
        "train_examples": len(split_examples(examples, "train")),
        "eval_examples": len(split_examples(examples, "eval")),
        "generated_records": int(len(records)),
        "heldout_exact_candidate_matches": int(heldout["exact_candidate_match"].sum()) if not heldout.empty else 0,
        "heldout_eval_rows": int(len(heldout)),
        "input_records_path": str(input_path),
        "generation_record_ledger_path": str(ledger_path),
        "heldout_eval_retrieval_path": str(out_dir / "heldout_eval_retrieval.csv"),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(summary, out_dir, Path(args.report))
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an auditable internal SFT candidate-generator dry run.")
    parser.add_argument("--sft-jsonl", default="artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl")
    parser.add_argument("--max-records", type=int, default=25)
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--generation-time", default="2026-06-06")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/sft_candidate_dry_run")
    parser.add_argument("--report", default="reports/sft_candidate_generator_dry_run.md")
    args = parser.parse_args()
    run_dry_run(args)


if __name__ == "__main__":
    main()

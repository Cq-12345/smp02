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


def stable_id(prefix: str, smiles: str, ratios: str, source_index: object) -> str:
    digest = hashlib.sha256(f"{prefix}|{smiles}|{ratios}|{source_index}".encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: object, default: float | None = None) -> float | None:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def source_metadata(row: pd.Series, source_index: int) -> dict[str, Any]:
    keys = [
        "proposal_index",
        "formula_id",
        "replace_side",
        "original_smiles",
        "replacement_smiles",
        "replacement_source",
        "replacement_label",
        "replacement_tanimoto",
        "replacement_latent_distance",
        "replacement_latent_rank",
        "feedback_constraint",
        "counterpart_compatibility_reason",
        "source_candidate_tg_c",
        "source_target_distance_c",
        "harness_pass",
        "target_ok",
        "chemistry_ok",
    ]
    payload = {"source_row_index": source_index}
    for key in keys:
        if key in row.index and not pd.isna(row[key]):
            value = row[key]
            if hasattr(value, "item"):
                value = value.item()
            payload[key] = value
    return payload


def record_from_scored_row(
    row: pd.Series,
    source_index: int,
    strategy: str,
    source_context: str,
    generator_id: str,
    target_tg_c: float,
    target_window_c: float,
    generation_time: str,
) -> dict[str, Any]:
    smiles = str(row["smiles"])
    ratios = str(row["ratios"])
    harness_pass = parse_bool(row.get("harness_pass", False))
    target_ok = parse_bool(row.get("target_ok", False))
    chemistry_ok = parse_bool(row.get("chemistry_ok", False))
    failure_reasons = []
    if not target_ok:
        failure_reasons.append("target_out_of_window")
    if not chemistry_ok:
        failure_reasons.append("chemistry_evidence_missing")
    if "harness_pass" in row.index and not harness_pass and not failure_reasons:
        failure_reasons.append("harness_failed")
    payload = source_metadata(row, source_index)
    prompt_text = (
        f"Generate an auditable SMP formulation with strategy={strategy}, "
        f"target_tg_c={target_tg_c:g}, target_window_c={target_window_c:g}; "
        "proposal must retain chemistry evidence and pass predictor/Harness before recommendation."
    )
    return {
        "generation_id": stable_id(strategy, smiles, ratios, row.get("proposal_index", source_index)),
        "strategy": strategy,
        "stage": "harnessed" if harness_pass else "predicted",
        "target_tg_c": float(target_tg_c),
        "target_window_c": float(target_window_c),
        "candidate_smiles": smiles,
        "candidate_ratios": ratios,
        "source_context": source_context,
        "generator_id": generator_id,
        "generation_time": generation_time,
        "prompt_id": f"{strategy}_proposal_eval_bridge",
        "prompt_text": prompt_text,
        "prompt_hash": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:16],
        "rag_query": "",
        "rag_context_refs": "trail/generation/generation_strategy_registry.yaml|reports/human_experiment_review_queue.md",
        "rag_context_digest": "proposal evaluation bridge; records scored replacement/local-search proposals after predictor and Harness.",
        "principle_hypothesis": str(row.get("feedback_constraint", "")),
        "functional_group_plan": str(row.get("compatibility_reasons", "")),
        "candidate_json": json.dumps(payload, ensure_ascii=False, sort_keys=True),
        "compatibility_reasons": str(row.get("compatibility_reasons", "")),
        "predicted_tg_mean_c": as_float(row.get("predicted_tg_mean_c")),
        "predicted_tg_sigma_c": as_float(row.get("predicted_tg_sigma_c")),
        "ood_penalty": as_float(row.get("ood_penalty"), 0.0),
        "pievo_round": "",
        "selected_by_ids": False,
        "harness_failure_reason": ";".join(failure_reasons),
        "review_status": "needs_review" if harness_pass else "rejected_by_harness",
        "notes": (
            f"Imported from scored proposal eval; source_context={source_context}; "
            "surrogate evidence only, not real DSC."
        ),
    }


def build_generation_record_input(
    scored_path: Path,
    strategy: str,
    source_context: str,
    generator_id: str,
    target_tg_c: float,
    target_window_c: float,
    generation_time: str,
    limit: int | None = None,
) -> pd.DataFrame:
    scored = pd.read_csv(scored_path)
    if limit is not None:
        scored = scored.head(limit).copy()
    required = {"smiles", "ratios", "predicted_tg_mean_c", "compatibility_reasons"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"Scored proposal file {scored_path} missing required columns: {missing}")
    rows = [
        record_from_scored_row(
            row,
            source_index=int(idx),
            strategy=strategy,
            source_context=source_context,
            generator_id=generator_id,
            target_tg_c=target_tg_c,
            target_window_c=target_window_c,
            generation_time=generation_time,
        )
        for idx, row in scored.iterrows()
    ]
    return pd.DataFrame(rows, columns=GENERATION_RECORD_COLUMNS)


def write_report(input_records: pd.DataFrame, ledger: pd.DataFrame, summary: dict[str, Any], out_dir: Path, report_path: Path) -> None:
    lines = [
        "# Proposal Evaluation -> Generation Records",
        "",
        "本文档把已经完成 predictor/Harness 的 replacement 或 VAE latent local search proposals 写回 generation record ledger。这样 SFT、扩散/流匹配和策略回流不只依赖少量 prompt/RAG smoke records。",
        "",
        "## 输出文件",
        "",
        f"- Input records: `{out_dir / 'proposal_generation_records_input.csv'}`",
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
            "## Harness State",
            "",
            "| item | value |",
            "| --- | ---: |",
            f"| input_records | {len(input_records)} |",
            f"| ledger_rows | {len(ledger)} |",
            f"| harness_pass | {int(ledger['harness_pass'].sum()) if 'harness_pass' in ledger else 0} |",
            f"| record_pass | {int(ledger['record_pass'].sum()) if 'record_pass' in ledger else 0} |",
            "",
            "## 解释",
            "",
            "- 这些 records 来自已评分 proposals，不是新的真实实验。",
            "- importer 会重新检查 SMILES、ratio、target window 和 compatibility evidence；失败项保留在 ledger 中用于反馈，训练集构建器只使用通过项。",
            "- 这样可以扩大 SFT / diffusion / flow 的 validated training corpus，同时保持 Harness 和审计链不被绕过。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_import(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    input_records = build_generation_record_input(
        Path(args.scored),
        strategy=args.strategy,
        source_context=args.source_context,
        generator_id=args.generator_id,
        target_tg_c=args.target_tg_c,
        target_window_c=args.target_window_c,
        generation_time=args.generation_time,
        limit=args.limit,
    )
    input_path = out_dir / "proposal_generation_records_input.csv"
    ledger_path = out_dir / "generation_record_ledger.csv"
    summary_path = out_dir / "generation_record_summary.json"
    input_records.to_csv(input_path, index=False)
    ledger, summary = import_generation_records(input_path, Path(args.schema), args.reward_temperature_c)
    ledger.to_csv(ledger_path, index=False)
    summary = summary | {
        "strategy": args.strategy,
        "source_context": args.source_context,
        "input_records_path": str(input_path),
        "generation_record_ledger_path": str(ledger_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(input_records, ledger, summary, out_dir, Path(args.report))
    return ledger, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert scored proposal evaluations into auditable generation record ledgers.")
    parser.add_argument("--scored", required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--source-context", required=True)
    parser.add_argument("--generator-id", default="")
    parser.add_argument("--target-tg-c", type=float, default=195.0)
    parser.add_argument("--target-window-c", type=float, default=5.0)
    parser.add_argument("--generation-time", default="2026-06-06")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--schema", default="trail/generation/generation_record_schema.yaml")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if not args.generator_id:
        args.generator_id = args.strategy
    run_import(args)


if __name__ == "__main__":
    main()

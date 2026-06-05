from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from trail.experiments.import_observations import import_observations


def truthy(value: object) -> bool:
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def finite(value: object) -> bool:
    try:
        return pd.notna(value) and pd.notna(float(value))
    except (TypeError, ValueError):
        return False


def safe_id(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9_+-]+", "_", text)
    return text.strip("_") or "unknown"


def generation_ledger_to_observation_input(
    ledger: pd.DataFrame,
    *,
    source_type: str,
    observation_prefix: str,
    operator: str,
    method: str,
    experiment_date: str,
    require_harness_pass: bool,
    require_record_pass: bool,
    limit: int | None = None,
) -> pd.DataFrame:
    required = [
        "generation_id",
        "strategy",
        "target_tg_c",
        "candidate_smiles",
        "candidate_ratios",
        "predicted_tg_mean_c",
    ]
    missing = [column for column in required if column not in ledger.columns]
    if missing:
        raise ValueError(f"Missing required generation ledger columns: {missing}")

    rows = []
    frame = ledger.copy()
    if require_harness_pass and "harness_pass" in frame.columns:
        frame = frame[frame["harness_pass"].map(truthy)].copy()
    if require_record_pass and "record_pass" in frame.columns:
        frame = frame[frame["record_pass"].map(truthy)].copy()
    frame = frame[frame["predicted_tg_mean_c"].map(finite)].copy()
    if "target_distance_c" in frame.columns:
        frame = frame.sort_values(["target_distance_c", "generation_id"])
    if limit is not None:
        frame = frame.head(limit).copy()

    for _, row in frame.iterrows():
        generation_id = str(row["generation_id"])
        strategy = str(row.get("strategy", "unknown_strategy"))
        observed_tg_c = float(row["predicted_tg_mean_c"])
        sigma = row.get("predicted_tg_sigma_c", "")
        notes_payload: dict[str, Any] = {
            "generation_id": generation_id,
            "strategy": strategy,
            "stage": row.get("stage", ""),
            "generator_id": row.get("generator_id", ""),
            "prompt_id": row.get("prompt_id", ""),
            "source_context": row.get("source_context", ""),
            "review_status": row.get("review_status", ""),
        }
        rows.append(
            {
                "observation_id": f"{observation_prefix}_{safe_id(strategy)}_{safe_id(generation_id)}",
                "source_type": source_type,
                "target_tg_c": float(row["target_tg_c"]),
                "observed_tg_c": observed_tg_c,
                "smiles": row["candidate_smiles"],
                "ratios": row["candidate_ratios"],
                "predicted_tg_mean_c": observed_tg_c,
                "predicted_tg_sigma_c": "" if not finite(sigma) else float(sigma),
                "experiment_date": experiment_date,
                "operator": operator,
                "method": method,
                "notes": json.dumps(notes_payload, ensure_ascii=False, sort_keys=True),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "observation_id",
            "source_type",
            "target_tg_c",
            "observed_tg_c",
            "smiles",
            "ratios",
            "predicted_tg_mean_c",
            "predicted_tg_sigma_c",
            "experiment_date",
            "operator",
            "method",
            "notes",
        ],
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_report(
    observation_input: pd.DataFrame,
    observation_ledger: pd.DataFrame,
    ledger_summary: dict[str, Any],
    report_path: Path,
    out_dir: Path,
    generation_ledger_path: Path,
    pievo_output_dir: Path | None,
) -> None:
    pievo_summary = read_json(pievo_output_dir / "pievo_faithful_summary.json") if pievo_output_dir else {}
    external_summary = read_json(pievo_output_dir / "external_observation_summary.json") if pievo_output_dir else {}
    lines = [
        "# Feedback-Aware LLM/RAG Records To PiEvo",
        "",
        "本文档记录 `feedback-aware LLM/RAG agent -> generation ledger -> observation ledger -> PiEvo-faithful posterior` 的闭环。当前仍使用单一小分子 SMILES / MoleCode；这里的 observation source 是 `surrogate`，因为 Tg 来自 VAE-WVCM-GPR 预测，不是真实 DSC。",
        "",
        "## Outputs",
        "",
        f"- Generation ledger: `{generation_ledger_path}`",
        f"- Observation input: `{out_dir / 'generation_observations_input.csv'}`",
        f"- Observation ledger: `{out_dir / 'generation_observation_ledger.csv'}`",
        f"- Observation summary: `{out_dir / 'generation_observation_ledger_summary.json'}`",
    ]
    if pievo_output_dir:
        lines.append(f"- PiEvo output: `{pievo_output_dir}`")
    lines.extend(
        [
            "",
            "## Observation Ledger Summary",
            "",
            "| item | value |",
            "| --- | ---: |",
        ]
    )
    for key, value in ledger_summary.items():
        if isinstance(value, dict):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Imported Records",
            "",
            "| observation id | source | Tg (C) | distance (C) | ledger pass | method |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )
    for _, row in observation_ledger.iterrows():
        distance = "" if pd.isna(row["target_distance_c"]) else f"{float(row['target_distance_c']):.3f}"
        lines.append(
            f"| {row['observation_id']} | {row['source_type']} | {float(row['observed_tg_c']):.3f} | "
            f"{distance} | {bool(row['ledger_pass'])} | {row.get('method', '')} |"
        )
    lines.extend(
        [
            "",
            "## PiEvo Feedback",
            "",
        ]
    )
    if pievo_summary:
        lines.extend(
            [
                "| item | value |",
                "| --- | ---: |",
                f"| external accepted rows | {external_summary.get('accepted_rows')} |",
                f"| external total authority weight | {external_summary.get('total_authority_weight')} |",
                f"| external mean reward | {external_summary.get('mean_reward')} |",
                f"| PiEvo rounds | {pievo_summary.get('rounds')} |",
                f"| history rows | {pievo_summary.get('history_rows')} |",
                f"| selected rows | {pievo_summary.get('selected_rows')} |",
                f"| best selected distance C | {pievo_summary.get('best_selected_target_distance_c')} |",
                f"| posterior entropy | {pievo_summary.get('posterior_entropy')} |",
                f"| MAP principle | {pievo_summary.get('map_principle')} |",
                "",
            ]
        )
    else:
        lines.append("- PiEvo output has not been attached yet.")
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "- 这一步把 LLM/RAG agent 的成功 records 作为低权重 surrogate observations 接入 PiEvo full-history posterior。",
            "- 失败或缺预测的 generation records 不会进入 observation ledger；它们仍留在 generation feedback 中约束下一轮生成。",
            "- 这不是把 LLM 输出当成物理事实，而是让 PiEvo 能审计“由 LLM/RAG 生成、由 predictor/Harness 验证过”的候选证据。",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_import(args: argparse.Namespace) -> tuple[pd.DataFrame, dict[str, Any]]:
    generation_ledger_path = Path(args.generation_ledger)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generation_ledger = pd.read_csv(generation_ledger_path)
    observation_input = generation_ledger_to_observation_input(
        generation_ledger,
        source_type=args.source_type,
        observation_prefix=args.observation_prefix,
        operator=args.operator,
        method=args.method,
        experiment_date=args.experiment_date,
        require_harness_pass=args.require_harness_pass,
        require_record_pass=args.require_record_pass,
        limit=args.limit,
    )
    input_path = out_dir / "generation_observations_input.csv"
    ledger_path = out_dir / "generation_observation_ledger.csv"
    summary_path = out_dir / "generation_observation_ledger_summary.json"
    observation_input.to_csv(input_path, index=False)
    observation_ledger, ledger_summary = import_observations(input_path, Path(args.schema), args.reward_temperature_c)
    observation_ledger.to_csv(ledger_path, index=False)
    summary_path.write_text(json.dumps(ledger_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(
        observation_input,
        observation_ledger,
        ledger_summary,
        Path(args.report),
        out_dir,
        generation_ledger_path,
        None if not args.pievo_output_dir else Path(args.pievo_output_dir),
    )
    return observation_ledger, ledger_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote harness-passing generation records into a surrogate observation ledger.")
    parser.add_argument("--generation-ledger", default="artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv")
    parser.add_argument("--schema", default="trail/experiments/observation_schema.yaml")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--source-type", default="surrogate")
    parser.add_argument("--observation-prefix", default="feedback_aware_llm_rag")
    parser.add_argument("--operator", default="feedback_aware_llm_rag_agent")
    parser.add_argument("--method", default="generation_record_surrogate_bridge")
    parser.add_argument("--experiment-date", default="2026-06-06")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--require-harness-pass", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--require-record-pass", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--pievo-output-dir", default="")
    parser.add_argument("--out-dir", default="artifacts/trail/generation/feedback_aware_llm_rag_observations")
    parser.add_argument("--report", default="reports/feedback_aware_llm_rag_pievo_feedback.md")
    args = parser.parse_args()
    run_import(args)


if __name__ == "__main__":
    main()

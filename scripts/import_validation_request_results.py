from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from trail.experiments.import_observations import import_observations  # noqa: E402


RESULT_COLUMNS = [
    "result_id",
    "request_id",
    "source_type",
    "observed_tg_c",
    "method",
    "experiment_date",
    "operator",
    "process_record_id",
    "process_ready",
    "reviewer_approved",
    "result_notes",
]

OBSERVATION_INPUT_COLUMNS = [
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
]


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "approved"}


def has_value(value: Any) -> bool:
    return value is not None and not pd.isna(value) and str(value).strip() != ""


def result_template_from_requests(requests: pd.DataFrame) -> pd.DataFrame:
    observation_requests = requests[requests["eligible_observation_source_type"].fillna("").astype(str).str.len() > 0].copy()
    rows = []
    for _, row in observation_requests.iterrows():
        rows.append(
            {
                "result_id": f"result_{row['request_id']}",
                "request_id": row["request_id"],
                "source_type": row["eligible_observation_source_type"],
                "observed_tg_c": "",
                "method": "",
                "experiment_date": "",
                "operator": "",
                "process_record_id": "",
                "process_ready": False,
                "reviewer_approved": False,
                "result_notes": "",
                "target_tg_c": row["target_tg_c"],
                "candidate_origin": row["candidate_origin"],
                "blocked_by_process_completion": row.get("blocked_by_process_completion", False),
                "required_process_inputs": row.get("required_inputs", ""),
                "smiles": row["smiles"],
                "ratios": row["ratios"],
            }
        )
    return pd.DataFrame(rows)


def read_results(results_path: Path) -> pd.DataFrame:
    if not results_path.exists():
        return pd.DataFrame(columns=RESULT_COLUMNS)
    results = pd.read_csv(results_path)
    for col in RESULT_COLUMNS:
        if col not in results.columns:
            results[col] = ""
    return results


def process_ready_from_ledger(process_ledger_path: Path) -> dict[str, bool]:
    if not process_ledger_path.exists():
        return {}
    ledger = pd.read_csv(process_ledger_path)
    if "process_record_id" not in ledger.columns or "ready_for_active_ledger" not in ledger.columns:
        return {}
    return {str(row["process_record_id"]): bool_value(row["ready_for_active_ledger"]) for _, row in ledger.iterrows()}


def evaluate_results(
    requests: pd.DataFrame,
    results: pd.DataFrame,
    process_ready_lookup: dict[str, bool] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    process_ready_lookup = process_ready_lookup or {}
    request_map = requests.set_index("request_id").to_dict(orient="index") if not requests.empty else {}
    review_rows = []
    observation_rows = []
    for _, result in results.iterrows():
        request_id = str(result.get("request_id", ""))
        request = request_map.get(request_id)
        reasons = []
        if request is None:
            reasons.append("unknown_request_id")
            request = {}
        eligible_source = str(request.get("eligible_observation_source_type", "") or "")
        source_type = str(result.get("source_type", "") or "")
        process_record_id = str(result.get("process_record_id", "") or "")
        process_ready = bool_value(result.get("process_ready")) or process_ready_lookup.get(process_record_id, False)
        reviewer_approved = bool_value(result.get("reviewer_approved"))
        if not eligible_source:
            reasons.append("request_not_observation_capable")
        if eligible_source and source_type != eligible_source:
            reasons.append("source_type_mismatch")
        if not has_value(result.get("observed_tg_c")):
            reasons.append("observed_tg_missing")
        if not process_ready:
            reasons.append("process_not_ready")
        if not reviewer_approved:
            reasons.append("reviewer_not_approved")
        accepted = len(reasons) == 0
        review_row = {
            **{f"result_{col}": result.get(col, "") for col in RESULT_COLUMNS},
            "request_id": request_id,
            "eligible_observation_source_type": eligible_source,
            "target_tg_c": request.get("target_tg_c"),
            "smiles": request.get("smiles", ""),
            "ratios": request.get("ratios", ""),
            "process_ready_effective": process_ready,
            "reviewer_approved_effective": reviewer_approved,
            "accepted_for_observation_ledger": accepted,
            "rejection_reasons": ";".join(reasons),
        }
        review_rows.append(review_row)
        if accepted:
            observation_rows.append(
                {
                    "observation_id": f"validation_result_{result.get('result_id')}",
                    "source_type": source_type,
                    "target_tg_c": request["target_tg_c"],
                    "observed_tg_c": result["observed_tg_c"],
                    "smiles": request["smiles"],
                    "ratios": request["ratios"],
                    "predicted_tg_mean_c": request.get("surrogate_tg_c", ""),
                    "predicted_tg_sigma_c": request.get("predicted_tg_sigma_c", ""),
                    "experiment_date": result.get("experiment_date", ""),
                    "operator": result.get("operator", ""),
                    "method": result.get("method", ""),
                    "notes": (
                        f"validation_request={request_id}; process_record_id={process_record_id}; "
                        f"candidate_origin={request.get('candidate_origin', '')}; notes={result.get('result_notes', '')}"
                    ),
                }
            )
    review = pd.DataFrame(review_rows)
    observation_input = pd.DataFrame(observation_rows, columns=OBSERVATION_INPUT_COLUMNS)
    rejection_counts: dict[str, int] = {}
    if not review.empty:
        for reasons in review["rejection_reasons"]:
            for reason in str(reasons).split(";"):
                if reason:
                    rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
    summary = {
        "result_rows": int(len(results)),
        "accepted_result_rows": int(len(observation_input)),
        "rejected_result_rows": int(len(results) - len(observation_input)),
        "rejection_reason_counts": rejection_counts,
        "accepted_source_counts": observation_input["source_type"].value_counts().to_dict() if not observation_input.empty else {},
        "process_ready_rows": int(review["process_ready_effective"].sum()) if not review.empty else 0,
        "reviewer_approved_rows": int(review["reviewer_approved_effective"].sum()) if not review.empty else 0,
    }
    return review, observation_input, summary


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Validation Result Intake",
        "",
        "本文档记录 validation request 完成结果如何进入 observation ledger。当前没有真实或高保真完成结果时，accepted rows 应为 0。",
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
    for title, counts in [
        ("Rejection Reasons", summary.get("rejection_reason_counts", {})),
        ("Accepted Source Counts", summary.get("accepted_source_counts", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Gate Rules",
            "",
            "- `source_type` 必须与 request 的 `eligible_observation_source_type` 一致。",
            "- `observed_tg_c`、`process_ready` 和 `reviewer_approved` 都必须满足，结果才会写入 observation input。",
            "- process completion request 本身不是 observation-capable request，不能直接产生 Tg observation。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", default="artifacts/trail/human_review/validation_request_queue.csv")
    parser.add_argument("--results", default="artifacts/trail/human_review/validation_result_completed.csv")
    parser.add_argument("--process-ledger", default="artifacts/trail/human_review/draft_process_record_ledger.csv")
    parser.add_argument("--observation-schema", default="trail/experiments/observation_schema.yaml")
    parser.add_argument("--reward-temperature-c", type=float, default=5.0)
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/validation_result_intake.md")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    requests = pd.read_csv(args.requests) if Path(args.requests).exists() else pd.DataFrame()
    template = result_template_from_requests(requests)
    template_path = out_dir / "validation_result_intake_template.csv"
    template.to_csv(template_path, index=False)

    results = read_results(Path(args.results))
    process_lookup = process_ready_from_ledger(Path(args.process_ledger))
    review, observation_input, intake_summary = evaluate_results(requests, results, process_lookup)
    review_path = out_dir / "validation_result_review.csv"
    observation_input_path = out_dir / "validation_result_observation_input.csv"
    observation_ledger_path = out_dir / "validation_result_observation_ledger.csv"
    observation_summary_path = out_dir / "validation_result_observation_summary.json"
    summary_path = out_dir / "validation_result_intake_summary.json"

    review.to_csv(review_path, index=False)
    observation_input.to_csv(observation_input_path, index=False)
    observation_ledger, observation_summary = import_observations(
        observation_input_path,
        Path(args.observation_schema),
        args.reward_temperature_c,
    )
    observation_ledger.to_csv(observation_ledger_path, index=False)
    observation_summary_path.write_text(json.dumps(observation_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {
        "template_rows": int(len(template)),
        **intake_summary,
        "observation_ledger_pass_rows": observation_summary.get("ledger_pass_rows", 0),
        "template_path": str(template_path),
        "review_path": str(review_path),
        "observation_input_path": str(observation_input_path),
        "observation_ledger_path": str(observation_ledger_path),
        "observation_summary_path": str(observation_summary_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(summary, Path(args.report))


if __name__ == "__main__":
    main()

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

from scripts.build_process_completion_packet import PROCESS_RECORD_COLUMNS, read_csv  # noqa: E402
from trail.experiments.import_process_records import import_process_records  # noqa: E402


APPROVAL_COLUMNS = [
    "approval_id",
    "request_id",
    "process_record_id",
    "linked_observation_id",
    "approval_decision",
    "process_ready",
    "reviewer_approved",
    "reviewer_id",
    "review_date",
    "review_notes",
]

TEMPLATE_COLUMNS = [
    *APPROVAL_COLUMNS,
    "target_tg_c",
    "surrogate_tg_c",
    "candidate_origin",
    "reaction_principle",
    "process_template",
    "suggested_inputs",
    "risk_flags",
    "evidence_level",
    "smiles",
    "ratios",
]


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "approved", "approve"}


def present(value: Any) -> bool:
    return value is not None and not pd.isna(value) and str(value).strip() != ""


def number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def approval_is_positive(value: Any) -> bool:
    return str(value).strip().lower() in {"approved", "approve", "accept", "accepted", "yes", "y", "true", "1"}


def build_approval_template(suggestions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in suggestions.iterrows():
        rows.append(
            {
                "approval_id": f"approval_{row.get('request_id', '')}",
                "request_id": row.get("request_id", ""),
                "process_record_id": row.get("process_record_id", ""),
                "linked_observation_id": row.get("linked_observation_id", ""),
                "approval_decision": "",
                "process_ready": False,
                "reviewer_approved": False,
                "reviewer_id": "",
                "review_date": "",
                "review_notes": "",
                "target_tg_c": row.get("target_tg_c", ""),
                "surrogate_tg_c": row.get("surrogate_tg_c", ""),
                "candidate_origin": row.get("candidate_origin", ""),
                "reaction_principle": row.get("reaction_principle", ""),
                "process_template": row.get("process_template", ""),
                "suggested_inputs": row.get("suggested_inputs", ""),
                "risk_flags": row.get("risk_flags", ""),
                "evidence_level": row.get("evidence_level", ""),
                "smiles": row.get("smiles", ""),
                "ratios": row.get("ratios", ""),
            }
        )
    return pd.DataFrame(rows, columns=TEMPLATE_COLUMNS)


def read_approvals(approval_path: Path) -> pd.DataFrame:
    if not approval_path.exists():
        return pd.DataFrame(columns=APPROVAL_COLUMNS)
    approvals = pd.read_csv(approval_path)
    for column in APPROVAL_COLUMNS:
        if column not in approvals.columns:
            approvals[column] = ""
    return approvals


def suggestion_lookup(suggestions: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if suggestions.empty or "process_record_id" not in suggestions.columns:
        return {}
    return {str(row["process_record_id"]): row.to_dict() for _, row in suggestions.iterrows()}


def suggested_process_lookup(process_records: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if process_records.empty or "process_record_id" not in process_records.columns:
        return {}
    return {str(row["process_record_id"]): row.to_dict() for _, row in process_records.iterrows()}


def process_rows_from_approvals(
    approvals: pd.DataFrame,
    suggestions: pd.DataFrame,
    suggested_process_records: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    by_process_id = suggestion_lookup(suggestions)
    process_by_id = suggested_process_lookup(suggested_process_records)
    review_rows: list[dict[str, Any]] = []
    process_rows: list[dict[str, Any]] = []
    for _, approval in approvals.iterrows():
        process_record_id = str(approval.get("process_record_id", ""))
        request_id = str(approval.get("request_id", ""))
        suggestion = by_process_id.get(process_record_id)
        base_process = process_by_id.get(process_record_id, {})
        reasons: list[str] = []
        if suggestion is None:
            reasons.append("unknown_process_record_id")
            suggestion = {}
        if request_id and suggestion.get("request_id") and request_id != str(suggestion.get("request_id", "")):
            reasons.append("request_id_mismatch")
        if not approval_is_positive(approval.get("approval_decision")):
            reasons.append("approval_decision_not_approved")
        if not bool_value(approval.get("process_ready")):
            reasons.append("process_ready_not_true")
        if not bool_value(approval.get("reviewer_approved")):
            reasons.append("reviewer_approved_not_true")
        if not present(approval.get("reviewer_id")):
            reasons.append("reviewer_id_missing")
        initially_accepted = len(reasons) == 0
        process_row = dict(base_process)
        for column in PROCESS_RECORD_COLUMNS:
            process_row.setdefault(column, "")
        process_row.update(
            {
                "process_record_id": process_record_id,
                "linked_observation_id": suggestion.get("linked_observation_id", approval.get("linked_observation_id", "")),
                "source_type": "surrogate_review",
                "target_tg_c": number(suggestion.get("target_tg_c", base_process.get("target_tg_c", 0.0))),
                "observed_tg_c": number(suggestion.get("surrogate_tg_c", base_process.get("observed_tg_c", 0.0))),
                "smiles": suggestion.get("smiles", base_process.get("smiles", "")),
                "ratios": suggestion.get("ratios", base_process.get("ratios", "")),
                "reaction_principle": suggestion.get("reaction_principle", base_process.get("reaction_principle", "")),
                "process_template": suggestion.get("process_template", base_process.get("process_template", "")),
                "review_status": "approved_for_active_ledger" if initially_accepted else "needs_human_review",
                "operator": approval.get("reviewer_id", base_process.get("operator", "")),
                "notes": (
                    "Human process approval intake; not a Tg observation; "
                    f"approval_id={approval.get('approval_id', '')}; decision={approval.get('approval_decision', '')}; "
                    f"notes={approval.get('review_notes', '')}"
                ),
            }
        )
        process_rows.append(process_row)
        review_rows.append(
            {
                **{f"approval_{column}": approval.get(column, "") for column in APPROVAL_COLUMNS},
                "request_id": request_id,
                "process_record_id": process_record_id,
                "linked_observation_id": suggestion.get("linked_observation_id", approval.get("linked_observation_id", "")),
                "target_tg_c": suggestion.get("target_tg_c", ""),
                "candidate_origin": suggestion.get("candidate_origin", ""),
                "process_template": suggestion.get("process_template", ""),
                "initially_accepted_for_process_import": initially_accepted,
                "initial_rejection_reasons": ";".join(reasons),
            }
        )
    return pd.DataFrame(review_rows), pd.DataFrame(process_rows)


def evaluate_process_approvals(
    approval_review: pd.DataFrame,
    process_ledger: pd.DataFrame,
) -> pd.DataFrame:
    if approval_review.empty:
        return approval_review
    ledger_map = (
        {str(row["process_record_id"]): row.to_dict() for _, row in process_ledger.iterrows()}
        if not process_ledger.empty and "process_record_id" in process_ledger.columns
        else {}
    )
    rows: list[dict[str, Any]] = []
    for _, row in approval_review.iterrows():
        process_record_id = str(row.get("process_record_id", ""))
        ledger = ledger_map.get(process_record_id, {})
        reasons = [reason for reason in str(row.get("initial_rejection_reasons", "")).split(";") if reason]
        process_record_pass = bool_value(ledger.get("process_record_pass"))
        process_fields_complete = bool_value(ledger.get("process_fields_complete"))
        ready_for_active_ledger = bool_value(ledger.get("ready_for_active_ledger"))
        if not process_record_pass:
            reasons.append("process_record_import_failed")
        if not process_fields_complete:
            reasons.append("process_fields_incomplete_after_approval")
        if not ready_for_active_ledger:
            reasons.append("process_record_not_ready_for_active_ledger")
        accepted = len(reasons) == 0
        rows.append(
            {
                **row.to_dict(),
                "process_record_pass": process_record_pass,
                "process_fields_complete": process_fields_complete,
                "ready_for_active_ledger": ready_for_active_ledger,
                "accepted_process_approval": accepted,
                "final_rejection_reasons": ";".join(dict.fromkeys(reasons)),
            }
        )
    return pd.DataFrame(rows)


def unblocked_observation_requests(requests: pd.DataFrame, approval_review: pd.DataFrame) -> pd.DataFrame:
    if requests.empty or approval_review.empty:
        return pd.DataFrame()
    accepted_ids = set(
        approval_review.loc[approval_review["accepted_process_approval"].map(bool_value), "linked_observation_id"].astype(str)
    )
    if not accepted_ids:
        return pd.DataFrame()
    unblocked = requests[
        requests["linked_observation_id"].astype(str).isin(accepted_ids)
        & requests["blocked_by_process_completion"].map(bool_value)
        & requests["eligible_observation_source_type"].fillna("").astype(str).str.len().gt(0)
    ].copy()
    if unblocked.empty:
        return unblocked
    unblocked["process_approval_unblocked"] = True
    unblocked["unblock_scope"] = "process_record_ready_human_approved; still requires validation result intake"
    return unblocked


def rejection_counts(review: pd.DataFrame, column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    if review.empty or column not in review.columns:
        return counts
    for reasons in review[column]:
        for reason in str(reasons).split(";"):
            if reason:
                counts[reason] = counts.get(reason, 0) + 1
    return counts


def import_process_approval_intake(
    suggestions_path: Path,
    suggested_process_records_path: Path,
    approvals_path: Path,
    validation_requests_path: Path,
    process_schema: Path,
    knowledge_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    suggestions = read_csv(suggestions_path)
    suggested_process_records = read_csv(suggested_process_records_path)
    approvals = read_approvals(approvals_path)
    requests = read_csv(validation_requests_path)
    template = build_approval_template(suggestions)
    initial_review, process_rows = process_rows_from_approvals(approvals, suggestions, suggested_process_records)
    if process_rows.empty:
        process_ledger = pd.DataFrame()
        final_review = initial_review
    else:
        temp_path = approvals_path.parent / ".process_approval_records.tmp.csv"
        process_rows.to_csv(temp_path, index=False)
        try:
            process_ledger, _ = import_process_records(temp_path, process_schema, knowledge_path)
        finally:
            temp_path.unlink(missing_ok=True)
        final_review = evaluate_process_approvals(initial_review, process_ledger)
    unblocked = unblocked_observation_requests(requests, final_review)
    accepted_rows = int(final_review["accepted_process_approval"].sum()) if not final_review.empty else 0
    ready_rows = int(final_review["ready_for_active_ledger"].sum()) if not final_review.empty else 0
    summary = {
        "suggestion_rows": int(len(suggestions)),
        "approval_template_rows": int(len(template)),
        "submitted_approval_rows": int(len(approvals)),
        "accepted_process_approval_rows": accepted_rows,
        "rejected_process_approval_rows": int(len(approvals) - accepted_rows),
        "ready_process_record_rows": ready_rows,
        "unblocked_observation_request_rows": int(len(unblocked)),
        "unblocked_target_counts": {
            f"{float(key):.1f}": int(value) for key, value in unblocked["target_tg_c"].value_counts().sort_index().items()
        }
        if not unblocked.empty
        else {},
        "unblocked_source_counts": unblocked["eligible_observation_source_type"].value_counts().to_dict() if not unblocked.empty else {},
        "rejection_reason_counts": rejection_counts(final_review, "final_rejection_reasons"),
        "approval_gate_status": "awaiting_human_process_approval" if accepted_rows == 0 else "process_approval_unblocked_requests",
    }
    return template, final_review, process_rows, process_ledger, unblocked, summary


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Process Approval Intake",
        "",
        "本文档记录知识模板工艺建议如何进入人工批准入口。它不产生 Tg observation；即使工艺被批准，也只是解锁后续高保真/真实结果 intake。",
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
        ("Unblocked Target Counts", summary.get("unblocked_target_counts", {})),
        ("Unblocked Source Counts", summary.get("unblocked_source_counts", {})),
        ("Rejection Reasons", summary.get("rejection_reason_counts", {})),
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
            "- `approval_decision`、`process_ready`、`reviewer_approved` 和 `reviewer_id` 必须同时满足。",
            "- 审批后的 process record 还必须通过 `import_process_records`，且 `ready_for_active_ledger=true`。",
            "- 被解锁的 high-fidelity/real request 仍必须走 validation result intake；本脚本不会写入 observation ledger。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import human process approvals and identify validation requests unblocked by approved process records.")
    parser.add_argument("--suggestions", default="artifacts/trail/human_review/process_design_suggestion_packet.csv")
    parser.add_argument(
        "--suggested-process-records",
        default="artifacts/trail/human_review/process_design_suggested_process_records.csv",
    )
    parser.add_argument("--approvals", default="artifacts/trail/human_review/process_completion_approval_completed.csv")
    parser.add_argument("--validation-requests", default="artifacts/trail/human_review/validation_request_queue.csv")
    parser.add_argument("--schema", default="trail/experiments/process_record_schema.yaml")
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/process_approval_intake.md")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    template, review, process_rows, ledger, unblocked, summary = import_process_approval_intake(
        Path(args.suggestions),
        Path(args.suggested_process_records),
        Path(args.approvals),
        Path(args.validation_requests),
        Path(args.schema),
        Path(args.knowledge),
    )
    template_path = out_dir / "process_completion_approval_template.csv"
    review_path = out_dir / "process_completion_approval_review.csv"
    records_path = out_dir / "process_completion_approved_process_records.csv"
    ledger_path = out_dir / "process_completion_approved_process_record_ledger.csv"
    unblocked_path = out_dir / "process_completion_unblocked_validation_requests.csv"
    summary_path = out_dir / "process_completion_approval_summary.json"
    template.to_csv(template_path, index=False)
    review.to_csv(review_path, index=False)
    process_rows.to_csv(records_path, index=False)
    ledger.to_csv(ledger_path, index=False)
    unblocked.to_csv(unblocked_path, index=False)
    summary = {
        **summary,
        "template_path": str(template_path),
        "review_path": str(review_path),
        "approved_process_records_path": str(records_path),
        "approved_process_record_ledger_path": str(ledger_path),
        "unblocked_requests_path": str(unblocked_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(summary, Path(args.report))


if __name__ == "__main__":
    main()

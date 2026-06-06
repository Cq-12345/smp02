from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


CHECKLIST_COLUMNS = [
    "checklist_rank",
    "approval_id",
    "request_id",
    "process_record_id",
    "linked_observation_id",
    "target_tg_c",
    "surrogate_tg_c",
    "target_distance_c",
    "predicted_tg_sigma_c",
    "candidate_origin",
    "reaction_principle",
    "process_template",
    "suggested_inputs",
    "suggested_field_count",
    "risk_flags",
    "reviewer_required_checks",
    "downstream_protocol_ids",
    "downstream_protocol_count",
    "downstream_required_methods",
    "downstream_authority_weight_if_completed",
    "approval_status",
    "ready_for_human_review",
    "already_submitted",
    "can_unlock_high_fidelity_protocol_after_approval",
    "creates_observation",
    "evidence_level",
    "smiles",
    "ratios",
]


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "approved", "accepted"}


def number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value)


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def semicolon_list(value: Any) -> list[str]:
    return [part.strip() for part in text(value).split(";") if part.strip()]


def suggested_field_names(value: Any) -> list[str]:
    fields = []
    for item in semicolon_list(value):
        if "=" not in item:
            continue
        key = item.split("=", 1)[0].strip()
        if key:
            fields.append(key)
    return fields


def approval_status(row: pd.Series) -> str:
    decision = text(row.get("approval_decision")).strip().lower()
    if not decision:
        return "awaiting_human_review"
    if decision in {"approve", "approved", "accept", "accepted"} and bool_value(row.get("process_ready")) and bool_value(
        row.get("reviewer_approved")
    ):
        return "accepted_process_approval"
    return "submitted_but_not_accepted"


def required_checks(row: pd.Series, protocols: pd.DataFrame) -> str:
    checks = [
        "verify suggested process values against chemistry and safety context",
        "confirm process_ready true only if required process fields are complete",
        "set reviewer_approved true only after human review",
        "fill reviewer_id and review_date",
    ]
    flags = set(semicolon_list(row.get("risk_flags")))
    methods = set()
    if not protocols.empty and "required_methods" in protocols.columns:
        for value in protocols["required_methods"]:
            methods.update(semicolon_list(value))
    if "high_tg_process_window" in flags or number(row.get("target_tg_c")) >= 240:
        checks.append("review high-Tg thermal stability and post-cure assumptions")
    if "high_predictor_sigma" in flags:
        checks.append("keep high-fidelity/model-ensemble recheck before any observation promotion")
    if "target_specific_literature_check" in methods:
        checks.append("attach target-specific literature or curated-source note before promotion")
    if "imidization_protocol_review" in methods:
        checks.append("verify solvent, imidization temperature, and imidization time")
    if "trimerization_catalyst_review" in methods:
        checks.append("verify catalyst and trimerization/post-cure assumptions")
    return ";".join(checks)


def build_reviewer_checklist(
    approval_template_path: Path,
    process_suggestion_path: Path,
    high_fidelity_protocol_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    approvals = read_csv(approval_template_path)
    suggestions = read_csv(process_suggestion_path)
    protocols = read_csv(high_fidelity_protocol_path)
    suggestion_by_request = {
        str(row["request_id"]): row for _, row in suggestions.iterrows()
    } if not suggestions.empty and "request_id" in suggestions.columns else {}
    rows: list[dict[str, Any]] = []
    for _, row in approvals.iterrows():
        request_id = text(row.get("request_id"))
        linked_id = text(row.get("linked_observation_id"))
        suggestion = suggestion_by_request.get(request_id)
        linked_protocols = (
            protocols[protocols["linked_observation_id"].astype(str) == linked_id].copy()
            if not protocols.empty and "linked_observation_id" in protocols.columns
            else pd.DataFrame()
        )
        status = approval_status(row)
        downstream_methods: list[str] = []
        for value in linked_protocols["required_methods"].tolist() if not linked_protocols.empty and "required_methods" in linked_protocols.columns else []:
            for method in semicolon_list(value):
                if method not in downstream_methods:
                    downstream_methods.append(method)
        suggested_inputs = text(row.get("suggested_inputs"))
        fields = suggested_field_names(suggested_inputs)
        rows.append(
            {
                "approval_id": text(row.get("approval_id")),
                "request_id": request_id,
                "process_record_id": text(row.get("process_record_id")),
                "linked_observation_id": linked_id,
                "target_tg_c": number(row.get("target_tg_c")),
                "surrogate_tg_c": number(row.get("surrogate_tg_c")),
                "target_distance_c": number(suggestion.get("target_distance_c") if suggestion is not None else None),
                "predicted_tg_sigma_c": number(suggestion.get("predicted_tg_sigma_c") if suggestion is not None else None),
                "candidate_origin": text(row.get("candidate_origin")),
                "reaction_principle": text(row.get("reaction_principle")),
                "process_template": text(row.get("process_template")),
                "suggested_inputs": suggested_inputs,
                "suggested_field_count": len(fields),
                "risk_flags": text(row.get("risk_flags")),
                "reviewer_required_checks": required_checks(row, linked_protocols),
                "downstream_protocol_ids": ";".join(linked_protocols["protocol_id"].astype(str).tolist())
                if not linked_protocols.empty and "protocol_id" in linked_protocols.columns
                else "",
                "downstream_protocol_count": int(len(linked_protocols)),
                "downstream_required_methods": ";".join(downstream_methods),
                "downstream_authority_weight_if_completed": float(linked_protocols["authority_weight_if_completed"].max())
                if not linked_protocols.empty and "authority_weight_if_completed" in linked_protocols.columns
                else 0.0,
                "approval_status": status,
                "ready_for_human_review": status == "awaiting_human_review",
                "already_submitted": text(row.get("approval_decision")).strip() != "",
                "can_unlock_high_fidelity_protocol_after_approval": len(linked_protocols) > 0,
                "creates_observation": False,
                "evidence_level": "process_approval_reviewer_checklist_not_observation",
                "smiles": text(row.get("smiles")),
                "ratios": text(row.get("ratios")),
            }
        )
    checklist = pd.DataFrame(rows)
    if checklist.empty:
        checklist = pd.DataFrame(columns=CHECKLIST_COLUMNS)
    else:
        checklist["approval_priority_score"] = (
            checklist["can_unlock_high_fidelity_protocol_after_approval"].astype(float)
            + 0.1 * checklist["downstream_authority_weight_if_completed"].astype(float)
            + 0.01 * checklist["predicted_tg_sigma_c"].astype(float)
            + (checklist["target_tg_c"].astype(float) >= 240).astype(float) * 0.2
        )
        checklist = checklist.sort_values(
            ["ready_for_human_review", "approval_priority_score", "target_distance_c"],
            ascending=[False, False, True],
        ).reset_index(drop=True)
        checklist.insert(0, "checklist_rank", range(1, len(checklist) + 1))
        checklist = checklist[CHECKLIST_COLUMNS]
    field_counts: dict[str, int] = {}
    for value in checklist["suggested_inputs"] if not checklist.empty else []:
        for field in suggested_field_names(value):
            field_counts[field] = field_counts.get(field, 0) + 1
    summary = {
        "input_approval_rows": int(len(approvals)),
        "checklist_rows": int(len(checklist)),
        "ready_for_human_review_rows": int(checklist["ready_for_human_review"].sum()) if not checklist.empty else 0,
        "already_submitted_rows": int(checklist["already_submitted"].sum()) if not checklist.empty else 0,
        "accepted_process_approval_rows": int((checklist["approval_status"] == "accepted_process_approval").sum()) if not checklist.empty else 0,
        "can_unlock_high_fidelity_protocol_rows": int(checklist["can_unlock_high_fidelity_protocol_after_approval"].sum()) if not checklist.empty else 0,
        "downstream_protocol_rows": int(checklist["downstream_protocol_count"].sum()) if not checklist.empty else 0,
        "target_counts": {f"{float(key):.1f}": int(value) for key, value in checklist["target_tg_c"].value_counts().sort_index().items()}
        if not checklist.empty
        else {},
        "candidate_origin_counts": checklist["candidate_origin"].value_counts().to_dict() if not checklist.empty else {},
        "process_template_counts": checklist["process_template"].value_counts().to_dict() if not checklist.empty else {},
        "suggested_field_frequency": field_counts,
        "approval_gate_status": "awaiting_human_process_approval"
        if not checklist.empty and int(checklist["ready_for_human_review"].sum()) > 0
        else "no_pending_human_review_rows",
        "max_downstream_authority_weight_if_completed": float(checklist["downstream_authority_weight_if_completed"].max())
        if not checklist.empty
        else 0.0,
        "creates_observation": False,
        "evidence_level": "process_approval_reviewer_checklist_not_observation",
    }
    return checklist, summary


def write_report(checklist: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Process Approval Reviewer Checklist",
        "",
        "本文档把 process approval template 转成可审查行动清单。它不代表人工已经批准，也不产生 Tg observation。",
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
        ("Target Counts", summary.get("target_counts", {})),
        ("Process Template Counts", summary.get("process_template_counts", {})),
        ("Suggested Field Frequency", summary.get("suggested_field_frequency", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    if not checklist.empty:
        lines.extend(
            [
                "",
                "## Review Rows",
                "",
                "| rank | approval | target | origin | template | downstream protocols | status |",
                "| ---: | --- | ---: | --- | --- | ---: | --- |",
            ]
        )
        for _, row in checklist.iterrows():
            lines.append(
                f"| {int(row['checklist_rank'])} | {row['approval_id']} | {float(row['target_tg_c']):.1f} | "
                f"{row['candidate_origin']} | {row['process_template']} | {int(row['downstream_protocol_count'])} | {row['approval_status']} |"
            )
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "- 审批人必须填写 `approval_decision`、`process_ready`、`reviewer_approved`、`reviewer_id` 和 `review_date`。",
            "- 通过审批只会解锁 downstream high-fidelity protocol；不会直接写入 observation ledger。",
            "- 高保真或真实结果仍必须单独通过 validation result intake 和 active evidence gate。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a human reviewer checklist for process approval rows.")
    parser.add_argument("--approval-template", default="artifacts/trail/human_review/process_completion_approval_template.csv")
    parser.add_argument("--process-suggestions", default="artifacts/trail/human_review/process_design_suggestion_packet.csv")
    parser.add_argument("--high-fidelity-protocol", default="artifacts/trail/human_review/high_fidelity_protocol_packet.csv")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/process_approval_reviewer_checklist.md")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    checklist, summary = build_reviewer_checklist(
        Path(args.approval_template),
        Path(args.process_suggestions),
        Path(args.high_fidelity_protocol),
    )
    checklist_path = out_dir / "process_approval_reviewer_checklist.csv"
    summary_path = out_dir / "process_approval_reviewer_checklist_summary.json"
    checklist.to_csv(checklist_path, index=False)
    summary = {
        **summary,
        "checklist_path": str(checklist_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(checklist, summary, Path(args.report))


if __name__ == "__main__":
    main()

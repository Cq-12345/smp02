from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PROTOCOL_COLUMNS = [
    "protocol_rank",
    "protocol_id",
    "request_id",
    "validation_rank",
    "linked_observation_id",
    "target_tg_c",
    "surrogate_tg_c",
    "target_distance_c",
    "predicted_tg_sigma_c",
    "candidate_origin",
    "process_template",
    "risk_flags",
    "eligible_observation_source_type",
    "authority_weight_if_completed",
    "required_methods",
    "method_count",
    "protocol_steps",
    "acceptance_criteria",
    "protocol_status",
    "blocked_by_process_completion",
    "process_approval_unblocked",
    "can_start_high_fidelity_protocol",
    "creates_observation",
    "required_result_fields",
    "evidence_level",
    "smiles",
    "ratios",
]


METHOD_LIBRARY = {
    "process_feasibility_review": {
        "step": "confirm suggested process fields are chemically feasible and internally consistent",
        "criteria": "process record has human approval and no unresolved required process fields",
    },
    "model_ensemble_recheck": {
        "step": "rerun or inspect predictor ensemble disagreement before any high-fidelity result is trusted",
        "criteria": "ensemble mean/std/range and model members are recorded with the result",
    },
    "high_fidelity_simulation_or_expanded_model_ensemble": {
        "step": "run high-fidelity Tg estimate or expanded model ensemble under the approved process context",
        "criteria": "method, observed_tg_c, confidence notes, and failure modes are recorded",
    },
    "thermal_stability_pre_screen": {
        "step": "screen high-Tg formulation for thermal stability or degradation risk before DSC planning",
        "criteria": "thermal-stability risk notes are present for target_tg_c >= 240 C",
    },
    "target_specific_literature_check": {
        "step": "check target-specific literature support for sparse-target chemistry",
        "criteria": "literature or curated-source note is attached before promotion",
    },
    "imidization_protocol_review": {
        "step": "review solvent, imidization temperature, and imidization time for anhydride-amine routes",
        "criteria": "imidization protocol fields are complete and reviewer-approved",
    },
    "trimerization_catalyst_review": {
        "step": "review trimerization catalyst and post-cure assumptions for cyanate ester routes",
        "criteria": "trimerization/catalyst fields are complete and reviewer-approved",
    },
    "moisture_control_review": {
        "step": "review dry handling, NCO index, and moisture-control plan for isocyanate routes",
        "criteria": "moisture-control fields are complete and reviewer-approved",
    },
}


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "approved"}


def number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def semicolon_list(value: Any) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def high_fidelity_requests(requests: pd.DataFrame) -> pd.DataFrame:
    if requests.empty or "task_type" not in requests.columns:
        return pd.DataFrame()
    selected = requests[requests["task_type"].astype(str) == "high_fidelity_validation"].copy()
    if selected.empty:
        return selected
    return selected.sort_values(["request_priority_score", "target_distance_c"], ascending=[False, True]).reset_index(drop=True)


def method_frequency(protocols: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    if protocols.empty or "required_methods" not in protocols.columns:
        return counts
    for methods in protocols["required_methods"]:
        for method in semicolon_list(methods):
            counts[method] = counts.get(method, 0) + 1
    return counts


def risk_frequency(protocols: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    if protocols.empty or "risk_flags" not in protocols.columns:
        return counts
    for flags in protocols["risk_flags"]:
        for flag in semicolon_list(flags):
            counts[flag] = counts.get(flag, 0) + 1
    return counts


def build_protocol_packet(
    validation_requests_path: Path,
    unblocked_requests_path: Path,
    approval_summary_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    requests = read_csv(validation_requests_path)
    unblocked = read_csv(unblocked_requests_path)
    approval_summary = read_json(approval_summary_path)
    high_fidelity = high_fidelity_requests(requests)
    unblocked_ids = set(unblocked["request_id"].astype(str)) if not unblocked.empty and "request_id" in unblocked.columns else set()
    rows: list[dict[str, Any]] = []
    for index, row in high_fidelity.iterrows():
        methods = semicolon_list(row.get("required_inputs"))
        steps = [METHOD_LIBRARY.get(method, {"step": f"document method `{method}`"})["step"] for method in methods]
        criteria = [METHOD_LIBRARY.get(method, {"criteria": f"record completion evidence for `{method}`"})["criteria"] for method in methods]
        request_id = str(row.get("request_id", ""))
        blocked = bool_value(row.get("blocked_by_process_completion"))
        unblocked_by_approval = request_id in unblocked_ids
        can_start = (not blocked) or unblocked_by_approval
        rows.append(
            {
                "protocol_rank": int(index) + 1,
                "protocol_id": f"protocol_{request_id}",
                "request_id": request_id,
                "validation_rank": int(number(row.get("validation_rank"), 0)),
                "linked_observation_id": row.get("linked_observation_id", ""),
                "target_tg_c": number(row.get("target_tg_c")),
                "surrogate_tg_c": number(row.get("surrogate_tg_c")),
                "target_distance_c": number(row.get("target_distance_c")),
                "predicted_tg_sigma_c": number(row.get("predicted_tg_sigma_c")),
                "candidate_origin": row.get("candidate_origin", ""),
                "process_template": row.get("process_template", ""),
                "risk_flags": row.get("risk_flags", ""),
                "eligible_observation_source_type": row.get("eligible_observation_source_type", ""),
                "authority_weight_if_completed": number(row.get("authority_weight_if_completed")),
                "required_methods": ";".join(methods),
                "method_count": int(len(methods)),
                "protocol_steps": "; ".join(steps),
                "acceptance_criteria": "; ".join(criteria),
                "protocol_status": "ready_for_high_fidelity_execution" if can_start else "blocked_pending_process_approval",
                "blocked_by_process_completion": blocked,
                "process_approval_unblocked": unblocked_by_approval,
                "can_start_high_fidelity_protocol": can_start,
                "creates_observation": False,
                "required_result_fields": "observed_tg_c;method;experiment_date;operator;process_record_id;process_ready;reviewer_approved;result_notes",
                "evidence_level": "high_fidelity_protocol_template_not_observation",
                "smiles": row.get("smiles", ""),
                "ratios": row.get("ratios", ""),
            }
        )
    protocols = pd.DataFrame(rows, columns=PROTOCOL_COLUMNS)
    ready_rows = int(protocols["can_start_high_fidelity_protocol"].sum()) if not protocols.empty else 0
    blocked_rows = int((~protocols["can_start_high_fidelity_protocol"]).sum()) if not protocols.empty else 0
    summary = {
        "input_request_rows": int(len(requests)),
        "high_fidelity_protocol_rows": int(len(protocols)),
        "ready_protocol_rows": ready_rows,
        "blocked_protocol_rows": blocked_rows,
        "process_approval_unblocked_rows": int(protocols["process_approval_unblocked"].sum()) if not protocols.empty else 0,
        "target_counts": {
            f"{float(key):.1f}": int(value) for key, value in protocols["target_tg_c"].value_counts().sort_index().items()
        }
        if not protocols.empty
        else {},
        "candidate_origin_counts": protocols["candidate_origin"].value_counts().to_dict() if not protocols.empty else {},
        "source_counts": protocols["eligible_observation_source_type"].value_counts().to_dict() if not protocols.empty else {},
        "method_frequency": method_frequency(protocols),
        "risk_flag_frequency": risk_frequency(protocols),
        "max_authority_weight_if_completed": float(protocols["authority_weight_if_completed"].max()) if not protocols.empty else 0.0,
        "approval_gate_status": approval_summary.get("approval_gate_status", "unknown"),
        "evidence_level": "high_fidelity_protocol_template_not_observation",
    }
    return protocols, summary


def write_report(protocols: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# High-fidelity Protocol Packet",
        "",
        "本文档把 high-fidelity validation request 转成方法协议包。它不是高保真结果，也不会写入 observation ledger。",
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
        ("Candidate Origin Counts", summary.get("candidate_origin_counts", {})),
        ("Method Frequency", summary.get("method_frequency", {})),
        ("Risk Flag Frequency", summary.get("risk_flag_frequency", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    if not protocols.empty:
        lines.extend(
            [
                "",
                "## Top Protocols",
                "",
                "| rank | request | target | origin | methods | status |",
                "| ---: | --- | ---: | --- | --- | --- |",
            ]
        )
        for _, row in protocols.head(15).iterrows():
            lines.append(
                f"| {int(row['protocol_rank'])} | {row['request_id']} | {float(row['target_tg_c']):.1f} | "
                f"{row['candidate_origin']} | {row['required_methods']} | {row['protocol_status']} |"
            )
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "- `blocked_pending_process_approval` 表示仍等待 process approval，不允许启动高保真结果 intake。",
            "- `ready_for_high_fidelity_execution` 也不等于 observation；它只允许后续填写 validation result。",
            "- 任何 Tg 数值仍必须通过 validation result intake、observation ledger 和 active evidence gate。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build high-fidelity validation protocol templates from validation requests.")
    parser.add_argument("--validation-requests", default="artifacts/trail/human_review/validation_request_queue.csv")
    parser.add_argument(
        "--unblocked-requests",
        default="artifacts/trail/human_review/process_completion_unblocked_validation_requests.csv",
    )
    parser.add_argument("--approval-summary", default="artifacts/trail/human_review/process_completion_approval_summary.json")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/high_fidelity_protocol_packet.md")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    protocols, summary = build_protocol_packet(
        Path(args.validation_requests),
        Path(args.unblocked_requests),
        Path(args.approval_summary),
    )
    packet_path = out_dir / "high_fidelity_protocol_packet.csv"
    summary_path = out_dir / "high_fidelity_protocol_summary.json"
    protocols.to_csv(packet_path, index=False)
    summary = {
        **summary,
        "packet_path": str(packet_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(protocols, summary, Path(args.report))


if __name__ == "__main__":
    main()

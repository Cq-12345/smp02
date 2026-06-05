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

from trail.experiments.import_process_records import import_process_records  # noqa: E402


PROCESS_RECORD_COLUMNS = [
    "process_record_id",
    "linked_observation_id",
    "source_type",
    "target_tg_c",
    "observed_tg_c",
    "smiles",
    "ratios",
    "reaction_principle",
    "process_template",
    "review_status",
    "literature_source",
    "operator",
    "catalyst",
    "catalyst_loading",
    "cure_temperature_c",
    "cure_time_h",
    "post_cure_temperature_c",
    "post_cure_time_h",
    "imidization_temperature_c",
    "imidization_time_h",
    "trimerization_temperature_c",
    "initiator_type",
    "initiator_loading",
    "moisture_control",
    "nco_index",
    "notes",
]


PACKET_COLUMNS = [
    "completion_rank",
    "request_id",
    "execution_rank",
    "validation_rank",
    "process_record_id",
    "linked_observation_id",
    "target_tg_c",
    "surrogate_tg_c",
    "target_distance_c",
    "predicted_tg_sigma_c",
    "candidate_origin",
    "process_template",
    "reaction_principle",
    "required_inputs",
    "required_input_count",
    "unlocks_observation_request",
    "process_completion_status",
    "process_ready",
    "reviewer_approved",
    "operator",
    "completion_notes",
    "smiles",
    "ratios",
]


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


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
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def draft_lookup(draft_records: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if draft_records.empty or "linked_observation_id" not in draft_records.columns:
        return {}
    return {str(row["linked_observation_id"]): row.to_dict() for _, row in draft_records.iterrows()}


def selected_process_completion_requests(schedule: pd.DataFrame, immediate_only: bool = True) -> pd.DataFrame:
    if schedule.empty:
        return pd.DataFrame()
    selected = schedule[schedule["task_type"].astype(str) == "process_completion"].copy()
    if immediate_only and "immediate_batch_selected" in selected.columns:
        selected = selected[selected["immediate_batch_selected"].map(bool_value)].copy()
    return selected.sort_values(["execution_rank", "request_priority_score"], ascending=[True, False]).reset_index(drop=True)


def build_process_completion_packet(
    schedule_path: Path,
    draft_process_records_path: Path,
    process_schema: Path,
    knowledge_path: Path,
    immediate_only: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    schedule = read_csv(schedule_path)
    draft_records = read_csv(draft_process_records_path)
    selected = selected_process_completion_requests(schedule, immediate_only=immediate_only)
    draft_by_observation = draft_lookup(draft_records)
    packet_rows: list[dict[str, Any]] = []
    process_rows: list[dict[str, Any]] = []
    required_field_frequency: dict[str, int] = {}
    for index, row in selected.iterrows():
        linked_id = str(row.get("linked_observation_id", ""))
        draft = draft_by_observation.get(linked_id, {})
        required_fields = semicolon_list(row.get("required_inputs"))
        for field in required_fields:
            required_field_frequency[field] = required_field_frequency.get(field, 0) + 1
        process_record_id = str(draft.get("process_record_id") or f"process_completion_{row.get('request_id')}")
        reaction_principle = str(draft.get("reaction_principle") or "")
        process_template = str(draft.get("process_template") or row.get("process_template", ""))
        operator = str(draft.get("operator") or "")
        notes = (
            f"Process completion intake template for request={row.get('request_id')}; "
            f"execution_status={row.get('execution_status', 'planned_not_completed')}; not active ledger evidence."
        )
        packet = {
            "completion_rank": int(index) + 1,
            "request_id": row.get("request_id", ""),
            "execution_rank": int(number(row.get("execution_rank"), int(index) + 1)),
            "validation_rank": int(number(row.get("validation_rank"), 0)),
            "process_record_id": process_record_id,
            "linked_observation_id": linked_id,
            "target_tg_c": number(row.get("target_tg_c")),
            "surrogate_tg_c": number(row.get("surrogate_tg_c")),
            "target_distance_c": number(row.get("target_distance_c")),
            "predicted_tg_sigma_c": number(row.get("predicted_tg_sigma_c")),
            "candidate_origin": row.get("candidate_origin", draft.get("literature_source", "")),
            "process_template": process_template,
            "reaction_principle": reaction_principle,
            "required_inputs": ";".join(required_fields),
            "required_input_count": int(len(required_fields)),
            "unlocks_observation_request": bool_value(row.get("unlocks_observation_request")),
            "process_completion_status": "pending_human_input",
            "process_ready": False,
            "reviewer_approved": False,
            "operator": operator,
            "completion_notes": "",
            "smiles": row.get("smiles", draft.get("smiles", "")),
            "ratios": row.get("ratios", draft.get("ratios", "")),
        }
        for field in required_fields:
            packet[field] = draft.get(field, "")
        packet_rows.append(packet)
        process_record = {column: draft.get(column, "") for column in PROCESS_RECORD_COLUMNS}
        process_record.update(
            {
                "process_record_id": process_record_id,
                "linked_observation_id": linked_id,
                "source_type": str(draft.get("source_type") or "surrogate_review"),
                "target_tg_c": number(row.get("target_tg_c")),
                "observed_tg_c": number(row.get("surrogate_tg_c")),
                "smiles": row.get("smiles", draft.get("smiles", "")),
                "ratios": row.get("ratios", draft.get("ratios", "")),
                "reaction_principle": reaction_principle,
                "process_template": process_template,
                "review_status": "needs_process_details",
                "operator": operator,
                "notes": notes,
            }
        )
        for field in required_fields:
            process_record[field] = draft.get(field, "")
        process_rows.append(process_record)
    packet = pd.DataFrame(packet_rows)
    if not packet.empty:
        dynamic_fields = [column for column in packet.columns if column not in PACKET_COLUMNS]
        packet = packet[PACKET_COLUMNS + sorted(dynamic_fields)]
    process_template = pd.DataFrame(process_rows)
    for column in PROCESS_RECORD_COLUMNS:
        if column not in process_template.columns:
            process_template[column] = ""
    process_template = process_template[PROCESS_RECORD_COLUMNS]
    if process_template.empty:
        ledger = pd.DataFrame()
        process_summary = {
            "input_rows": 0,
            "process_record_pass_rows": 0,
            "ready_for_active_ledger_rows": 0,
            "process_incomplete_rows": 0,
        }
    else:
        temp_path = schedule_path.parent / ".process_completion_process_record_template.tmp.csv"
        process_template.to_csv(temp_path, index=False)
        try:
            ledger, process_summary = import_process_records(temp_path, process_schema, knowledge_path)
        finally:
            temp_path.unlink(missing_ok=True)
    summary = {
        "input_schedule_rows": int(len(schedule)),
        "selected_process_completion_rows": int(len(packet)),
        "draft_record_matches": int(sum(str(row.get("linked_observation_id", "")) in draft_by_observation for _, row in selected.iterrows())),
        "unlocks_observation_rows": int(packet["unlocks_observation_request"].sum()) if not packet.empty else 0,
        "target_counts": {f"{float(key):.1f}": int(value) for key, value in packet["target_tg_c"].value_counts().sort_index().items()}
        if not packet.empty
        else {},
        "candidate_origin_counts": packet["candidate_origin"].value_counts().to_dict() if not packet.empty else {},
        "required_field_frequency": required_field_frequency,
        "process_record_pass_rows": int(process_summary.get("process_record_pass_rows", 0)),
        "ready_for_active_ledger_rows": int(process_summary.get("ready_for_active_ledger_rows", 0)),
        "process_incomplete_rows": int(process_summary.get("process_incomplete_rows", 0)),
    }
    return packet, process_template, ledger, summary


def write_report(packet: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Process Completion Packet",
        "",
        "本文档把 immediate validation execution batch 展开成可填写的工艺补全包。它不代表工艺已经完成，也不产生 observation。",
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
        ("Required Field Frequency", summary.get("required_field_frequency", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Packet Rows",
            "",
            "| rank | request | target Tg C | origin | template | required inputs | unlocks observation |",
            "| ---: | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for _, row in packet.head(20).iterrows():
        lines.append(
            f"| {int(row['completion_rank'])} | {row['request_id']} | {float(row['target_tg_c']):.1f} | "
            f"{row['candidate_origin']} | {row['process_template']} | {row['required_inputs']} | "
            f"{bool(row['unlocks_observation_request'])} |"
        )
    lines.extend(
        [
            "",
            "## Gate Rules",
            "",
            "- `process_ready=false` 和 `reviewer_approved=false` 是默认值；人工填写前不得升级为 active evidence。",
            "- `process_record_template` 可进入 process record importer，但当前缺字段，因此 `ready_for_active_ledger_rows` 应为 0。",
            "- 完成工艺字段后，仍需 reviewer approval，才能解锁 high-fidelity result intake。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build fillable process-completion packets for the immediate validation batch.")
    parser.add_argument("--schedule", default="artifacts/trail/human_review/validation_execution_schedule.csv")
    parser.add_argument("--draft-process-records", default="artifacts/trail/human_review/draft_process_records.csv")
    parser.add_argument("--process-schema", default="trail/experiments/process_record_schema.yaml")
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/process_completion_packet.md")
    parser.add_argument("--all-process-requests", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet, process_template, ledger, summary = build_process_completion_packet(
        Path(args.schedule),
        Path(args.draft_process_records),
        Path(args.process_schema),
        Path(args.knowledge),
        immediate_only=not args.all_process_requests,
    )
    packet_path = out_dir / "process_completion_packet.csv"
    process_template_path = out_dir / "process_completion_process_record_template.csv"
    process_ledger_path = out_dir / "process_completion_process_record_ledger.csv"
    summary_path = out_dir / "process_completion_packet_summary.json"
    packet.to_csv(packet_path, index=False)
    process_template.to_csv(process_template_path, index=False)
    ledger.to_csv(process_ledger_path, index=False)
    summary = {
        **summary,
        "packet_path": str(packet_path),
        "process_template_path": str(process_template_path),
        "process_ledger_path": str(process_ledger_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(packet, summary, Path(args.report))


if __name__ == "__main__":
    main()

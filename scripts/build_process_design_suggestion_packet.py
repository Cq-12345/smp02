from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from scripts.build_process_completion_packet import PROCESS_RECORD_COLUMNS, read_csv, semicolon_list  # noqa: E402
from trail.experiments.import_process_records import import_process_records  # noqa: E402


SUGGESTION_COLUMNS = [
    "suggestion_rank",
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
    "template_trigger",
    "template_catalyst",
    "required_inputs",
    "suggested_inputs",
    "unresolved_inputs_after_suggestion",
    "suggestion_status",
    "evidence_level",
    "risk_flags",
    "suggestion_basis",
    "human_review_required",
    "can_unlock_observation_after_human_approval",
    "smiles",
    "ratios",
]


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def present(value: Any) -> bool:
    return value is not None and not pd.isna(value) and str(value).strip() != ""


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def stable_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value and value not in seen:
            out.append(value)
            seen.add(value)
    return out


def process_templates(knowledge_path: Path) -> dict[str, dict[str, Any]]:
    knowledge = load_yaml(knowledge_path)
    return knowledge.get("process_condition_templates", {})


def suggested_value(field: str, process_template: str, target_tg_c: float) -> Any:
    high_tg = target_tg_c >= 240.0
    if process_template == "epoxy_amine_thermal_cure":
        defaults = {
            "mix_temperature_c": 60.0,
            "cure_temperature_c": 140.0 if high_tg else 120.0,
            "cure_time_h": 2.0,
            "post_cure_temperature_c": 220.0 if high_tg else 180.0,
            "post_cure_time_h": 2.0,
        }
    elif process_template == "epoxy_anhydride_catalyzed_cure":
        defaults = {
            "mix_temperature_c": 80.0,
            "catalyst_loading": "0.5-2.0 wt% tertiary amine or imidazole; verify equivalent basis",
            "cure_temperature_c": 170.0 if high_tg else 150.0,
            "cure_time_h": 2.0,
            "post_cure_temperature_c": 230.0 if high_tg else 200.0,
            "post_cure_time_h": 2.0,
        }
    elif process_template == "anhydride_amine_imidization":
        defaults = {
            "solvent": "dry NMP or DMAc; verify monomer solubility before scale-up",
            "imidization_temperature_c": 220.0 if high_tg else 180.0,
            "imidization_time_h": 2.0,
        }
    elif process_template == "isocyanate_urethane_urea":
        defaults = {
            "moisture_control": "dry glassware and dry nitrogen blanket",
            "nco_index": "1.00-1.05 starting range; verify equivalent weights",
            "cure_temperature_c": 100.0 if high_tg else 80.0,
        }
    elif process_template == "radical_vinyl_cure":
        defaults = {
            "initiator_type": "thermal peroxide or photoinitiator selected by trigger",
            "initiator_loading": "0.5-2.0 wt%; verify against inhibitor content",
            "irradiation_or_cure_temperature_c": 90.0 if high_tg else 70.0,
        }
    elif process_template == "thiol_click_cure":
        defaults = {
            "thiol_ene_stoichiometry": "1:1 functional equivalent starting point",
            "catalyst_or_initiator": "base, photoinitiator, or radical initiator matched to trigger",
            "cure_temperature_c": 80.0 if high_tg else 60.0,
        }
    elif process_template == "cyanate_ester_triazine_cure":
        defaults = {
            "trimerization_temperature_c": 220.0 if high_tg else 200.0,
            "catalyst_loading": "0-1.0 wt% metal or phenolic catalyst; verify latency",
            "post_cure_temperature_c": 260.0 if high_tg else 230.0,
        }
    elif process_template == "maleimide_addition_or_copolymerization":
        defaults = {
            "cure_temperature_c": 180.0 if high_tg else 160.0,
            "co_reactant_stoichiometry": "1:1 functional equivalent starting point",
            "post_cure_temperature_c": 240.0 if high_tg else 220.0,
        }
    else:
        defaults = {}
    return defaults.get(field, "human_review_required")


def risk_flags(row: pd.Series) -> list[str]:
    flags: list[str] = []
    target_tg_c = number(row.get("target_tg_c"))
    sigma = number(row.get("predicted_tg_sigma_c"))
    origin = str(row.get("candidate_origin", ""))
    template = str(row.get("process_template", ""))
    if target_tg_c >= 240.0:
        flags.append("high_tg_process_window")
    if sigma >= 75.0:
        flags.append("high_predictor_sigma")
    if "sparse_target" in origin:
        flags.append("sparse_target_candidate_origin")
    if template in {"epoxy_anhydride_catalyzed_cure", "cyanate_ester_triazine_cure"}:
        flags.append("catalyst_sensitive_template")
    if template == "anhydride_amine_imidization":
        flags.append("solvent_and_imidization_sensitive_template")
    return flags or ["standard_human_review"]


def build_suggestions(
    packet_path: Path,
    process_record_template_path: Path,
    process_schema: Path,
    knowledge_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    packet = read_csv(packet_path)
    process_records = read_csv(process_record_template_path)
    templates = process_templates(knowledge_path)
    process_by_id = (
        {str(row["process_record_id"]): row.to_dict() for _, row in process_records.iterrows()}
        if not process_records.empty and "process_record_id" in process_records.columns
        else {}
    )
    suggestion_rows: list[dict[str, Any]] = []
    suggested_process_rows: list[dict[str, Any]] = []
    field_frequency: dict[str, int] = {}
    suggested_field_frequency: dict[str, int] = {}
    for index, row in packet.iterrows():
        template_name = str(row.get("process_template", ""))
        template = templates.get(template_name, {})
        packet_required = semicolon_list(row.get("required_inputs"))
        template_required = [str(field) for field in template.get("cure_schedule_fields", [])]
        suggested_fields = stable_unique(packet_required + template_required)
        for field in packet_required:
            field_frequency[field] = field_frequency.get(field, 0) + 1
        suggestions = {field: suggested_value(field, template_name, number(row.get("target_tg_c"))) for field in suggested_fields}
        for field, value in suggestions.items():
            if present(value):
                suggested_field_frequency[field] = suggested_field_frequency.get(field, 0) + 1
        unresolved = [field for field, value in suggestions.items() if not present(value) or str(value) == "human_review_required"]
        process_record_id = str(row.get("process_record_id", ""))
        process_row = {column: process_by_id.get(process_record_id, {}).get(column, "") for column in PROCESS_RECORD_COLUMNS}
        process_row.update(
            {
                "process_record_id": process_record_id,
                "linked_observation_id": row.get("linked_observation_id", ""),
                "source_type": "surrogate_review",
                "target_tg_c": number(row.get("target_tg_c")),
                "observed_tg_c": number(row.get("surrogate_tg_c")),
                "smiles": row.get("smiles", process_row.get("smiles", "")),
                "ratios": row.get("ratios", process_row.get("ratios", "")),
                "reaction_principle": row.get("reaction_principle", process_row.get("reaction_principle", "")),
                "process_template": template_name,
                "review_status": "needs_human_review",
                "literature_source": row.get("candidate_origin", process_row.get("literature_source", "")),
                "operator": process_row.get("operator") or "smp02_process_design_suggestion",
                "notes": (
                    "Knowledge-template process design suggestion only; not observed process data; "
                    f"request={row.get('request_id', '')}; human approval required before any high-authority ledger use."
                ),
            }
        )
        process_row.update(suggestions)
        suggested_process_rows.append(process_row)
        flags = risk_flags(row)
        suggestion_rows.append(
            {
                "suggestion_rank": int(index) + 1,
                "request_id": row.get("request_id", ""),
                "process_record_id": process_record_id,
                "linked_observation_id": row.get("linked_observation_id", ""),
                "target_tg_c": number(row.get("target_tg_c")),
                "surrogate_tg_c": number(row.get("surrogate_tg_c")),
                "target_distance_c": number(row.get("target_distance_c")),
                "predicted_tg_sigma_c": number(row.get("predicted_tg_sigma_c")),
                "candidate_origin": row.get("candidate_origin", ""),
                "reaction_principle": row.get("reaction_principle", ""),
                "process_template": template_name,
                "template_trigger": template.get("trigger", ""),
                "template_catalyst": template.get("catalyst", ""),
                "required_inputs": ";".join(packet_required),
                "suggested_inputs": ";".join(f"{field}={suggestions[field]}" for field in suggested_fields),
                "unresolved_inputs_after_suggestion": ";".join(unresolved),
                "suggestion_status": "draft_process_design_requires_human_review",
                "evidence_level": "knowledge_template_suggestion_not_observation",
                "risk_flags": ";".join(flags),
                "suggestion_basis": (
                    f"knowledge.process_condition_templates.{template_name}; "
                    f"reaction_principle={row.get('reaction_principle', '')}; "
                    "not measured and not literature-confirmed"
                ),
                "human_review_required": True,
                "can_unlock_observation_after_human_approval": bool_value(row.get("unlocks_observation_request"))
                and len(unresolved) == 0,
                "smiles": row.get("smiles", ""),
                "ratios": row.get("ratios", ""),
                **{f"suggested_{field}": value for field, value in suggestions.items()},
            }
        )
    suggestions = pd.DataFrame(suggestion_rows)
    if not suggestions.empty:
        dynamic_columns = [column for column in suggestions.columns if column not in SUGGESTION_COLUMNS]
        suggestions = suggestions[SUGGESTION_COLUMNS + sorted(dynamic_columns)]
    suggested_process = pd.DataFrame(suggested_process_rows)
    if not suggested_process.empty:
        base_columns = [column for column in PROCESS_RECORD_COLUMNS if column in suggested_process.columns]
        extra_columns = sorted(column for column in suggested_process.columns if column not in base_columns)
        suggested_process = suggested_process[base_columns + extra_columns]
    if suggested_process.empty:
        ledger = pd.DataFrame()
        process_summary = {
            "process_record_pass_rows": 0,
            "ready_for_active_ledger_rows": 0,
            "process_incomplete_rows": 0,
        }
    else:
        temp_path = packet_path.parent / ".process_design_suggested_process_records.tmp.csv"
        suggested_process.to_csv(temp_path, index=False)
        try:
            ledger, process_summary = import_process_records(temp_path, process_schema, knowledge_path)
        finally:
            temp_path.unlink(missing_ok=True)
    summary = {
        "input_packet_rows": int(len(packet)),
        "suggestion_rows": int(len(suggestions)),
        "target_counts": {
            f"{float(key):.1f}": int(value) for key, value in suggestions["target_tg_c"].value_counts().sort_index().items()
        }
        if not suggestions.empty
        else {},
        "process_template_counts": suggestions["process_template"].value_counts().to_dict() if not suggestions.empty else {},
        "candidate_origin_counts": suggestions["candidate_origin"].value_counts().to_dict() if not suggestions.empty else {},
        "required_field_frequency": field_frequency,
        "suggested_field_frequency": suggested_field_frequency,
        "high_tg_rows": int((suggestions["target_tg_c"] >= 240.0).sum()) if not suggestions.empty else 0,
        "high_sigma_rows": int((suggestions["predicted_tg_sigma_c"] >= 75.0).sum()) if not suggestions.empty else 0,
        "human_review_required_rows": int(suggestions["human_review_required"].sum()) if not suggestions.empty else 0,
        "can_unlock_observation_after_human_approval_rows": int(suggestions["can_unlock_observation_after_human_approval"].sum())
        if not suggestions.empty
        else 0,
        "suggested_process_record_pass_rows": int(process_summary.get("process_record_pass_rows", 0)),
        "suggested_process_fields_complete_rows": int(len(ledger) - process_summary.get("process_incomplete_rows", 0))
        if not ledger.empty
        else 0,
        "suggested_ready_for_active_ledger_rows": int(process_summary.get("ready_for_active_ledger_rows", 0)),
        "evidence_level": "knowledge_template_suggestion_not_observation",
    }
    return suggestions, suggested_process, ledger, summary


def write_report(suggestions: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Process Design Suggestion Packet",
        "",
        "本文档把 process completion packet 进一步转成知识模板驱动的工艺建议。它不是实测工艺，不是文献复现，也不会产生 observation。",
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
        ("Candidate Origin Counts", summary.get("candidate_origin_counts", {})),
        ("Suggested Field Frequency", summary.get("suggested_field_frequency", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    if not suggestions.empty:
        preview_columns = [
            "suggestion_rank",
            "request_id",
            "target_tg_c",
            "process_template",
            "suggested_inputs",
            "risk_flags",
            "can_unlock_observation_after_human_approval",
        ]
        lines.extend(["", "## Immediate Suggestions", "", "| rank | request | target | template | suggested inputs | risk flags | unlock after approval |", "| ---: | --- | ---: | --- | --- | --- | --- |"])
        for _, row in suggestions[preview_columns].head(12).iterrows():
            lines.append(
                "| {rank} | {request} | {target:.1f} | {template} | {inputs} | {flags} | {unlock} |".format(
                    rank=int(row["suggestion_rank"]),
                    request=row["request_id"],
                    target=float(row["target_tg_c"]),
                    template=row["process_template"],
                    inputs=str(row["suggested_inputs"]).replace("|", "/"),
                    flags=row["risk_flags"],
                    unlock=row["can_unlock_observation_after_human_approval"],
                )
            )
    lines.extend(
        [
            "",
            "## Gate",
            "",
            "- `suggested_process_fields_complete_rows` 只表示知识模板把字段草案填全，不代表实验已完成。",
            "- 所有 suggested process records 保持 `review_status=needs_human_review`。",
            "- `suggested_ready_for_active_ledger_rows` 必须保持 0；只有人工批准且真实/高保真/文献 observation 通过后，才能进入 active evidence ledger。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build knowledge-template process design suggestions from process completion packet.")
    parser.add_argument("--packet", default="artifacts/trail/human_review/process_completion_packet.csv")
    parser.add_argument(
        "--process-record-template",
        default="artifacts/trail/human_review/process_completion_process_record_template.csv",
    )
    parser.add_argument("--schema", default="trail/experiments/process_record_schema.yaml")
    parser.add_argument("--knowledge", default="trail/knowledge/smp_prior_knowledge.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/process_design_suggestion_packet.md")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    suggestions, suggested_process, ledger, summary = build_suggestions(
        Path(args.packet),
        Path(args.process_record_template),
        Path(args.schema),
        Path(args.knowledge),
    )
    suggestions.to_csv(out_dir / "process_design_suggestion_packet.csv", index=False)
    suggested_process.to_csv(out_dir / "process_design_suggested_process_records.csv", index=False)
    ledger.to_csv(out_dir / "process_design_suggested_process_record_ledger.csv", index=False)
    (out_dir / "process_design_suggestion_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_report(suggestions, summary, Path(args.report))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def semicolon_list(value: Any) -> list[str]:
    if value is None or pd.isna(value):
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def number(value: Any, default: float = 0.0) -> float:
    if value is None or pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_authority_weights(schema_path: Path) -> dict[str, float]:
    if not schema_path.exists():
        return {"high_fidelity_simulation": 3.0, "real_dsc": 5.0}
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8")) or {}
    return {str(key): float(value) for key, value in (schema.get("authority_weights", {}) or {}).items()}


def request_base(row: pd.Series, task_type: str, authority_weight: float, source_type: str) -> dict[str, Any]:
    validation_rank = int(number(row.get("validation_rank"), default=0))
    return {
        "request_id": f"validation_{validation_rank:03d}_{task_type}",
        "validation_rank": validation_rank,
        "linked_observation_id": row.get("linked_observation_id", ""),
        "task_type": task_type,
        "target_tg_c": number(row.get("target_tg_c")),
        "surrogate_tg_c": number(row.get("observed_tg_c")),
        "target_distance_c": number(row.get("target_distance_c")),
        "predicted_tg_sigma_c": number(row.get("predicted_tg_sigma_c")),
        "candidate_origin": row.get("candidate_origin", ""),
        "process_template": row.get("process_template", ""),
        "risk_flags": row.get("risk_flags", ""),
        "validation_lane": row.get("validation_lane", ""),
        "eligible_observation_source_type": source_type,
        "authority_weight_if_completed": authority_weight,
        "smiles": row.get("smiles", ""),
        "ratios": row.get("ratios", ""),
    }


def build_requests(
    plan_path: Path,
    observation_schema: Path,
    top_k: int = 30,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    plan = pd.read_csv(plan_path) if plan_path.exists() else pd.DataFrame()
    if plan.empty:
        return pd.DataFrame(), {
            "input_plan_rows": 0,
            "request_rows": 0,
            "task_type_counts": {},
            "target_counts": {},
            "candidate_origin_counts": {},
            "expected_observation_source_counts": {},
            "blocked_by_process_completion_rows": 0,
            "max_authority_weight_if_completed": 0.0,
        }
    weights = load_authority_weights(observation_schema)
    requests: list[dict[str, Any]] = []
    for _, row in plan.head(top_k).iterrows():
        missing_fields = semicolon_list(row.get("missing_process_fields"))
        methods = semicolon_list(row.get("validation_methods"))
        validation_score = number(row.get("validation_score"))
        if bool_value(row.get("process_completion_required")):
            record = request_base(row, "process_completion", 0.0, "")
            record.update(
                {
                    "request_priority_score": validation_score,
                    "required_inputs": ";".join(missing_fields),
                    "expected_output": "completed process record with required curing/process fields",
                    "blocked_by_process_completion": False,
                    "promotion_gate": "does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval",
                }
            )
            requests.append(record)
        if bool_value(row.get("high_fidelity_required")):
            record = request_base(
                row,
                "high_fidelity_validation",
                weights.get("high_fidelity_simulation", 3.0),
                "high_fidelity_simulation",
            )
            record.update(
                {
                    "request_priority_score": validation_score * 0.95,
                    "required_inputs": ";".join(methods),
                    "expected_output": "high-fidelity Tg estimate, method notes, and confidence/risk assessment",
                    "blocked_by_process_completion": bool_value(row.get("process_completion_required")),
                    "promotion_gate": "append to observation ledger only after process fields are complete and reviewer approves",
                }
            )
            requests.append(record)
        if bool_value(row.get("dsc_ready_without_process_completion")):
            record = request_base(row, "real_dsc_planning", weights.get("real_dsc", 5.0), "real_dsc")
            record.update(
                {
                    "request_priority_score": validation_score * 1.1,
                    "required_inputs": "DSC protocol;sample preparation;operator approval",
                    "expected_output": "real DSC Tg observation with curve quality notes",
                    "blocked_by_process_completion": False,
                    "promotion_gate": "append to active observation ledger only after DSC quality and process record are approved",
                }
            )
            requests.append(record)
    request_df = pd.DataFrame(requests)
    if not request_df.empty:
        request_df = request_df.sort_values(["request_priority_score", "target_distance_c"], ascending=[False, True]).copy()
        request_df.insert(0, "request_rank", range(1, len(request_df) + 1))
    summary = {
        "input_plan_rows": int(len(plan)),
        "request_rows": int(len(request_df)),
        "task_type_counts": request_df["task_type"].value_counts().to_dict() if not request_df.empty else {},
        "target_counts": {f"{float(key):.1f}": int(value) for key, value in request_df["target_tg_c"].value_counts().sort_index().items()}
        if not request_df.empty
        else {},
        "candidate_origin_counts": request_df["candidate_origin"].value_counts().to_dict() if not request_df.empty else {},
        "expected_observation_source_counts": request_df["eligible_observation_source_type"].replace("", "none").value_counts().to_dict()
        if not request_df.empty
        else {},
        "blocked_by_process_completion_rows": int(request_df["blocked_by_process_completion"].sum()) if not request_df.empty else 0,
        "max_authority_weight_if_completed": float(request_df["authority_weight_if_completed"].max()) if not request_df.empty else 0.0,
        "real_dsc_request_rows": int((request_df["task_type"] == "real_dsc_planning").sum()) if not request_df.empty else 0,
        "high_fidelity_request_rows": int((request_df["task_type"] == "high_fidelity_validation").sum()) if not request_df.empty else 0,
        "process_completion_request_rows": int((request_df["task_type"] == "process_completion").sum()) if not request_df.empty else 0,
    }
    return request_df, summary


def write_report(requests: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Validation Request Packet",
        "",
        "本文档把实验前验证计划转成可分派 request queue。它不是 observation ledger；只有任务完成、工艺字段补齐且人工批准后，结果才可以写入高权重 observation ledger。",
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
        ("Task Type Distribution", summary.get("task_type_counts", {})),
        ("Target Tg Distribution", summary.get("target_counts", {})),
        ("Expected Observation Source Distribution", summary.get("expected_observation_source_counts", {})),
        ("Candidate Origin Distribution", summary.get("candidate_origin_counts", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Top Requests",
            "",
            "| rank | task | target Tg (C) | distance (C) | origin | source if completed | blocked | required inputs | gate |",
            "| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for _, row in requests.head(20).iterrows():
        source = row["eligible_observation_source_type"] if row["eligible_observation_source_type"] else "none"
        lines.append(
            f"| {int(row['request_rank'])} | {row['task_type']} | {float(row['target_tg_c']):.1f} | "
            f"{float(row['target_distance_c']):.3f} | {row['candidate_origin']} | {source} | "
            f"{bool(row['blocked_by_process_completion'])} | {row['required_inputs']} | {row['promotion_gate']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Rules",
            "",
            "- `process_completion` request 只补工艺记录，不产生 Tg observation。",
            "- `high_fidelity_validation` request 完成后也必须通过工艺完整性和人工批准，才能以 `high_fidelity_simulation` 写入 observation ledger。",
            "- `real_dsc_planning` 只有在工艺和人工质量门已经满足时才生成；当前若为 0，说明没有候选可直接排 DSC。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="artifacts/trail/human_review/pre_experiment_validation_plan.csv")
    parser.add_argument("--observation-schema", default="trail/experiments/observation_schema.yaml")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/validation_request_packet.md")
    parser.add_argument("--top-k", type=int, default=30)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    requests, summary = build_requests(Path(args.plan), Path(args.observation_schema), top_k=args.top_k)
    request_path = out_dir / "validation_request_queue.csv"
    summary_path = out_dir / "validation_request_summary.json"
    requests.to_csv(request_path, index=False)
    summary = {
        **summary,
        "request_path": str(request_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(requests, summary, Path(args.report))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


PHASE_ORDER = {
    "process_completion_now": 1,
    "high_fidelity_ready": 2,
    "real_dsc_planning_ready": 3,
    "blocked_until_process_completion": 4,
    "blocked_unknown_dependency": 5,
}


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "blocked"}


def number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def request_id(validation_rank: int, task_type: str) -> str:
    return f"validation_{validation_rank:03d}_{task_type}"


def execution_phase(row: pd.Series, process_request_ids: set[str]) -> tuple[str, str, bool]:
    task_type = str(row.get("task_type", ""))
    blocked = bool_value(row.get("blocked_by_process_completion"))
    validation_rank = int(number(row.get("validation_rank"), 0))
    dependency = request_id(validation_rank, "process_completion") if blocked else ""
    if task_type == "process_completion":
        return "process_completion_now", "", True
    if task_type == "real_dsc_planning" and not blocked:
        return "real_dsc_planning_ready", "", True
    if task_type == "high_fidelity_validation" and not blocked:
        return "high_fidelity_ready", "", True
    if blocked and dependency in process_request_ids:
        return "blocked_until_process_completion", dependency, False
    if blocked:
        return "blocked_unknown_dependency", dependency, False
    return "high_fidelity_ready", "", True


def schedule_score(row: pd.Series, phase: str, unlocks_observation_request: bool) -> float:
    priority = number(row.get("request_priority_score"))
    distance = number(row.get("target_distance_c"), 999.0)
    authority = number(row.get("authority_weight_if_completed"))
    score = priority + 0.05 * authority + 0.02 / max(distance, 0.02)
    if phase == "process_completion_now" and unlocks_observation_request:
        score += 0.25
    if phase in {"blocked_until_process_completion", "blocked_unknown_dependency"}:
        score -= 1.0
    return float(score)


def build_execution_schedule(
    request_path: Path,
    immediate_batch_size: int = 12,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    requests = pd.read_csv(request_path) if request_path.exists() else pd.DataFrame()
    if requests.empty:
        return pd.DataFrame(), {
            "input_request_rows": 0,
            "schedule_rows": 0,
            "immediate_executable_rows": 0,
            "immediate_batch_rows": 0,
            "blocked_rows": 0,
            "process_completion_rows": 0,
            "observation_capable_rows": 0,
        }
    process_request_ids = set(requests.loc[requests["task_type"] == "process_completion", "request_id"].astype(str))
    observation_by_rank = (
        requests[
            requests["eligible_observation_source_type"].fillna("").astype(str).str.len() > 0
        ]["validation_rank"]
        .astype(int)
        .value_counts()
        .to_dict()
    )
    rows: list[dict[str, Any]] = []
    for _, row in requests.iterrows():
        validation_rank = int(number(row.get("validation_rank"), 0))
        phase, dependency, immediate = execution_phase(row, process_request_ids)
        unlocks_observation_request = str(row.get("task_type", "")) == "process_completion" and observation_by_rank.get(validation_rank, 0) > 0
        rows.append(
            {
                **row.to_dict(),
                "execution_phase": phase,
                "execution_phase_order": PHASE_ORDER.get(phase, 99),
                "dependency_request_id": dependency,
                "immediate_executable": immediate,
                "unlocks_observation_request": unlocks_observation_request,
                "execution_score": schedule_score(row, phase, unlocks_observation_request),
                "execution_status": "planned_not_completed",
            }
        )
    schedule = pd.DataFrame(rows)
    schedule = schedule.sort_values(
        ["execution_phase_order", "execution_score", "target_distance_c"],
        ascending=[True, False, True],
    ).reset_index(drop=True)
    schedule.insert(0, "execution_rank", range(1, len(schedule) + 1))
    schedule["immediate_batch_selected"] = False
    immediate_indices = schedule[schedule["immediate_executable"]].head(max(0, int(immediate_batch_size))).index
    schedule.loc[immediate_indices, "immediate_batch_selected"] = True
    immediate_batch = schedule[schedule["immediate_batch_selected"]]
    blocked = schedule[~schedule["immediate_executable"]]
    observation_capable = schedule["eligible_observation_source_type"].fillna("").astype(str).str.len() > 0
    summary = {
        "input_request_rows": int(len(requests)),
        "schedule_rows": int(len(schedule)),
        "immediate_executable_rows": int(schedule["immediate_executable"].sum()),
        "immediate_batch_rows": int(schedule["immediate_batch_selected"].sum()),
        "blocked_rows": int((~schedule["immediate_executable"]).sum()),
        "process_completion_rows": int((schedule["task_type"] == "process_completion").sum()),
        "observation_capable_rows": int(observation_capable.sum()),
        "immediate_process_completion_rows": int(
            ((schedule["task_type"] == "process_completion") & schedule["immediate_executable"]).sum()
        ),
        "process_completion_unlock_rows": int(schedule["unlocks_observation_request"].sum()),
        "blocked_observation_rows": int((blocked["eligible_observation_source_type"].fillna("").astype(str).str.len() > 0).sum())
        if not blocked.empty
        else 0,
        "ready_real_dsc_rows": int((schedule["execution_phase"] == "real_dsc_planning_ready").sum()),
        "ready_high_fidelity_rows": int((schedule["execution_phase"] == "high_fidelity_ready").sum()),
        "immediate_batch_size": int(immediate_batch_size),
        "phase_counts": schedule["execution_phase"].value_counts().to_dict(),
        "target_counts": {f"{float(key):.1f}": int(value) for key, value in schedule["target_tg_c"].value_counts().sort_index().items()},
        "immediate_batch_target_counts": {
            f"{float(key):.1f}": int(value) for key, value in immediate_batch["target_tg_c"].value_counts().sort_index().items()
        }
        if not immediate_batch.empty
        else {},
        "immediate_batch_task_type_counts": immediate_batch["task_type"].value_counts().to_dict() if not immediate_batch.empty else {},
        "immediate_batch_candidate_origin_counts": immediate_batch["candidate_origin"].value_counts().to_dict()
        if not immediate_batch.empty
        else {},
        "blocked_observation_target_counts": {
            f"{float(key):.1f}": int(value) for key, value in blocked["target_tg_c"].value_counts().sort_index().items()
        }
        if not blocked.empty
        else {},
        "max_authority_weight_after_unblock": float(blocked["authority_weight_if_completed"].max()) if not blocked.empty else 0.0,
    }
    return schedule, summary


def write_report(schedule: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Validation Execution Schedule",
        "",
        "本文档把 validation request queue 转成执行顺序。它只安排任务，不代表任务已经完成，也不产生 observation。",
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
        ("Execution Phase Counts", summary.get("phase_counts", {})),
        ("Immediate Batch Target Counts", summary.get("immediate_batch_target_counts", {})),
        ("Immediate Batch Task Type Counts", summary.get("immediate_batch_task_type_counts", {})),
        ("Blocked Observation Target Counts", summary.get("blocked_observation_target_counts", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Immediate Execution Batch",
            "",
            "| execution rank | request | task | target Tg C | distance C | origin | unlocks observation | required inputs |",
            "| ---: | --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    immediate = schedule[schedule["immediate_batch_selected"]] if not schedule.empty else pd.DataFrame()
    for _, row in immediate.iterrows():
        lines.append(
            f"| {int(row['execution_rank'])} | {row['request_id']} | {row['task_type']} | "
            f"{float(row['target_tg_c']):.1f} | {float(row['target_distance_c']):.3f} | "
            f"{row['candidate_origin']} | {bool(row['unlocks_observation_request'])} | {row['required_inputs']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Rules",
            "",
            "- `process_completion_now` 是当前唯一能立即推进高权重证据链的任务类型。",
            "- `blocked_until_process_completion` 任务必须等对应 `dependency_request_id` 完成并获批后，才能填写 result intake。",
            "- `execution_status=planned_not_completed` 表示这里只是排程，不得当作完成结果或 observation ledger。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a target-aware execution schedule for validation requests.")
    parser.add_argument("--requests", default="artifacts/trail/human_review/validation_request_queue.csv")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/validation_execution_schedule.md")
    parser.add_argument("--immediate-batch-size", type=int, default=12)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    schedule, summary = build_execution_schedule(Path(args.requests), args.immediate_batch_size)
    schedule_path = out_dir / "validation_execution_schedule.csv"
    summary_path = out_dir / "validation_execution_schedule_summary.json"
    schedule.to_csv(schedule_path, index=False)
    summary = {
        **summary,
        "schedule_path": str(schedule_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(schedule, summary, Path(args.report))


if __name__ == "__main__":
    main()

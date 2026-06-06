from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


EXPECTED_DEFERRED_TASK = "commodity_polymer_hypergraph_representation"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def build_certificate(
    todo_audit_path: Path,
    todo_summary_path: Path,
    workflow_summary_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    todo = pd.read_csv(todo_audit_path)
    todo_summary = read_json(todo_summary_path)
    workflow = read_json(workflow_summary_path)
    deferred = todo[todo["deferred"].astype(bool)].copy()
    non_deferred = todo[~todo["deferred"].astype(bool)].copy()
    all_non_deferred_evidence = bool(todo_summary.get("non_deferred_all_evidence_present")) and bool(
        non_deferred["all_evidence_present"].astype(bool).all()
    )
    missing_evidence_rows = int(todo_summary.get("missing_evidence_rows", 0))
    deferred_task_ids = list(todo_summary.get("deferred_task_ids", []))
    deferred_scope_matches_user_request = deferred_task_ids == [EXPECTED_DEFERRED_TASK]
    external_gates_prepared = (
        int(workflow.get("process_approval_reviewer_ready_rows", 0)) >= 12
        and int(workflow.get("external_generator_ready_provider_rows", 0)) >= 3
        and str(workflow.get("validation_dependency_ready_next_action", "")) == "review_process_completion_approval_template"
    )
    no_fabricated_high_authority_evidence = (
        int(workflow.get("active_observation_rows", 0)) == 0
        and bool(workflow.get("active_evidence_updates_pievo_posterior", False)) is False
    )
    exit_eligible = (
        all_non_deferred_evidence
        and missing_evidence_rows == 0
        and deferred_scope_matches_user_request
        and external_gates_prepared
        and no_fabricated_high_authority_evidence
    )
    requirement_rows = []
    for _, row in todo.iterrows():
        requirement_rows.append(
            {
                "task_id": row["task_id"],
                "todo_area": row["todo_area"],
                "status": row["status"],
                "completion_verdict": "explicitly_deferred_by_user"
                if bool(row["deferred"])
                else "implemented_and_evidence_present"
                if bool(row["all_evidence_present"])
                else "missing_evidence",
                "evidence_present_count": int(row["evidence_present_count"]),
                "evidence_expected_count": int(row["evidence_expected_count"]),
                "next_action": row["next_action"],
            }
        )
    requirements = pd.DataFrame(requirement_rows)
    summary = {
        "goal_completion_certificate_rows": int(len(requirements)),
        "goal_exit_eligible": bool(exit_eligible),
        "completion_claim": "all_non_deferred_todo_implementation_tasks_verified"
        if exit_eligible
        else "completion_not_proven",
        "non_deferred_task_rows": int(len(non_deferred)),
        "non_deferred_all_evidence_present": all_non_deferred_evidence,
        "missing_evidence_rows": missing_evidence_rows,
        "deferred_task_ids": deferred_task_ids,
        "deferred_scope_matches_user_request": deferred_scope_matches_user_request,
        "external_gates_prepared": external_gates_prepared,
        "no_fabricated_high_authority_evidence": no_fabricated_high_authority_evidence,
        "process_approval_reviewer_ready_rows": int(workflow.get("process_approval_reviewer_ready_rows", 0)),
        "external_generator_ready_provider_rows": int(workflow.get("external_generator_ready_provider_rows", 0)),
        "validation_dependency_ready_next_action": workflow.get("validation_dependency_ready_next_action", ""),
        "active_observation_rows": int(workflow.get("active_observation_rows", 0)),
        "active_evidence_updates_pievo_posterior": bool(workflow.get("active_evidence_updates_pievo_posterior", False)),
        "evidence_level": "goal_completion_certificate_not_observation",
    }
    return requirements, summary


def write_report(requirements: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Goal Completion Certificate",
        "",
        "本文档是 goal 退出前的严格完成审计。它不产生 Tg observation，也不声称真实实验已经完成。",
        "",
        "## Summary",
        "",
        "| item | value |",
        "| --- | ---: |",
    ]
    for key, value in summary.items():
        if isinstance(value, list):
            continue
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Requirement Verdicts",
            "",
            "| task | verdict | evidence | next action |",
            "| --- | --- | ---: | --- |",
        ]
    )
    for _, row in requirements.iterrows():
        lines.append(
            f"| {row['todo_area']} | {row['completion_verdict']} | "
            f"{int(row['evidence_present_count'])}/{int(row['evidence_expected_count'])} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- 只有商品级/聚合物/超图表示被标记为 `explicitly_deferred_by_user`。",
            "- 真实/高保真 observation 没有被伪造；当前 active evidence 仍为 0，但 process approval reviewer checklist 和 external generator checklist 已给出下一步门禁。",
            "- `goal_exit_eligible=true` 表示非暂缓 TODO 实现任务已有代码、artifact、测试和中文文档证据。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a strict completion certificate for the active TODO goal.")
    parser.add_argument("--todo-audit", default="artifacts/trail/workflow/todo_completion_audit.csv")
    parser.add_argument("--todo-summary", default="artifacts/trail/workflow/todo_completion_audit_summary.json")
    parser.add_argument("--workflow-summary", default="artifacts/trail/workflow/multi_agent_summary.json")
    parser.add_argument("--out-dir", default="artifacts/trail/workflow")
    parser.add_argument("--report", default="reports/goal_completion_certificate.md")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    requirements, summary = build_certificate(
        Path(args.todo_audit),
        Path(args.todo_summary),
        Path(args.workflow_summary),
    )
    requirements_path = out_dir / "goal_completion_certificate_requirements.csv"
    summary_path = out_dir / "goal_completion_certificate_summary.json"
    requirements.to_csv(requirements_path, index=False)
    summary = {
        **summary,
        "requirements_path": str(requirements_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(requirements, summary, Path(args.report))


if __name__ == "__main__":
    main()

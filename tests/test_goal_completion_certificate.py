from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.build_goal_completion_certificate import build_certificate


def write_inputs(
    tmp_path: Path,
    *,
    missing: int = 0,
    deferred_task: str = "commodity_polymer_hypergraph_representation",
) -> tuple[Path, Path, Path]:
    audit = pd.DataFrame(
        [
            {
                "task_id": "variable_tg_targets",
                "todo_area": "真实 Tg 温度不固定",
                "status": "implemented",
                "deferred": False,
                "all_evidence_present": missing == 0,
                "evidence_present_count": 1 - missing,
                "evidence_expected_count": 1,
                "next_action": "none",
            },
            {
                "task_id": deferred_task,
                "todo_area": "真实商品级组分/聚合物/超图表示",
                "status": "deferred_by_user",
                "deferred": True,
                "all_evidence_present": True,
                "evidence_present_count": 1,
                "evidence_expected_count": 1,
                "next_action": "wait",
            },
        ]
    )
    todo_summary = {
        "non_deferred_all_evidence_present": missing == 0,
        "missing_evidence_rows": missing,
        "deferred_task_ids": [deferred_task],
    }
    workflow = {
        "process_approval_reviewer_ready_rows": 12,
        "external_generator_ready_provider_rows": 3,
        "validation_dependency_ready_next_action": "review_process_completion_approval_template",
        "active_observation_rows": 0,
        "active_evidence_updates_pievo_posterior": False,
    }
    audit_path = tmp_path / "audit.csv"
    todo_summary_path = tmp_path / "todo_summary.json"
    workflow_path = tmp_path / "workflow.json"
    audit.to_csv(audit_path, index=False)
    todo_summary_path.write_text(json.dumps(todo_summary), encoding="utf-8")
    workflow_path.write_text(json.dumps(workflow), encoding="utf-8")
    return audit_path, todo_summary_path, workflow_path


def test_goal_completion_certificate_is_exit_eligible_with_expected_deferred_scope(tmp_path: Path) -> None:
    audit_path, todo_summary_path, workflow_path = write_inputs(tmp_path)

    requirements, summary = build_certificate(audit_path, todo_summary_path, workflow_path)

    assert summary["goal_exit_eligible"] is True
    assert summary["completion_claim"] == "all_non_deferred_todo_implementation_tasks_verified"
    assert summary["deferred_scope_matches_user_request"] is True
    assert summary["external_gates_prepared"] is True
    assert summary["no_fabricated_high_authority_evidence"] is True
    assert requirements.loc[requirements["task_id"] == "variable_tg_targets", "completion_verdict"].iloc[0] == "implemented_and_evidence_present"


def test_goal_completion_certificate_rejects_missing_evidence_or_wrong_deferred_scope(tmp_path: Path) -> None:
    audit_path, todo_summary_path, workflow_path = write_inputs(tmp_path, missing=1)
    _, missing_summary = build_certificate(audit_path, todo_summary_path, workflow_path)
    assert missing_summary["goal_exit_eligible"] is False

    audit_path, todo_summary_path, workflow_path = write_inputs(tmp_path, deferred_task="other_deferred_task")
    _, deferred_summary = build_certificate(audit_path, todo_summary_path, workflow_path)
    assert deferred_summary["goal_exit_eligible"] is False
    assert deferred_summary["deferred_scope_matches_user_request"] is False

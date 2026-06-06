from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.build_validation_dependency_graph import build_dependency_graph


def write_common_inputs(
    tmp_path: Path,
    *,
    approval_decision: str = "",
    approval_process_ready: bool = False,
    approval_reviewer_approved: bool = False,
    protocol_ready: bool = False,
    protocol_unblocked: bool = False,
) -> tuple[Path, Path, Path, Path, Path, Path]:
    requests = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "validation_rank": 1,
                "linked_observation_id": "candidate_001",
                "task_type": "process_completion",
                "target_tg_c": 250.0,
                "candidate_origin": "sparse_target_replacement_250",
                "eligible_observation_source_type": "",
                "blocked_by_process_completion": False,
            },
            {
                "request_id": "validation_001_high_fidelity_validation",
                "validation_rank": 1,
                "linked_observation_id": "candidate_001",
                "task_type": "high_fidelity_validation",
                "target_tg_c": 250.0,
                "candidate_origin": "sparse_target_replacement_250",
                "eligible_observation_source_type": "high_fidelity_simulation",
                "blocked_by_process_completion": True,
            },
        ]
    )
    schedule = pd.DataFrame(
        [
            {
                "request_id": "validation_001_process_completion",
                "immediate_executable": True,
                "immediate_batch_selected": True,
                "dependency_request_id": "",
            },
            {
                "request_id": "validation_001_high_fidelity_validation",
                "immediate_executable": False,
                "immediate_batch_selected": False,
                "dependency_request_id": "validation_001_process_completion",
            },
        ]
    )
    approval = pd.DataFrame(
        [
            {
                "approval_id": "approval_validation_001_process_completion",
                "request_id": "validation_001_process_completion",
                "linked_observation_id": "candidate_001",
                "approval_decision": approval_decision,
                "process_ready": approval_process_ready,
                "reviewer_approved": approval_reviewer_approved,
                "target_tg_c": 250.0,
                "candidate_origin": "sparse_target_replacement_250",
                "evidence_level": "knowledge_template_suggestion_not_observation",
            }
        ]
    )
    protocol = pd.DataFrame(
        [
            {
                "protocol_id": "protocol_validation_001_high_fidelity_validation",
                "request_id": "validation_001_high_fidelity_validation",
                "linked_observation_id": "candidate_001",
                "target_tg_c": 250.0,
                "candidate_origin": "sparse_target_replacement_250",
                "protocol_status": "ready_for_high_fidelity_execution"
                if protocol_ready
                else "blocked_pending_process_approval",
                "can_start_high_fidelity_protocol": protocol_ready,
                "process_approval_unblocked": protocol_unblocked,
                "evidence_level": "high_fidelity_protocol_template_not_observation",
            }
        ]
    )
    result = pd.DataFrame(
        [
            {
                "result_id": "result_validation_001_high_fidelity_validation",
                "request_id": "validation_001_high_fidelity_validation",
                "target_tg_c": 250.0,
                "candidate_origin": "sparse_target_replacement_250",
                "observed_tg_c": "",
                "process_ready": False,
                "reviewer_approved": False,
            }
        ]
    )
    active_summary = {"active_rows": 0}
    paths = (
        tmp_path / "requests.csv",
        tmp_path / "schedule.csv",
        tmp_path / "approval.csv",
        tmp_path / "protocol.csv",
        tmp_path / "result.csv",
        tmp_path / "active.json",
    )
    requests.to_csv(paths[0], index=False)
    schedule.to_csv(paths[1], index=False)
    approval.to_csv(paths[2], index=False)
    protocol.to_csv(paths[3], index=False)
    result.to_csv(paths[4], index=False)
    paths[5].write_text(json.dumps(active_summary), encoding="utf-8")
    return paths


def test_validation_dependency_graph_marks_protocol_blocked_until_process_approval(tmp_path: Path) -> None:
    nodes, edges, summary = build_dependency_graph(*write_common_inputs(tmp_path))

    protocol_node = nodes[nodes["node_id"] == "protocol_validation_001_high_fidelity_validation"].iloc[0]
    assert summary["request_rows"] == 2
    assert summary["process_approval_template_rows"] == 1
    assert summary["pending_process_approval_rows"] == 1
    assert summary["blocked_high_fidelity_protocol_rows"] == 1
    assert summary["ready_next_action"] == "review_process_completion_approval_template"
    assert summary["ready_next_action_rows"] == 1
    assert protocol_node["status"] == "blocked_pending_process_approval"
    assert bool(protocol_node["is_blocked"]) is True
    assert "process_approval_not_unblocked" in summary["blocker_reason_counts"]
    assert "pending_completed_result" in summary["edge_status_counts"]
    assert len(edges[edges["edge_type"] == "process_completion_unlocks_observation_request"]) == 1


def test_validation_dependency_graph_moves_to_high_fidelity_execution_after_approval(tmp_path: Path) -> None:
    paths = write_common_inputs(
        tmp_path,
        approval_decision="approved",
        approval_process_ready=True,
        approval_reviewer_approved=True,
        protocol_ready=True,
        protocol_unblocked=True,
    )
    nodes, edges, summary = build_dependency_graph(*paths)

    protocol_node = nodes[nodes["node_id"] == "protocol_validation_001_high_fidelity_validation"].iloc[0]
    assert summary["pending_process_approval_rows"] == 0
    assert summary["ready_high_fidelity_protocol_rows"] == 1
    assert summary["blocked_high_fidelity_protocol_rows"] == 0
    assert summary["ready_next_action"] == "execute_high_fidelity_protocol_and_fill_validation_result"
    assert summary["ready_next_action_rows"] == 1
    assert bool(protocol_node["ready_for_next_action"]) is True
    assert edges[edges["edge_type"] == "process_approval_unblocks_protocol"].iloc[0]["edge_status"] == "satisfied"
    assert edges[edges["edge_type"] == "protocol_allows_result_intake"].iloc[0]["edge_status"] == "ready_for_result_intake"

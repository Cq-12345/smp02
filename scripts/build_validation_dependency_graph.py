from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


NODE_COLUMNS = [
    "node_id",
    "node_type",
    "request_id",
    "linked_observation_id",
    "task_type",
    "target_tg_c",
    "candidate_origin",
    "status",
    "ready_for_next_action",
    "is_blocked",
    "is_completed",
    "blocker_reason",
    "evidence_level",
    "creates_observation",
]

EDGE_COLUMNS = [
    "from_node_id",
    "to_node_id",
    "edge_type",
    "linked_observation_id",
    "target_tg_c",
    "edge_status",
    "gate_condition",
    "blocker_reason",
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def request_id_for(validation_rank: Any, task_type: str) -> str:
    return f"validation_{int(number(validation_rank)):03d}_{task_type}"


def by_column(frame: pd.DataFrame, column: str) -> dict[str, pd.Series]:
    if frame.empty or column not in frame.columns:
        return {}
    return {str(row[column]): row for _, row in frame.iterrows()}


def approval_is_accepted(row: pd.Series) -> bool:
    decision = text(row.get("approval_decision")).lower()
    return decision in {"approve", "approved", "accept", "accepted"} and bool_value(row.get("process_ready")) and bool_value(
        row.get("reviewer_approved")
    )


def result_is_completed(row: pd.Series) -> bool:
    return (
        text(row.get("observed_tg_c")) != ""
        and bool_value(row.get("process_ready"))
        and bool_value(row.get("reviewer_approved"))
    )


def protocol_ready(protocol_by_request: dict[str, pd.Series], request_id: str) -> bool:
    row = protocol_by_request.get(request_id)
    return bool_value(row.get("can_start_high_fidelity_protocol")) if row is not None else False


def protocol_unblocked(protocol_by_request: dict[str, pd.Series], request_id: str) -> bool:
    row = protocol_by_request.get(request_id)
    return bool_value(row.get("process_approval_unblocked")) if row is not None else False


def request_status(row: pd.Series, schedule_by_request: dict[str, pd.Series], protocol_by_request: dict[str, pd.Series]) -> tuple[str, bool, bool, str]:
    request_id = text(row.get("request_id"))
    task_type = text(row.get("task_type"))
    schedule = schedule_by_request.get(request_id)
    if task_type == "process_completion":
        immediate = bool_value(schedule.get("immediate_executable")) if schedule is not None else True
        selected = bool_value(schedule.get("immediate_batch_selected")) if schedule is not None else False
        status = "immediate_batch_process_completion" if selected else "process_completion_ready"
        return status, immediate, False, ""
    if task_type == "high_fidelity_validation":
        ready = protocol_ready(protocol_by_request, request_id)
        if ready:
            return "ready_for_high_fidelity_execution", True, False, ""
        return "blocked_pending_process_approval", False, True, "process_completion_and_human_approval_required"
    if bool_value(row.get("blocked_by_process_completion")):
        return "blocked_pending_process_approval", False, True, "process_completion_and_human_approval_required"
    return "request_ready", True, False, ""


def make_node(
    node_id: str,
    node_type: str,
    request_id: str = "",
    linked_observation_id: str = "",
    task_type: str = "",
    target_tg_c: float = 0.0,
    candidate_origin: str = "",
    status: str = "",
    ready_for_next_action: bool = False,
    is_blocked: bool = False,
    is_completed: bool = False,
    blocker_reason: str = "",
    evidence_level: str = "",
    creates_observation: bool = False,
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "node_type": node_type,
        "request_id": request_id,
        "linked_observation_id": linked_observation_id,
        "task_type": task_type,
        "target_tg_c": target_tg_c,
        "candidate_origin": candidate_origin,
        "status": status,
        "ready_for_next_action": ready_for_next_action,
        "is_blocked": is_blocked,
        "is_completed": is_completed,
        "blocker_reason": blocker_reason,
        "evidence_level": evidence_level,
        "creates_observation": creates_observation,
    }


def make_edge(
    from_node_id: str,
    to_node_id: str,
    edge_type: str,
    linked_observation_id: str = "",
    target_tg_c: float = 0.0,
    edge_status: str = "",
    gate_condition: str = "",
    blocker_reason: str = "",
) -> dict[str, Any]:
    return {
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "edge_type": edge_type,
        "linked_observation_id": linked_observation_id,
        "target_tg_c": target_tg_c,
        "edge_status": edge_status,
        "gate_condition": gate_condition,
        "blocker_reason": blocker_reason,
    }


def build_dependency_graph(
    validation_requests_path: Path,
    execution_schedule_path: Path,
    process_approval_template_path: Path,
    high_fidelity_protocol_path: Path,
    validation_result_template_path: Path,
    active_observation_summary_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    requests = read_csv(validation_requests_path)
    schedule = read_csv(execution_schedule_path)
    approvals = read_csv(process_approval_template_path)
    protocols = read_csv(high_fidelity_protocol_path)
    results = read_csv(validation_result_template_path)
    active_summary = read_json(active_observation_summary_path)

    schedule_by_request = by_column(schedule, "request_id")
    approval_by_request = by_column(approvals, "request_id")
    approval_by_link = by_column(approvals, "linked_observation_id")
    protocol_by_request = by_column(protocols, "request_id")
    result_by_request = by_column(results, "request_id")

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for _, row in requests.iterrows():
        request_id = text(row.get("request_id"))
        status, ready, blocked, blocker = request_status(row, schedule_by_request, protocol_by_request)
        nodes.append(
            make_node(
                node_id=request_id,
                node_type="validation_request",
                request_id=request_id,
                linked_observation_id=text(row.get("linked_observation_id")),
                task_type=text(row.get("task_type")),
                target_tg_c=number(row.get("target_tg_c")),
                candidate_origin=text(row.get("candidate_origin")),
                status=status,
                ready_for_next_action=ready,
                is_blocked=blocked,
                blocker_reason=blocker,
                creates_observation=text(row.get("eligible_observation_source_type")) != "",
            )
        )

    for _, row in approvals.iterrows():
        accepted = approval_is_accepted(row)
        request_id = text(row.get("request_id"))
        approval_id = text(row.get("approval_id")) or f"approval_{request_id}"
        status = "process_approval_accepted" if accepted else "awaiting_human_process_approval"
        nodes.append(
            make_node(
                node_id=approval_id,
                node_type="process_approval_gate",
                request_id=request_id,
                linked_observation_id=text(row.get("linked_observation_id")),
                task_type="process_approval",
                target_tg_c=number(row.get("target_tg_c")),
                candidate_origin=text(row.get("candidate_origin")),
                status=status,
                ready_for_next_action=not accepted,
                is_blocked=not accepted,
                is_completed=accepted,
                blocker_reason="" if accepted else "human_process_approval_missing",
                evidence_level=text(row.get("evidence_level")),
            )
        )
        edges.append(
            make_edge(
                from_node_id=request_id,
                to_node_id=approval_id,
                edge_type="requires_process_approval",
                linked_observation_id=text(row.get("linked_observation_id")),
                target_tg_c=number(row.get("target_tg_c")),
                edge_status="satisfied" if accepted else "pending_human_process_approval",
                gate_condition="process_ready_and_reviewer_approved",
                blocker_reason="" if accepted else "human_process_approval_missing",
            )
        )

    for _, row in protocols.iterrows():
        request_id = text(row.get("request_id"))
        protocol_id = text(row.get("protocol_id")) or f"protocol_{request_id}"
        ready = bool_value(row.get("can_start_high_fidelity_protocol"))
        nodes.append(
            make_node(
                node_id=protocol_id,
                node_type="high_fidelity_protocol",
                request_id=request_id,
                linked_observation_id=text(row.get("linked_observation_id")),
                task_type="high_fidelity_protocol",
                target_tg_c=number(row.get("target_tg_c")),
                candidate_origin=text(row.get("candidate_origin")),
                status=text(row.get("protocol_status")) or ("ready_for_high_fidelity_execution" if ready else "blocked_pending_process_approval"),
                ready_for_next_action=ready,
                is_blocked=not ready,
                blocker_reason="" if ready else "process_approval_not_unblocked",
                evidence_level=text(row.get("evidence_level")),
                creates_observation=False,
            )
        )
        edges.append(
            make_edge(
                from_node_id=request_id,
                to_node_id=protocol_id,
                edge_type="request_to_high_fidelity_protocol",
                linked_observation_id=text(row.get("linked_observation_id")),
                target_tg_c=number(row.get("target_tg_c")),
                edge_status="satisfied" if ready else "blocked_pending_process_approval",
                gate_condition="process_completion_unblocked_request",
                blocker_reason="" if ready else "process_approval_not_unblocked",
            )
        )

    for _, row in results.iterrows():
        request_id = text(row.get("request_id"))
        result_id = text(row.get("result_id")) or f"result_{request_id}"
        completed = result_is_completed(row)
        ready_protocol = protocol_ready(protocol_by_request, request_id)
        status = "result_completed_pending_active_gate" if completed else "awaiting_completed_validation_result"
        if not ready_protocol and not completed:
            status = "blocked_pending_high_fidelity_protocol"
        nodes.append(
            make_node(
                node_id=result_id,
                node_type="validation_result_intake",
                request_id=request_id,
                linked_observation_id=text(protocol_by_request.get(request_id, {}).get("linked_observation_id", "")),
                task_type="validation_result_intake",
                target_tg_c=number(row.get("target_tg_c")),
                candidate_origin=text(row.get("candidate_origin")),
                status=status,
                ready_for_next_action=ready_protocol and not completed,
                is_blocked=not ready_protocol and not completed,
                is_completed=completed,
                blocker_reason="" if ready_protocol or completed else "protocol_not_ready",
                creates_observation=completed,
            )
        )
        protocol_id = text(protocol_by_request.get(request_id, {}).get("protocol_id", f"protocol_{request_id}"))
        edges.append(
            make_edge(
                from_node_id=protocol_id,
                to_node_id=result_id,
                edge_type="protocol_allows_result_intake",
                linked_observation_id=text(protocol_by_request.get(request_id, {}).get("linked_observation_id", "")),
                target_tg_c=number(row.get("target_tg_c")),
                edge_status="ready_for_result_intake" if ready_protocol else "blocked_pending_protocol",
                gate_condition="high_fidelity_protocol_ready_and_result_fields_filled",
                blocker_reason="" if ready_protocol else "protocol_not_ready",
            )
        )
    active_rows = int(active_summary.get("active_rows", 0))
    active_gate_id = "active_high_authority_evidence_gate"
    nodes.append(
        make_node(
            node_id=active_gate_id,
            node_type="active_evidence_gate",
            status="active_evidence_available" if active_rows > 0 else "no_active_evidence_noop",
            ready_for_next_action=False,
            is_blocked=active_rows == 0,
            is_completed=active_rows > 0,
            blocker_reason="" if active_rows > 0 else "no_completed_approved_high_authority_result",
            evidence_level="high_authority_observation_gate",
        )
    )
    for _, row in results.iterrows():
        request_id = text(row.get("request_id"))
        result_id = text(row.get("result_id")) or f"result_{request_id}"
        completed = result_is_completed(row)
        edges.append(
            make_edge(
                from_node_id=result_id,
                to_node_id=active_gate_id,
                edge_type="result_must_pass_active_evidence_gate",
                target_tg_c=number(row.get("target_tg_c")),
                edge_status="ready_for_active_gate" if completed else "pending_completed_result",
                gate_condition="observed_tg_process_ready_reviewer_approved_and_ledger_pass",
                blocker_reason="" if completed else "validation_result_missing_or_unapproved",
            )
        )

    high_fidelity_requests = requests[requests["task_type"].astype(str) == "high_fidelity_validation"] if not requests.empty else pd.DataFrame()
    for _, row in high_fidelity_requests.iterrows():
        request_id = text(row.get("request_id"))
        validation_rank = row.get("validation_rank")
        dependency_id = text(schedule_by_request.get(request_id, {}).get("dependency_request_id"))
        if not dependency_id:
            dependency_id = request_id_for(validation_rank, "process_completion")
        if dependency_id not in set(requests["request_id"].astype(str)):
            continue
        unblocked = protocol_unblocked(protocol_by_request, request_id)
        link_id = text(row.get("linked_observation_id"))
        edges.append(
            make_edge(
                from_node_id=dependency_id,
                to_node_id=request_id,
                edge_type="process_completion_unlocks_observation_request",
                linked_observation_id=link_id,
                target_tg_c=number(row.get("target_tg_c")),
                edge_status="satisfied" if unblocked else "blocked_pending_process_approval",
                gate_condition="completed_process_record_ready_for_active_ledger_and_human_approved",
                blocker_reason="" if unblocked else "process_approval_not_unblocked",
            )
        )
        approval = approval_by_link.get(link_id)
        if approval is not None:
            approval_id = text(approval.get("approval_id")) or f"approval_{dependency_id}"
            edges.append(
                make_edge(
                    from_node_id=approval_id,
                    to_node_id=text(protocol_by_request.get(request_id, {}).get("protocol_id", f"protocol_{request_id}")),
                    edge_type="process_approval_unblocks_protocol",
                    linked_observation_id=link_id,
                    target_tg_c=number(row.get("target_tg_c")),
                    edge_status="satisfied" if unblocked else "blocked_pending_process_approval",
                    gate_condition="approved_process_record_matches_linked_observation",
                    blocker_reason="" if unblocked else "human_process_approval_missing",
                )
            )

    node_frame = pd.DataFrame(nodes, columns=NODE_COLUMNS)
    edge_frame = pd.DataFrame(edges, columns=EDGE_COLUMNS)
    blocked_edges = (
        edge_frame["edge_status"].fillna("").astype(str).str.startswith("blocked")
        | edge_frame["edge_status"].fillna("").astype(str).str.startswith("pending")
    )
    pending_approvals = node_frame[node_frame["status"] == "awaiting_human_process_approval"]
    ready_protocols = node_frame[
        (node_frame["node_type"] == "high_fidelity_protocol") & (node_frame["status"] == "ready_for_high_fidelity_execution")
    ]
    if not pending_approvals.empty:
        next_action = "review_process_completion_approval_template"
        next_action_rows = int(len(pending_approvals))
    elif not ready_protocols.empty:
        next_action = "execute_high_fidelity_protocol_and_fill_validation_result"
        next_action_rows = int(len(ready_protocols))
    else:
        next_action = "build_next_process_completion_packet"
        next_action_rows = 0
    summary = {
        "request_rows": int(len(requests)),
        "node_rows": int(len(node_frame)),
        "edge_rows": int(len(edge_frame)),
        "blocked_or_pending_edge_rows": int(blocked_edges.sum()) if not edge_frame.empty else 0,
        "process_completion_request_rows": int((requests["task_type"] == "process_completion").sum()) if not requests.empty else 0,
        "high_fidelity_request_rows": int((requests["task_type"] == "high_fidelity_validation").sum()) if not requests.empty else 0,
        "process_approval_template_rows": int(len(approvals)),
        "pending_process_approval_rows": int(len(pending_approvals)),
        "high_fidelity_protocol_rows": int((node_frame["node_type"] == "high_fidelity_protocol").sum()) if not node_frame.empty else 0,
        "ready_high_fidelity_protocol_rows": int(len(ready_protocols)),
        "blocked_high_fidelity_protocol_rows": int(
            ((node_frame["node_type"] == "high_fidelity_protocol") & node_frame["is_blocked"].fillna(False).astype(bool)).sum()
        )
        if not node_frame.empty
        else 0,
        "validation_result_template_rows": int((node_frame["node_type"] == "validation_result_intake").sum()) if not node_frame.empty else 0,
        "completed_validation_result_rows": int(
            ((node_frame["node_type"] == "validation_result_intake") & node_frame["is_completed"].fillna(False).astype(bool)).sum()
        )
        if not node_frame.empty
        else 0,
        "active_evidence_rows": active_rows,
        "ready_next_action": next_action,
        "ready_next_action_rows": next_action_rows,
        "edge_status_counts": edge_frame["edge_status"].value_counts().to_dict() if not edge_frame.empty else {},
        "blocker_reason_counts": edge_frame.loc[blocked_edges, "blocker_reason"].value_counts().to_dict()
        if not edge_frame.empty
        else {},
        "blocked_protocol_target_counts": {
            f"{float(key):.1f}": int(value)
            for key, value in node_frame[
                (node_frame["node_type"] == "high_fidelity_protocol") & node_frame["is_blocked"].fillna(False).astype(bool)
            ]["target_tg_c"]
            .value_counts()
            .sort_index()
            .items()
        }
        if not node_frame.empty
        else {},
        "evidence_level": "validation_dependency_graph_not_observation",
    }
    return node_frame, edge_frame, summary


def write_report(nodes: pd.DataFrame, edges: pd.DataFrame, summary: dict[str, Any], report_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Validation Dependency Graph",
        "",
        "本文档把人工验证闭环形式化为 DAG。它只记录 gate、依赖和阻塞原因，不产生 Tg observation。",
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
        ("Edge Status Counts", summary.get("edge_status_counts", {})),
        ("Blocker Reason Counts", summary.get("blocker_reason_counts", {})),
        ("Blocked Protocol Target Counts", summary.get("blocked_protocol_target_counts", {})),
    ]:
        if not counts:
            continue
        lines.extend(["", f"## {title}", "", "| item | rows |", "| --- | ---: |"])
        for key, value in counts.items():
            lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            f"- `{summary.get('ready_next_action')}`: {summary.get('ready_next_action_rows')} rows.",
            "",
            "## Blocked High-fidelity Protocols",
            "",
            "| node | request | target | origin | blocker |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    blocked_protocols = nodes[
        (nodes["node_type"] == "high_fidelity_protocol") & nodes["is_blocked"].fillna(False).astype(bool)
    ] if not nodes.empty else pd.DataFrame()
    for _, row in blocked_protocols.head(15).iterrows():
        lines.append(
            f"| {row['node_id']} | {row['request_id']} | {float(row['target_tg_c']):.1f} | "
            f"{row['candidate_origin']} | {row['blocker_reason']} |"
        )
    lines.extend(
        [
            "",
            "## Gate Rules",
            "",
            "- process completion request 不产生 observation；它只为后续 high-fidelity/real request 解锁工艺条件。",
            "- process approval gate 需要 `process_ready=true`、`reviewer_approved=true` 和明确审批决定。",
            "- high-fidelity protocol ready 后仍不等于 observation；必须填写 result intake，并通过 active evidence gate。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a DAG-style dependency graph for validation gates.")
    parser.add_argument("--validation-requests", default="artifacts/trail/human_review/validation_request_queue.csv")
    parser.add_argument("--execution-schedule", default="artifacts/trail/human_review/validation_execution_schedule.csv")
    parser.add_argument("--process-approval-template", default="artifacts/trail/human_review/process_completion_approval_template.csv")
    parser.add_argument("--high-fidelity-protocol", default="artifacts/trail/human_review/high_fidelity_protocol_packet.csv")
    parser.add_argument("--validation-result-template", default="artifacts/trail/human_review/validation_result_intake_template.csv")
    parser.add_argument("--active-observation-summary", default="artifacts/trail/human_review/active_high_authority_observation_summary.json")
    parser.add_argument("--out-dir", default="artifacts/trail/human_review")
    parser.add_argument("--report", default="reports/validation_dependency_graph.md")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes, edges, summary = build_dependency_graph(
        Path(args.validation_requests),
        Path(args.execution_schedule),
        Path(args.process_approval_template),
        Path(args.high_fidelity_protocol),
        Path(args.validation_result_template),
        Path(args.active_observation_summary),
    )
    nodes_path = out_dir / "validation_dependency_nodes.csv"
    edges_path = out_dir / "validation_dependency_edges.csv"
    summary_path = out_dir / "validation_dependency_summary.json"
    nodes.to_csv(nodes_path, index=False)
    edges.to_csv(edges_path, index=False)
    summary = {
        **summary,
        "nodes_path": str(nodes_path),
        "edges_path": str(edges_path),
        "summary_path": str(summary_path),
        "report_path": str(Path(args.report)),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(nodes, edges, summary, Path(args.report))


if __name__ == "__main__":
    main()

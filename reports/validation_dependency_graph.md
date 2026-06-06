# Validation Dependency Graph

本文档把人工验证闭环形式化为 DAG。它只记录 gate、依赖和阻塞原因，不产生 Tg observation。

## Summary

| item | value |
| --- | ---: |
| request_rows | 55 |
| node_rows | 118 |
| edge_rows | 125 |
| blocked_or_pending_edge_rows | 125 |
| process_completion_request_rows | 30 |
| high_fidelity_request_rows | 25 |
| process_approval_template_rows | 12 |
| pending_process_approval_rows | 12 |
| high_fidelity_protocol_rows | 25 |
| ready_high_fidelity_protocol_rows | 0 |
| blocked_high_fidelity_protocol_rows | 25 |
| validation_result_template_rows | 25 |
| completed_validation_result_rows | 0 |
| active_evidence_rows | 0 |
| ready_next_action | review_process_completion_approval_template |
| ready_next_action_rows | 12 |
| evidence_level | validation_dependency_graph_not_observation |
| nodes_path | artifacts/trail/human_review/validation_dependency_nodes.csv |
| edges_path | artifacts/trail/human_review/validation_dependency_edges.csv |
| summary_path | artifacts/trail/human_review/validation_dependency_summary.json |
| report_path | reports/validation_dependency_graph.md |

## Edge Status Counts

| item | rows |
| --- | ---: |
| blocked_pending_process_approval | 63 |
| blocked_pending_protocol | 25 |
| pending_completed_result | 25 |
| pending_human_process_approval | 12 |

## Blocker Reason Counts

| item | rows |
| --- | ---: |
| process_approval_not_unblocked | 50 |
| human_process_approval_missing | 25 |
| protocol_not_ready | 25 |
| validation_result_missing_or_unapproved | 25 |

## Blocked Protocol Target Counts

| item | rows |
| --- | ---: |
| 195.0 | 12 |
| 250.0 | 13 |

## Next Action

- `review_process_completion_approval_template`: 12 rows.

## Blocked High-fidelity Protocols

| node | request | target | origin | blocker |
| --- | --- | ---: | --- | --- |
| protocol_validation_001_high_fidelity_validation | validation_001_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_002_high_fidelity_validation | validation_002_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_003_high_fidelity_validation | validation_003_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_006_high_fidelity_validation | validation_006_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_007_high_fidelity_validation | validation_007_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_008_high_fidelity_validation | validation_008_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_009_high_fidelity_validation | validation_009_high_fidelity_validation | 195.0 | pievo_latent_local_search_selected | process_approval_not_unblocked |
| protocol_validation_010_high_fidelity_validation | validation_010_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_011_high_fidelity_validation | validation_011_high_fidelity_validation | 195.0 | pievo_latent_local_search_selected | process_approval_not_unblocked |
| protocol_validation_014_high_fidelity_validation | validation_014_high_fidelity_validation | 195.0 | vae_latent_local_search | process_approval_not_unblocked |
| protocol_validation_016_high_fidelity_validation | validation_016_high_fidelity_validation | 195.0 | vae_latent_local_search | process_approval_not_unblocked |
| protocol_validation_017_high_fidelity_validation | validation_017_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_approval_not_unblocked |
| protocol_validation_018_high_fidelity_validation | validation_018_high_fidelity_validation | 195.0 | pievo_latent_local_search_selected | process_approval_not_unblocked |
| protocol_validation_019_high_fidelity_validation | validation_019_high_fidelity_validation | 195.0 | vae_latent_local_search | process_approval_not_unblocked |
| protocol_validation_020_high_fidelity_validation | validation_020_high_fidelity_validation | 195.0 | pievo_ensemble_guard_selected | process_approval_not_unblocked |

## Gate Rules

- process completion request 不产生 observation；它只为后续 high-fidelity/real request 解锁工艺条件。
- process approval gate 需要 `process_ready=true`、`reviewer_approved=true` 和明确审批决定。
- high-fidelity protocol ready 后仍不等于 observation；必须填写 result intake，并通过 active evidence gate。

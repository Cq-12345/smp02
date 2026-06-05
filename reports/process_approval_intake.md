# Process Approval Intake

本文档记录知识模板工艺建议如何进入人工批准入口。它不产生 Tg observation；即使工艺被批准，也只是解锁后续高保真/真实结果 intake。

## Summary

| item | value |
| --- | ---: |
| suggestion_rows | 12 |
| approval_template_rows | 12 |
| submitted_approval_rows | 0 |
| accepted_process_approval_rows | 0 |
| rejected_process_approval_rows | 0 |
| ready_process_record_rows | 0 |
| unblocked_observation_request_rows | 0 |
| approval_gate_status | awaiting_human_process_approval |
| template_path | artifacts/trail/human_review/process_completion_approval_template.csv |
| review_path | artifacts/trail/human_review/process_completion_approval_review.csv |
| approved_process_records_path | artifacts/trail/human_review/process_completion_approved_process_records.csv |
| approved_process_record_ledger_path | artifacts/trail/human_review/process_completion_approved_process_record_ledger.csv |
| unblocked_requests_path | artifacts/trail/human_review/process_completion_unblocked_validation_requests.csv |
| summary_path | artifacts/trail/human_review/process_completion_approval_summary.json |
| report_path | reports/process_approval_intake.md |

## Gate Rules

- `approval_decision`、`process_ready`、`reviewer_approved` 和 `reviewer_id` 必须同时满足。
- 审批后的 process record 还必须通过 `import_process_records`，且 `ready_for_active_ledger=true`。
- 被解锁的 high-fidelity/real request 仍必须走 validation result intake；本脚本不会写入 observation ledger。

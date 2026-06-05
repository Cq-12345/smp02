# Validation Result Intake

本文档记录 validation request 完成结果如何进入 observation ledger。当前没有真实或高保真完成结果时，accepted rows 应为 0。

## Summary

| item | value |
| --- | ---: |
| template_rows | 25 |
| result_rows | 0 |
| accepted_result_rows | 0 |
| rejected_result_rows | 0 |
| process_ready_rows | 0 |
| reviewer_approved_rows | 0 |
| observation_ledger_pass_rows | 0 |
| template_path | artifacts/trail/human_review/validation_result_intake_template.csv |
| review_path | artifacts/trail/human_review/validation_result_review.csv |
| observation_input_path | artifacts/trail/human_review/validation_result_observation_input.csv |
| observation_ledger_path | artifacts/trail/human_review/validation_result_observation_ledger.csv |
| observation_summary_path | artifacts/trail/human_review/validation_result_observation_summary.json |
| summary_path | artifacts/trail/human_review/validation_result_intake_summary.json |
| report_path | reports/validation_result_intake.md |

## Gate Rules

- `source_type` 必须与 request 的 `eligible_observation_source_type` 一致。
- `observed_tg_c`、`process_ready` 和 `reviewer_approved` 都必须满足，结果才会写入 observation input。
- process completion request 本身不是 observation-capable request，不能直接产生 Tg observation。

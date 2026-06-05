# Validation Execution Schedule

本文档把 validation request queue 转成执行顺序。它只安排任务，不代表任务已经完成，也不产生 observation。

## Summary

| item | value |
| --- | ---: |
| input_request_rows | 55 |
| schedule_rows | 55 |
| immediate_executable_rows | 30 |
| immediate_batch_rows | 12 |
| blocked_rows | 25 |
| process_completion_rows | 30 |
| observation_capable_rows | 25 |
| immediate_process_completion_rows | 30 |
| process_completion_unlock_rows | 25 |
| blocked_observation_rows | 25 |
| ready_real_dsc_rows | 0 |
| ready_high_fidelity_rows | 0 |
| immediate_batch_size | 12 |
| max_authority_weight_after_unblock | 3.0 |
| schedule_path | artifacts/trail/human_review/validation_execution_schedule.csv |
| summary_path | artifacts/trail/human_review/validation_execution_schedule_summary.json |
| report_path | reports/validation_execution_schedule.md |

## Execution Phase Counts

| item | rows |
| --- | ---: |
| process_completion_now | 30 |
| blocked_until_process_completion | 25 |

## Immediate Batch Target Counts

| item | rows |
| --- | ---: |
| 195.0 | 4 |
| 250.0 | 8 |

## Immediate Batch Task Type Counts

| item | rows |
| --- | ---: |
| process_completion | 12 |

## Blocked Observation Target Counts

| item | rows |
| --- | ---: |
| 195.0 | 12 |
| 250.0 | 13 |

## Immediate Execution Batch

| execution rank | request | task | target Tg C | distance C | origin | unlocks observation | required inputs |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | validation_001_process_completion | process_completion | 250.0 | 0.034 | sparse_target_replacement_250 | True | catalyst_loading;cure_temperature_c;post_cure_temperature_c |
| 2 | validation_011_process_completion | process_completion | 195.0 | 0.059 | pievo_latent_local_search_selected | True | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h |
| 3 | validation_002_process_completion | process_completion | 250.0 | 0.111 | sparse_target_replacement_250 | True | solvent;imidization_temperature_c;imidization_time_h |
| 4 | validation_009_process_completion | process_completion | 195.0 | 0.119 | pievo_latent_local_search_selected | True | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h |
| 5 | validation_003_process_completion | process_completion | 250.0 | 0.554 | sparse_target_replacement_250 | True | solvent;imidization_temperature_c;imidization_time_h |
| 6 | validation_006_process_completion | process_completion | 250.0 | 0.384 | sparse_target_replacement_250 | True | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h |
| 7 | validation_008_process_completion | process_completion | 250.0 | 0.595 | sparse_target_replacement_250 | True | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h |
| 8 | validation_007_process_completion | process_completion | 250.0 | 0.767 | sparse_target_replacement_250 | True | catalyst_loading;cure_temperature_c;post_cure_temperature_c |
| 9 | validation_010_process_completion | process_completion | 250.0 | 0.852 | sparse_target_replacement_250 | True | catalyst_loading;cure_temperature_c;post_cure_temperature_c |
| 10 | validation_014_process_completion | process_completion | 195.0 | 0.472 | vae_latent_local_search | True | cure_temperature_c;co_reactant_stoichiometry;post_cure_temperature_c |
| 11 | validation_017_process_completion | process_completion | 250.0 | 0.553 | sparse_target_replacement_250 | True | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h |
| 12 | validation_018_process_completion | process_completion | 195.0 | 0.584 | pievo_latent_local_search_selected | True | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h |

## Gate Rules

- `process_completion_now` 是当前唯一能立即推进高权重证据链的任务类型。
- `blocked_until_process_completion` 任务必须等对应 `dependency_request_id` 完成并获批后，才能填写 result intake。
- `execution_status=planned_not_completed` 表示这里只是排程，不得当作完成结果或 observation ledger。

# Process Approval Reviewer Checklist

本文档把 process approval template 转成可审查行动清单。它不代表人工已经批准，也不产生 Tg observation。

## Summary

| item | value |
| --- | ---: |
| input_approval_rows | 12 |
| checklist_rows | 12 |
| ready_for_human_review_rows | 12 |
| already_submitted_rows | 0 |
| accepted_process_approval_rows | 0 |
| can_unlock_high_fidelity_protocol_rows | 12 |
| downstream_protocol_rows | 13 |
| approval_gate_status | awaiting_human_process_approval |
| max_downstream_authority_weight_if_completed | 3.0 |
| creates_observation | False |
| evidence_level | process_approval_reviewer_checklist_not_observation |
| checklist_path | artifacts/trail/human_review/process_approval_reviewer_checklist.csv |
| summary_path | artifacts/trail/human_review/process_approval_reviewer_checklist_summary.json |
| report_path | reports/process_approval_reviewer_checklist.md |

## Target Counts

| item | rows |
| --- | ---: |
| 195.0 | 4 |
| 250.0 | 8 |

## Process Template Counts

| item | rows |
| --- | ---: |
| epoxy_amine_thermal_cure | 5 |
| epoxy_anhydride_catalyzed_cure | 4 |
| anhydride_amine_imidization | 2 |
| maleimide_addition_or_copolymerization | 1 |

## Suggested Field Frequency

| item | rows |
| --- | ---: |
| mix_temperature_c | 6 |
| cure_temperature_c | 10 |
| cure_time_h | 6 |
| post_cure_temperature_c | 10 |
| post_cure_time_h | 6 |
| catalyst_loading | 4 |
| solvent | 2 |
| imidization_temperature_c | 2 |
| imidization_time_h | 2 |
| co_reactant_stoichiometry | 1 |

## Review Rows

| rank | approval | target | origin | template | downstream protocols | status |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | approval_validation_017_process_completion | 250.0 | sparse_target_replacement_250 | epoxy_amine_thermal_cure | 1 | awaiting_human_review |
| 2 | approval_validation_010_process_completion | 250.0 | sparse_target_replacement_250 | epoxy_anhydride_catalyzed_cure | 1 | awaiting_human_review |
| 3 | approval_validation_007_process_completion | 250.0 | sparse_target_replacement_250 | epoxy_anhydride_catalyzed_cure | 1 | awaiting_human_review |
| 4 | approval_validation_002_process_completion | 250.0 | sparse_target_replacement_250 | anhydride_amine_imidization | 1 | awaiting_human_review |
| 5 | approval_validation_001_process_completion | 250.0 | sparse_target_replacement_250 | epoxy_anhydride_catalyzed_cure | 1 | awaiting_human_review |
| 6 | approval_validation_006_process_completion | 250.0 | sparse_target_replacement_250 | epoxy_amine_thermal_cure | 1 | awaiting_human_review |
| 7 | approval_validation_008_process_completion | 250.0 | sparse_target_replacement_250 | epoxy_amine_thermal_cure | 1 | awaiting_human_review |
| 8 | approval_validation_003_process_completion | 250.0 | sparse_target_replacement_250 | anhydride_amine_imidization | 1 | awaiting_human_review |
| 9 | approval_validation_014_process_completion | 195.0 | vae_latent_local_search | maleimide_addition_or_copolymerization | 1 | awaiting_human_review |
| 10 | approval_validation_011_process_completion | 195.0 | pievo_latent_local_search_selected | epoxy_amine_thermal_cure | 1 | awaiting_human_review |
| 11 | approval_validation_018_process_completion | 195.0 | pievo_latent_local_search_selected | epoxy_anhydride_catalyzed_cure | 2 | awaiting_human_review |
| 12 | approval_validation_009_process_completion | 195.0 | pievo_latent_local_search_selected | epoxy_amine_thermal_cure | 1 | awaiting_human_review |

## Gate

- 审批人必须填写 `approval_decision`、`process_ready`、`reviewer_approved`、`reviewer_id` 和 `review_date`。
- 通过审批只会解锁 downstream high-fidelity protocol；不会直接写入 observation ledger。
- 高保真或真实结果仍必须单独通过 validation result intake 和 active evidence gate。

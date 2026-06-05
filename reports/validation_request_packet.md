# Validation Request Packet

本文档把实验前验证计划转成可分派 request queue。它不是 observation ledger；只有任务完成、工艺字段补齐且人工批准后，结果才可以写入高权重 observation ledger。

## Summary

| item | value |
| --- | ---: |
| input_plan_rows | 30 |
| request_rows | 55 |
| blocked_by_process_completion_rows | 25 |
| max_authority_weight_if_completed | 3.0 |
| real_dsc_request_rows | 0 |
| high_fidelity_request_rows | 25 |
| process_completion_request_rows | 30 |
| request_path | artifacts/trail/human_review/validation_request_queue.csv |
| summary_path | artifacts/trail/human_review/validation_request_summary.json |
| report_path | reports/validation_request_packet.md |

## Task Type Distribution

| item | rows |
| --- | ---: |
| process_completion | 30 |
| high_fidelity_validation | 25 |

## Target Tg Distribution

| item | rows |
| --- | ---: |
| 195.0 | 29 |
| 250.0 | 26 |

## Expected Observation Source Distribution

| item | rows |
| --- | ---: |
| none | 30 |
| high_fidelity_simulation | 25 |

## Candidate Origin Distribution

| item | rows |
| --- | ---: |
| sparse_target_replacement_250 | 26 |
| vae_latent_local_search | 18 |
| pievo_latent_local_search_selected | 6 |
| pievo_ensemble_guard_selected | 3 |
| expanded_inventory_replacement | 2 |

## Top Requests

| rank | task | target Tg (C) | distance (C) | origin | source if completed | blocked | required inputs | gate |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | process_completion | 250.0 | 0.034 | sparse_target_replacement_250 | none | False | catalyst_loading;cure_temperature_c;post_cure_temperature_c | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 2 | process_completion | 250.0 | 0.111 | sparse_target_replacement_250 | none | False | solvent;imidization_temperature_c;imidization_time_h | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 3 | high_fidelity_validation | 250.0 | 0.034 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | append to observation ledger only after process fields are complete and reviewer approves |
| 4 | process_completion | 250.0 | 0.554 | sparse_target_replacement_250 | none | False | solvent;imidization_temperature_c;imidization_time_h | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 5 | high_fidelity_validation | 250.0 | 0.111 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check;imidization_protocol_review | append to observation ledger only after process fields are complete and reviewer approves |
| 6 | process_completion | 195.0 | 0.200 | vae_latent_local_search | none | False | trimerization_temperature_c;catalyst_loading;post_cure_temperature_c | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 7 | high_fidelity_validation | 250.0 | 0.554 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check;imidization_protocol_review | append to observation ledger only after process fields are complete and reviewer approves |
| 8 | process_completion | 195.0 | 0.373 | vae_latent_local_search | none | False | trimerization_temperature_c;catalyst_loading;post_cure_temperature_c | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 9 | process_completion | 250.0 | 0.384 | sparse_target_replacement_250 | none | False | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 10 | process_completion | 250.0 | 0.767 | sparse_target_replacement_250 | none | False | catalyst_loading;cure_temperature_c;post_cure_temperature_c | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 11 | process_completion | 250.0 | 0.595 | sparse_target_replacement_250 | none | False | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 12 | process_completion | 195.0 | 0.119 | pievo_latent_local_search_selected | none | False | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 13 | high_fidelity_validation | 250.0 | 0.384 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | append to observation ledger only after process fields are complete and reviewer approves |
| 14 | process_completion | 250.0 | 0.852 | sparse_target_replacement_250 | none | False | catalyst_loading;cure_temperature_c;post_cure_temperature_c | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 15 | process_completion | 195.0 | 0.059 | pievo_latent_local_search_selected | none | False | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 16 | process_completion | 195.0 | 0.885 | pievo_ensemble_guard_selected | none | False | catalyst_loading;cure_temperature_c;post_cure_temperature_c | does not create observation; unlocks high_fidelity_simulation or real_dsc only after human approval |
| 17 | high_fidelity_validation | 250.0 | 0.767 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | append to observation ledger only after process fields are complete and reviewer approves |
| 18 | high_fidelity_validation | 250.0 | 0.595 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | append to observation ledger only after process fields are complete and reviewer approves |
| 19 | high_fidelity_validation | 195.0 | 0.119 | pievo_latent_local_search_selected | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | append to observation ledger only after process fields are complete and reviewer approves |
| 20 | high_fidelity_validation | 250.0 | 0.852 | sparse_target_replacement_250 | high_fidelity_simulation | True | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | append to observation ledger only after process fields are complete and reviewer approves |

## Gate Rules

- `process_completion` request 只补工艺记录，不产生 Tg observation。
- `high_fidelity_validation` request 完成后也必须通过工艺完整性和人工批准，才能以 `high_fidelity_simulation` 写入 observation ledger。
- `real_dsc_planning` 只有在工艺和人工质量门已经满足时才生成；当前若为 0，说明没有候选可直接排 DSC。

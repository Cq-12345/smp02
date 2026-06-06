# High-fidelity Protocol Packet

本文档把 high-fidelity validation request 转成方法协议包。它不是高保真结果，也不会写入 observation ledger。

## Summary

| item | value |
| --- | ---: |
| input_request_rows | 55 |
| high_fidelity_protocol_rows | 25 |
| ready_protocol_rows | 0 |
| blocked_protocol_rows | 25 |
| process_approval_unblocked_rows | 0 |
| max_authority_weight_if_completed | 3.0 |
| approval_gate_status | awaiting_human_process_approval |
| evidence_level | high_fidelity_protocol_template_not_observation |
| packet_path | artifacts/trail/human_review/high_fidelity_protocol_packet.csv |
| summary_path | artifacts/trail/human_review/high_fidelity_protocol_summary.json |
| report_path | reports/high_fidelity_protocol_packet.md |

## Target Counts

| item | rows |
| --- | ---: |
| 195.0 | 12 |
| 250.0 | 13 |

## Candidate Origin Counts

| item | rows |
| --- | ---: |
| sparse_target_replacement_250 | 13 |
| vae_latent_local_search | 7 |
| pievo_latent_local_search_selected | 3 |
| pievo_ensemble_guard_selected | 1 |
| expanded_inventory_replacement | 1 |

## Method Frequency

| item | rows |
| --- | ---: |
| process_feasibility_review | 25 |
| model_ensemble_recheck | 25 |
| high_fidelity_simulation_or_expanded_model_ensemble | 25 |
| thermal_stability_pre_screen | 13 |
| target_specific_literature_check | 13 |
| imidization_protocol_review | 4 |
| trimerization_catalyst_review | 2 |

## Risk Flag Frequency

| item | rows |
| --- | ---: |
| process_incomplete | 25 |
| high_predictor_sigma | 23 |
| high_ood_penalty | 22 |
| high_tg_target | 13 |
| sparse_target_origin | 13 |
| new_component | 14 |

## Top Protocols

| rank | request | target | origin | methods | status |
| ---: | --- | ---: | --- | --- | --- |
| 1 | validation_001_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | blocked_pending_process_approval |
| 2 | validation_002_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check;imidization_protocol_review | blocked_pending_process_approval |
| 3 | validation_003_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check;imidization_protocol_review | blocked_pending_process_approval |
| 4 | validation_006_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | blocked_pending_process_approval |
| 5 | validation_007_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | blocked_pending_process_approval |
| 6 | validation_008_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | blocked_pending_process_approval |
| 7 | validation_009_high_fidelity_validation | 195.0 | pievo_latent_local_search_selected | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |
| 8 | validation_010_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | blocked_pending_process_approval |
| 9 | validation_011_high_fidelity_validation | 195.0 | pievo_latent_local_search_selected | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |
| 10 | validation_014_high_fidelity_validation | 195.0 | vae_latent_local_search | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |
| 11 | validation_016_high_fidelity_validation | 195.0 | vae_latent_local_search | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |
| 12 | validation_017_high_fidelity_validation | 250.0 | sparse_target_replacement_250 | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble;thermal_stability_pre_screen;target_specific_literature_check | blocked_pending_process_approval |
| 13 | validation_018_high_fidelity_validation | 195.0 | pievo_latent_local_search_selected | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |
| 14 | validation_019_high_fidelity_validation | 195.0 | vae_latent_local_search | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |
| 15 | validation_020_high_fidelity_validation | 195.0 | pievo_ensemble_guard_selected | process_feasibility_review;model_ensemble_recheck;high_fidelity_simulation_or_expanded_model_ensemble | blocked_pending_process_approval |

## Gate

- `blocked_pending_process_approval` 表示仍等待 process approval，不允许启动高保真结果 intake。
- `ready_for_high_fidelity_execution` 也不等于 observation；它只允许后续填写 validation result。
- 任何 Tg 数值仍必须通过 validation result intake、observation ledger 和 active evidence gate。

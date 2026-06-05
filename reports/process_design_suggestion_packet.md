# Process Design Suggestion Packet

本文档把 process completion packet 进一步转成知识模板驱动的工艺建议。它不是实测工艺，不是文献复现，也不会产生 observation。

## Summary

| item | value |
| --- | ---: |
| input_packet_rows | 12 |
| suggestion_rows | 12 |
| high_tg_rows | 8 |
| high_sigma_rows | 5 |
| human_review_required_rows | 12 |
| can_unlock_observation_after_human_approval_rows | 12 |
| suggested_process_record_pass_rows | 12 |
| suggested_process_fields_complete_rows | 12 |
| suggested_ready_for_active_ledger_rows | 0 |
| evidence_level | knowledge_template_suggestion_not_observation |

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

## Candidate Origin Counts

| item | rows |
| --- | ---: |
| sparse_target_replacement_250 | 8 |
| pievo_latent_local_search_selected | 3 |
| vae_latent_local_search | 1 |

## Suggested Field Frequency

| item | rows |
| --- | ---: |
| catalyst_loading | 4 |
| cure_temperature_c | 10 |
| post_cure_temperature_c | 10 |
| mix_temperature_c | 6 |
| cure_time_h | 6 |
| post_cure_time_h | 6 |
| solvent | 2 |
| imidization_temperature_c | 2 |
| imidization_time_h | 2 |
| co_reactant_stoichiometry | 1 |

## Immediate Suggestions

| rank | request | target | template | suggested inputs | risk flags | unlock after approval |
| ---: | --- | ---: | --- | --- | --- | --- |
| 1 | validation_001_process_completion | 250.0 | epoxy_anhydride_catalyzed_cure | catalyst_loading=0.5-2.0 wt% tertiary amine or imidazole; verify equivalent basis;cure_temperature_c=170.0;post_cure_temperature_c=230.0 | high_tg_process_window;high_predictor_sigma;sparse_target_candidate_origin;catalyst_sensitive_template | True |
| 2 | validation_011_process_completion | 195.0 | epoxy_amine_thermal_cure | mix_temperature_c=60.0;cure_temperature_c=120.0;cure_time_h=2.0;post_cure_temperature_c=180.0;post_cure_time_h=2.0 | standard_human_review | True |
| 3 | validation_002_process_completion | 250.0 | anhydride_amine_imidization | solvent=dry NMP or DMAc; verify monomer solubility before scale-up;imidization_temperature_c=220.0;imidization_time_h=2.0 | high_tg_process_window;high_predictor_sigma;sparse_target_candidate_origin;solvent_and_imidization_sensitive_template | True |
| 4 | validation_009_process_completion | 195.0 | epoxy_amine_thermal_cure | mix_temperature_c=60.0;cure_temperature_c=120.0;cure_time_h=2.0;post_cure_temperature_c=180.0;post_cure_time_h=2.0 | standard_human_review | True |
| 5 | validation_003_process_completion | 250.0 | anhydride_amine_imidization | solvent=dry NMP or DMAc; verify monomer solubility before scale-up;imidization_temperature_c=220.0;imidization_time_h=2.0 | high_tg_process_window;sparse_target_candidate_origin;solvent_and_imidization_sensitive_template | True |
| 6 | validation_006_process_completion | 250.0 | epoxy_amine_thermal_cure | mix_temperature_c=60.0;cure_temperature_c=140.0;cure_time_h=2.0;post_cure_temperature_c=220.0;post_cure_time_h=2.0 | high_tg_process_window;sparse_target_candidate_origin | True |
| 7 | validation_008_process_completion | 250.0 | epoxy_amine_thermal_cure | mix_temperature_c=60.0;cure_temperature_c=140.0;cure_time_h=2.0;post_cure_temperature_c=220.0;post_cure_time_h=2.0 | high_tg_process_window;sparse_target_candidate_origin | True |
| 8 | validation_007_process_completion | 250.0 | epoxy_anhydride_catalyzed_cure | catalyst_loading=0.5-2.0 wt% tertiary amine or imidazole; verify equivalent basis;cure_temperature_c=170.0;post_cure_temperature_c=230.0 | high_tg_process_window;high_predictor_sigma;sparse_target_candidate_origin;catalyst_sensitive_template | True |
| 9 | validation_010_process_completion | 250.0 | epoxy_anhydride_catalyzed_cure | catalyst_loading=0.5-2.0 wt% tertiary amine or imidazole; verify equivalent basis;cure_temperature_c=170.0;post_cure_temperature_c=230.0 | high_tg_process_window;high_predictor_sigma;sparse_target_candidate_origin;catalyst_sensitive_template | True |
| 10 | validation_014_process_completion | 195.0 | maleimide_addition_or_copolymerization | cure_temperature_c=160.0;co_reactant_stoichiometry=1:1 functional equivalent starting point;post_cure_temperature_c=220.0 | standard_human_review | True |
| 11 | validation_017_process_completion | 250.0 | epoxy_amine_thermal_cure | mix_temperature_c=60.0;cure_temperature_c=140.0;cure_time_h=2.0;post_cure_temperature_c=220.0;post_cure_time_h=2.0 | high_tg_process_window;high_predictor_sigma;sparse_target_candidate_origin | True |
| 12 | validation_018_process_completion | 195.0 | epoxy_anhydride_catalyzed_cure | mix_temperature_c=80.0;cure_temperature_c=150.0;cure_time_h=2.0;post_cure_temperature_c=200.0;post_cure_time_h=2.0;catalyst_loading=0.5-2.0 wt% tertiary amine or imidazole; verify equivalent basis | catalyst_sensitive_template | True |

## Gate

- `suggested_process_fields_complete_rows` 只表示知识模板把字段草案填全，不代表实验已完成。
- 所有 suggested process records 保持 `review_status=needs_human_review`。
- `suggested_ready_for_active_ledger_rows` 必须保持 0；只有人工批准且真实/高保真/文献 observation 通过后，才能进入 active evidence ledger。

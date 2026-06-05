# Human Experiment Review Queue

本文档把 TODO 中“人工闭环、真实实验结果迭代优化”推进为可运行的候选复核队列。当前所有输入仍是 surrogate / Harness / PiEvo evidence，不会自动升级为真实 DSC 或 active high-authority ledger。

## 输出文件

- Review queue: `artifacts/trail/human_review/human_experiment_review_queue.csv`
- Draft process records: `artifacts/trail/human_review/draft_process_records.csv`
- Draft process ledger: `artifacts/trail/human_review/draft_process_record_ledger.csv`
- Summary: `artifacts/trail/human_review/human_experiment_review_queue_summary.json`
- Report: `reports/human_experiment_review_queue.md`

## Queue Summary

| item | value |
| --- | ---: |
| input_candidates | 58 |
| deduplicated_candidates | 43 |
| queue_rows | 30 |
| ready_for_active_ledger_rows | 0 |
| mean_target_distance_c | 1.4210625575319018 |
| best_target_distance_c | 0.0590323055353962 |
| draft_process_record_pass_rows | 30 |
| draft_ready_for_active_ledger_rows | 0 |
| queue_path | artifacts/trail/human_review/human_experiment_review_queue.csv |
| draft_process_records_path | artifacts/trail/human_review/draft_process_records.csv |
| draft_process_record_ledger_path | artifacts/trail/human_review/draft_process_record_ledger.csv |

## Draft Process Ledger Gate

| item | value |
| --- | ---: |
| input_rows | 30 |
| process_record_pass_rows | 30 |
| ready_for_active_ledger_rows | 0 |
| process_incomplete_rows | 30 |
| mean_target_distance_c | 1.4210625575319114 |

## Top Review Items

| rank | Tg (C) | distance (C) | sigma (C) | template | missing process fields | priority | action |
| ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 195.20 | 0.200 | 37.34 | cyanate_ester_triazine_cure | trimerization_temperature_c;catalyst_loading;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 2 | 194.63 | 0.373 | 37.49 | cyanate_ester_triazine_cure | trimerization_temperature_c;catalyst_loading;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 3 | 195.89 | 0.885 | 31.74 | epoxy_anhydride_catalyzed_cure | catalyst_loading;cure_temperature_c;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 4 | 195.57 | 0.569 | 37.69 | epoxy_amine_thermal_cure | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 5 | 195.12 | 0.119 | 46.46 | epoxy_amine_thermal_cure | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 6 | 194.08 | 0.922 | 48.12 | isocyanate_urethane_urea | moisture_control;nco_index;cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 7 | 195.72 | 0.721 | 62.53 | epoxy_anhydride_catalyzed_cure | catalyst_loading;cure_temperature_c;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 8 | 195.59 | 0.595 | 73.07 | maleimide_addition_or_copolymerization | cure_temperature_c;co_reactant_stoichiometry;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 9 | 195.58 | 0.584 | 48.52 | epoxy_amine_thermal_cure | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 10 | 195.69 | 0.689 | 73.87 | maleimide_addition_or_copolymerization | cure_temperature_c;co_reactant_stoichiometry;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 11 | 195.06 | 0.059 | 57.64 | epoxy_amine_thermal_cure | mix_temperature_c;cure_temperature_c;cure_time_h;post_cure_temperature_c;post_cure_time_h | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 12 | 195.47 | 0.472 | 70.25 | maleimide_addition_or_copolymerization | cure_temperature_c;co_reactant_stoichiometry;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 13 | 194.04 | 0.959 | 55.74 | epoxy_anhydride_catalyzed_cure | catalyst_loading;cure_temperature_c;post_cure_temperature_c | process_design_for_dsc | complete missing process fields, then decide whether to schedule synthesis/DSC. |
| 14 | 194.48 | 0.523 | 96.19 | cyanate_ester_triazine_cure | trimerization_temperature_c;catalyst_loading;post_cure_temperature_c | high_fidelity_before_dsc | run high-fidelity or ensemble review before committing DSC resources. |
| 15 | 193.49 | 1.506 | 90.91 | anhydride_amine_imidization | solvent;imidization_temperature_c;imidization_time_h | high_fidelity_before_dsc | run high-fidelity or ensemble review before committing DSC resources. |

## 解释

- 这个队列只决定哪些 surrogate 候选值得人工补工艺条件、做高保真复核或排实验优先级。
- `draft_process_record_ledger.csv` 应保持 `ready_for_active_ledger=false`，直到人类补齐工艺字段并显式批准。
- 真实 DSC 或文献复现实验完成后，应写入 observation ledger，并用更高 authority weight 更新 PiEvo posterior。

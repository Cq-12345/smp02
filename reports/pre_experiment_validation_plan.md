# Pre-experiment Validation Plan

本文档把人工复核队列推进为高保真/真实实验前的验证计划。它不会把 surrogate 候选升级为真实 observation，只给出人工补工艺和高保真复核顺序。

## Summary

| item | value |
| --- | ---: |
| input_review_rows | 30 |
| plan_rows | 30 |
| process_completion_required_rows | 30 |
| high_fidelity_required_rows | 25 |
| dsc_ready_without_process_completion_rows | 0 |
| best_target_distance_c | 0.0342827100285205 |
| best_validation_score | 0.9553479867260357 |
| plan_path | artifacts/trail/human_review/pre_experiment_validation_plan.csv |
| summary_path | artifacts/trail/human_review/pre_experiment_validation_plan_summary.json |
| report_path | reports/pre_experiment_validation_plan.md |

## Target Tg Distribution

| item | rows |
| --- | ---: |
| 195.0 | 17 |
| 250.0 | 13 |

## Validation Lane Distribution

| item | rows |
| --- | ---: |
| process_plus_high_fidelity | 25 |
| process_completion_before_dsc | 5 |

## Candidate Origin Distribution

| item | rows |
| --- | ---: |
| sparse_target_replacement_250 | 13 |
| vae_latent_local_search | 11 |
| pievo_latent_local_search_selected | 3 |
| pievo_ensemble_guard_selected | 2 |
| expanded_inventory_replacement | 1 |

## Top Validation Items

| rank | target Tg (C) | Tg (C) | distance (C) | sigma (C) | lane | origin | template | flags | action |
| ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 250.0 | 249.97 | 0.034 | 77.99 | process_plus_high_fidelity | sparse_target_replacement_250 | epoxy_anhydride_catalyzed_cure | process_incomplete;high_predictor_sigma;high_ood_penalty;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 2 | 250.0 | 249.89 | 0.111 | 83.05 | process_plus_high_fidelity | sparse_target_replacement_250 | anhydride_amine_imidization | process_incomplete;high_predictor_sigma;high_ood_penalty;new_component;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 3 | 250.0 | 250.55 | 0.554 | 64.77 | process_plus_high_fidelity | sparse_target_replacement_250 | anhydride_amine_imidization | process_incomplete;high_predictor_sigma;new_component;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 4 | 195.0 | 195.20 | 0.200 | 37.34 | process_completion_before_dsc | vae_latent_local_search | cyanate_ester_triazine_cure | process_incomplete | complete process fields and feasibility review before scheduling DSC. |
| 5 | 195.0 | 194.63 | 0.373 | 37.49 | process_completion_before_dsc | vae_latent_local_search | cyanate_ester_triazine_cure | process_incomplete | complete process fields and feasibility review before scheduling DSC. |
| 6 | 250.0 | 249.62 | 0.384 | 74.65 | process_plus_high_fidelity | sparse_target_replacement_250 | epoxy_amine_thermal_cure | process_incomplete;high_predictor_sigma;high_ood_penalty;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 7 | 250.0 | 250.77 | 0.767 | 85.46 | process_plus_high_fidelity | sparse_target_replacement_250 | epoxy_anhydride_catalyzed_cure | process_incomplete;high_predictor_sigma;high_ood_penalty;new_component;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 8 | 250.0 | 249.41 | 0.595 | 73.70 | process_plus_high_fidelity | sparse_target_replacement_250 | epoxy_amine_thermal_cure | process_incomplete;high_predictor_sigma;high_ood_penalty;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 9 | 195.0 | 195.12 | 0.119 | 46.46 | process_plus_high_fidelity | pievo_latent_local_search_selected | epoxy_amine_thermal_cure | process_incomplete;high_ood_penalty;new_component | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 10 | 250.0 | 250.85 | 0.852 | 85.72 | process_plus_high_fidelity | sparse_target_replacement_250 | epoxy_anhydride_catalyzed_cure | process_incomplete;high_predictor_sigma;high_ood_penalty;new_component;high_tg_target;sparse_target_origin | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 11 | 195.0 | 195.06 | 0.059 | 57.64 | process_plus_high_fidelity | pievo_latent_local_search_selected | epoxy_amine_thermal_cure | process_incomplete;high_predictor_sigma;high_ood_penalty;new_component | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 12 | 195.0 | 195.89 | 0.885 | 31.74 | process_completion_before_dsc | pievo_ensemble_guard_selected | epoxy_anhydride_catalyzed_cure | process_incomplete;new_component | complete process fields and feasibility review before scheduling DSC. |
| 13 | 195.0 | 195.57 | 0.569 | 37.69 | process_completion_before_dsc | vae_latent_local_search | epoxy_amine_thermal_cure | process_incomplete | complete process fields and feasibility review before scheduling DSC. |
| 14 | 195.0 | 195.47 | 0.472 | 70.25 | process_plus_high_fidelity | vae_latent_local_search | maleimide_addition_or_copolymerization | process_incomplete;high_predictor_sigma;high_ood_penalty;new_component | complete process fields, run high-fidelity/model-ensemble validation, then decide whether to schedule DSC. |
| 15 | 195.0 | 194.08 | 0.922 | 48.12 | process_completion_before_dsc | vae_latent_local_search | isocyanate_urethane_urea | process_incomplete | complete process fields and feasibility review before scheduling DSC. |

## Gate Rules

- `process_completion_required=true` 表示仍需人工补齐工艺字段，不能进入 active high-authority ledger。
- `high_fidelity_required=true` 表示预测不确定性、高 Tg 稀疏目标或 OOD 风险较高，应先做高保真/集成模型复核。
- 只有人工补齐工艺、真实或高保真观测完成并显式批准后，才允许写入高权重 observation ledger。

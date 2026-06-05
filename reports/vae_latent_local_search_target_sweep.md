# VAE Latent Local Search Target Sweep

本文档把 VAE latent local search 从单一 195 C 扩展到多个目标 Tg。latent proposals 保持同一批 VAE-neighborhood 候选；每个目标都会重新计算 predictor/Harness target window、observation ledger reward，并作为 PiEvo-faithful external history 运行。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM-GPR，不涉及暂缓的商品级组分或聚合物超图表示。

## Artifacts

- Latent/evaluation root: `artifacts/trail/generation/vae_latent_local_search_target_sweep`
- PiEvo output root: `artifacts/pievo_faithful_vae_latent_local_search_target_sweep`

## Aggregate

| item | value |
| --- | ---: |
| targets | 4 |
| target_values | [190.0, 195.0, 200.0, 250.0] |
| output_root | artifacts/trail/generation/vae_latent_local_search_target_sweep |
| pievo_output_root | artifacts/pievo_faithful_vae_latent_local_search_target_sweep |
| total_latent_input_proposals | 800 |
| total_latent_harness_pass | 126 |
| total_latent_observations | 126 |
| total_pievo_external_rows | 126 |
| all_pievo_selected_pass | True |
| all_pievo_selected_within_guard | True |
| best_target_tg_c | 190.0 |
| best_selected_predicted_tg_mean_c | 189.99761785234935 |
| best_selected_target_distance_c | 0.0023821476506213 |
| best_target_map_principle | maleimide_rigid_network |

## Target Summary

| target Tg (C) | latent pass | latent best dist (C) | literature template pass | external rows | PiEvo rounds | best selected Tg (C) | best selected dist (C) | posterior entropy | MAP principle | MAP posterior | pass |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |
| 190.0 | 38 | 0.167 | 4 | 38 | 4 | 190.00 | 0.002 | 3.290 | maleimide_rigid_network | 0.105 | True |
| 195.0 | 42 | 0.200 | 7 | 42 | 4 | 195.06 | 0.059 | 3.353 | reaction_839cd29ef5d7 | 0.074 | True |
| 200.0 | 41 | 0.305 | 10 | 41 | 4 | 199.96 | 0.043 | 3.200 | sulfone_diamine_rigidity | 0.078 | True |
| 250.0 | 5 | 1.084 | 1 | 5 | 4 | 249.49 | 0.511 | 3.523 | reaction_a5dd26ae10ad | 0.037 | True |

## Interpretation

- 这一步检验“真实 Tg 不固定”：VAE latent local search 不是只服务 195 C，而是对每个目标重新计算 target window、reward 和 PiEvo posterior。
- latent-neighborhood 排序本身不等于物理规律；它只是给 replacement proposal 提供一个 VAE 表示空间邻域信号，所有结果仍要经过 predictor、Harness、PiEvo 和人工审核。
- 若某个目标的 latent pass 很少，说明同一批 latent proposals 对该目标覆盖不足，下一轮应改变 source candidate pool 或按目标重新运行 latent retrieval。
- 当前是 smoke 规模；后续可以把该 sweep 的失败原因回流给 strategy bandit，或与 Tanimoto replacement、rule-template 和 trained SFT/flow projection 做目标级预算对比。

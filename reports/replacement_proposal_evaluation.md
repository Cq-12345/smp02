# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 120 |
| rebuilt_formulas | 107 |
| scored_formulas | 107 |
| harness_pass | 10 |
| rejected_proposals | 13 |
| best_distance_c | 0.377581 |
| within_1c | 4 |
| within_5c | 10 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 10 |

目标 Tg: 195.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 194.62 | 0.38 | 134.31 | a | 0.560 | 氰酸酯-胺共反应。 |
| 2 | 195.51 | 0.51 | 37.66 | b | 0.375 | 环氧-伯胺开环固化。 |
| 3 | 194.31 | 0.69 | 37.47 | b | 0.471 | 氰酸酯-胺共反应。 |
| 4 | 194.22 | 0.78 | 48.07 | b | 0.375 | 异氰酸酯-伯胺形成聚脲。 |
| 5 | 196.21 | 1.21 | 12.38 | b | 0.471 | 环氧-伯胺开环固化。 |
| 6 | 193.31 | 1.69 | 62.97 | b | 0.897 | 环氧-伯胺开环固化。 |
| 7 | 192.42 | 2.58 | 52.41 | b | 0.323 | 异氰酸酯-伯胺形成聚脲。 |
| 8 | 197.73 | 2.73 | 37.92 | b | 0.323 | 环氧-伯胺开环固化。 |
| 9 | 198.27 | 3.27 | 103.61 | b | 0.560 | 环氧-伯胺开环固化。 |
| 10 | 190.83 | 4.17 | 36.01 | a | 0.705 | 环氧-伯胺开环固化。 |

## Rejection Reasons

- replacement_formula_failed_reaction_or_ratio_constraints: 13

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

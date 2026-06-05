# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 200 |
| rebuilt_formulas | 200 |
| scored_formulas | 200 |
| harness_pass | 18 |
| rejected_proposals | 0 |
| best_distance_c | 0.20046 |
| within_1c | 6 |
| within_5c | 18 |
| literature_template_scored | 29 |
| literature_template_harness_pass | 3 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 18 |

目标 Tg: 195.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 195.20 | 0.20 | 37.34 | b | 0.471 | 氰酸酯-胺共反应。 source=library |
| 2 | 194.63 | 0.37 | 37.49 | b | 0.471 | 氰酸酯-胺共反应。 source=library |
| 3 | 194.55 | 0.45 | 134.25 | a | 0.560 | 氰酸酯-胺共反应。 source=library |
| 4 | 194.48 | 0.52 | 96.19 | b | 0.630 | 氰酸酯-胺共反应。 source=literature_template |
| 5 | 195.57 | 0.57 | 37.69 | b | 0.375 | 环氧-伯胺开环固化。 source=library |
| 6 | 194.08 | 0.92 | 48.12 | b | 0.375 | 异氰酸酯-伯胺形成聚脲。 source=library |
| 7 | 196.29 | 1.29 | 12.38 | b | 0.471 | 环氧-伯胺开环固化。 source=library |
| 8 | 193.53 | 1.47 | 132.78 | b | 0.520 | 异氰酸酯-伯胺形成聚脲。 source=generated |
| 9 | 193.18 | 1.82 | 62.88 | b | 0.897 | 环氧-伯胺开环固化。 source=library |
| 10 | 196.88 | 1.88 | 62.43 | b | 0.895 | 环氧-伯胺开环固化。 source=library |
| 11 | 192.77 | 2.23 | 68.27 | b | 0.312 | 环氧-伯胺开环固化。 source=generated |
| 12 | 192.56 | 2.44 | 98.04 | a | 0.442 | 环氧-伯胺开环固化。 source=library |
| 13 | 197.64 | 2.64 | 49.81 | a | 0.538 | 异氰酸酯-伯胺形成聚脲。 source=literature_template |
| 14 | 192.28 | 2.72 | 52.48 | b | 0.323 | 异氰酸酯-伯胺形成聚脲。 source=library |
| 15 | 197.80 | 2.80 | 37.96 | b | 0.323 | 环氧-伯胺开环固化。 source=library |
| 16 | 198.32 | 3.32 | 103.67 | b | 0.560 | 环氧-伯胺开环固化。 source=library |
| 17 | 191.53 | 3.47 | 101.68 | a | 0.562 | 氰酸酯-胺共反应。 source=literature_template |
| 18 | 190.99 | 4.01 | 35.99 | a | 0.705 | 环氧-伯胺开环固化。 source=library |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

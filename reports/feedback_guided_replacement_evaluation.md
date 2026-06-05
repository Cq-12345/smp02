# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 120 |
| rebuilt_formulas | 120 |
| scored_formulas | 120 |
| harness_pass | 11 |
| rejected_proposals | 0 |
| best_distance_c | 0.373243 |
| within_1c | 4 |
| within_5c | 11 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 11 |

目标 Tg: 195.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 194.63 | 0.37 | 37.49 | b | 0.471 | 氰酸酯-胺共反应。 |
| 2 | 194.55 | 0.45 | 134.25 | a | 0.560 | 氰酸酯-胺共反应。 |
| 3 | 195.57 | 0.57 | 37.69 | b | 0.375 | 环氧-伯胺开环固化。 |
| 4 | 194.08 | 0.92 | 48.12 | b | 0.375 | 异氰酸酯-伯胺形成聚脲。 |
| 5 | 196.29 | 1.29 | 12.38 | b | 0.471 | 环氧-伯胺开环固化。 |
| 6 | 193.60 | 1.40 | 98.37 | b | 0.368 | 氰酸酯-胺共反应。 |
| 7 | 193.18 | 1.82 | 62.88 | b | 0.897 | 环氧-伯胺开环固化。 |
| 8 | 192.28 | 2.72 | 52.48 | b | 0.323 | 异氰酸酯-伯胺形成聚脲。 |
| 9 | 197.80 | 2.80 | 37.96 | b | 0.323 | 环氧-伯胺开环固化。 |
| 10 | 198.32 | 3.32 | 103.67 | b | 0.560 | 环氧-伯胺开环固化。 |
| 11 | 190.99 | 4.01 | 35.99 | a | 0.705 | 环氧-伯胺开环固化。 |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

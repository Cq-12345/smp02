# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 120 |
| rebuilt_formulas | 120 |
| scored_formulas | 120 |
| harness_pass | 13 |
| rejected_proposals | 0 |
| best_distance_c | 0.994115 |
| within_1c | 1 |
| within_5c | 13 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 13 |

目标 Tg: 190.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 190.99 | 0.99 | 35.99 | a | 0.705 | 环氧-伯胺开环固化。 |
| 2 | 187.85 | 2.15 | 65.17 | b | 0.930 | 环氧-伯胺开环固化。 |
| 3 | 187.80 | 2.20 | 72.96 | b | 0.162 | 环氧-酸酐固化，常需催化剂。 |
| 4 | 192.28 | 2.28 | 52.48 | b | 0.323 | 异氰酸酯-伯胺形成聚脲。 |
| 5 | 186.93 | 3.07 | 71.88 | a | 0.306 | 异氰酸酯-伯胺形成聚脲。 |
| 6 | 193.18 | 3.18 | 62.88 | b | 0.897 | 环氧-伯胺开环固化。 |
| 7 | 186.75 | 3.25 | 58.71 | a | 0.500 | 环氧-伯胺开环固化。 |
| 8 | 186.63 | 3.37 | 73.00 | a | 0.471 | 环氧-伯胺开环固化。 |
| 9 | 193.60 | 3.60 | 98.37 | b | 0.368 | 氰酸酯-胺共反应。 |
| 10 | 194.08 | 4.08 | 48.12 | b | 0.375 | 异氰酸酯-伯胺形成聚脲。 |
| 11 | 185.86 | 4.14 | 82.53 | b | 0.583 | 环氧-伯胺开环固化。 |
| 12 | 194.55 | 4.55 | 134.25 | a | 0.560 | 氰酸酯-胺共反应。 |
| 13 | 194.63 | 4.63 | 37.49 | b | 0.471 | 氰酸酯-胺共反应。 |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

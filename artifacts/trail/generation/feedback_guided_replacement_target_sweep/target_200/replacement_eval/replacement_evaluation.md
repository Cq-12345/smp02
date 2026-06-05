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
| best_distance_c | 0.444883 |
| within_1c | 2 |
| within_5c | 11 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 11 |

目标 Tg: 200.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 200.44 | 0.44 | 89.14 | b | 0.471 | 氰酸酯-胺共反应。 |
| 2 | 200.56 | 0.56 | 96.75 | a | 0.424 | 环氧-伯胺开环固化。 |
| 3 | 201.20 | 1.20 | 65.73 | b | 0.308 | 环氧-羟基醚化，常需催化剂。 |
| 4 | 201.24 | 1.24 | 106.09 | a | 0.442 | 环氧-伯胺开环固化。 |
| 5 | 198.32 | 1.68 | 103.67 | b | 0.560 | 环氧-伯胺开环固化。 |
| 6 | 201.69 | 1.69 | 18.34 | b | 0.429 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| 7 | 197.80 | 2.20 | 37.96 | b | 0.323 | 环氧-伯胺开环固化。 |
| 8 | 202.53 | 2.53 | 127.76 | b | 0.560 | 环氧-伯胺开环固化。 |
| 9 | 203.27 | 3.27 | 101.68 | a | 0.421 | 环氧-伯胺开环固化。 |
| 10 | 196.29 | 3.71 | 12.38 | b | 0.471 | 环氧-伯胺开环固化。 |
| 11 | 195.57 | 4.43 | 37.69 | b | 0.375 | 环氧-伯胺开环固化。 |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

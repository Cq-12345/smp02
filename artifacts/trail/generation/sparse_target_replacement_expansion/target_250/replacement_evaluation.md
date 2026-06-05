# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 320 |
| rebuilt_formulas | 318 |
| scored_formulas | 318 |
| harness_pass | 42 |
| rejected_proposals | 2 |
| best_distance_c | 0.034283 |
| within_1c | 8 |
| within_5c | 42 |
| literature_template_scored | 37 |
| literature_template_harness_pass | 9 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 42 |
| latent_local_search_scored | 0 |
| latent_local_search_harness_pass | 0 |

目标 Tg: 250.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | latent dist | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 249.97 | 0.03 | 77.99 | b |  | 0.878 | 环氧-羟基醚化，常需催化剂。 source=library |
| 2 | 249.89 | 0.11 | 83.05 | a |  | 0.517 | 酸酐-羟基酯化。 source=literature_template |
| 3 | 249.62 | 0.38 | 74.65 | a |  | 0.400 | 环氧-伯胺开环固化。 source=library |
| 4 | 249.45 | 0.55 | 99.42 | b |  | 0.409 | 环氧-伯胺开环固化。 source=library |
| 5 | 250.55 | 0.55 | 64.77 | b |  | 0.500 | 酸酐-羟基酯化。 source=generated |
| 6 | 249.41 | 0.59 | 73.70 | a |  | 0.930 | 环氧-伯胺开环固化。 source=library |
| 7 | 250.77 | 0.77 | 85.46 | b |  | 0.517 | 环氧-酸酐固化，常需催化剂。 source=literature_template |
| 8 | 250.85 | 0.85 | 85.72 | b |  | 0.517 | 环氧-酸酐固化，常需催化剂。 source=literature_template |
| 9 | 248.99 | 1.01 | 79.33 | a |  | 0.636 | 环氧-酸酐固化，常需催化剂。 source=library |
| 10 | 248.81 | 1.19 | 75.17 | a |  | 0.659 | 环氧-酸酐固化，常需催化剂。 source=library |
| 11 | 251.26 | 1.26 | 72.06 | a |  | 0.897 | 环氧-伯胺开环固化。 source=library |
| 12 | 248.74 | 1.26 | 77.09 | b |  | 0.317 | 酸酐-羟基酯化。 source=library |
| 13 | 251.47 | 1.47 | 84.95 | a |  | 0.593 | 环氧-伯胺开环固化。 source=library |
| 14 | 251.48 | 1.48 | 47.12 | b |  | 0.556 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 source=generated |
| 15 | 251.61 | 1.61 | 55.33 | b |  | 0.556 | 酸酐-胺开环形成酰胺酸。 source=generated |
| 16 | 251.69 | 1.69 | 101.85 | a |  | 0.705 | 环氧-羟基醚化，常需催化剂。 source=library |
| 17 | 248.13 | 1.87 | 41.46 | b |  | 0.197 | 酸酐-胺开环形成酰胺酸。 source=library |
| 18 | 247.98 | 2.02 | 78.48 | a |  | 0.522 | 环氧-酸酐固化，常需催化剂。 source=library |
| 19 | 247.67 | 2.33 | 92.86 | a |  | 0.500 | 酸酐-羟基酯化。 source=generated |
| 20 | 247.62 | 2.38 | 46.05 | b |  | 0.577 | 酸酐-胺开环形成酰胺酸。 source=literature_template |

## Rejection Reasons

- duplicate_replacement_formula: 2

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

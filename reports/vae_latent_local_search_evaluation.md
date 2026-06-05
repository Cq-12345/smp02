# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 200 |
| rebuilt_formulas | 200 |
| scored_formulas | 200 |
| harness_pass | 42 |
| rejected_proposals | 0 |
| best_distance_c | 0.20046 |
| within_1c | 10 |
| within_5c | 42 |
| literature_template_scored | 39 |
| literature_template_harness_pass | 7 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 42 |
| latent_local_search_scored | 200 |
| latent_local_search_harness_pass | 42 |

目标 Tg: 195.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | latent dist | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 195.20 | 0.20 | 37.34 | b | 0.0331 | 0.471 | 氰酸酯-胺共反应。 source=library |
| 2 | 194.63 | 0.37 | 37.49 | b | 0.0224 | 0.471 | 氰酸酯-胺共反应。 source=library |
| 3 | 195.47 | 0.47 | 70.25 | a | 0.0974 | 0.114 | 马来酰亚胺-胺 Michael 加成。 source=literature_template |
| 4 | 194.48 | 0.52 | 96.19 | b | 0.0265 | 0.630 | 氰酸酯-胺共反应。 source=literature_template |
| 5 | 195.57 | 0.57 | 37.69 | b | 0.0056 | 0.375 | 环氧-伯胺开环固化。 source=library |
| 6 | 195.59 | 0.59 | 73.07 | a | 0.0234 | 0.538 | 马来酰亚胺与烯基共聚/加成。 source=library |
| 7 | 195.66 | 0.66 | 117.03 | b | 0.0566 | 0.100 | 环氧-伯胺开环固化。 source=chembl |
| 8 | 195.69 | 0.69 | 73.87 | a | 0.0404 | 0.114 | 马来酰亚胺与烯基共聚/加成。 source=library |
| 9 | 195.72 | 0.72 | 62.53 | b | 0.0175 | 0.111 | 环氧-羧酸开环酯化。 source=literature_template |
| 10 | 194.08 | 0.92 | 48.12 | b | 0.0056 | 0.375 | 异氰酸酯-伯胺形成聚脲。 source=library |
| 11 | 196.29 | 1.29 | 12.38 | b | 0.0224 | 0.471 | 环氧-伯胺开环固化。 source=library |
| 12 | 193.53 | 1.47 | 132.78 | b | 0.0276 | 0.520 | 异氰酸酯-伯胺形成聚脲。 source=generated |
| 13 | 193.49 | 1.51 | 90.91 | a | 0.0472 | 0.135 | 酸酐-胺开环形成酰胺酸。 source=chembl |
| 14 | 193.19 | 1.81 | 74.03 | a | 0.0370 | 0.283 | 环氧-伯胺开环固化。 source=library |
| 15 | 193.18 | 1.82 | 62.88 | b | 0.0064 | 0.897 | 环氧-伯胺开环固化。 source=library |
| 16 | 196.88 | 1.88 | 62.43 | b | 0.0717 | 0.895 | 环氧-伯胺开环固化。 source=library |
| 17 | 193.10 | 1.90 | 84.33 | b | 0.0297 | 0.136 | 氰酸酯-酚共固化/催化三聚。 source=library |
| 18 | 192.77 | 2.23 | 68.27 | b | 0.0843 | 0.312 | 环氧-伯胺开环固化。 source=generated |
| 19 | 197.39 | 2.39 | 108.71 | a | 0.0678 | 0.320 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 source=library |
| 20 | 197.64 | 2.64 | 49.81 | a | 0.0092 | 0.538 | 异氰酸酯-伯胺形成聚脲。 source=literature_template |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

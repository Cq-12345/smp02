# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 200 |
| rebuilt_formulas | 200 |
| scored_formulas | 200 |
| harness_pass | 41 |
| rejected_proposals | 0 |
| best_distance_c | 0.305115 |
| within_1c | 10 |
| within_5c | 41 |
| literature_template_scored | 39 |
| literature_template_harness_pass | 10 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 41 |
| latent_local_search_scored | 200 |
| latent_local_search_harness_pass | 41 |

目标 Tg: 200.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | latent dist | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 199.69 | 0.31 | 97.47 | b | 0.0990 | 0.189 | 异氰酸酯-伯胺形成聚脲。 source=literature_template |
| 2 | 200.35 | 0.35 | 86.51 | b | 0.0882 | 0.441 | 马来酰亚胺与烯基共聚/加成。 source=literature_template |
| 3 | 200.44 | 0.44 | 89.14 | b | 0.0224 | 0.471 | 氰酸酯-胺共反应。 source=library |
| 4 | 199.46 | 0.54 | 74.99 | b | 0.0090 | 0.429 | 环氧-伯胺开环固化。 source=library |
| 5 | 200.62 | 0.62 | 37.24 | b | 0.0383 | 0.471 | 氰酸酯-胺共反应。 source=library |
| 6 | 199.37 | 0.63 | 70.83 | a | 0.0379 | 0.062 | 马来酰亚胺-胺 Michael 加成。 source=library |
| 7 | 199.31 | 0.69 | 73.08 | a | 0.0725 | 0.089 | 马来酰亚胺-胺 Michael 加成。 source=literature_template |
| 8 | 199.24 | 0.76 | 80.37 | b | 0.0472 | 0.135 | 环氧-仲胺开环固化。 source=chembl |
| 9 | 199.20 | 0.80 | 96.72 | b | 0.0853 | 0.467 | 氰酸酯-胺共反应。 source=literature_template |
| 10 | 199.10 | 0.90 | 85.85 | a | 0.0692 | 0.333 | 环氧-伯胺开环固化。 source=library |
| 11 | 201.20 | 1.20 | 65.73 | b | 0.0119 | 0.308 | 环氧-羟基醚化，常需催化剂。 source=library |
| 12 | 201.36 | 1.36 | 95.80 | a | 0.0249 | 0.304 | 环氧-伯胺开环固化。 source=library |
| 13 | 198.12 | 1.88 | 24.53 | a | 0.0625 | 0.304 | 环氧-伯胺开环固化。 source=library |
| 14 | 201.92 | 1.92 | 86.94 | a | 0.0391 | 0.103 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 source=library |
| 15 | 202.01 | 2.01 | 61.20 | b | 0.0338 | 0.205 | 异氰酸酯-伯胺形成聚脲。 source=library |
| 16 | 197.85 | 2.15 | 109.32 | b | 0.0559 | 0.138 | 环氧-伯胺开环固化。 source=chembl |
| 17 | 197.83 | 2.17 | 68.30 | b | 0.0725 | 0.319 | 环氧-伯胺开环固化。 source=library |
| 18 | 197.80 | 2.20 | 37.96 | b | 0.0125 | 0.323 | 环氧-伯胺开环固化。 source=library |
| 19 | 197.64 | 2.36 | 49.81 | a | 0.0092 | 0.538 | 异氰酸酯-伯胺形成聚脲。 source=literature_template |
| 20 | 202.51 | 2.51 | 137.04 | b | 0.1604 | 0.092 | 环氧-仲胺开环固化。 source=chembl |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

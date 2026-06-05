# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 200 |
| rebuilt_formulas | 200 |
| scored_formulas | 200 |
| harness_pass | 38 |
| rejected_proposals | 0 |
| best_distance_c | 0.166559 |
| within_1c | 11 |
| within_5c | 38 |
| literature_template_scored | 39 |
| literature_template_harness_pass | 4 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 38 |
| latent_local_search_scored | 200 |
| latent_local_search_harness_pass | 38 |

目标 Tg: 190.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | latent dist | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 190.17 | 0.17 | 86.88 | a | 0.0419 | 0.122 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 source=library |
| 2 | 190.18 | 0.18 | 98.57 | b | 0.0472 | 0.135 | 环氧-仲胺开环固化。 source=chembl |
| 3 | 189.76 | 0.24 | 108.22 | b | 0.0534 | 0.059 | 环氧-仲胺开环固化。 source=chembl |
| 4 | 190.25 | 0.25 | 92.46 | b | 0.0288 | 0.125 | 环氧-仲胺开环固化。 source=chembl |
| 5 | 189.71 | 0.29 | 56.36 | a | 0.1029 | 0.306 | 环氧-羟基醚化，常需催化剂。 source=generated |
| 6 | 190.41 | 0.41 | 112.11 | a | 0.0755 | 0.068 | 马来酰亚胺-胺 Michael 加成。 source=chembl |
| 7 | 189.58 | 0.42 | 54.49 | a | 0.0249 | 0.304 | 环氧-羟基醚化，常需催化剂。 source=library |
| 8 | 189.42 | 0.58 | 89.62 | a | 0.0713 | 0.088 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 source=library |
| 9 | 190.70 | 0.70 | 108.91 | a | 0.0370 | 0.283 | 环氧-伯胺开环固化。 source=library |
| 10 | 190.86 | 0.86 | 51.55 | a | 0.0577 | 0.388 | 环氧-羟基醚化，常需催化剂。 source=library |
| 11 | 190.99 | 0.99 | 35.99 | a | 0.0313 | 0.705 | 环氧-伯胺开环固化。 source=library |
| 12 | 188.33 | 1.67 | 53.37 | b | 0.0125 | 0.286 | 环氧-羟基醚化，常需催化剂。 source=library |
| 13 | 188.28 | 1.72 | 104.62 | b | 0.0534 | 0.059 | 环氧-仲胺开环固化。 source=chembl |
| 14 | 188.22 | 1.78 | 112.41 | a | 0.0743 | 0.400 | 环氧-伯胺开环固化。 source=generated |
| 15 | 188.07 | 1.93 | 84.70 | a | 0.0927 | 0.140 | 氰酸酯-酚共固化/催化三聚。 source=chembl |
| 16 | 192.13 | 2.13 | 112.45 | a | 0.0790 | 0.077 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 source=generated |
| 17 | 187.85 | 2.15 | 65.17 | b | 0.0454 | 0.930 | 环氧-伯胺开环固化。 source=library |
| 18 | 192.20 | 2.20 | 86.77 | b | 0.0472 | 0.135 | 环氧-仲胺开环固化。 source=chembl |
| 19 | 192.28 | 2.28 | 52.48 | b | 0.0125 | 0.323 | 异氰酸酯-伯胺形成聚脲。 source=library |
| 20 | 192.33 | 2.33 | 37.35 | b | 0.0297 | 0.136 | 氰酸酯-酚共固化/催化三聚。 source=library |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

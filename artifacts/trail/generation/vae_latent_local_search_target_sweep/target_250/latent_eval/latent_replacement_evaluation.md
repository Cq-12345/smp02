# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 200 |
| rebuilt_formulas | 200 |
| scored_formulas | 200 |
| harness_pass | 5 |
| rejected_proposals | 0 |
| best_distance_c | 1.084208 |
| within_1c | 0 |
| within_5c | 5 |
| literature_template_scored | 39 |
| literature_template_harness_pass | 1 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 5 |
| latent_local_search_scored | 200 |
| latent_local_search_harness_pass | 5 |

目标 Tg: 250.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | latent dist | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 248.92 | 1.08 | 101.79 | b | 0.0639 | 0.135 | 氰酸酯-酚共固化/催化三聚。 source=chembl |
| 2 | 252.03 | 2.03 | 66.07 | a | 0.0743 | 0.400 | 环氧-伯胺开环固化。 source=generated |
| 3 | 252.15 | 2.15 | 95.27 | a | 0.0977 | 0.576 | 异氰酸酯-伯胺形成聚脲。 source=library |
| 4 | 245.45 | 4.55 | 77.84 | a | 0.1025 | 0.043 | 酸酐-羟基酯化。 source=library |
| 5 | 245.29 | 4.71 | 81.44 | a | 0.1083 | 0.043 | 酸酐-羟基酯化。 source=literature_template |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

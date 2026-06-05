# VAE Replacement Proposals: Prediction And Harness Evaluation

本文档回应 TODO 中“生成模型：VAE 替换策略”和“生成 -> 预测/评估 -> 优化”的要求：这里把 replacement proposals 重建为完整配方，送入 VAE-WVCM predictor，并用 Harness 做硬约束检查。

## Summary

| item | value |
| --- | ---: |
| input_proposals | 120 |
| rebuilt_formulas | 120 |
| scored_formulas | 120 |
| harness_pass | 4 |
| rejected_proposals | 0 |
| best_distance_c | 0.489437 |
| within_1c | 1 |
| within_5c | 4 |
| predictor | VAE (512) + GaussianProcess_RBF |
| latent_size | 512 |
| replacement_observations | 4 |

目标 Tg: 250.0 C

## Top Harness-Passing Replacements

| rank | predicted Tg (C) | distance (C) | sigma (C) | replacement side | tanimoto | chemistry |
| ---: | ---: | ---: | ---: | --- | ---: | --- |
| 1 | 249.51 | 0.49 | 70.04 | b | 0.727 | 环氧-伯胺开环固化。 |
| 2 | 251.48 | 1.48 | 88.24 | a | 0.410 | 环氧-伯胺开环固化。 |
| 3 | 252.15 | 2.15 | 95.27 | a | 0.576 | 异氰酸酯-伯胺形成聚脲。 |
| 4 | 246.92 | 3.08 | 53.19 | b | 0.824 | 环氧-伯胺开环固化。 |

## Rejection Reasons

- No rejected proposals.

## Interpretation

- 这一步不是重新生成分子，而是对已生成的 VAE replacement proposals 做完整配方级验证。
- `harness_pass` 同时要求 SMILES 有效、比例和为 1、预测 Tg 落入目标窗口、且存在官能团反应兼容关系。
- 通过项已经写入 replacement observation ledger，可作为外部 surrogate history 进入 PiEvo-faithful；未通过项应回流到生成策略，调整官能团匹配或比例搜索。

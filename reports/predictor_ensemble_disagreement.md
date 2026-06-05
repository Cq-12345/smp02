# 预测模型集成分歧审计

本文档回应 TODO 中“预测模型：GNN、CNN/SVR/RF 论文对比，以及更多模型”的后续补强：不只选单个最佳模型，而是用当前 model zoo 的强模型集成来标记候选的 epistemic disagreement / OOD 风险。当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM 表示，不涉及暂缓的超图表示。

## 输出文件

- Scored candidates: `artifacts/trail/predictors/ensemble_disagreement/candidate_ensemble_disagreement.csv`
- Predictor table: `artifacts/trail/predictors/ensemble_disagreement/ensemble_predictors.csv`
- Summary: `artifacts/trail/predictors/ensemble_disagreement/ensemble_disagreement_summary.json`
- Low-disagreement near-target candidates: `artifacts/trail/predictors/ensemble_disagreement/low_disagreement_near_target.csv`
- High-disagreement near-target candidates: `artifacts/trail/predictors/ensemble_disagreement/high_disagreement_near_target.csv`

## 集成成员

| rank | model | MAPEK test (%) | MAE test (C) | R2 test |
| ---: | --- | ---: | ---: | ---: |
| 1 | VAE (512) + GaussianProcess_RBF | 3.9778 | 18.7641 | 0.8233 |
| 2 | VAE (512) + NuSVR_RBF | 4.1379 | 17.9836 | 0.8965 |
| 3 | VAE (512) + XGBoost_hist_depth3 | 4.5591 | 20.4429 | 0.8390 |
| 4 | VAE (512) + ExtraTrees_300 | 4.5974 | 20.6033 | 0.8184 |
| 5 | VAE (512) + ExtraTrees_600 | 4.6436 | 20.8470 | 0.8153 |
| 6 | VAE (512) + GradientBoosting_squared | 4.6513 | 20.6229 | 0.8501 |

## 汇总

| item | value |
| --- | ---: |
| candidate_rows | 10000 |
| ensemble_models | 6 |
| target_tg_c | 195.0 |
| target_window_c | 5.0 |
| mean_ensemble_std_c | 32.16103728846615 |
| median_ensemble_std_c | 30.918520578260548 |
| max_ensemble_std_c | 83.5055129324988 |
| near_target_rows | 1045 |
| near_target_low_disagreement_rows | 84 |
| near_target_high_disagreement_rows | 526 |
| mean_abs_best_model_delta_c | 30.374043040674035 |
| consensus_std_c | 10.0 |
| high_disagreement_std_c | 25.0 |

## 低分歧近目标候选示例

| rank | ensemble Tg (C) | std (C) | GPR delta (C) | chemistry | ratios |
| ---: | ---: | ---: | ---: | --- | --- |
| 1 | 194.877 | 9.617 | -4.327 | 环氧-伯胺开环固化。 | 0.75000:0.25000 |
| 2 | 194.811 | 8.902 | -14.288 | 环氧-伯胺开环固化。 | 0.95000:0.05000 |
| 3 | 195.228 | 5.934 | 5.689 | 氰酸酯-酚共固化/催化三聚。 | 0.50000:0.50000 |
| 4 | 195.228 | 6.158 | 9.928 | 环氧-伯胺开环固化。 | 0.40000:0.60000 |
| 5 | 195.237 | 9.609 | -4.848 | 环氧-伯胺开环固化。 | 0.65000:0.35000 |
| 6 | 194.670 | 5.837 | -0.407 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 | 0.05000:0.95000 |
| 7 | 195.499 | 9.112 | -2.878 | 环氧-伯胺开环固化。 | 0.80000:0.20000 |
| 8 | 194.469 | 3.864 | -3.603 | 环氧-伯胺开环固化。 | 0.40000:0.60000 |
| 9 | 195.607 | 9.170 | -13.211 | 环氧-伯胺开环固化。 | 0.95000:0.05000 |
| 10 | 194.342 | 8.264 | 11.182 | 环氧-羟基醚化，常需催化剂。 | 0.45000:0.55000 |

## 高分歧近目标候选示例

| rank | ensemble Tg (C) | std (C) | range (C) | GPR delta (C) | chemistry |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 198.826 | 79.807 | 222.520 | -9.815 | 异氰酸酯-伯胺形成聚脲。 |
| 2 | 195.533 | 76.320 | 215.514 | 22.004 | 异氰酸酯-伯胺形成聚脲。 |
| 3 | 194.183 | 75.059 | 209.379 | 7.594 | 异氰酸酯-伯胺形成聚脲。 |
| 4 | 190.530 | 74.468 | 210.525 | -18.174 | 异氰酸酯-伯胺形成聚脲。 |
| 5 | 191.466 | 72.344 | 226.494 | 5.642 | 环氧-羟基醚化，常需催化剂。 |
| 6 | 196.734 | 71.927 | 206.246 | -18.121 | 异氰酸酯-伯胺形成聚脲。 |
| 7 | 192.348 | 71.555 | 201.735 | -14.985 | 异氰酸酯-伯胺形成聚脲。 |
| 8 | 194.074 | 70.327 | 220.662 | 5.828 | 环氧-羟基醚化，常需催化剂。 |
| 9 | 199.655 | 69.305 | 215.383 | 8.311 | 环氧-羟基醚化，常需催化剂。 |
| 10 | 197.836 | 69.264 | 193.462 | 2.435 | 异氰酸酯-羟基形成聚氨酯。 |

## 解释

- `ensemble_std_tg_c` 是模型间分歧，不等价于物理不确定性；它适合作为候选推荐和人工审核的 epistemic/OOD 信号。
- 低分歧且接近目标的候选适合优先进入 PiEvo/人工审核；高分歧但接近目标的候选适合标记为需要更多模型或实验验证。
- 当前 best model 仍可作为主代理，但 `best_model_delta_c` 能暴露 GPR 与强点预测模型集体判断的偏差。

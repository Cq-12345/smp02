# Reproduction Summary

Run date: 2026-06-05 Asia/Shanghai

## VAE

- Completed latent sizes: 16, 32, 64, 128, 256, 512, 1024.
- Full checkpoints are under `artifacts/reproduce/vae/` and are ignored by git.
- Default high-performance config uses both visible GPUs, VAE batch size 2048, 24 DataLoader workers, and CUDA convolution/matmul speed settings.

## Tg Predictor Model Zoo

- Evaluated rows: 343 model/latent combinations.
- Primary selection metric: `MAPEK test dataset (%)`; lower is better.
- Best model: `VAE (512) + GaussianProcess_RBF`.
- Best test metrics: MAPEK 3.977805%, MAE 18.764 C, RMSE 40.437 C, R2 0.823343, legacy MAPE 16.597%.
- Full top-50 leaderboard: `reports/model_zoo_leaderboard_top50.csv`.

| Rank | Method | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test | Legacy MAPE test (%) |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | VAE (512) + GaussianProcess_RBF | 3.977805 | 18.764 | 40.437 | 0.823343 | 16.597 |
| 2 | VAE (512) + NuSVR_RBF | 4.137925 | 17.984 | 30.946 | 0.896541 | 33.124 |
| 3 | VAE (512) + XGBoost_hist_depth3 | 4.559110 | 20.443 | 38.606 | 0.838983 | 92.620 |
| 4 | VAE (512) + ExtraTrees_300 | 4.597351 | 20.603 | 41.002 | 0.818374 | 100.606 |
| 5 | VAE (512) + ExtraTrees_600 | 4.643616 | 20.847 | 41.347 | 0.815302 | 100.051 |
| 6 | VAE (512) + GradientBoosting_squared | 4.651347 | 20.623 | 37.244 | 0.850138 | 130.732 |
| 7 | VAE (512) + LightGBM_leaves31 | 4.691672 | 21.236 | 39.310 | 0.833055 | 99.658 |
| 8 | VAE (512) + NGBoost | 4.699063 | 20.963 | 37.801 | 0.845625 | 115.054 |
| 9 | VAE (256) + ExtraTrees_600 | 4.702636 | 21.595 | 45.073 | 0.780518 | 67.288 |
| 10 | VAE (256) + ExtraTrees_300 | 4.713204 | 21.597 | 44.883 | 0.782357 | 65.896 |

## Functional-Group Discovery

- Discovery uses SMARTS-based monomer functional-group classification and thermoset compatibility rules.
- Monomers: 231.
- Compatible monomer pairs: 6467.
- Ratio candidates: 122873.
- Full ratio candidate table: `artifacts/reproduce/discovery/all_ratio_candidates.csv`.
- Selected candidates in 190-200 C: 500.
- Harness pass rate on selected candidates: 500/500.
- Full top-50 selected candidates: `reports/selected_candidates_top50.csv`.

| Rank | Ratio A | Ratio B | Predicted Tg | Distance | Compatibility |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0.65 | 0.35 | 194.9968 | 0.0032 | 异氰酸酯-伯胺形成聚脲。 |
| 2 | 0.30 | 0.70 | 195.0054 | 0.0054 | 马来酰亚胺与烯基共聚/加成。 |
| 3 | 0.10 | 0.90 | 194.9927 | 0.0073 | 环氧-伯胺开环固化。 |
| 4 | 0.70 | 0.30 | 195.0075 | 0.0075 | 环氧-伯胺开环固化。 |
| 5 | 0.35 | 0.65 | 195.0196 | 0.0196 | 环氧-羟基醚化，常需催化剂。 |
| 6 | 0.80 | 0.20 | 195.0225 | 0.0225 | 氰酸酯-胺共反应。 |
| 7 | 0.45 | 0.55 | 194.9719 | 0.0281 | 氰酸酯-胺共反应。 |
| 8 | 0.40 | 0.60 | 194.9717 | 0.0283 | 酸酐-羟基酯化。 |
| 9 | 0.45 | 0.55 | 194.9706 | 0.0294 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| 10 | 0.80 | 0.20 | 194.9681 | 0.0319 | 环氧-伯胺开环固化。 |

## Closed Loop

- Iterations: 5; selected per iteration: 50.
- Iteration best predicted Tg values:
  - Iteration 1: 194.9968 C
  - Iteration 2: 194.8925 C
  - Iteration 3: 195.1338 C
  - Iteration 4: 194.7131 C
  - Iteration 5: 195.4009 C
- Top evolved reaction principles:
  - 环氧-伯胺开环固化。: 126
  - 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。: 28
  - 环氧-羟基醚化，常需催化剂。: 26
  - 马来酰亚胺与烯基共聚/加成。: 10
  - 环氧-酸酐固化，常需催化剂。: 10
  - 酸酐-羟基酯化。: 9
  - 异氰酸酯-伯胺形成聚脲。: 8
  - 氰酸酯-胺共反应。: 8
  - 环氧-羧酸开环酯化。: 7
  - 马来酰亚胺-胺 Michael 加成。: 6

## Verification

- `python -m compileall -q src tests`: passed.
- `pytest -q`: passed.
- `trail/harness/constraints.py`: generated `artifacts/reproduce/discovery/harness_validation.csv`.
- `trail/workflow/multi_agent_workflow.py`: generated `artifacts/reproduce/closed_loop/multi_agent_summary.json`.

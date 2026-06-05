# Reproduction Summary

Run date: 2026-06-05 Asia/Shanghai

## VAE

- Completed latent sizes: 16, 32, 64, 128, 256, 512, 1024.
- Full checkpoints are under `artifacts/reproduce/vae/` and are ignored by git.
- Default high-performance config now uses both visible GPUs, VAE batch size 2048, 24 DataLoader workers, and CUDA convolution/matmul speed settings.

## Tg Predictor Model Zoo

- Evaluated rows: 343 model/latent combinations.
- Best by `R2 test`: `VAE (512) + NuSVR_RBF`.
- Best test R2: 0.896252; test MAPE: 33.977%; test PCP: 63.235%.
- Full top-50 leaderboard: `reports/model_zoo_leaderboard_top50.csv`.

| Rank | Method | R2 test | MAPE test (%) | PCP test (%) |
| ---: | --- | ---: | ---: | ---: |
| 1 | VAE (512) + NuSVR_RBF | 0.896252 | 33.977 | 63.235 |
| 2 | VAE (512) + NGBoost | 0.847590 | 116.065 | 60.294 |
| 3 | VAE (512) + GradientBoosting_huber | 0.844728 | 77.941 | 58.824 |
| 4 | VAE (512) + GradientBoosting_squared | 0.842347 | 114.426 | 60.294 |
| 5 | VAE (512) + XGBoost_hist_depth3 | 0.842136 | 99.229 | 63.235 |
| 6 | VAE (512) + HistGradientBoosting | 0.828870 | 140.417 | 58.824 |
| 7 | VAE (512) + LightGBM_leaves31 | 0.827215 | 78.337 | 60.294 |
| 8 | VAE (512) + XGBoost_hist_depth5 | 0.826867 | 126.456 | 57.353 |
| 9 | VAE (512) + LightGBM_leaves63 | 0.824371 | 96.992 | 58.824 |
| 10 | VAE (512) + GaussianProcess_RBF | 0.823350 | 16.623 | 66.176 |

## Discovery

- Monomers: 231.
- Compatible monomer pairs: 6467.
- Ratio candidates: 122873.
- Selected candidates in 190-200 C: 500.
- Harness pass rate on selected candidates: 500/500.
- Full top-50 selected candidates: `reports/selected_candidates_top50.csv`.

| Rank | Ratio A | Ratio B | Predicted Tg | Distance | Compatibility |
| ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 0.85 | 0.15 | 195.0006 | 0.0006 | 环氧-仲胺开环固化。 |
| 2 | 0.25 | 0.75 | 195.0061 | 0.0061 | 环氧-酸酐固化，常需催化剂。 |
| 3 | 0.80 | 0.20 | 195.0084 | 0.0084 | 异氰酸酯-仲胺形成脲键。 |
| 4 | 0.10 | 0.90 | 195.0104 | 0.0104 | 马来酰亚胺与烯基共聚/加成。 |
| 5 | 0.60 | 0.40 | 194.9894 | 0.0106 | 氰酸酯-胺共反应。 |
| 6 | 0.35 | 0.65 | 195.0110 | 0.0110 | 环氧-羟基醚化，常需催化剂。 |
| 7 | 0.95 | 0.05 | 194.9883 | 0.0117 | 环氧-伯胺开环固化。 |
| 8 | 0.45 | 0.55 | 195.0137 | 0.0137 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |
| 9 | 0.25 | 0.75 | 194.9854 | 0.0146 | 环氧-伯胺开环固化。 |
| 10 | 0.30 | 0.70 | 195.0168 | 0.0168 | 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。 |

## Closed Loop

- Iterations: 5; selected per iteration: 50.
- Iteration best predicted Tg values:
  - Iteration 1: 195.0006 C
  - Iteration 2: 194.8913 C
  - Iteration 3: 195.1331 C
  - Iteration 4: 195.2338 C
  - Iteration 5: 194.6519 C
- Top evolved reaction principles:
  - 环氧-伯胺开环固化。: 96
  - 环氧-羟基醚化，常需催化剂。: 27
  - 酸酐-胺形成聚酰胺酸/聚酰亚胺前体。: 21
  - 马来酰亚胺-胺 Michael 加成。: 17
  - 环氧-酸酐固化，常需催化剂。: 14
  - 氰酸酯-胺共反应。: 12
  - 马来酰亚胺与烯基共聚/加成。: 11
  - 异氰酸酯-伯胺形成聚脲。: 9
  - 酸酐-羟基酯化。: 9
  - 硫醇-烯点击反应。: 9

## Verification

- `python -m compileall -q src tests`: passed.
- `pytest -q`: 4 passed.
- `trail/harness/constraints.py`: generated `artifacts/reproduce/discovery/harness_validation.csv`.
- `trail/workflow/multi_agent_workflow.py`: generated `artifacts/reproduce/closed_loop/multi_agent_summary.json`.

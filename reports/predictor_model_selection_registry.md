# Predictor Model Selection Registry

本文档把当前 model zoo 的选择结果固化为可被 workflow 读取的注册表。它不重新训练模型，只把已有 85/15 split 指标转成后续闭环的模型契约。

## Summary

| item | value |
| --- | ---: |
| metrics_rows | 343 |
| usable_joblib_rows | 336 |
| selection_metric | MAPEK test dataset (%) |
| primary_method | VAE (512) + GaussianProcess_RBF |
| primary_latent_size | 512 |
| primary_model_path | artifacts/reproduce/predictors/latent_512/zoo_gaussianprocess_rbf_latent_512.joblib |
| primary_model_exists | True |
| primary_mapek_test_pct | 3.9778051975274606 |
| primary_mae_test_c | 18.764057961351714 |
| primary_rmse_test_c | 40.43710014932832 |
| primary_r2_test | 0.823342857763097 |
| mae_backup_method | VAE (512) + NuSVR_RBF |
| mae_backup_mae_test_c | 17.983606911126735 |
| rmse_backup_method | VAE (512) + NuSVR_RBF |
| rmse_backup_rmse_test_c | 30.945529773132304 |
| r2_backup_method | VAE (512) + NuSVR_RBF |
| r2_backup_r2_test | 0.8965412951519194 |
| uncertainty_provider_method | VAE (512) + GaussianProcess_RBF |
| uncertainty_provider_latent_size | 512 |
| ensemble_member_rows | 6 |
| recommended_default_predictor | primary_closed_loop_predictor |
| recommended_guard | ensemble_guard_member |
| evidence_level | predictor_selection_registry_not_new_training |
| registry_path | artifacts/trail/predictors/model_selection_registry/predictor_model_selection_registry.csv |
| summary_path | artifacts/trail/predictors/model_selection_registry/predictor_model_selection_summary.json |
| report_path | reports/predictor_model_selection_registry.md |

## Registry Rows

| role | rank | model | latent | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| primary_closed_loop_predictor | 1 | VAE (512) + GaussianProcess_RBF | 512 | 3.9778 | 18.7641 | 40.4371 | 0.8233 |
| point_error_backup_mae | 1 | VAE (512) + NuSVR_RBF | 512 | 4.1379 | 17.9836 | 30.9455 | 0.8965 |
| point_error_backup_rmse | 1 | VAE (512) + NuSVR_RBF | 512 | 4.1379 | 17.9836 | 30.9455 | 0.8965 |
| point_error_backup_r2 | 1 | VAE (512) + NuSVR_RBF | 512 | 4.1379 | 17.9836 | 30.9455 | 0.8965 |
| uncertainty_provider | 1 | VAE (512) + GaussianProcess_RBF | 512 | 3.9778 | 18.7641 | 40.4371 | 0.8233 |
| ensemble_guard_member | 1 | VAE (512) + GaussianProcess_RBF | 512 | 3.9778 | 18.7641 | 40.4371 | 0.8233 |
| ensemble_guard_member | 2 | VAE (512) + NuSVR_RBF | 512 | 4.1379 | 17.9836 | 30.9455 | 0.8965 |
| ensemble_guard_member | 3 | VAE (512) + XGBoost_hist_depth3 | 512 | 4.5591 | 20.4429 | 38.6056 | 0.8390 |
| ensemble_guard_member | 4 | VAE (512) + ExtraTrees_300 | 512 | 4.5974 | 20.6033 | 41.0018 | 0.8184 |
| ensemble_guard_member | 5 | VAE (512) + ExtraTrees_600 | 512 | 4.6436 | 20.8470 | 41.3472 | 0.8153 |
| ensemble_guard_member | 6 | VAE (512) + GradientBoosting_squared | 512 | 4.6513 | 20.6229 | 37.2444 | 0.8501 |

## Usage

- `primary_closed_loop_predictor` 是默认闭环代理模型；当前应继续使用 `VAE(512)+GaussianProcess_RBF`。
- `point_error_backup_*` 是点预测误差视角的备选，不替代 uncertainty provider。
- `ensemble_guard_member` 是 PiEvo live ensemble guard 和候选 OOD/disagreement 审计使用的模型集合。
- 该 registry 的 `evidence_level` 表明这里只是选择契约，不是新训练结果，也不是物理实验观测。

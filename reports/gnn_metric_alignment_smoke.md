# GNN 指标对齐 Smoke 报告

本文档回应 TODO 中“预测模型：GNN”的部分。本轮没有引入超图/聚合物表示，仍然使用当前小分子 SMILES 图：每个配方由多个小分子图拼接，节点特征包含原子信息和该组分摩尔比例。

## 1. 运行配置

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python trail/gnn/train_gnn.py \
  --epochs 10 \
  --batch-size 32 \
  --out artifacts/trail/gnn_aligned_smoke
```

输出：

- `artifacts/trail/gnn_aligned_smoke/metrics.json`
- `artifacts/trail/gnn_aligned_smoke/metrics.csv`
- `artifacts/trail/gnn_aligned_smoke/train_predictions.csv`
- `artifacts/trail/gnn_aligned_smoke/test_predictions.csv`
- 新版训练脚本按架构保存模型，例如 `gnn_gcn_tg_regressor.pt`、`gnn_mpnn_tg_regressor.pt`。

## 2. 指标

| metric | value |
| --- | ---: |
| MAPEK training dataset (%) | 14.6723 |
| MAPEK test dataset (%) | 16.3492 |
| MAE training dataset (C) | 55.7873 |
| MAE test dataset (C) | 65.8156 |
| RMSE training dataset (C) | 68.6622 |
| RMSE test dataset (C) | 78.8365 |
| PCP training dataset (%) | 20.2632 |
| PCP test dataset (%) | 16.1765 |
| R2 training | 0.2833 |
| R2 test | 0.3285 |

## 3. 解释

这个 smoke GNN 不应直接作为最终候选模型。它只有 10 epochs，且结构很简单，性能明显弱于当前最佳 VAE-WVCM model zoo：

- `VAE(512)+GaussianProcess_RBF`: MAPEK test 3.9778%，MAE test 18.7641 C。
- `VAE(512)+NuSVR_RBF`: MAPEK test 4.1379%，MAE test 17.9836 C。
- GNN smoke: MAPEK test 16.3492%，MAE test 65.8156 C。

但本轮已经完成关键对齐：

- GNN 使用 85/15 train/test split。
- GNN 输出 MAPEK、MAE、RMSE、PCP、R2，与 model zoo 一致。
- 后续可以把 GNN 纳入同一 leaderboard，而不是只给单独 R2。

## 4. 下一步

- GIN/GAT/MPNN 已完成 5 epoch smoke，见 `reports/gnn_architecture_smoke_leaderboard.md`。
- MPNN 在 smoke 中最好，MAPEK test 为 11.0512%，MAE test 为 47.1922 C，但仍弱于 VAE-WVCM-GPR/NuSVR。
- Global formulation feature smoke 已完成，见 `reports/gnn_global_feature_smoke.md`。当前特征包括组分数/比例熵、RDKit 加权结构描述符、官能团权重和 reaction compatibility 覆盖；暂未把 process condition template 作为模型输入。
- 5 epoch MPNN 对比中，global-feature case 的 MAPEK test 为 11.6125%，baseline 为 11.0512%；短训下没有改善 MAPEK/MAE，但 RMSE/R2 略好。因此它目前是可审计特征契约和结构视角信号，不应替代 VAE-WVCM model zoo。
- VAE-WVCM model zoo ensemble disagreement 已先行落地，见 `reports/predictor_ensemble_disagreement.md`；GNN 后续应作为独立结构视角加入同一 disagreement/OOD 审计，而不是替代主代理模型。

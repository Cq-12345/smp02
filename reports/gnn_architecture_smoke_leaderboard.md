# GNN Architecture Smoke Leaderboard

本文档回应 TODO 中“预测模型：GNN”和“尝试 GIN/GAT/MPNN”的要求。当前仍使用单一小分子 SMILES 图，不涉及商品级组分、聚合物或超图表示。

## Run

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_gnn_architecture_smoke.py --epochs 5 --batch-size 32 --out-dir artifacts/trail/gnn_architecture_smoke
```

## Leaderboard

| rank | architecture | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | mpnn | 11.0512 | 47.1922 | 63.4471 | 0.5651 |
| 2 | gin | 15.2202 | 60.4392 | 71.8617 | 0.4421 |
| 3 | gcn | 27.0801 | 122.5737 | 155.0486 | -1.5972 |
| 4 | gat | 27.6658 | 124.8956 | 157.0857 | -1.6659 |

## Interpretation

- 本 smoke 最优 GNN 架构为 `mpnn`，MAPEK test 为 11.0512%。
- 这些 GNN 仍是短训 smoke，不应替代当前最佳 VAE-WVCM-GPR/NuSVR 模型。
- GNN 的价值更适合作为结构视角 ensemble 成员、disagreement/OOD 信号，以及未来加入 bond/process/global formulation features 后再正式比较。

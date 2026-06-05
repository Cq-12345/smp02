# GNN Global Feature Smoke

本文档回应 TODO 中“预测模型：GNN”和“知识/反应/global formulation 上下文进入模型”的后续推进。当前仍只使用单一小分子 SMILES 图，不涉及暂缓的商品级组分或聚合物超图表示。

## Run

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python scripts/run_gnn_global_feature_smoke.py --architecture mpnn --epochs 5 --batch-size 32
```

## Compared Cases

| rank | case | global features | MAPEK test (%) | MAE test (C) | RMSE test (C) | R2 test |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | mpnn_baseline | False | 11.0512 | 47.1922 | 63.4470 | 0.5651 |
| 2 | mpnn_global | True | 11.6125 | 47.9002 | 61.4415 | 0.5922 |

## Global Feature Contract

- 特征在 graph pooling 后拼接进入 GNN head，不改变小分子图表示。
- 向量包含组分数/比例熵、加权重原子数、芳香/杂原子/环/可旋转键信息、18 类官能团权重、互补反应对覆盖和 reactive group weight。
- 这些特征来自 RDKit、SMARTS 官能团分类和现有 reaction compatibility rule；它们是模型输入和 OOD 审计信号，不是物理真理。

## Interpretation

- 本 smoke 最优 case 为 `mpnn_baseline`，MAPEK test 为 11.0512%。
- global-feature case 相对 baseline 的 MAPEK delta 为 0.5613%，MAE delta 为 0.7079 C。
- 单次短训 smoke 只能验证链路和特征契约，不能证明 GNN 已超过 VAE-WVCM model zoo；后续若扩大 epochs，应把该 GNN 作为结构视角加入 ensemble disagreement/OOD 审计。

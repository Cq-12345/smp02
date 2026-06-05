# 真实实验与人工闭环接入方案

本文档回应 TODO 中“RL，人工闭环，真实实验结果迭代优化”的部分。当前仍然只处理小分子 SMILES / MoleCode 配方，不处理商品级组分和聚合物超图。

## 1. 为什么需要 observation ledger

当前 PiEvo-faithful 的 observation 主要来自 VAE-WVCM surrogate，因此发现的是 surrogate-consistent candidate principles。要把候选规律升级为更可靠的物理规律，必须接入更高权重的观测：

- 真实 DSC / DMA。
- 高保真模拟。
- 文献复现实验。
- 人工审核后的实验记录。

这些观测应进入统一 observation ledger，而不是散落在 notebook 或聊天记录里。

## 2. Schema

Schema 文件：

- `trail/experiments/observation_schema.yaml`

核心字段：

- `observation_id`
- `source_type`: `surrogate`、`real_dsc`、`high_fidelity_simulation`、`literature`
- `target_tg_c`
- `observed_tg_c`
- `smiles`
- `ratios`

权重：

```text
surrogate: 1
literature: 2
high_fidelity_simulation: 3
real_dsc: 5
```

这个权重不是最终科学结论，只是告诉 PiEvo posterior：真实实验比 surrogate 更有解释权。

## 3. Reward

目标 Tg 不固定，因此每条 observation 单独保存 `target_tg_c`：

```text
reward = exp(-abs(observed_tg_c - target_tg_c) / tau)
weighted_reward = reward * authority_weight
```

## 4. 导入脚本

```bash
PYTHONPATH=src python trail/experiments/import_observations.py \
  --input trail/experiments/example_observations.csv \
  --out artifacts/trail/experiments/observation_ledger.csv \
  --summary artifacts/trail/experiments/observation_ledger_summary.json
```

输出：

- `observation_ledger.csv`
- `observation_ledger_summary.json`

## 5. 与 PiEvo 的连接

后续 PiEvo-faithful 应把 ledger 中通过审核的 observation 加入 history：

```text
H_t = H_surrogate + H_real + H_literature
```

并在 likelihood 中考虑权重：

```text
log p_t(P) = log p0(P) + sum_s w_s * log p(y_s | h_s, P)
```

这样真实实验可以更快压低无法解释真实 Tg 的 principle，也可以提升能解释真实 anomaly 的 principle。

## 6. 人工闭环

建议人工审核字段：

- 是否真实合成成功。
- DSC 曲线是否可靠。
- 是否有多峰 Tg 或相分离。
- 固化程序是否完整。
- 样品是否降解。
- 是否应进入 active ledger。

人工审核不是替代模型，而是控制数据质量，避免错误实验记录污染 posterior。

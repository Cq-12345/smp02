# PiEvo-Faithful 外部观测 Ledger Smoke

本文档记录第四轮对 TODO 中“RL、人工闭环、真实实验结果迭代优化”的落实情况。当前仍然只使用单一小分子 SMILES / MoleCode 表示，不进入商品级组分或聚合物超图表示。

## 运行命令

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.cli \
  pievo-faithful \
  --config configs/pievo_faithful_ledger_smoke.yaml
```

## 本轮实现点

- `pievo_faithful` 支持读取外部 observation ledger。
- 通过 `ledger_pass` 的外部观测会作为 round 0 history 进入 posterior。
- posterior 更新从无权重乘积改为加权 log likelihood：

```text
log p_t(P) = log p0(P) + sum_s w_s log p(y_s | h_s, P)
```

- 每条观测单独携带 `target_tg_c`，支持不同真实 Tg 目标混合进入历史。
- 输出拆分为：
  - `observation_history.csv`：完整 posterior history。
  - `external_observations_used.csv`：实际接收的外部观测。
  - `selected_formulations.csv`：PiEvo 本轮新选择的 surrogate 配方。

## Smoke 结果

| item | value |
| --- | ---: |
| external input rows | 2 |
| external accepted rows | 2 |
| external rejected rows | 0 |
| external total authority weight | 6.0 |
| posterior history rows | 6 |
| posterior total authority weight | 10.0 |
| selected surrogate rows | 4 |
| best selected target distance (C) | 0.3653 |
| posterior entropy | 3.6636 |

外部来源计数：

```json
{"surrogate": 1, "real_dsc": 1}
```

本轮最佳新选择：

```text
predicted Tg = 249.63 C
target distance = 0.37 C
reward = 0.9296
```

## 解释

这个 smoke 证明 ledger 已经不只是文档或 CSV，而是真正进入了 PiEvo-faithful 的 full-history posterior。高权重真实观测可以通过 likelihood 项更快改变 principle posterior，从而更接近 PiEvo 中“用历史证据发现/淘汰原则”的数学结构。

当前 ledger 里的 `real_dsc` 行是 schema 占位示例，不是实际 DSC 结论。因此本报告只能证明接口和数学链路可运行，不能证明该占位配方有真实物理 Tg。

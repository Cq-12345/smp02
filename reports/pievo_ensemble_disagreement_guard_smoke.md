# PiEvo Live Ensemble Disagreement Guard Smoke

本文档回应 TODO 中“预测/评估 -> 优化假设”的进一步闭环要求：上一轮已完成固定候选表的 predictor ensemble disagreement 审计，本轮把 ensemble disagreement 改为 PiEvo 每轮候选批次的 live risk signal，并接入 IDS 选择域。

当前仍使用单一小分子 SMILES / MoleCode / VAE-WVCM 表示；不涉及暂缓的商品级组分、聚合物或超图表示。

## 运行命令

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.pievo_faithful \
  --config configs/pievo_faithful_ensemble_guard_195_smoke.yaml
```

输出目录：

- `artifacts/pievo_faithful_ensemble_guard_195_smoke/selected_formulations.csv`
- `artifacts/pievo_faithful_ensemble_guard_195_smoke/candidate_diagnostics.csv`
- `artifacts/pievo_faithful_ensemble_guard_195_smoke/round_history.json`
- `artifacts/pievo_faithful_ensemble_guard_195_smoke/predictor_ensemble_members.csv`
- `artifacts/pievo_faithful_ensemble_guard_195_smoke/pievo_faithful_summary.json`

## 配置要点

- 目标 Tg：195 C，target guard：5 C。
- PiEvo rounds：6。
- 每轮候选批次：260。
- Live ensemble 成员数：6。
- Ensemble guard：`predictor_ensemble_std_tg_c <= 25 C`。
- IDS 公式保持不变；guard 只收缩候选选择域，不进入 principle posterior likelihood。

## 结果汇总

| item | value |
| --- | ---: |
| selected rows | 6 |
| best selected target distance C | 0.0590 |
| all selected within target guard | true |
| all selected within ensemble guard | true |
| mean selected ensemble std C | 16.3977 |
| selected low-disagreement rows, std <= 10 C | 0 |
| selected high-disagreement rows, std >= 25 C | 0 |
| posterior entropy | 3.6107 |
| MAP principle | aromatic_backbones_raise_tg |

## 每轮选择

| round | selected Tg C | target distance C | selection method | risk-feasible candidates | selected ensemble std C | bucket |
| ---: | ---: | ---: | --- | ---: | ---: | --- |
| 1 | 197.64 | 2.64 | target_and_ensemble_guard_warmup_max_variance | 3 | 14.57 | moderate_disagreement |
| 2 | 191.81 | 3.19 | target_and_ensemble_guard_warmup_max_variance | 5 | 15.72 | moderate_disagreement |
| 3 | 195.06 | 0.06 | target_and_ensemble_guard_ids_min_regret2_over_information | 7 | 20.33 | moderate_disagreement |
| 4 | 194.04 | 0.96 | target_and_ensemble_guard_ids_min_regret2_over_information | 5 | 15.91 | moderate_disagreement |
| 5 | 195.89 | 0.89 | target_and_ensemble_guard_ids_min_regret2_over_information | 4 | 10.62 | moderate_disagreement |
| 6 | 196.61 | 1.61 | target_and_ensemble_guard_ids_min_regret2_over_information | 5 | 21.24 | moderate_disagreement |

## 解释

- 这次不是把上一轮 `candidate_space_top_scored.csv` 的 disagreement 结果硬 join 到 PiEvo。实际检查显示该固定候选池与 PiEvo 当前 smoke 的每轮候选没有交集，因此本轮改为 live ensemble prediction。
- `target_and_ensemble_guard_*` 表示两层 guard 都实际启用：先要求 primary GPR prediction 距 195 C 不超过 5 C，再要求同一候选的 ensemble std 不超过 25 C。
- 本轮 selected 没有进入 `low_disagreement`，但全部避开了 `high_disagreement`。这说明在当前候选批次和 6 轮 smoke 下，PiEvo 更偏向中等分歧但目标接近的候选。
- Ensemble disagreement 是 epistemic/OOD 风险信号，不是物理真实不确定性。它不应直接改变 principle posterior；真实 DSC 或高保真 observation 仍应以更高 authority weight 进入 full-history posterior。

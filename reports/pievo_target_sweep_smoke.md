# PiEvo-Faithful 多目标 Tg Smoke

本文档回应 TODO 中“真实 Tg 温度不固定”的要求：这里不是对同一个候选池重排序，而是把不同目标 Tg 分别放入 PiEvo-faithful 闭环运行。

- Base config: `configs/pievo_faithful_smoke.yaml`

## Summary

| target Tg (C) | best selected Tg (C) | selected distance (C) | closest candidate Tg (C) | closest distance (C) | all selected within guard | MAP principle | pass |
| ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 190.0 | 189.87 | 0.13 | 189.87 | 0.13 | True | maleimide_rigid_network | True |
| 200.0 | 199.89 | 0.11 | 199.89 | 0.11 | True | aromatic_backbones_raise_tg | True |
| 250.0 | 249.47 | 0.53 | 249.47 | 0.53 | True | reaction_839cd29ef5d7 | True |

## Interpretation

- `target_tg_c` 已经是闭环任务参数，不再只是后处理筛选参数。
- 每个目标都拥有独立 output directory、round history、posterior 和 selected formulations。
- `best selected` 表示 target-feasible IDS/暖启动实际选择并写入 observation history 的最好样本；`closest candidate` 表示该目标运行过程中候选诊断表里最接近目标的样本。
- target guard 启用后，IDS 仍按信息增益选择，但搜索域被限制在近目标可行候选中；若没有足够近目标候选，系统才回退到全候选。
- 该 smoke 使用小规模候选批次，适合验证链路；正式运行应提高 `candidate_batch_size` 和 `rounds`。

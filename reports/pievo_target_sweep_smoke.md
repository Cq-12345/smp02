# PiEvo-Faithful 多目标 Tg Smoke

本文档回应 TODO 中“真实 Tg 温度不固定”的要求：这里不是对同一个候选池重排序，而是把不同目标 Tg 分别放入 PiEvo-faithful 闭环运行。

- Base config: `configs/pievo_faithful_smoke.yaml`

## Summary

| target Tg (C) | best selected Tg (C) | selected distance (C) | closest candidate Tg (C) | closest distance (C) | MAP principle | pass |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 190.0 | 159.68 | 30.32 | 189.87 | 0.13 | aromatic_backbones_raise_tg | True |
| 200.0 | 239.72 | 39.72 | 200.23 | 0.23 | maleimide_rigid_network | True |
| 250.0 | 266.89 | 16.89 | 249.63 | 0.37 | aromatic_backbones_raise_tg | True |

## Interpretation

- `target_tg_c` 已经是闭环任务参数，不再只是后处理筛选参数。
- 每个目标都拥有独立 output directory、round history、posterior 和 selected formulations。
- `best selected` 表示 IDS/暖启动实际选择并写入 observation history 的最好样本；`closest candidate` 表示该目标运行过程中候选诊断表里最接近目标的样本。
- 如果 `best selected` 明显差于 `closest candidate`，说明短 smoke 的探索策略还没有充分利用近目标候选；正式运行应提高 rounds、降低 warmup 或加入目标命中约束。
- 该 smoke 使用小规模候选批次，适合验证链路；正式运行应提高 `candidate_batch_size` 和 `rounds`。

# Replacement Proposals Into PiEvo-Faithful Smoke

本文档记录 VAE replacement proposals 进入 PiEvo-faithful 的闭环结果。当前仍然只使用单一小分子 SMILES / MoleCode 表示，不涉及商品级组分或聚合物超图。

## Pipeline

```text
replacement_proposals.csv
  -> rebuild complete formulations
  -> VAE-WVCM-GPR prediction
  -> Harness validation
  -> replacement observation ledger
  -> PiEvo-faithful external history
```

## Replacement Evaluation

| item | value |
| --- | ---: |
| input proposals | 120 |
| rebuilt formulas | 107 |
| scored formulas | 107 |
| harness pass | 10 |
| rejected proposals | 13 |
| best replacement distance (C) | 0.3732 |
| within 1C | 4 |
| within 5C | 10 |

输出：

- `artifacts/trail/generation/replacement_eval/replacement_proposals_scored.csv`
- `artifacts/trail/generation/replacement_eval/replacement_proposals_harness.csv`
- `artifacts/trail/generation/replacement_eval/replacement_observation_ledger.csv`

## PiEvo-Faithful Smoke

配置：

```bash
PYTHONPATH=src /home/user4/conda_envs/mhc_pyg314/bin/python -m smp02.cli \
  pievo-faithful \
  --config configs/pievo_faithful_replacement_195_smoke.yaml
```

结果：

| item | value |
| --- | ---: |
| accepted replacement observations | 10 |
| external authority weight | 10.0 |
| posterior history rows | 14 |
| selected surrogate rows | 4 |
| all selected within 5C guard | true |
| best selected distance (C) | 0.0055 |
| posterior entropy | 2.4869 |

本轮 PiEvo 新选择的最好配方预测 Tg 为 194.99 C，距 195 C 目标 0.01 C。

## Interpretation

- Replacement proposals 现在已经不是孤立 CSV，而是进入了 `生成 -> 预测 -> Harness -> observation ledger -> PiEvo posterior` 的闭环。
- 10 条 replacement surrogate observation 作为外部历史影响 principle posterior；当前 MAP principle 为 `long_aliphatic_penalty`。
- Replacement 评估脚本现在默认使用 CPU deterministic VAE encoding；这里报告的是稳定审计路径，不是 CUDA 非确定路径的瞬时数值。
- 这些 observation 仍然是 surrogate 证据，不是真实 DSC。它们适合用于候选筛选、posterior 预热和人工审核优先级排序。

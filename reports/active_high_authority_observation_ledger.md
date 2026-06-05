# Active High-authority Observation Ledger

本文档记录哪些 observation ledger 行可以作为 active evidence 进入后续 PiEvo posterior、策略更新或人工闭环统计。
当前规则只接受已经通过 `ledger_pass` 的 `high_fidelity_simulation`、`real_dsc`、`literature`；`surrogate` 不进入这一层。

## Summary

| item | value |
| --- | ---: |
| input_rows | 0 |
| ledger_pass_rows | 0 |
| allowed_source_rows | 0 |
| active_rows | 0 |
| validation_result_active_rows | 0 |
| authority_weight_sum | 0.0 |
| max_authority_weight | None |
| mean_target_distance_c | None |
| mean_weighted_reward | None |

## Outputs

- active ledger: `artifacts/trail/human_review/active_high_authority_observation_ledger.csv`

## Gate Rules

- 必须已经通过前一层 observation ledger 的 `ledger_pass`。
- `source_type` 必须属于 `high_fidelity_simulation`、`real_dsc` 或 `literature`。
- validation request result 仍必须先经过 request/source/process/reviewer gate；本脚本不接收原始 result template。
- 当前若 `active_rows=0`，表示还没有完成并获批的高权重观测，不表示候选生成链路失败。

# Active Evidence PiEvo Bridge

本文档验证 active high-authority observation ledger 是否已经能进入 PiEvo 的外部观测加载和 full-history posterior 更新路径。
它不生成新候选，也不把 surrogate 候选升级成真实证据。

## Summary

| item | value |
| --- | ---: |
| external_input_rows | 0 |
| external_candidate_rows_after_ledger_pass | 0 |
| external_candidate_rows_after_source_filter | 0 |
| external_candidate_rows_after_active_filter | 0 |
| external_accepted_rows | 0 |
| external_rejected_rows | 0 |
| posterior_history_rows | 0 |
| total_authority_weight | 0.0 |
| posterior_entropy | 3.663561646129646 |

## Gate

- external ledger: `artifacts/trail/human_review/active_high_authority_observation_ledger.csv`
- allowed source types: `['high_fidelity_simulation', 'real_dsc', 'literature']`
- require active evidence: `True`
- bridge status: `no_active_evidence_noop`

## Interpretation

- `active_evidence_updates_posterior` 表示已有高权重观测进入 full-history posterior；当前为 false 时，本 bridge 的 posterior 输入仅为先验，主闭环仍依赖 surrogate smoke 证据。
- `no_active_evidence_noop` 表示 active ledger 为空或没有可接收行，这是正确的质量门行为。
- 如果未来填入真实 DSC、高保真模拟或文献复现实验，本脚本会在同一路径中记录 accepted rows、authority weight 和 posterior MAP principle。

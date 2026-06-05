# Proposal Evaluation -> Generation Records

本文档把已经完成 predictor/Harness 的 replacement 或 VAE latent local search proposals 写回 generation record ledger。这样 SFT、扩散/流匹配和策略回流不只依赖少量 prompt/RAG smoke records。

## 输出文件

- Input records: `artifacts/trail/generation/expanded_inventory_replacement_records/proposal_generation_records_input.csv`
- Ledger: `artifacts/trail/generation/expanded_inventory_replacement_records/generation_record_ledger.csv`
- Summary: `artifacts/trail/generation/expanded_inventory_replacement_records/generation_record_summary.json`
- Report: `reports/expanded_inventory_replacement_generation_records.md`

## Summary

| item | value |
| --- | ---: |
| input_rows | 200 |
| record_pass_rows | 200 |
| ready_for_prediction_rows | 0 |
| harness_pass_rows | 18 |
| harness_fail_rows | 182 |
| best_distance_c | 0.2004599427478979 |
| mean_generation_reward | 0.09395763800555328 |
| reward_temperature_c | 5.0 |
| strategy | functional_group_replacement |
| source_context | expanded_inventory_replacement_eval |
| input_records_path | artifacts/trail/generation/expanded_inventory_replacement_records/proposal_generation_records_input.csv |
| generation_record_ledger_path | artifacts/trail/generation/expanded_inventory_replacement_records/generation_record_ledger.csv |

## Harness State

| item | value |
| --- | ---: |
| input_records | 200 |
| ledger_rows | 200 |
| harness_pass | 18 |
| record_pass | 200 |

## 解释

- 这些 records 来自已评分 proposals，不是新的真实实验。
- importer 会重新检查 SMILES、ratio、target window 和 compatibility evidence；失败项保留在 ledger 中用于反馈，训练集构建器只使用通过项。
- 这样可以扩大 SFT / diffusion / flow 的 validated training corpus，同时保持 Harness 和审计链不被绕过。

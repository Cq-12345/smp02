# Rule-template Generation Records

本文档把枚举搜索空间中的近目标候选写成 `rule_template` generation records。它们不是新物理实验，而是规则/模板生成器的可审计基线种子。

## 输出文件

- Input records: `artifacts/trail/generation/rule_template_records/rule_template_generation_records_input.csv`
- Ledger: `artifacts/trail/generation/rule_template_records/generation_record_ledger.csv`
- Summary: `artifacts/trail/generation/rule_template_records/generation_record_summary.json`
- Report: `reports/rule_template_generation_records.md`

## Summary

| item | value |
| --- | ---: |
| input_rows | 50 |
| record_pass_rows | 50 |
| ready_for_prediction_rows | 0 |
| harness_pass_rows | 50 |
| harness_fail_rows | 0 |
| best_distance_c | 0.0031802513673540034 |
| mean_generation_reward | 0.9887598357832142 |
| reward_temperature_c | 5.0 |
| target_tg_c | 195.0 |
| target_window_c | 5.0 |
| selected_candidates_path | artifacts/reproduce/discovery/selected_candidates.csv |
| input_records_path | artifacts/trail/generation/rule_template_records/rule_template_generation_records_input.csv |
| generation_record_ledger_path | artifacts/trail/generation/rule_template_records/generation_record_ledger.csv |

## 解释

- 这些 records 来自当前小分子 SMILES / MoleCode 搜索空间，不进入暂缓的商品级/聚合物超图表示。
- importer 会重新检查 RDKit、ratio、target window 和 compatibility evidence；失败项不会进入训练标签。
- 它们为 SFT 和 diffusion/flow 提供规则模板基线种子，后续生成器输出仍必须走同一 Harness/PiEvo/人工审核链路。

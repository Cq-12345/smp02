# Process Record Schema Smoke

本文档回应 TODO 中“真实实验结果迭代优化、人工闭环、文献配方/固化程序结构化”的要求。当前仍只处理单一小分子 SMILES / MoleCode，不做商品级复杂组分或聚合物超图表示。

## Outputs

- Schema: `trail/experiments/process_record_schema.yaml`
- Example input: `trail/experiments/example_process_records.csv`
- Importer: `trail/experiments/import_process_records.py`
- Ledger: `artifacts/trail/experiments/process_record_ledger.csv`
- Summary: `artifacts/trail/experiments/process_record_summary.json`

## Summary

| item | value |
| --- | ---: |
| input rows | 3 |
| process record pass | 3 |
| ready for active ledger | 0 |
| process incomplete rows | 3 |
| literature rows | 2 |
| surrogate review rows | 1 |

## Records

| record | source | template | Tg distance (C) | ready | missing fields |
| --- | --- | --- | ---: | --- | --- |
| paper_table6_A | literature | anhydride_amine_imidization | 16.86 | false | solvent;imidization_temperature_c;imidization_time_h |
| paper_table6_B | literature | anhydride_amine_imidization | 27.07 | false | solvent;imidization_temperature_c;imidization_time_h |
| replacement_surrogate_107 | surrogate_review | cyanate_ester_triazine_cure | 0.37 | false | trimerization_temperature_c;catalyst_loading;post_cure_temperature_c |

## Interpretation

- Observation ledger 负责 Tg/reward/authority；process record ledger 负责固化程序、催化剂、后固化和人工审核完整性。
- Paper Table 6 的 A/B 文献 Tg 已能结构化记录，但当前缺少可复现实验工艺字段，因此不能直接标记为 `approved_for_active_ledger`。
- Replacement surrogate 107 虽然预测接近 195 C，但仍需要人工提出氰酸酯三聚/共反应的工艺条件，才适合进入真实实验计划。
- 这一步避免把“有 Tg 数字”的记录自动当作高权重真实证据；缺工艺条件的记录只能作为待审核上下文。

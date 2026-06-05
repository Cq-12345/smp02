# Generation Record Schema Smoke

本文档记录 TODO 中“LLM / prompt / RAG / Harness 约束控制”的落地状态。当前没有调用外部 LLM；本 smoke 用可复现的候选模拟 LLM/RAG 输出，目的是固定输入输出契约和失败回流字段。

## Outputs

- Prompt/RAG packet: `artifacts/trail/generation/prompt_records/prompt_rag_packet.md`
- Input records: `artifacts/trail/generation/prompt_records/prompt_generation_records_input.csv`
- Ledger: `artifacts/trail/generation/prompt_records/generation_record_ledger.csv`
- Summary: `artifacts/trail/generation/prompt_records/generation_record_summary.json`

## Summary

| item | value |
| --- | ---: |
| input_rows | 4 |
| record_pass_rows | 4 |
| ready_for_prediction_rows | 1 |
| harness_pass_rows | 3 |
| harness_fail_rows | 1 |
| best_distance_c | 0.0031802513673540034 |
| mean_generation_reward | 0.9754536990269568 |
| reward_temperature_c | 5.0 |

## Strategy Counts

| strategy | rows |
| --- | ---: |
| llm_rag_principle_generation | 2 |
| functional_group_replacement | 1 |
| llm_smiles_generation | 1 |

## Records

| generation id | strategy | stage | predicted Tg (C) | distance (C) | harness | failure reason |
| --- | --- | --- | ---: | ---: | --- | --- |
| prompt_rag_selected_001 | llm_rag_principle_generation | harnessed | 195.00 | 0.00 | True |  |
| prompt_rag_selected_002 | llm_rag_principle_generation | harnessed | 195.01 | 0.01 | True |  |
| prompt_rag_replacement_001 | functional_group_replacement | harnessed | 194.63 | 0.37 | True |  |
| prompt_rag_failed_001 | llm_smiles_generation | draft |  |  | False | prediction_missing;chemistry_evidence_missing;replacement_formula_failed_reaction_or_ratio_constraints |

## Interpretation

- `generation_record_schema.yaml` 现在把 prompt、RAG refs、候选 JSON、预测值、Harness 判定和 PiEvo 选择状态放在同一个 ledger 契约里。
- `llm_smiles_generation` 的失败样例说明：LLM/RAG 草案即使 SMILES 有效，也可能因为缺预测、缺化学兼容证据或反应/比例约束失败而不能进入推荐。
- 后续真正接入 LLM、SFT、扩散或流匹配时，应先写 generation record，再进入 predictor/Harness/PiEvo。

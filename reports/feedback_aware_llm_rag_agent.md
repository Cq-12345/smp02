# Feedback-Aware LLM/RAG Agent Smoke

本文档记录一个真正可运行的 LLM/RAG agent 契约：agent 读取知识库 RAG 上下文、generation feedback policy，并输出 `generation_record_schema.yaml` 约束下的候选 records。当前运行使用 `offline_policy` provider 保持可复现；如果设置 `OPENAI_API_KEY`，同一脚本可切到 `openai_compatible` provider，但输出仍必须先进入 generation ledger、predictor/Harness/PiEvo。

## Outputs

- Agent packet: `artifacts/trail/generation/feedback_aware_llm_rag/feedback_aware_llm_rag_packet.md`
- Input records: `artifacts/trail/generation/feedback_aware_llm_rag/feedback_aware_generation_records_input.csv`
- Ledger: `artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv`
- Summary: `artifacts/trail/generation/feedback_aware_llm_rag/generation_record_summary.json`

## Provider And Policy

- provider: `offline_policy`
- preferred strategies: `functional_group_replacement, llm_rag_principle_generation`
- suppressed strategies: `llm_smiles_generation`

## Summary

| item | value |
| --- | ---: |
| input_rows | 2 |
| record_pass_rows | 2 |
| ready_for_prediction_rows | 0 |
| harness_pass_rows | 2 |
| harness_fail_rows | 0 |
| best_distance_c | 0.0031802513673540034 |
| mean_generation_reward | 0.9637168072058939 |
| reward_temperature_c | 5.0 |

## Records

| generation id | strategy | stage | predicted Tg (C) | distance (C) | harness | failure reason |
| --- | --- | --- | ---: | ---: | --- | --- |
| feedback_rag_selected_001 | llm_rag_principle_generation | harnessed | 195.00 | 0.00 | True |  |
| feedback_rag_replacement_context_001 | llm_rag_principle_generation | harnessed | 194.63 | 0.37 | True |  |

## Interpretation

- `llm_smiles_generation` 当前被 policy 抑制，因为上一轮反馈显示其 pass rate 为 0 且缺 predictor/chemistry evidence。
- `functional_group_replacement` 和 `llm_rag_principle_generation` 在 strict feedback 中都被保留；agent 用成功 strict replacement 记录作为 RAG 证据，而不是继续沿用旧失败状态。
- `llm_rag_principle_generation` 被保留，用 RAG 上下文和成功 strict replacement 记录提出候选原则/配方证据。
- 这一步不是绕过 Harness 的自由文本生成；所有候选先进入 generation record ledger，再由 importer 计算 SMILES、ratio、prediction、target 和 chemistry gate。
- 真正外部 LLM 只负责提出候选 JSON；是否可信仍由 RDKit、predictor、Harness、PiEvo 和人工审核决定。

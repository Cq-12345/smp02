# Feedback-Aware LLM/RAG Records To PiEvo

本文档记录 `feedback-aware LLM/RAG agent -> generation ledger -> observation ledger -> PiEvo-faithful posterior` 的闭环。当前仍使用单一小分子 SMILES / MoleCode；这里的 observation source 是 `surrogate`，因为 Tg 来自 VAE-WVCM-GPR 预测，不是真实 DSC。

## Outputs

- Generation ledger: `artifacts/trail/generation/feedback_aware_llm_rag/generation_record_ledger.csv`
- Observation input: `artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observations_input.csv`
- Observation ledger: `artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger.csv`
- Observation summary: `artifacts/trail/generation/feedback_aware_llm_rag_observations/generation_observation_ledger_summary.json`
- PiEvo output: `artifacts/pievo_faithful_feedback_aware_llm_rag_195_smoke`

## Observation Ledger Summary

| item | value |
| --- | ---: |
| input_rows | 2 |
| ledger_pass_rows | 2 |
| mean_target_distance_c | 0.18821186873655904 |
| mean_weighted_reward | 0.9637168072058939 |
| reward_temperature_c | 5.0 |

## Imported Records

| observation id | source | Tg (C) | distance (C) | ledger pass | method |
| --- | --- | ---: | ---: | --- | --- |
| feedback_aware_llm_rag_llm_rag_principle_generation_feedback_rag_selected_001 | surrogate | 194.997 | 0.003 | True | generation_record_surrogate_bridge |
| feedback_aware_llm_rag_llm_rag_principle_generation_feedback_rag_replacement_context_001 | surrogate | 194.627 | 0.373 | True | generation_record_surrogate_bridge |

## PiEvo Feedback

| item | value |
| --- | ---: |
| external accepted rows | 2 |
| external total authority weight | 2.0 |
| external mean reward | 0.9637168072058939 |
| PiEvo rounds | 6 |
| history rows | 8 |
| selected rows | 6 |
| best selected distance C | 0.005546302352854582 |
| posterior entropy | 3.503753334197624 |
| MAP principle | reaction_a5dd26ae10ad |

## Interpretation

- 这一步把 LLM/RAG agent 的成功 records 作为低权重 surrogate observations 接入 PiEvo full-history posterior。
- 失败或缺预测的 generation records 不会进入 observation ledger；它们仍留在 generation feedback 中约束下一轮生成。
- 这不是把 LLM 输出当成物理事实，而是让 PiEvo 能审计“由 LLM/RAG 生成、由 predictor/Harness 验证过”的候选证据。

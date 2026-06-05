# Generation Strategy Bandit Policy

本文档把 TODO 中“RL、人工闭环、搜索空间优化”的部分落成一个可审计的 strategy-level contextual bandit。这里的 arm 是生成策略，reward 来自 Harness pass、target reward 和 observation throughput；它不是物理真理，也不替代 PiEvo IDS。

## 输出文件

- Policy table: `artifacts/trail/generation_strategy_policy/generation_strategy_bandit_policy.csv`
- Summary: `artifacts/trail/generation_strategy_policy/generation_strategy_bandit_summary.json`
- Report: `reports/generation_strategy_bandit_policy.md`

## Summary

| item | value |
| --- | ---: |
| strategies | 6 |
| eligible_active_strategies | 3 |
| total_attempts | 413 |
| total_budget | 100 |
| top_strategy | llm_rag_principle_generation |
| suppressed_strategies | 1 |
| data_collection_only_strategies | 2 |

## Policy

| strategy | status | attempts | successes | beta pass mean | utility | UCB bonus | score | allocation/100 | review | action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| llm_rag_principle_generation | active | 2 | 2 | 0.750 | 0.840 | 0.354 | 1.294 | 89 | high | allocate 89/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| functional_group_replacement | active | 200 | 18 | 0.094 | 0.484 | 0.043 | 0.627 | 6 | high | allocate 6/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| vae_latent_local_search | active | 200 | 42 | 0.213 | 0.549 | 0.043 | 0.593 | 5 | high | allocate 5/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| sft_candidate_generator | data_collection_only | 5 | 0 | 0.059 | 0.059 | 0.251 | -0.241 | 0 | gate_review | collect more Harness-passing, prediction-backed generation records before training. |
| diffusion_or_flow_matching | data_collection_only | 5 | 0 | 0.010 | 0.010 | 0.251 | -0.289 | 0 | gate_review | collect more Harness-passing, prediction-backed generation records before training. |
| llm_smiles_generation | suppressed | 1 | 0 | 0.333 | 0.333 | 0.434 | -0.383 | 0 | gate_review | predictor_feedback: run VAE-WVCM/GNN predictor before recommendation. |

## 解释

- `allocation_per_100` 是下一轮生成预算建议，不是最终推荐配方。
- `sft_candidate_generator` 和 `diffusion_or_flow_matching` 在 readiness gate 未通过前不获得训练/生成预算，只获得数据收集建议。
- `llm_smiles_generation` 若仍缺 predictor 或 chemistry evidence，会被压到 gate review，而不是进入 PiEvo 或实验推荐。
- 高 allocation 的策略仍必须把候选写入 generation/proposal ledger，再经过 predictor、Harness、PiEvo 和人工审核。

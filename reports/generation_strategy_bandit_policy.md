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
| eligible_active_strategies | 4 |
| total_attempts | 492 |
| total_budget | 100 |
| top_strategy | llm_rag_principle_generation |
| suppressed_strategies | 1 |
| data_collection_only_strategies | 1 |

## Policy

| strategy | status | attempts | successes | beta pass mean | utility | UCB bonus | score | allocation/100 | review | action |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| llm_rag_principle_generation | active | 2 | 2 | 0.750 | 0.840 | 0.359 | 1.299 | 70 | high | allocate 70/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| sft_candidate_generator | active | 25 | 25 | 0.963 | 0.880 | 0.122 | 1.002 | 21 | high | allocate 21/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| functional_group_replacement | active | 200 | 18 | 0.094 | 0.484 | 0.044 | 0.628 | 5 | high | allocate 5/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| vae_latent_local_search | active | 200 | 42 | 0.213 | 0.549 | 0.044 | 0.593 | 4 | high | allocate 4/100 next-round proposal budget; keep predictor/Harness/PiEvo gates active. |
| llm_smiles_generation | suppressed | 1 | 0 | 0.333 | 0.333 | 0.440 | -0.376 | 0 | gate_review | predictor_feedback: run VAE-WVCM/GNN predictor before recommendation. |
| diffusion_or_flow_matching | data_collection_only | 64 | 0 | 0.026 | 0.026 | 0.077 | -0.446 | 0 | gate_review | collect more Harness-passing, prediction-backed generation records before training. |

## 解释

- `allocation_per_100` 是下一轮生成预算建议，不是最终推荐配方。
- `sft_candidate_generator` 只有在 SFT JSONL 达到最小样本和 eval split 后才会成为 active arm；否则只保留数据收集建议。
- `diffusion_or_flow_matching` 在 seed table 未达到最小样本前不获得训练/生成预算，只获得数据收集建议。
- `llm_smiles_generation` 若仍缺 predictor 或 chemistry evidence，会被压到 gate review，而不是进入 PiEvo 或实验推荐。
- 高 allocation 的策略仍必须把候选写入 generation/proposal ledger，再经过 predictor、Harness、PiEvo 和人工审核。

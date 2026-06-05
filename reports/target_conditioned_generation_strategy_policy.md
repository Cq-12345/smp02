# Target-conditioned Generation Strategy Policy

本文档把“真实 Tg 不固定”的要求落成目标条件化的下一轮生成预算。它保留当前全局 strategy bandit，但不再把 195 C 附近的全局证据直接外推到所有目标。

## 输出文件

- Policy table: `artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_policy.csv`
- Target summary: `artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_target_summary.csv`
- Summary: `artifacts/trail/generation_strategy_policy_target_conditioned/target_conditioned_generation_strategy_summary.json`
- Report: `reports/target_conditioned_generation_strategy_policy.md`

## Summary

| item | value |
| --- | ---: |
| targets | 4 |
| target_values | [190.0, 195.0, 200.0, 250.0] |
| strategies_per_target | 6 |
| total_budget_per_target | 100 |
| base_transfer_budget | 25 |
| min_transfer_budget | 8 |
| reference_transfer_target_tg_c | 195.0 |
| transfer_decay_c | 80.0 |
| target_specific_strategies | ['functional_group_replacement', 'vae_latent_local_search'] |
| transfer_strategies | ['llm_rag_principle_generation', 'sft_candidate_generator', 'diffusion_or_flow_matching', 'llm_smiles_generation'] |
| all_targets_allocation_sum_100 | True |
| top_strategy_by_target | {'190.0': 'vae_latent_local_search', '195.0': 'vae_latent_local_search', '200.0': 'vae_latent_local_search', '250.0': 'functional_group_replacement'} |
| top_target_specific_strategy_by_target | {'190.0': 'vae_latent_local_search', '195.0': 'vae_latent_local_search', '200.0': 'vae_latent_local_search', '250.0': 'functional_group_replacement'} |
| transfer_budget_by_target | {'190.0': 23, '195.0': 25, '200.0': 23, '250.0': 13} |
| sparse_targets | [] |
| sparse_target_count | 0 |
| target_high_authority_evidence_status | awaiting_target_high_authority_evidence |
| target_high_authority_budget_mode | target_surrogate_backed_allocation |
| target_high_authority_next_action | execute target-specific validation requests before changing target-conditioned budgets with high-authority evidence. |
| target_high_authority_active_targets | [] |
| target_high_authority_rows_by_target | {'190.0': 0, '195.0': 0, '200.0': 0, '250.0': 0} |
| target_high_authority_authority_weight_by_target | {'190.0': 0.0, '195.0': 0.0, '200.0': 0.0, '250.0': 0.0} |
| active_evidence_bridge_status | no_active_evidence_noop |
| active_evidence_updates_pievo_posterior | False |

## Target High-authority Evidence Gate

- Status: `awaiting_target_high_authority_evidence`
- Budget mode: `target_surrogate_backed_allocation`
- Active target rows: `{'190.0': 0, '195.0': 0, '200.0': 0, '250.0': 0}`
- Active evidence bridge status: `no_active_evidence_noop`
- Active evidence updates PiEvo posterior: `False`
- Next action: execute target-specific validation requests before changing target-conditioned budgets with high-authority evidence.

当前 target-conditioned allocation 仍由 target sweep 和 global-transfer surrogate evidence 计算；高权重 evidence 进入 PiEvo posterior 后，应先按目标比较 posterior shift，再调整每个 Tg 的预算。

## Target Summary

| target Tg C | target-specific budget | transferable budget | target successes | active high-authority rows | active authority weight | top strategy | top target-specific strategy | sparse |
| ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| 190.0 | 77 | 23 | 51 | 0 | 0.0 | vae_latent_local_search | vae_latent_local_search | False |
| 195.0 | 75 | 25 | 53 | 0 | 0.0 | vae_latent_local_search | vae_latent_local_search | False |
| 200.0 | 77 | 23 | 52 | 0 | 0.0 | vae_latent_local_search | vae_latent_local_search | False |
| 250.0 | 87 | 13 | 47 | 0 | 0.0 | functional_group_replacement | functional_group_replacement | False |

## Policy

| target Tg C | strategy | scope | status | attempts | successes | best selected distance C | score | allocation/100 | action |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 190.0 | vae_latent_local_search | target_sweep | active | 200 | 38 | 0.002 | 0.756 | 44 | allocate 44/100 for 190.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 190.0 | functional_group_replacement | target_sweep | active | 120 | 13 | 0.057 | 0.705 | 33 | allocate 33/100 for 190.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 190.0 | llm_rag_principle_generation | global_transfer | active | 2 | 2 | 0.003 | 1.218 | 12 | allocate 12/100 transferable exploration budget from 195.0 C evidence; validate at 190.0 C before use. |
| 190.0 | sft_candidate_generator | global_transfer | active | 23 | 23 | 0.003 | 1.029 | 6 | allocate 6/100 transferable exploration budget from 195.0 C evidence; validate at 190.0 C before use. |
| 190.0 | diffusion_or_flow_matching | global_transfer | active | 23 | 23 | 0.005 | 0.991 | 5 | allocate 5/100 transferable exploration budget from 195.0 C evidence; validate at 190.0 C before use. |
| 190.0 | llm_smiles_generation | global_transfer | suppressed | 1 | 0 |  | -0.357 | 0 | hold: wait for predictor/chemistry/Harness evidence before allocating target budget. |
| 195.0 | vae_latent_local_search | target_sweep | active | 200 | 42 | 0.059 | 0.747 | 39 | allocate 39/100 for 195.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 195.0 | functional_group_replacement | target_sweep | active | 120 | 11 | 0.006 | 0.732 | 36 | allocate 36/100 for 195.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 195.0 | llm_rag_principle_generation | global_transfer | active | 2 | 2 | 0.003 | 1.297 | 14 | allocate 14/100 transferable exploration budget from 195.0 C evidence; validate at 195.0 C before use. |
| 195.0 | sft_candidate_generator | global_transfer | active | 23 | 23 | 0.003 | 1.095 | 6 | allocate 6/100 transferable exploration budget from 195.0 C evidence; validate at 195.0 C before use. |
| 195.0 | diffusion_or_flow_matching | global_transfer | active | 23 | 23 | 0.005 | 1.055 | 5 | allocate 5/100 transferable exploration budget from 195.0 C evidence; validate at 195.0 C before use. |
| 195.0 | llm_smiles_generation | global_transfer | suppressed | 1 | 0 |  | -0.380 | 0 | hold: wait for predictor/chemistry/Harness evidence before allocating target budget. |
| 200.0 | vae_latent_local_search | target_sweep | active | 200 | 41 | 0.043 | 0.746 | 41 | allocate 41/100 for 200.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 200.0 | functional_group_replacement | target_sweep | active | 120 | 11 | 0.204 | 0.723 | 36 | allocate 36/100 for 200.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 200.0 | llm_rag_principle_generation | global_transfer | active | 2 | 2 | 0.003 | 1.218 | 12 | allocate 12/100 transferable exploration budget from 195.0 C evidence; validate at 200.0 C before use. |
| 200.0 | sft_candidate_generator | global_transfer | active | 23 | 23 | 0.003 | 1.029 | 6 | allocate 6/100 transferable exploration budget from 195.0 C evidence; validate at 200.0 C before use. |
| 200.0 | diffusion_or_flow_matching | global_transfer | active | 23 | 23 | 0.005 | 0.991 | 5 | allocate 5/100 transferable exploration budget from 195.0 C evidence; validate at 200.0 C before use. |
| 200.0 | llm_smiles_generation | global_transfer | suppressed | 1 | 0 |  | -0.357 | 0 | hold: wait for predictor/chemistry/Harness evidence before allocating target budget. |
| 250.0 | functional_group_replacement | target_sweep | active | 320 | 42 | 0.099 | 0.718 | 51 | allocate 51/100 for 250.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 250.0 | vae_latent_local_search | target_sweep | active | 200 | 5 | 0.511 | 0.654 | 36 | allocate 36/100 for 250.0 C target-conditioned proposals; rerun ledger, predictor, Harness and PiEvo. |
| 250.0 | llm_rag_principle_generation | global_transfer | active | 2 | 2 | 0.003 | 0.652 | 7 | allocate 7/100 transferable exploration budget from 195.0 C evidence; validate at 250.0 C before use. |
| 250.0 | sft_candidate_generator | global_transfer | active | 23 | 23 | 0.003 | 0.551 | 3 | allocate 3/100 transferable exploration budget from 195.0 C evidence; validate at 250.0 C before use. |
| 250.0 | diffusion_or_flow_matching | global_transfer | active | 23 | 23 | 0.005 | 0.531 | 3 | allocate 3/100 transferable exploration budget from 195.0 C evidence; validate at 250.0 C before use. |
| 250.0 | llm_smiles_generation | global_transfer | suppressed | 1 | 0 |  | -0.191 | 0 | hold: wait for predictor/chemistry/Harness evidence before allocating target budget. |

## 解释

- `target_sweep` 证据来自该目标 Tg 下实际跑过的 replacement/VAE latent sweep、sparse-target expansion 和 PiEvo selected reward；同一目标下会优先采用更强的 replacement evidence。
- `global_transfer` 证据来自全局 strategy bandit；它只拿可迁移 exploration budget，且离 195 C 参考目标越远预算越小。
- `allocation_per_100` 是下一轮 proposal 预算，不是最终配方推荐；所有候选仍必须写入 ledger，并重新经过 predictor、Harness、PiEvo 和人工审核。
- `sparse_targets` 非空时，含义是目标条件化成功样本少，应优先扩大对应温区候选池或引入新 principle，而不是把 195 C 规律硬外推；当前若为空，只表示 sample-count gate 暂时通过，不表示物理真值已验证。

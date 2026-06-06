# External Generator Output Checklist

本文档把真实外部 LLM/SFT/decoder/flow 输出接入前的门禁结构化。它不调用外部模型，也不把 draft 输出当作 observation。

## Summary

| item | value |
| --- | ---: |
| checklist_rows | 4 |
| ready_external_provider_rows | 3 |
| suppressed_or_blocked_rows | 1 |
| sft_ready | True |
| diffusion_flow_ready | True |
| sft_examples | 268 |
| diffusion_flow_seed_rows | 268 |
| strategy_policy_top_strategy | llm_rag_principle_generation |
| strategy_policy_high_authority_evidence_status | awaiting_high_authority_evidence |
| creates_observation | False |
| evidence_level | external_generator_output_checklist_not_observation |
| checklist_path | artifacts/trail/generation/external_generator_output_checklist/external_generator_output_checklist.csv |
| summary_path | artifacts/trail/generation/external_generator_output_checklist/external_generator_output_checklist_summary.json |
| report_path | reports/external_generator_output_checklist.md |

## Provider Rows

| rank | provider task | strategy | status | can submit | current pass rows |
| ---: | --- | --- | --- | --- | ---: |
| 1 | external_llm_rag_principle_generation | llm_rag_principle_generation | ready_for_external_provider_output | True | 2 |
| 2 | external_sft_finetune_generation | sft_candidate_generator | ready_for_external_provider_output | True | 23 |
| 3 | external_diffusion_flow_decoder_generation | diffusion_or_flow_matching | ready_for_external_provider_output | True | 23 |
| 4 | external_llm_free_smiles_generation | llm_smiles_generation | suppressed_pending_predictor_and_chemistry_evidence | False | 0 |

## Gate

- 外部生成器只能提交 generation record rows，不能直接推荐配方。
- 所有输出必须继续经过 predictor、Harness、PiEvo IDS 和人工审核。
- `creates_observation=false` 表示这一步不是实验结果，也不会进入 active high-authority evidence ledger。

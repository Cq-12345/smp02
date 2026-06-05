# Generative Model Training Set Readiness

本文档回应 TODO 中“LLM 微调 SFT、扩散生成、流匹配”的生成模型后续要求。当前仍只使用单一小分子 SMILES / MoleCode，不进入暂缓的商品级组分或聚合物超图表示。

## Outputs

- SFT JSONL: `artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl`
- Diffusion/flow seed table: `artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv`
- Summary: `artifacts/trail/generation/generative_training_sets/generative_training_summary.json`

## Summary

| item | value |
| --- | ---: |
| input_rows | 1165 |
| harness_pass_rows | 177 |
| training_candidate_rows | 143 |
| sft_examples | 143 |
| sft_train_examples | 124 |
| sft_eval_examples | 19 |
| sft_ready | True |
| diffusion_flow_seed_rows | 143 |
| diffusion_flow_train_rows | 124 |
| diffusion_flow_eval_rows | 19 |
| diffusion_flow_ready | True |
| next_data_needed_for_sft | 0 |
| next_data_needed_for_diffusion_flow | 0 |

## Strategy Counts

| strategy | records |
| --- | ---: |
| rule_template | 50 |
| functional_group_replacement | 47 |
| vae_latent_local_search | 42 |
| llm_rag_principle_generation | 4 |

## Interpretation

- SFT JSONL 只使用已经通过 generation record/Harness 的 records；draft 或缺 predictor/chemistry evidence 的样本不会进入训练目标。
- Diffusion/flow seed table 是未来条件生成模型的数据契约，记录目标 Tg、SMILES、比例、预测 Tg、reward 和 compatibility evidence；本轮不训练扩散/流匹配模型。
- readiness gate 的作用是阻止在样本过少时训练一个看似可用但不可泛化的生成模型；若某个 gate 已通过，仍必须在训练后让新候选重新经过 predictor/Harness/PiEvo。
- 未通过的 gate 继续要求更多通过 Harness 且最好被 observation ledger 验证的 records。

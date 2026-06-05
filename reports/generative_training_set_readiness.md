# Generative Model Training Set Readiness

本文档回应 TODO 中“LLM 微调 SFT、扩散生成、流匹配”的生成模型后续要求。当前仍只使用单一小分子 SMILES / MoleCode，不进入暂缓的商品级组分或聚合物超图表示。

## Outputs

- SFT JSONL: `artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl`
- Diffusion/flow seed table: `artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv`
- Summary: `artifacts/trail/generation/generative_training_sets/generative_training_summary.json`

## Summary

| item | value |
| --- | ---: |
| input_rows | 8 |
| harness_pass_rows | 7 |
| training_candidate_rows | 5 |
| sft_examples | 5 |
| sft_train_examples | 4 |
| sft_eval_examples | 1 |
| sft_ready | False |
| diffusion_flow_seed_rows | 5 |
| diffusion_flow_train_rows | 4 |
| diffusion_flow_eval_rows | 1 |
| diffusion_flow_ready | False |
| next_data_needed_for_sft | 15 |
| next_data_needed_for_diffusion_flow | 95 |

## Strategy Counts

| strategy | records |
| --- | ---: |
| llm_rag_principle_generation | 4 |
| functional_group_replacement | 1 |

## Interpretation

- SFT JSONL 只使用已经通过 generation record/Harness 的 records；draft 或缺 predictor/chemistry evidence 的样本不会进入训练目标。
- Diffusion/flow seed table 是未来条件生成模型的数据契约，记录目标 Tg、SMILES、比例、预测 Tg、reward 和 compatibility evidence；本轮不训练扩散/流匹配模型。
- readiness gate 的作用是阻止在样本过少时训练一个看似可用但不可泛化的生成模型。
- 当前结果如果显示 `sft_ready=false` 或 `diffusion_flow_ready=false`，含义是训练数据契约已落地，但还需要更多通过 Harness 且最好被 observation ledger 验证的 records。

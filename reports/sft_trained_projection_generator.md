# Supervised SFT Projection Generator Smoke

本文档把 SFT 从 prototype replay dry-run 推进一步：在 SFT generation record 的结构化特征空间训练一个轻量监督 MLP，再把模型输出投影回最近的 validated train-split record，并写入 `sft_candidate_generator` generation ledger。

这不是外部 LLM 微调，也不是自由 SMILES 生成；它验证的是 SFT 语料、神经权重训练、结构化投影、Harness 和策略回流链路。

## 输出文件

- Input records: `artifacts/trail/generation/sft_trained_projection_generator/sft_projection_generation_records_input.csv`
- Ledger: `artifacts/trail/generation/sft_trained_projection_generator/generation_record_ledger.csv`
- Projection table: `artifacts/trail/generation/sft_trained_projection_generator/nearest_sft_record_projection.csv`
- Training metrics: `artifacts/trail/generation/sft_trained_projection_generator/sft_projection_training_summary.json`
- Model: `artifacts/trail/generation/sft_trained_projection_generator/sft_record_projection_model.pt`
- Report: `reports/sft_trained_projection_generator.md`

## Summary

| item | value |
| --- | ---: |
| input_rows | 23 |
| record_pass_rows | 23 |
| ready_for_prediction_rows | 0 |
| harness_pass_rows | 23 |
| harness_fail_rows | 0 |
| best_distance_c | 0.0031802513673540034 |
| mean_generation_reward | 0.9564690371891499 |
| reward_temperature_c | 5.0 |
| generator_mode | supervised_neural_sft_projection |
| sft_jsonl | artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl |
| train_examples | 124 |
| eval_examples | 19 |
| condition_dim | 11 |
| output_dim | 40 |
| hidden_dim | 64 |
| epochs | 120 |
| batch_size | 64 |
| learning_rate | 0.001 |
| condition_noise_std | 0.05 |
| generated_continuous_outputs | 184 |
| projected_records | 23 |
| projection_pool_rows | 107 |
| projection_distance_mean | 3.5848927912504776 |
| projection_distance_min | 2.6975746154785156 |
| projection_distance_max | 4.689859390258789 |
| train_loss_initial | 0.8800587058067322 |
| train_loss_final | 0.6180704832077026 |
| eval_loss_final | 0.8099173903465271 |
| model_path | artifacts/trail/generation/sft_trained_projection_generator/sft_record_projection_model.pt |
| scaler_path | artifacts/trail/generation/sft_trained_projection_generator/sft_projection_scaler.json |
| projection_path | artifacts/trail/generation/sft_trained_projection_generator/nearest_sft_record_projection.csv |
| generated_records | 23 |
| heldout_exact_candidate_matches | 1 |
| heldout_eval_rows | 19 |
| input_records_path | artifacts/trail/generation/sft_trained_projection_generator/sft_projection_generation_records_input.csv |
| generation_record_ledger_path | artifacts/trail/generation/sft_trained_projection_generator/generation_record_ledger.csv |
| heldout_eval_retrieval_path | artifacts/trail/generation/sft_trained_projection_generator/heldout_eval_retrieval.csv |

## 解释

- 训练输入是 SFT prompt/source 条件特征；训练输出是候选配方的 formulation global features、预测 Tg、reward 和来源策略特征。
- 连续模型输出不会直接被当成配方；必须投影到最近 validated train-split record，随后重新经过 generation record importer 和 Harness。
- 该 smoke 验证的是有权重更新的 SFT-style 训练链路，不证明 LLM 已完成微调，也不证明模型能分布外创造新 SMILES。

# Conditional Flow-Matching Generator Smoke

本文档把 diffusion/flow 从 seed replay dry-run 推进一步：在 formulation global feature 空间训练一个轻量条件 flow-matching MLP，然后把连续生成点投影回最近的 validated seed row 并写入 `diffusion_or_flow_matching` generation ledger。

这仍不是直接 SMILES 扩散生成；它是小分子 SMILES/MoleCode 范围内的训练型原型，用来验证权重训练、采样、离散投影、Harness 和策略回流链路。

## 输出文件

- Input records: `artifacts/trail/generation/diffusion_flow_trained_generator/flow_matching_generation_records_input.csv`
- Ledger: `artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_ledger.csv`
- Projection table: `artifacts/trail/generation/diffusion_flow_trained_generator/nearest_seed_projection.csv`
- Training metrics: `artifacts/trail/generation/diffusion_flow_trained_generator/flow_matching_training_summary.json`
- Model: `artifacts/trail/generation/diffusion_flow_trained_generator/conditional_flow_matching_model.pt`
- Report: `reports/diffusion_flow_trained_generator.md`

## Summary

| item | value |
| --- | ---: |
| input_rows | 23 |
| record_pass_rows | 23 |
| ready_for_prediction_rows | 0 |
| harness_pass_rows | 23 |
| harness_fail_rows | 0 |
| best_distance_c | 0.0031802513673540034 |
| mean_generation_reward | 0.8644566894747596 |
| reward_temperature_c | 5.0 |
| generator_mode | conditional_flow_matching_trained_projection |
| seed_table | artifacts/trail/generation/generative_training_sets/diffusion_flow_seed_table.csv |
| train_seed_rows | 192 |
| eval_seed_rows | 35 |
| feature_dim | 31 |
| hidden_dim | 64 |
| epochs | 120 |
| batch_size | 64 |
| learning_rate | 0.001 |
| integration_steps | 24 |
| generated_continuous_samples | 184 |
| projected_records | 23 |
| projection_pool_rows | 139 |
| projection_distance_mean | 4.6286066407742705 |
| projection_distance_min | 3.1989145278930664 |
| projection_distance_max | 6.26177978515625 |
| train_loss_initial | 1.8595678408940632 |
| train_loss_final | 1.2820241451263428 |
| eval_loss_final | 1.501653790473938 |
| model_path | artifacts/trail/generation/diffusion_flow_trained_generator/conditional_flow_matching_model.pt |
| scaler_path | artifacts/trail/generation/diffusion_flow_trained_generator/flow_matching_scaler.json |
| projection_path | artifacts/trail/generation/diffusion_flow_trained_generator/nearest_seed_projection.csv |
| input_records_path | artifacts/trail/generation/diffusion_flow_trained_generator/flow_matching_generation_records_input.csv |
| generation_record_ledger_path | artifacts/trail/generation/diffusion_flow_trained_generator/generation_record_ledger.csv |

## 解释

- flow-matching 训练目标是预测从 Gaussian noise 到 formulation global feature 的 velocity，并以目标 Tg 作为条件。
- 连续生成点不会直接被当成配方；必须投影到最近 validated seed row，随后重新经过 generation record importer 和 Harness。
- 该 smoke 验证的是训练与审计链路，不证明神经 flow 已能产生分布外新 SMILES。后续若要取消 nearest-seed projection，必须新增 SMILES decoder、predictor 和 Harness 复评。

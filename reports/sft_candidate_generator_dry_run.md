# SFT Candidate Generator Dry Run

本文档把已经通过 readiness gate 的 SFT JSONL 推进一步：用 train split 中的 validated generation records 做一个可复现的 prototype-replay dry-run，并重新写入 `sft_candidate_generator` generation ledger。

这不是神经网络权重微调完成，也不是外部 LLM 输出；它的作用是验证 SFT 生成器激活后的审计链、Harness 门禁和策略回流接口。

## 输出文件

- Input records: `artifacts/trail/generation/sft_candidate_dry_run/sft_candidate_records_input.csv`
- Ledger: `artifacts/trail/generation/sft_candidate_dry_run/generation_record_ledger.csv`
- Summary: `artifacts/trail/generation/sft_candidate_dry_run/generation_record_summary.json`
- Heldout eval table: `artifacts/trail/generation/sft_candidate_dry_run/heldout_eval_retrieval.csv`
- Report: `reports/sft_candidate_generator_dry_run.md`

## Summary

| item | value |
| --- | ---: |
| input_rows | 25 |
| record_pass_rows | 25 |
| ready_for_prediction_rows | 0 |
| harness_pass_rows | 25 |
| harness_fail_rows | 0 |
| best_distance_c | 0.0031802513673540034 |
| mean_generation_reward | 0.9921940687487707 |
| reward_temperature_c | 5.0 |
| generator_mode | prototype_replay_not_weight_update |
| sft_jsonl | artifacts/trail/generation/generative_training_sets/sft_generation_records.jsonl |
| train_examples | 192 |
| eval_examples | 35 |
| generated_records | 25 |
| heldout_exact_candidate_matches | 0 |
| heldout_eval_rows | 35 |
| input_records_path | artifacts/trail/generation/sft_candidate_dry_run/sft_candidate_records_input.csv |
| generation_record_ledger_path | artifacts/trail/generation/sft_candidate_dry_run/generation_record_ledger.csv |
| heldout_eval_retrieval_path | artifacts/trail/generation/sft_candidate_dry_run/heldout_eval_retrieval.csv |

## 解释

- `sft_candidate_generator` 的输出仍然必须满足 generation record schema、RDKit、ratio、prediction、target 和 chemistry evidence。
- dry-run 只复用 validated train-split prototypes，因此可以验证链路，但不能证明模型已经学会分布外生成。
- 后续若真正训练 LLM/SFT 权重，应把模型输出写入同一 ledger，并和本 dry-run 的 Harness pass、target distance、重复率做对比。
